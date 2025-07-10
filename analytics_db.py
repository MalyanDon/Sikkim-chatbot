import sqlite3
import csv
import pandas as pd
import datetime
import json
import os
from typing import Dict, List, Optional

class AnalyticsDatabase:
    """
    Comprehensive analytics and conversation tracking database for SajiloSewa Chatbot
    """
    
    def __init__(self, db_path: str = "sajilosewa_chatbot_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all required tables for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Complete conversation tracking - EVERY message
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                message TEXT NOT NULL,
                bot_response TEXT,
                language TEXT,
                intent TEXT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER,
                was_cached BOOLEAN DEFAULT FALSE,
                user_location TEXT,
                platform TEXT DEFAULT 'telegram'
            )
        ''')
        
        # 2. Application status checks - separate tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                application_id TEXT NOT NULL,
                applicant_name TEXT,
                village TEXT,
                status TEXT,
                amount INTEGER,
                check_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                language TEXT
            )
        ''')
        
        # 3. User sessions - track user engagement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_end DATETIME,
                total_messages INTEGER DEFAULT 0,
                languages_used TEXT,
                intents_triggered TEXT,
                session_duration_minutes INTEGER,
                completed_tasks TEXT
            )
        ''')
        
        # 4. Bot performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_messages INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                cache_hit_rate REAL DEFAULT 0.0,
                avg_response_time_ms REAL DEFAULT 0.0,
                language_distribution TEXT,
                intent_distribution TEXT,
                error_count INTEGER DEFAULT 0,
                peak_hour INTEGER,
                total_status_checks INTEGER DEFAULT 0
            )
        ''')
        
        # 5. Error tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT,
                stack_trace TEXT,
                user_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # 6. Popular queries and responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS popular_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                normalized_query TEXT,
                intent TEXT,
                language TEXT,
                frequency INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 100.0,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Analytics database initialized successfully")
    
    def log_conversation(self, user_id: str, username: str, message: str, 
                        bot_response: str, language: str, intent: str, 
                        response_time_ms: int = 0, was_cached: bool = False,
                        session_id: str = None):
        """Log every single conversation - even simple greetings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (user_id, username, message, bot_response, language, intent, 
             session_id, response_time_ms, was_cached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, message, bot_response, language, intent,
              session_id, response_time_ms, was_cached))
        
        conn.commit()
        conn.close()
    
    def log_status_check(self, user_id: str, username: str, application_id: str,
                        applicant_name: str, village: str, status: str, 
                        amount: int, language: str):
        """Separate tracking for application status checks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO status_checks 
            (user_id, username, application_id, applicant_name, village, 
             status, amount, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, application_id, applicant_name, village,
              status, amount, language))
        
        conn.commit()
        conn.close()
    
    def start_user_session(self, user_id: str, username: str):
        """Start tracking a user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # End any existing open session for this user
        cursor.execute('''
            UPDATE user_sessions 
            SET session_end = CURRENT_TIMESTAMP,
                session_duration_minutes = 
                    CAST((julianday(CURRENT_TIMESTAMP) - julianday(session_start)) * 1440 AS INTEGER)
            WHERE user_id = ? AND session_end IS NULL
        ''', (user_id,))
        
        # Start new session
        cursor.execute('''
            INSERT INTO user_sessions (user_id, username)
            VALUES (?, ?)
        ''', (user_id, username))
        
        conn.commit()
        conn.close()
    
    def update_session_activity(self, user_id: str, language: str, intent: str):
        """Update current session with activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET total_messages = total_messages + 1,
                languages_used = COALESCE(languages_used || ',' || ?, ?),
                intents_triggered = COALESCE(intents_triggered || ',' || ?, ?)
            WHERE user_id = ? AND session_end IS NULL
        ''', (language, language, intent, intent, user_id))
        
        conn.commit()
        conn.close()
    
    def log_error(self, user_id: str, error_type: str, error_message: str,
                  stack_trace: str = None, user_message: str = None):
        """Log errors for debugging and improvement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs 
            (user_id, error_type, error_message, stack_trace, user_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, error_type, error_message, stack_trace, user_message))
        
        conn.commit()
        conn.close()
    
    def update_popular_query(self, query_text: str, intent: str, language: str):
        """Track popular queries for optimization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Normalize query (basic cleanup)
        normalized = query_text.lower().strip()
        
        # Check if query exists
        cursor.execute('''
            SELECT id, frequency FROM popular_queries 
            WHERE normalized_query = ? AND intent = ? AND language = ?
        ''', (normalized, intent, language))
        
        result = cursor.fetchone()
        
        if result:
            # Update frequency
            cursor.execute('''
                UPDATE popular_queries 
                SET frequency = frequency + 1, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (result[0],))
        else:
            # Insert new query
            cursor.execute('''
                INSERT INTO popular_queries 
                (query_text, normalized_query, intent, language)
                VALUES (?, ?, ?, ?)
            ''', (query_text, normalized, intent, language))
        
        conn.commit()
        conn.close()
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """Get comprehensive daily statistics"""
        if not date:
            date = datetime.date.today().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total messages today
        cursor.execute('''
            SELECT COUNT(*) FROM conversations 
            WHERE DATE(timestamp) = ?
        ''', (date,))
        stats['total_messages'] = cursor.fetchone()[0]
        
        # Unique users today
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM conversations 
            WHERE DATE(timestamp) = ?
        ''', (date,))
        stats['unique_users'] = cursor.fetchone()[0]
        
        # Language distribution
        cursor.execute('''
            SELECT language, COUNT(*) FROM conversations 
            WHERE DATE(timestamp) = ?
            GROUP BY language
        ''', (date,))
        stats['language_distribution'] = dict(cursor.fetchall())
        
        # Intent distribution
        cursor.execute('''
            SELECT intent, COUNT(*) FROM conversations 
            WHERE DATE(timestamp) = ?
            GROUP BY intent
        ''', (date,))
        stats['intent_distribution'] = dict(cursor.fetchall())
        
        # Status checks today
        cursor.execute('''
            SELECT COUNT(*) FROM status_checks 
            WHERE DATE(check_timestamp) = ?
        ''', (date,))
        stats['status_checks'] = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute('''
            SELECT AVG(response_time_ms) FROM conversations 
            WHERE DATE(timestamp) = ? AND response_time_ms > 0
        ''', (date,))
        result = cursor.fetchone()[0]
        stats['avg_response_time_ms'] = result if result else 0
        
        # Cache hit rate
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN was_cached THEN 1 ELSE 0 END) * 100.0 / COUNT(*) 
            FROM conversations 
            WHERE DATE(timestamp) = ?
        ''', (date,))
        result = cursor.fetchone()[0]
        stats['cache_hit_rate'] = result if result else 0
        
        conn.close()
        return stats
    
    def get_user_journey(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get complete user conversation journey"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT timestamp, message, bot_response, language, intent, was_cached
            FROM conversations 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', conn, params=(user_id, limit))
        
        conn.close()
        return df.to_dict('records')
    
    def get_popular_queries(self, language: str = None, limit: int = 20) -> List[Dict]:
        """Get most popular user queries"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT query_text, intent, language, frequency, last_used
            FROM popular_queries 
        '''
        params = []
        
        if language:
            query += ' WHERE language = ?'
            params.append(language)
        
        query += ' ORDER BY frequency DESC LIMIT ?'
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df.to_dict('records')
    
    def export_to_csv(self, table_name: str, output_file: str):
        """Export any table to CSV for analysis"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
        df.to_csv(output_file, index=False)
        
        conn.close()
        print(f"✅ Exported {table_name} to {output_file}")
    
    def generate_weekly_report(self) -> Dict:
        """Generate comprehensive weekly analytics report"""
        conn = sqlite3.connect(self.db_path)
        
        # Get date range (last 7 days)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        
        report = {
            'report_period': f"{start_date} to {end_date}",
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        # Weekly totals
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM conversations 
            WHERE DATE(timestamp) BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        totals = cursor.fetchone()
        report['totals'] = {
            'messages': totals[0],
            'unique_users': totals[1], 
            'active_days': totals[2]
        }
        
        # Daily breakdown
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as messages,
                COUNT(DISTINCT user_id) as users
            FROM conversations 
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (start_date, end_date))
        
        report['daily_breakdown'] = [
            {'date': row[0], 'messages': row[1], 'users': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Top intents
        cursor.execute('''
            SELECT intent, COUNT(*) as frequency
            FROM conversations 
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY intent
            ORDER BY frequency DESC
            LIMIT 10
        ''', (start_date, end_date))
        
        report['top_intents'] = [
            {'intent': row[0], 'frequency': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Status checks
        cursor.execute('''
            SELECT COUNT(*) FROM status_checks 
            WHERE DATE(check_timestamp) BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        report['status_checks'] = cursor.fetchone()[0]
        
        conn.close()
        return report
    
    def save_report_to_file(self, report: Dict, filename: str = None):
        """Save analytics report to JSON file"""
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sajilosewa_bot_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analytics report saved to {filename}")
        return filename

# Utility functions for dashboard
class DashboardGenerator:
    """Generate HTML dashboard for analytics"""
    
    def __init__(self, analytics_db: AnalyticsDatabase):
        self.db = analytics_db
    
    def generate_dashboard_html(self) -> str:
        """Generate a simple HTML dashboard"""
        stats = self.db.get_daily_stats()
        popular_queries = self.db.get_popular_queries(limit=10)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SajiloSewa Chatbot Analytics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .card {{ border: 1px solid #ddd; padding: 20px; margin: 10px; border-radius: 8px; }}
        .metric {{ font-size: 2em; color: #2196F3; }}
        .chart {{ width: 100%; height: 300px; border: 1px solid #eee; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>📊 Sikkim Chatbot Analytics Dashboard</h1>
    <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="card">
        <h2>📈 Today's Metrics</h2>
        <div style="display: flex; justify-content: space-around;">
            <div>
                <div class="metric">{stats['total_messages']}</div>
                <div>Total Messages</div>
            </div>
            <div>
                <div class="metric">{stats['unique_users']}</div>
                <div>Unique Users</div>
            </div>
            <div>
                <div class="metric">{stats['status_checks']}</div>
                <div>Status Checks</div>
            </div>
            <div>
                <div class="metric">{stats['cache_hit_rate']:.1f}%</div>
                <div>Cache Hit Rate</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>🗣️ Language Distribution</h2>
        <table>
            <tr><th>Language</th><th>Messages</th></tr>
            {''.join([f"<tr><td>{lang}</td><td>{count}</td></tr>" 
                     for lang, count in stats['language_distribution'].items()])}
        </table>
    </div>
    
    <div class="card">
        <h2>🎯 Intent Distribution</h2>
        <table>
            <tr><th>Intent</th><th>Frequency</th></tr>
            {''.join([f"<tr><td>{intent}</td><td>{count}</td></tr>" 
                     for intent, count in stats['intent_distribution'].items()])}
        </table>
    </div>
    
    <div class="card">
        <h2>🔥 Popular Queries</h2>
        <table>
            <tr><th>Query</th><th>Intent</th><th>Language</th><th>Frequency</th></tr>
            {''.join([f"<tr><td>{q['query_text']}</td><td>{q['intent']}</td><td>{q['language']}</td><td>{q['frequency']}</td></tr>" 
                     for q in popular_queries])}
        </table>
    </div>
    
    <div class="card">
        <h2>⚡ Performance</h2>
        <p><strong>Average Response Time:</strong> {stats['avg_response_time_ms']:.0f}ms</p>
        <p><strong>Cache Hit Rate:</strong> {stats['cache_hit_rate']:.1f}%</p>
    </div>
</body>
</html>
        """
        
        return html
    
    def save_dashboard(self, filename: str = None) -> str:
        """Save dashboard to HTML file"""
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sajilosewa_bot_dashboard_{timestamp}.html"
        
        html = self.generate_dashboard_html()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Dashboard saved to {filename}")
        return filename 
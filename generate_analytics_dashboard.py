#!/usr/bin/env python3
"""
Analytics Dashboard Generator for Sikkim Chatbot
Generates comprehensive reports and HTML dashboard
"""

import sys
import os
import datetime
import json
from analytics_db import AnalyticsDatabase, DashboardGenerator

def main():
    """Main function to generate analytics dashboard and reports"""
    
    print("🎯 Sikkim Chatbot Analytics Dashboard Generator")
    print("=" * 60)
    
    # Initialize analytics database
    analytics_db = AnalyticsDatabase()
    dashboard_gen = DashboardGenerator(analytics_db)
    
    # Get current date
    today = datetime.date.today()
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"📊 Generating analytics for {today}")
    
    # 1. Generate daily statistics
    print("\n1️⃣ Generating Daily Statistics...")
    daily_stats = analytics_db.get_daily_stats()
    
    print(f"   📈 Total Messages Today: {daily_stats['total_messages']}")
    print(f"   👥 Unique Users Today: {daily_stats['unique_users']}")
    print(f"   🔍 Status Checks: {daily_stats['status_checks']}")
    print(f"   ⚡ Avg Response Time: {daily_stats['avg_response_time_ms']:.0f}ms")
    print(f"   💾 Cache Hit Rate: {daily_stats['cache_hit_rate']:.1f}%")
    
    # 2. Generate weekly report
    print("\n2️⃣ Generating Weekly Report...")
    weekly_report = analytics_db.generate_weekly_report()
    report_file = analytics_db.save_report_to_file(weekly_report, f"weekly_report_{timestamp}.json")
    print(f"   ✅ Weekly report saved: {report_file}")
    
    # 3. Generate HTML Dashboard
    print("\n3️⃣ Generating HTML Dashboard...")
    dashboard_file = dashboard_gen.save_dashboard(f"sikkim_dashboard_{timestamp}.html")
    print(f"   ✅ Dashboard saved: {dashboard_file}")
    
    # 4. Export CSV files for detailed analysis
    print("\n4️⃣ Exporting CSV Files...")
    
    export_files = [
        ("conversations", f"conversations_export_{timestamp}.csv"),
        ("status_checks", f"status_checks_export_{timestamp}.csv"),
        ("user_sessions", f"user_sessions_export_{timestamp}.csv"),
        ("popular_queries", f"popular_queries_export_{timestamp}.csv")
    ]
    
    for table_name, filename in export_files:
        try:
            analytics_db.export_to_csv(table_name, filename)
            print(f"   ✅ Exported {table_name}: {filename}")
        except Exception as e:
            print(f"   ❌ Error exporting {table_name}: {e}")
    
    # 5. Show popular queries
    print("\n5️⃣ Popular Queries Analysis...")
    popular_queries = analytics_db.get_popular_queries(limit=10)
    
    if popular_queries:
        print("   🔥 Top 10 Popular Queries:")
        for i, query in enumerate(popular_queries, 1):
            print(f"   {i:2d}. {query['query_text'][:50]}... (Intent: {query['intent']}, Freq: {query['frequency']})")
    else:
        print("   📝 No popular queries data available yet")
    
    # 6. Language distribution
    if daily_stats['language_distribution']:
        print("\n6️⃣ Language Distribution Today:")
        for lang, count in daily_stats['language_distribution'].items():
            percentage = (count / daily_stats['total_messages']) * 100 if daily_stats['total_messages'] > 0 else 0
            print(f"   🗣️ {lang.upper()}: {count} messages ({percentage:.1f}%)")
    
    # 7. Intent distribution
    if daily_stats['intent_distribution']:
        print("\n7️⃣ Intent Distribution Today:")
        for intent, count in daily_stats['intent_distribution'].items():
            percentage = (count / daily_stats['total_messages']) * 100 if daily_stats['total_messages'] > 0 else 0
            print(f"   🎯 {intent}: {count} times ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ Analytics Generation Complete!")
    print(f"📁 Files generated in current directory")
    print(f"📈 Open {dashboard_file} in browser to view dashboard")
    print(f"📊 Check {report_file} for detailed JSON report")
    
    # 8. Generate performance summary
    print("\n📋 Performance Summary:")
    if daily_stats['total_messages'] > 0:
        print(f"   🚀 Bot handled {daily_stats['total_messages']} messages today")
        print(f"   👤 Served {daily_stats['unique_users']} unique users")
        print(f"   🎯 Processed {daily_stats['status_checks']} status checks")
        
        if daily_stats['cache_hit_rate'] > 50:
            print(f"   ✅ Good cache performance: {daily_stats['cache_hit_rate']:.1f}% hit rate")
        else:
            print(f"   ⚠️ Cache could be improved: {daily_stats['cache_hit_rate']:.1f}% hit rate")
            
        if daily_stats['avg_response_time_ms'] < 1000:
            print(f"   ⚡ Excellent response time: {daily_stats['avg_response_time_ms']:.0f}ms")
        elif daily_stats['avg_response_time_ms'] < 3000:
            print(f"   ✅ Good response time: {daily_stats['avg_response_time_ms']:.0f}ms")
        else:
            print(f"   ⚠️ Response time could be improved: {daily_stats['avg_response_time_ms']:.0f}ms")
    else:
        print("   📝 No activity today - bot may not be receiving messages")

def show_user_journey(user_id: str = None):
    """Show detailed user journey for analysis"""
    if not user_id:
        print("Usage: python generate_analytics_dashboard.py --user <user_id>")
        return
    
    analytics_db = AnalyticsDatabase()
    journey = analytics_db.get_user_journey(user_id, limit=20)
    
    print(f"\n👤 User Journey for {user_id}")
    print("=" * 50)
    
    if journey:
        for i, step in enumerate(journey, 1):
            print(f"{i:2d}. [{step['timestamp']}] {step['language'].upper()}")
            print(f"    User: {step['message'][:60]}...")
            print(f"    Bot:  {step['bot_response'][:60]}...")
            print(f"    Intent: {step['intent']} | Cached: {step['was_cached']}")
            print()
    else:
        print(f"No conversation history found for user {user_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--user":
        if len(sys.argv) > 2:
            show_user_journey(sys.argv[2])
        else:
            show_user_journey()
    else:
        main() 
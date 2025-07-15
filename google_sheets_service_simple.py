#!/usr/bin/env python3
"""
Simplified Google Sheets Integration Service for SmartGov Bot
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class SimpleGoogleSheetsService:
    """Simplified service class for Google Sheets operations"""
    
    def __init__(self, api_key: str, spreadsheet_id: str, service_account_email: str):
        """Initialize Google Sheets service with API key and service account email"""
        self.api_key = api_key
        self.spreadsheet_id = spreadsheet_id
        self.service_account_email = service_account_email
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using API key"""
        try:
            self.service = build('sheets', 'v4', developerKey=self.api_key)
            logger.info("✅ Google Sheets API authenticated successfully with API key")
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {str(e)}")
    
    def create_sheet_if_not_exists(self, sheet_name: str, headers: List[str]) -> bool:
        """Create a new sheet if it doesn't exist"""
        try:
            # Check if sheet exists
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name not in sheet_names:
                # Create new sheet
                request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
                # Add headers
                self.append_row(sheet_name, headers)
                logger.info(f"✅ Created new sheet: {sheet_name}")
                return True
            else:
                logger.info(f"✅ Sheet already exists: {sheet_name}")
                return True
                
        except HttpError as error:
            logger.error(f"❌ Error creating sheet {sheet_name}: {error}")
            return False
    
    def append_row(self, sheet_name: str, row_data: List[Any]) -> bool:
        """Append a row to the specified sheet"""
        try:
            range_name = f"{sheet_name}!A:Z"
            
            body = {
                'values': [row_data]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Row appended to {sheet_name}: {len(result.get('updates', {}).get('updatedRows', 0))} rows")
            return True
            
        except HttpError as error:
            logger.error(f"❌ Error appending row to {sheet_name}: {error}")
            return False
    
    def log_complaint(self, user_id: int, user_name: str, complaint_text: str, 
                     complaint_type: str, language: str, status: str = "New") -> bool:
        """Log a complaint to the complaints sheet"""
        if not self.service:
            logger.error("❌ Google Sheets service not initialized")
            return False
        
        sheet_name = "Complaints"
        headers = [
            "Timestamp", "User ID", "User Name", "Complaint Type", 
            "Complaint Text", "Language", "Status", "Date"
        ]
        
        # Create sheet if not exists
        if not self.create_sheet_if_not_exists(sheet_name, headers):
            return False
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        row_data = [
            timestamp,
            user_id,
            user_name,
            complaint_type,
            complaint_text,
            language,
            status,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_emergency_service(self, user_id: int, user_name: str, service_type: str,
                            query_text: str, language: str, result: str) -> bool:
        """Log an emergency service query to the emergency services sheet"""
        if not self.service:
            logger.error("❌ Google Sheets service not initialized")
            return False
        
        sheet_name = "Emergency_Services"
        headers = [
            "Timestamp", "User ID", "User Name", "Service Type", "Query Text",
            "Language", "Result", "Date"
        ]
        
        # Create sheet if not exists
        if not self.create_sheet_if_not_exists(sheet_name, headers):
            return False
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        row_data = [
            timestamp,
            user_id,
            user_name,
            service_type,
            query_text,
            language,
            result,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_homestay_query(self, user_id: int, user_name: str, place: str, 
                          query_text: str, language: str, result: str) -> bool:
        """Log a homestay query to the homestay queries sheet"""
        if not self.service:
            logger.error("❌ Google Sheets service not initialized")
            return False
        
        sheet_name = "Homestay_Queries"
        headers = [
            "Timestamp", "User ID", "User Name", "Place", "Query Text",
            "Language", "Result", "Date"
        ]
        
        # Create sheet if not exists
        if not self.create_sheet_if_not_exists(sheet_name, headers):
            return False
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        row_data = [
            timestamp,
            user_id,
            user_name,
            place,
            query_text,
            language,
            result,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_general_interaction(self, user_id: int, user_name: str, interaction_type: str,
                              query_text: str, language: str, bot_response: str) -> bool:
        """Log general bot interactions"""
        if not self.service:
            logger.error("❌ Google Sheets service not initialized")
            return False
        
        sheet_name = "General_Interactions"
        headers = [
            "Timestamp", "User ID", "User Name", "Interaction Type", "Query Text",
            "Language", "Bot Response", "Date"
        ]
        
        # Create sheet if not exists
        if not self.create_sheet_if_not_exists(sheet_name, headers):
            return False
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        row_data = [
            timestamp,
            user_id,
            user_name,
            interaction_type,
            query_text,
            language,
            bot_response,
            date
        ]
        
        return self.append_row(sheet_name, row_data) 
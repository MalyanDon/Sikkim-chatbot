#!/usr/bin/env python3
"""
Google Sheets Integration Service for SmartGov Bot
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service class for Google Sheets operations"""
    
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """Initialize Google Sheets service with credentials file"""
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            from google.oauth2 import service_account
            
            if not os.path.exists(self.credentials_file):
                logger.error(f"Credentials file not found: {self.credentials_file}")
                logger.info("Please download credentials.json from Google Cloud Console")
                return
            
            # Use service account credentials
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.SCOPES)
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info(" Google Sheets API authenticated successfully with service account")
        except Exception as e:
            logger.error(f" Google Sheets authentication failed: {str(e)}")
    
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
                logger.info(f" Created new sheet: {sheet_name}")
                return True
            else:
                logger.info(f" Sheet already exists: {sheet_name}")
                return True
                
        except HttpError as error:
            logger.error(f" Error creating sheet {sheet_name}: {error}")
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
            
            updated_rows = result.get('updates', {}).get('updatedRows', 0)
            logger.info(f" Row appended to {sheet_name}: {updated_rows} rows")
            return True
            
        except HttpError as error:
            logger.error(f" Error appending row to {sheet_name}: {error}")
            return False
    
    def log_complaint(self, user_id: int, user_name: str, complaint_text: str, 
                     complaint_type: str, language: str, status: str = "New") -> bool:
        """Log a complaint to the complaints sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
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
    
    def log_certificate_query(self, user_id: int, user_name: str, query_text: str,
                            certificate_type: str, language: str, result: str) -> bool:
        """Log a certificate query to the certificate queries sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Certificate_Queries"
        headers = [
            "Timestamp", "User ID", "User Name", "Certificate Type",
            "Query Text", "Language", "Result", "Date"
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
            certificate_type,
            query_text,
            language,
            result,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_ex_gratia_application(self, user_id: int, user_name: str, application_data: Dict[str, Any],
                                 language: str, status: str = "Submitted") -> bool:
        """Log an ex-gratia application to the applications sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Ex_Gratia_Applications"
        headers = [
            "Timestamp", "User ID", "User Name", "Full Name", "Phone", "Address",
            "Damage Type", "Damage Description", "Language", "Status", "Date"
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
            application_data.get('name', ''),
            application_data.get('phone', ''),
            application_data.get('address', ''),
            application_data.get('damage_type', ''),
            application_data.get('damage_description', ''),
            language,
            status,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_status_check(self, user_id: int, user_name: str, application_id: str,
                        status_result: str, language: str) -> bool:
        """Log a status check to the status checks sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Status_Checks"
        headers = [
            "Timestamp", "User ID", "User Name", "Application ID",
            "Status Result", "Language", "Date"
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
            application_id,
            status_result,
            language,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def get_sheet_data(self, sheet_name: str, range_name: str = None) -> Optional[List[List[Any]]]:
        """Get data from a sheet"""
        try:
            if not range_name:
                range_name = f"{sheet_name}!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except HttpError as error:
            logger.error(f" Error getting data from {sheet_name}: {error}")
            return None
    
    def log_homestay_query(self, user_id: int, user_name: str, place: str, 
                          query_text: str, language: str, result: str) -> bool:
        """Log a homestay query to the homestay queries sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
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
    
    def log_emergency_service(self, user_id: int, user_name: str, service_type: str,
                            query_text: str, language: str, result: str) -> bool:
        """Log an emergency service query to the emergency services sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
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
    
    def log_cab_booking_query(self, user_id: int, user_name: str, destination: str,
                             query_text: str, language: str, result: str) -> bool:
        """Log a cab booking query to the cab booking sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Cab_Booking_Queries"
        headers = [
            "Timestamp", "User ID", "User Name", "Destination", "Query Text",
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
            destination,
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
            logger.error(" Google Sheets service not initialized")
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
    
    def log_scheme_application(self, user_id: int, user_name: str, scheme_name: str,
                             applicant_name: str, father_name: str, phone: str,
                             village: str, ward: str, gpu: str, block: str,
                             reference_number: str, application_status: str,
                             submission_date: str, language: str = "english") -> bool:
        """Log scheme application details to a dedicated sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Scheme_Applications"
        headers = [
            "Timestamp", "User ID", "User Name", "Scheme Name", "Applicant Name",
            "Father's Name", "Phone", "Village", "Ward", "GPU", "Block",
            "Reference Number", "Application Status", "Submission Date", "Language", "Date"
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
            scheme_name,
            applicant_name,
            father_name,
            phone,
            village,
            ward,
            gpu,
            block,
            reference_number,
            application_status,
            submission_date,
            language,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_certificate_application(self, user_id: int, user_name: str, certificate_type: str,
                                  applicant_name: str, father_name: str, phone: str,
                                  village: str, gpu: str, block: str,
                                  reference_number: str, application_status: str,
                                  submission_date: str, language: str = "english") -> bool:
        """Log certificate application details to a dedicated sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "Certificate_Applications"
        headers = [
            "Timestamp", "User ID", "User Name", "Certificate Type", "Applicant Name",
            "Father's Name", "Phone", "Village", "GPU", "Block",
            "Reference Number", "Application Status", "Submission Date", "Language", "Date"
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
            certificate_type,
            applicant_name,
            father_name,
            phone,
            village,
            gpu,
            block,
            reference_number,
            application_status,
            submission_date,
            language,
            date
        ]
        
        return self.append_row(sheet_name, row_data)
    
    def log_csc_operator_update(self, reference_number: str, operator_name: str,
                               update_type: str, update_details: str,
                               status_change: str = None) -> bool:
        """Log CSC operator updates to a dedicated sheet"""
        if not self.service:
            logger.error(" Google Sheets service not initialized")
            return False
        
        sheet_name = "CSC_Operator_Updates"
        headers = [
            "Timestamp", "Reference Number", "Operator Name", "Update Type",
            "Update Details", "Status Change", "Date"
        ]
        
        # Create sheet if not exists
        if not self.create_sheet_if_not_exists(sheet_name, headers):
            return False
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        row_data = [
            timestamp,
            reference_number,
            operator_name,
            update_type,
            update_details,
            status_change or "",
            date
        ]
        
        return self.append_row(sheet_name, row_data)
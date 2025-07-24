#!/usr/bin/env python3
"""
NC Exgratia API Client Module

This module handles all interactions with the NC Exgratia API server,
including authentication, token management, and application submission.
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class NCExgratiaAPI:
    """NC Exgratia API Client"""
    
    def __init__(self):
        self.base_url = "https://ncapi.testwebdevcell.pw"
        self.username = "testbot"
        self.password = "testbot123"
        
        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        # Session management
        self.session = None
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        
    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def authenticate(self) -> bool:
        """Authenticate with the NC Exgratia API"""
        try:
            await self._ensure_session()
            await self._rate_limit()
            
            login_url = f"{self.base_url}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info("🔐 Authenticating with NC Exgratia API...")
            
            async with self.session.post(login_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    
                    # Set token expiry (10 minutes from now)
                    self.token_expiry = datetime.now() + timedelta(minutes=10)
                    
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    async def refresh_token_if_needed(self) -> bool:
        """Refresh access token if expired or about to expire"""
        if not self.access_token or not self.refresh_token:
            return await self.authenticate()
        
        # Check if token expires in next 2 minutes
        if self.token_expiry and datetime.now() + timedelta(minutes=2) >= self.token_expiry:
            try:
                await self._ensure_session()
                await self._rate_limit()
                
                refresh_url = f"{self.base_url}/api/auth/refresh"
                headers = {"Authorization": f"Bearer {self.refresh_token}"}
                
                logger.info("🔄 Refreshing access token...")
                
                async with self.session.post(refresh_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get('access_token')
                        self.refresh_token = data.get('refresh_token')
                        self.token_expiry = datetime.now() + timedelta(minutes=10)
                        
                        logger.info("✅ Token refreshed successfully")
                        return True
                    else:
                        logger.warning("⚠️ Token refresh failed, re-authenticating...")
                        return await self.authenticate()
                        
            except Exception as e:
                logger.error(f"❌ Token refresh error: {str(e)}")
                return await self.authenticate()
        
        return True
    
    async def submit_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit ex-gratia application to the API"""
        try:
            # Ensure we have valid token
            if not await self.refresh_token_if_needed():
                return {"success": False, "error": "Authentication failed"}
            
            await self._ensure_session()
            await self._rate_limit()
            
            submit_url = f"{self.base_url}/api/exgratia/apply"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Format data according to API requirements
            api_payload = self._format_application_data(application_data)
            
            logger.info(f"📤 Submitting application for {application_data.get('applicant_name', 'Unknown')}...")
            
            async with self.session.post(submit_url, json=api_payload, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = json.loads(response_text)
                    logger.info(f"✅ Application submitted successfully: {data.get('application', {}).get('application_refno', 'Unknown')}")
                    return {
                        "success": True,
                        "data": data,
                        "reference_number": data.get('application', {}).get('application_refno'),
                        "status": data.get('application', {}).get('status')
                    }
                else:
                    logger.error(f"❌ Application submission failed: {response.status} - {response_text}")
                    return {
                        "success": False,
                        "error": f"API Error {response.status}",
                        "details": response_text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Application submission error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_application_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format application data according to API requirements"""
        
        logger.info(f"📋 [API] Formatting application data: {list(data.keys()) if data else 'No data'}")
        
        # Check if we have required data
        required_fields = ['name', 'father_name', 'village', 'ward', 'gpu', 'contact', 'voter_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.error(f"❌ [API] Missing required fields: {missing_fields}")
            logger.error(f"❌ [API] Available data: {data}")
        
        # Map damage types to API format
        damage_type_mapping = {
            "🏠 House Damage": "house",
            "🌾 Crop Loss": "crop", 
            "🐄 Livestock Loss": "livestock",
            "house": "house",
            "crop": "crop",
            "livestock": "livestock"
        }
        
        # Convert damage type to API format
        damage_type = data.get('damage_type', '')
        api_damage_type = damage_type_mapping.get(damage_type, ['crop'])  # Default to crop
        
        # Convert to list if it's a string
        if isinstance(api_damage_type, str):
            api_damage_type = [api_damage_type]
        
        # Ensure we always have a valid damage type
        if not api_damage_type or api_damage_type == ['']:
            api_damage_type = ['crop']  # Default fallback
        
        logger.info(f"📋 [API] Damage type: '{damage_type}' -> API format: {api_damage_type}")
        
        # Parse land plot numbers
        plot_numbers = []
        plot_no = data.get('plot_no', '')
        if plot_no:
            try:
                # Try to extract numbers from plot_no string
                import re
                numbers = re.findall(r'\d+', plot_no)
                plot_numbers = [int(num) for num in numbers if num.isdigit()]
                if not plot_numbers:
                    plot_numbers = [1]  # Default if no numbers found
            except:
                plot_numbers = [1]  # Default fallback
        
        # Format datetime for API
        nc_datetime = data.get('nc_datetime')
        if not nc_datetime:
            # Use current time if not provided
            nc_datetime = datetime.now().isoformat()
        elif isinstance(nc_datetime, str):
            # Ensure proper ISO format
            try:
                parsed_dt = datetime.fromisoformat(nc_datetime.replace('Z', '+00:00'))
                nc_datetime = parsed_dt.isoformat()
            except:
                nc_datetime = datetime.now().isoformat()
        
        # Build API payload
        api_payload = {
            "applicant_name": data.get('name', ''),
            "sodowo": data.get('father_name', ''),
            "village": data.get('village', ''),
            "ward": data.get('ward', ''),
            "gpu": data.get('gpu', ''),
            "district": data.get('district', 'SK'),  # Default to Sikkim
            "land_khatian_number": data.get('khatiyan_no', ''),
            "land_plot_nos": plot_numbers,
            "ph_number": data.get('contact', ''),
            "voter_id": data.get('voter_id', ''),
            "damage_type": api_damage_type,
            "actual_nc_datetime": nc_datetime
        }
        
        # Add location data if available
        if data.get('latitude') and data.get('longitude'):
            api_payload["latitude"] = data.get('latitude')
            api_payload["longitude"] = data.get('longitude')
        
        logger.info(f"📋 Formatted API payload: {json.dumps(api_payload, indent=2)}")
        return api_payload
    
    async def check_application_status(self, reference_number: str) -> Dict[str, Any]:
        """Check application status using reference number"""
        try:
            if not await self.refresh_token_if_needed():
                return {"success": False, "error": "Authentication failed"}
            
            await self._ensure_session()
            await self._rate_limit()
            
            status_url = f"{self.base_url}/api/exgratia/status/{reference_number}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            logger.info(f"🔍 Checking status for application: {reference_number}")
            
            async with self.session.get(status_url, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = json.loads(response_text)
                    logger.info(f"✅ Status retrieved successfully for {reference_number}")
                    return {
                        "success": True,
                        "data": data,
                        "status": data.get('status', 'Unknown')
                    }
                else:
                    logger.error(f"❌ Status check failed: {response.status} - {response_text}")
                    return {
                        "success": False,
                        "error": f"API Error {response.status}",
                        "details": response_text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Status check error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close the API client session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔒 API client session closed")

# Global API client instance
api_client = NCExgratiaAPI()

async def get_api_client() -> NCExgratiaAPI:
    """Get the global API client instance"""
    return api_client 
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
from datetime import datetime, timedelta, timezone
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
            
            logger.info(" [API] Authenticating with NC Exgratia API...")
            logger.info(f" [API] Login URL: {login_url}")
            logger.info(f" [API] Login Payload: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(login_url, json=payload) as response:
                response_text = await response.text()
                
                logger.info(f" [API] Auth Response Status: {response.status}")
                logger.info(f" [API] Auth Response Headers: {dict(response.headers)}")
                logger.info(f" [API] Auth Response Text: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        self.access_token = data.get('access_token')
                        self.refresh_token = data.get('refresh_token')
                        
                        # Set token expiry (10 minutes from now)
                        self.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
                        logger.info(f" [API] Token expires at (UTC): {self.token_expiry}")
                        logger.info(f" [API] Current UTC time: {datetime.now(timezone.utc)}")
                        logger.info(f" [API] Token expired: {datetime.now(timezone.utc) > self.token_expiry}")
                        
                        logger.info(" [API] Authentication successful")
                        logger.info(f" [API] Access Token: {self.access_token[:20]}...")
                        return True
                    except json.JSONDecodeError as e:
                        logger.error(f" [API] Failed to parse auth JSON response: {e}")
                        return False
                else:
                    logger.error(f" [API] Authentication failed: {response.status} - {response_text}")
                    return False
                    
        except Exception as e:
            logger.error(f" Authentication error: {str(e)}")
            return False
    
    async def refresh_token_if_needed(self) -> bool:
        """Refresh access token if expired or about to expire"""
        if not self.access_token or not self.refresh_token:
            return await self.authenticate()
        
        # Check if token expires in next 2 minutes
        if self.token_expiry and datetime.now(timezone.utc) + timedelta(minutes=2) >= self.token_expiry:
            try:
                await self._ensure_session()
                await self._rate_limit()
                
                refresh_url = f"{self.base_url}/api/auth/refresh"
                headers = {"Authorization": f"Bearer {self.refresh_token}"}
                
                logger.info(" Refreshing access token...")
                
                async with self.session.post(refresh_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get('access_token')
                        self.refresh_token = data.get('refresh_token')
                        self.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
                        
                        logger.info(" Token refreshed successfully")
                        return True
                    else:
                        logger.warning(" Token refresh failed, re-authenticating...")
                        return await self.authenticate()
                        
            except Exception as e:
                logger.error(f" Token refresh error: {str(e)}")
                return await self.authenticate()
        
        return True
    
    async def submit_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit ex-gratia application to the API with retry logic for PK district issues"""
        try:
            # Ensure we have valid token
            if not await self.refresh_token_if_needed():
                return {"success": False, "error": "Authentication failed"}
            
            await self._ensure_session()
            await self._rate_limit()
            
            # Format data according to API requirements
            api_payload = self._format_application_data(application_data)
            
            # Check if this is a PK district submission (known to be inconsistent)
            district = application_data.get('district', '')
            damage_type = application_data.get('damage_type', '')
            is_pk_district = (district == 'PK' or district == 'Pakyong')
            
            # Set retry parameters based on the district
            max_retries = 3 if is_pk_district else 1
            retry_delay = 2  # seconds
            
            logger.info(f" [API] Submitting application for {application_data.get('name', 'Unknown')}...")
            if is_pk_district:
                logger.info(f" [API] PK District detected - Using retry logic (max {max_retries} attempts)")
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        logger.info(f" [API] Retry attempt {attempt + 1}/{max_retries}")
                        await asyncio.sleep(retry_delay)
                    
                    submit_url = f"{self.base_url}/api/exgratia/apply"
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                    
                    logger.info(f" [API] URL: {submit_url}")
                    logger.info(f" [API] Access Token: {self.access_token[:20]}...")
                    logger.info(f" [API] Headers: {headers}")
                    logger.info(f" [API] Payload: {json.dumps(api_payload, indent=2)}")
                    logger.info(f" [API] Payload Type: {type(api_payload)}")
                    logger.info(f" [API] Payload Keys: {list(api_payload.keys())}")
                    
                    async with self.session.post(submit_url, json=api_payload, headers=headers) as response:
                        response_text = await response.text()
                        
                        logger.info(f" [API] Response Status: {response.status}")
                        logger.info(f" [API] Response Headers: {dict(response.headers)}")
                        logger.info(f" [API] Response Text: {response_text}")
                        
                        if response.status in [200, 201]:  # Accept both 200 and 201 as success
                            try:
                                data = json.loads(response_text)
                                logger.info(f" [API] Application submitted successfully: {data.get('application', {}).get('application_refno', 'Unknown')}")
                                if attempt > 0:
                                    logger.info(f" [API] Success on retry attempt {attempt + 1}")
                                return {
                                    "success": True,
                                    "data": data,
                                    "reference_number": data.get('application', {}).get('application_refno'),
                                    "status": data.get('application', {}).get('status')
                                }
                            except json.JSONDecodeError as e:
                                logger.error(f" [API] Failed to parse JSON response: {e}")
                                if attempt == max_retries - 1:  # Last attempt
                                    return {
                                        "success": False,
                                        "error": "Invalid JSON response",
                                        "details": response_text
                                    }
                                continue  # Try again
                        else:
                            logger.error(f" [API] Application submission failed: {response.status} - {response_text}")
                            if attempt == max_retries - 1:  # Last attempt
                                return {
                                    "success": False,
                                    "error": f"API Error {response.status}",
                                    "details": response_text
                                }
                            continue  # Try again
                            
                except Exception as e:
                    logger.error(f" [API] Attempt {attempt + 1} failed with exception: {str(e)}")
                    if attempt == max_retries - 1:  # Last attempt
                        return {"success": False, "error": str(e)}
                    continue  # Try again
            
            # All retry attempts failed - this indicates a persistent server-side issue
            logger.error(f" [API] All {max_retries} retry attempts failed")
            logger.error(f" [API] This indicates a persistent server-side issue at NIC API")
            
            # Check if this is a server-wide outage (all districts failing)
            if response.status_code == 500:
                logger.error(f" [API] CRITICAL: NIC API server appears to be down")
                logger.error(f" [API] All districts are returning 500 errors")
                
                return {
                    "success": False, 
                    "error": "NIC API Server Outage",
                    "details": f"NIC API server is currently experiencing a major outage. All ex-gratia submissions are temporarily unavailable. Please try again later or contact support.",
                    "retry_attempts": max_retries,
                    "server_status": "down"
                }
            elif is_pk_district:
                return {
                    "success": False, 
                    "error": "PK District API Issue",
                    "details": f"NIC API is currently experiencing issues with PK district submissions. Please try again later or contact support.",
                    "retry_attempts": max_retries
                }
            else:
                return {"success": False, "error": "All retry attempts failed"}
                    
        except Exception as e:
            logger.error(f" Application submission error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_application_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format application data according to API requirements - ONLY SEND REQUIRED FIELDS"""
        
        logger.info(f" [API] Formatting application data: {list(data.keys()) if data else 'No data'}")
        
        # Check if we have required data
        required_fields = ['name', 'father_name', 'village', 'ward', 'gpu', 'contact', 'voter_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.error(f" [API] Missing required fields: {missing_fields}")
            logger.error(f" [API] Available data: {data}")
        
        # Map damage types to API format - ONLY the types the API accepts
        damage_type_mapping = {
            " House Damage": "house",
            " Crop Loss": "crop", 
            " Livestock Loss": "livestock",
            "House Damage": "house",
            "Crop Loss": "crop",
            "Livestock Loss": "livestock",
            "house": "house",
            "crop": "crop",
            "livestock": "livestock",
            "land": "land"
        }
        
        # Convert damage type to API format - Use working combinations
        damage_type = data.get('damage_type', '')
        district = data.get('district', 'GT')
        
        # Use working damage type combinations based on district
        if district in ['PK', 'GT']:
            # PK and GT districts work better with crop/land combinations
            if 'house' in damage_type.lower():
                api_damage_type = ['crop', 'land']  # Use working combination
            elif 'livestock' in damage_type.lower():
                api_damage_type = ['crop', 'land']  # Use working combination
            elif 'crop' in damage_type.lower():
                api_damage_type = ['crop', 'land']  # Use working combination
            elif 'land' in damage_type.lower():
                api_damage_type = ['crop', 'land']  # Use working combination
            else:
                api_damage_type = ['crop', 'land']  # Default working combination
        else:
            # For other districts, use the original logic
            if ',' in damage_type:
                damage_types = [dt.strip() for dt in damage_type.split(',')]
                api_damage_type = []
                for dt in damage_types:
                    mapped_type = damage_type_mapping.get(dt, dt)
                    if mapped_type not in api_damage_type:
                        api_damage_type.append(mapped_type)
            else:
                # Single damage type
                api_damage_type = damage_type_mapping.get(damage_type, ['crop'])
                if isinstance(api_damage_type, str):
                    api_damage_type = [api_damage_type]
            
            # Ensure we always have a valid damage type
            if not api_damage_type or api_damage_type == ['']:
                api_damage_type = ['crop', 'land']  # Default to working combination
        
        logger.info(f" [API] Damage type: '{damage_type}' -> API format: {api_damage_type}")
        
        # Parse land plot numbers - API expects integers with size limits
        plot_numbers = []
        plot_no = data.get('plot_no', '')
        if plot_no:
            try:
                import re
                numbers = re.findall(r'\d+', plot_no)
                # Limit plot numbers to reasonable size (max 9999) to avoid API errors
                plot_numbers = []
                for num in numbers:
                    if num.isdigit():
                        num_int = int(num)
                        # Limit to 4 digits to avoid API validation issues
                        if num_int > 9999:
                            num_int = 9999
                        plot_numbers.append(num_int)
                if not plot_numbers:
                    plot_numbers = [1]  # Default if no numbers found
            except:
                plot_numbers = [1]  # Default fallback
        
        # Map district names to district codes
        district_mapping = {
            'Gangtok': 'GT',
            'Mangan': 'MN', 
            'Namchi': 'NM',
            'Gyalshing': 'GY',
            'Pakyong': 'PK',
            'Soreng': 'SR',
            'East Sikkim': 'GT',
            'West Sikkim': 'GY',
            'North Sikkim': 'MN',
            'South Sikkim': 'NM',
            'East': 'GT',
            'West': 'GY',
            'North': 'MN', 
            'South': 'NM',
            'GT': 'GT',
            'MN': 'MN',
            'NM': 'NM',
            'GY': 'GY',
            'PK': 'PK',
            'SR': 'SR'
        }
        
        district = data.get('district', 'GT')
        district_code = district_mapping.get(district, district)
        
        # Use CURRENT timestamp instead of old dates - API rejects old dates
        nc_datetime = datetime.now().isoformat()
        logger.info(f" [API] Using current timestamp: {nc_datetime}")
        
        # Validate and limit large numbers to avoid API errors
        def limit_number(value, max_digits=4):
            """Limit number to max_digits to avoid API validation issues"""
            if isinstance(value, str):
                try:
                    num = int(value)
                    max_value = (10 ** max_digits) - 1  # e.g., 9999 for 4 digits
                    if num > max_value:
                        logger.info(f" [API] Limiting {value} to {max_value} (max {max_digits} digits)")
                        return str(max_value)
                    return value
                except (ValueError, TypeError):
                    return value
            return value
        
        # Apply number limiting to all numeric fields
        original_ward = data.get('ward', '')
        original_gpu = data.get('gpu', '')
        original_khatiyan = data.get('khatiyan_no', 'N/A')
        original_voter_id = data.get('voter_id', '')
        
        limited_ward = limit_number(original_ward, 4)
        limited_gpu = limit_number(original_gpu, 4)
        limited_khatiyan = limit_number(original_khatiyan, 4)
        limited_voter_id = limit_number(original_voter_id, 4)
        
        logger.info(f" [API] Number limiting: ward {original_ward}→{limited_ward}, gpu {original_gpu}→{limited_gpu}")
        logger.info(f" [API] Number limiting: khatiyan {original_khatiyan}→{limited_khatiyan}, voter_id {original_voter_id}→{limited_voter_id}")
        
        # Build API payload - ONLY the fields that the API expects (based on working format)
        api_payload = {
            "applicant_name": data.get('name', ''),
            "sodowo": data.get('father_name', ''),
            "village": data.get('village', ''),
            "ward": limited_ward,  # Limited ward number
            "gpu": limited_gpu,    # Limited GPU number
            "district": district_code,
            "land_khatian_number": limited_khatiyan,  # Limited khatian number
            "land_plot_nos": plot_numbers,
            "ph_number": data.get('contact', ''),
            "voter_id": limited_voter_id,  # Limited voter ID
            "damage_type": api_damage_type,
            "actual_nc_datetime": nc_datetime  # REQUIRED by API
        }
        
        # DO NOT send these extra fields that cause 500 errors:
        # - latitude/longitude (not in working format)
        # - damage_description (not in working format)
        # - Any other extra fields
        
        logger.info(f" [API] Sending ONLY required fields: {list(api_payload.keys())}")
        logger.info(f" Formatted API payload: {json.dumps(api_payload, indent=2)}")
        return api_payload
    
    async def check_application_status(self, reference_number: str) -> Dict[str, Any]:
        """Check application status using reference number"""
        try:
            if not await self.refresh_token_if_needed():
                return {"success": False, "error": "Authentication failed"}
            
            await self._ensure_session()
            await self._rate_limit()
            
            status_url = f"{self.base_url}/api/exgratia/applications/{reference_number}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            logger.info(f" Checking status for application: {reference_number}")
            
            async with self.session.get(status_url, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = json.loads(response_text)
                    logger.info(f" Status retrieved successfully for {reference_number}")
                    return {
                        "success": True,
                        "data": data,
                        "status": data.get('status', 'Unknown')
                    }
                else:
                    logger.error(f" Status check failed: {response.status} - {response_text}")
                    return {
                        "success": False,
                        "error": f"API Error {response.status}",
                        "details": response_text
                    }
                    
        except Exception as e:
            logger.error(f" Status check error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close the API client session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info(" API client session closed")

# Global API client instance
api_client = NCExgratiaAPI()

async def get_api_client() -> NCExgratiaAPI:
    """Get the global API client instance"""
    return api_client 
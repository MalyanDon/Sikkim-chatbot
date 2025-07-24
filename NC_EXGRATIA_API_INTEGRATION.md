# NC Exgratia API Integration - Complete Implementation

## 🎯 Overview

This document describes the complete integration of the NC Exgratia API with the SmartGov Assistant Telegram bot. The integration allows users to submit ex-gratia applications directly to the government API and receive real reference numbers for tracking.

## 🔗 API Configuration

### Base URL
- **Production**: `https://ncapi.testwebdevcell.pw`
- **Authentication**: POST `/api/auth/login`
- **Application Submission**: POST `/api/exgratia/apply`
- **Status Check**: GET `/api/exgratia/status/{reference_number}`

### Credentials
- **Username**: `testbot`
- **Password**: `testbot123`
- **Token Expiry**: Access token (10 minutes), Refresh token (30 days)

## 📋 Required API Fields

The bot now collects all required fields for the NC Exgratia API:

```json
{
  "applicant_name": "Full name",
  "sodowo": "S/o Father Name", 
  "village": "Village name",
  "ward": "Ward name",
  "gpu": "GPU name",
  "district": "District code",
  "land_khatian_number": "Land khatian number",
  "land_plot_nos": [123, 456],
  "ph_number": "Phone number",
  "voter_id": "Voter ID",
  "damage_type": ["crop", "land"],
  "actual_nc_datetime": "2023-10-01T10:00:00"
}
```

## 🔄 Enhanced Data Collection Flow

### 1. Personal Information
- **Name**: Full applicant name
- **Father's Name**: S/o format for API
- **Contact**: 10-digit mobile number
- **Voter ID**: Government voter identification

### 2. Address Details
- **Village**: Village name
- **Ward**: Ward name
- **GPU**: Gram Panchayat Unit
- **District**: Dropdown selection (East/West/North/South Sikkim)

### 3. Land Details
- **Khatiyan Number**: Land record number
- **Plot Number**: Land plot identification

### 4. Incident Details
- **Date & Time**: Natural calamity occurrence (DD/MM/YYYY HH:MM)
- **Damage Type**: House/Crop/Livestock damage
- **Description**: Detailed damage description

### 5. Location Data
- **GPS Coordinates**: Latitude/Longitude via Telegram location sharing
- **Timestamp**: Location sharing timestamp

## 🏗️ Technical Implementation

### 1. API Client Module (`nc_exgratia_api.py`)

#### Key Features:
- **Authentication Management**: Automatic login and token refresh
- **Rate Limiting**: 100ms delay between requests
- **Error Handling**: Comprehensive error processing
- **Session Management**: Efficient aiohttp session handling

#### Core Methods:
```python
async def authenticate() -> bool
async def refresh_token_if_needed() -> bool
async def submit_application(data: dict) -> dict
async def check_application_status(ref_no: str) -> dict
```

### 2. Enhanced Bot Workflow

#### Updated Steps:
1. **Name** → **Father's Name** → **Village** → **Contact**
2. **Voter ID** → **Ward** → **GPU** → **District** (dropdown)
3. **Khatiyan** → **Plot** → **NC DateTime** → **Damage Type**
4. **Damage Description** → **Location** → **Confirmation**
5. **API Submission** → **Reference Number**

#### New Features:
- **District Selection**: Interactive dropdown for district choice
- **DateTime Validation**: Multiple format support (DD/MM/YYYY, YYYY-MM-DD)
- **Location Integration**: GPS coordinates collection
- **API Submission**: Real-time government API integration

### 3. Status Checking

#### Methods:
- **Command**: `/status SK2025MN0003`
- **Menu**: Disaster Management → Check Status
- **Button**: Direct from submission confirmation

#### Status Response:
```json
{
  "application": {
    "application_refno": "SK2025MN0003",
    "status": "SUBMITTED",
    "applicant_name": "John Doe",
    "created_at": "2025-07-24T02:56:21.477895"
  }
}
```

## 📊 Data Storage

### Local Backup (CSV)
All applications are stored locally as backup:
- **File**: `data/exgratia_applications.csv`
- **Fields**: All collected data + API reference number
- **Purpose**: Backup and local tracking

### Google Sheets Logging
Enhanced logging includes:
- **API Reference Number**: Government-issued reference
- **API Status**: Submission status from government API
- **Location Data**: GPS coordinates
- **Timestamp**: Complete audit trail

## 🎨 User Experience Enhancements

### 1. Progress Indicators
- **Processing Messages**: "Submitting to NC Exgratia API..."
- **Status Updates**: Real-time submission feedback
- **Error Recovery**: Graceful error handling with retry options

### 2. Confirmation Screen
Enhanced confirmation shows all collected data:
```
📋 Please Review Your NC Exgratia Application

Personal Details:
👤 Name: John Doe
👨‍👦 Father's Name: S/o Peter Doe
🆔 Voter ID: VOTER123456
📱 Contact: 9876543210

Address Details:
📍 Village: Pentok
🏘️ Ward: Sakten
🏛️ GPU: Karzi Mangnam GP
🏛️ District: East Sikkim

Land Details:
📄 Khatiyan Number: KH123456
🗺️ Plot Number: 789

Incident Details:
📅 Date & Time: 15/10/2023 14:30
🏷️ Damage Type: 🌾 Crop Loss
📝 Description: Heavy rainfall damaged crops

Location:
📍 Coordinates: 27.338900, 88.606500
```

### 3. Success Response
```
✅ NC Exgratia Application Submitted Successfully!

🆔 Reference Number: SK2025MN0003
👤 Applicant: John Doe
📅 Submitted: 24/07/2025 10:30
📊 Status: SUBMITTED

Important Information:
• Save this reference number: SK2025MN0003
• Check status anytime: /status SK2025MN0003
• Contact support if needed: +91-1234567890

Next Steps:
1. Your application will be reviewed by officials
2. You'll receive updates via SMS
3. Processing time: 7-10 working days
```

## 🔧 Configuration

### Environment Variables
```python
# config.py
NC_EXGRATIA_API_URL = "https://ncapi.testwebdevcell.pw"
NC_EXGRATIA_USERNAME = "testbot"
NC_EXGRATIA_PASSWORD = "testbot123"
NC_EXGRATIA_ENABLED = True
```

### Bot Initialization
```python
# Initialize API client
self.api_client = None
if Config.NC_EXGRATIA_ENABLED:
    self.api_client = NCExgratiaAPI()
    logger.info("🔗 NC Exgratia API client initialized")
```

## 🧪 Testing

### Test Script: `test_nc_exgratia_api.py`
Comprehensive testing of:
1. **Authentication**: Login and token management
2. **Token Refresh**: Automatic token renewal
3. **Application Submission**: End-to-end submission test
4. **Status Checking**: Reference number validation
5. **Error Handling**: API error scenarios

### Test Commands:
```bash
# Test API integration
python test_nc_exgratia_api.py

# Test bot functionality
python comprehensive_smartgov_bot.py
```

## 🚀 Usage Instructions

### For Users:
1. **Start Application**: Disaster Management → Apply for Ex-gratia
2. **Complete Form**: Follow the step-by-step process
3. **Share Location**: Use Telegram location sharing
4. **Confirm Details**: Review all collected information
5. **Submit**: Get government reference number
6. **Track Status**: Use `/status` command or menu

### For Administrators:
1. **Monitor Logs**: Check application submissions
2. **API Status**: Verify API connectivity
3. **Error Handling**: Review failed submissions
4. **Data Backup**: Export CSV data for analysis

## 🔒 Security & Error Handling

### Authentication Security:
- **Token Management**: Automatic refresh before expiry
- **Session Security**: Secure aiohttp sessions
- **Rate Limiting**: Prevent API abuse

### Error Scenarios:
1. **API Unavailable**: Graceful degradation with retry
2. **Invalid Data**: Clear validation messages
3. **Network Issues**: Queue and retry mechanism
4. **Token Expiry**: Automatic refresh without user interruption

### Data Validation:
- **Phone Numbers**: 10-digit validation
- **DateTime**: Multiple format support
- **Location**: GPS coordinate validation
- **Required Fields**: Complete field validation

## 📈 Benefits

### For Citizens:
- **Real Reference Numbers**: Government-issued tracking IDs
- **Instant Submission**: Direct API integration
- **Status Tracking**: Real-time application status
- **Location Accuracy**: GPS-based location verification

### For Government:
- **Standardized Data**: API-compliant submissions
- **Real-time Processing**: Immediate application receipt
- **Audit Trail**: Complete submission logging
- **Data Quality**: Validated and formatted data

### For System:
- **Reliability**: Backup storage and error recovery
- **Scalability**: Efficient API client management
- **Monitoring**: Comprehensive logging and tracking
- **Maintenance**: Easy configuration and updates

## 🔄 Future Enhancements

### Planned Features:
1. **Bulk Operations**: Handle multiple applications
2. **Document Upload**: Photo/scan attachments
3. **SMS Integration**: Automated status updates
4. **Admin Dashboard**: Application management interface
5. **Analytics**: Submission statistics and reports

### API Extensions:
1. **Document API**: File upload endpoints
2. **Notification API**: SMS/email integration
3. **Analytics API**: Statistical data access
4. **Admin API**: Administrative functions

## 📞 Support

### Technical Support:
- **API Issues**: Check authentication and connectivity
- **Bot Problems**: Review logs and error messages
- **Data Issues**: Verify CSV and Google Sheets integration

### User Support:
- **Application Help**: Guide users through the process
- **Status Queries**: Assist with reference number tracking
- **Error Resolution**: Help resolve submission issues

---

**Implementation Status**: ✅ **COMPLETE**
**Last Updated**: July 24, 2025
**Version**: 1.0.0 
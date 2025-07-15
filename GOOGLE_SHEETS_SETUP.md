# Google Sheets Integration Setup for SmartGov Bot

This document explains how to set up Google Sheets integration with your SmartGov bot to log all interactions and complaints.

## 🚀 Quick Setup

### 1. Google Sheets API Key (Already Configured)

Your API key is already configured in `config.py`:
```python
GOOGLE_SHEETS_API_KEY = "AIzaSyDOGeGFOwaLeRuVEQmbOE4E-YgHsh3OgV0"
```

### 2. Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```

### 3. Configure Spreadsheet ID

Set your spreadsheet ID in the environment or update `config.py`:

```python
# In config.py
GOOGLE_SHEETS_SPREADSHEET_ID = "your_spreadsheet_id_here"
```

Or set as environment variable:
```bash
export GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id_here"
```

## 📊 Sheets Created Automatically

The bot will automatically create the following sheets in your Google Spreadsheet:

### 1. **Complaints** 📝
- Logs all complaint submissions
- Columns: Timestamp, User ID, User Name, Complaint Type, Complaint Text, Language, Status, Date

### 2. **Emergency_Services** 🚨
- Logs emergency service requests
- Columns: Timestamp, User ID, User Name, Service Type, Query Text, Language, Result, Date

### 3. **Homestay_Queries** 🏡
- Logs homestay booking queries
- Columns: Timestamp, User ID, User Name, Place, Query Text, Language, Result, Date

### 4. **Cab_Booking_Queries** 🚕
- Logs cab booking requests
- Columns: Timestamp, User ID, User Name, Destination, Query Text, Language, Result, Date

### 5. **Ex_Gratia_Applications** 🆘
- Logs disaster relief applications
- Columns: Timestamp, User ID, User Name, Full Name, Phone, Address, Damage Type, Damage Description, Language, Status, Date

### 6. **Certificate_Queries** 💻
- Logs certificate application queries
- Columns: Timestamp, User ID, User Name, Certificate Type, Query Text, Language, Result, Date

### 7. **General_Interactions** 💬
- Logs all other bot interactions
- Columns: Timestamp, User ID, User Name, Interaction Type, Query Text, Language, Bot Response, Date

## 🧪 Testing the Integration

Run the test script to verify everything works:

```bash
python test_google_sheets_integration.py
```

This will:
- Test Google Sheets service initialization
- Create a test sheet
- Test all logging methods
- Verify API connectivity

## 🔧 Configuration Options

### Enable/Disable Google Sheets

In `config.py`:
```python
GOOGLE_SHEETS_ENABLED = True  # Set to False to disable
```

### Customize Sheet Names

You can modify sheet names in `google_sheets_service.py`:
```python
sheet_name = "Your_Custom_Sheet_Name"
```

## 📈 Data Analytics

With this integration, you can:

1. **Track User Engagement**
   - See which services are most popular
   - Monitor user language preferences
   - Analyze peak usage times

2. **Monitor Complaints**
   - Track complaint types and status
   - Monitor response times
   - Identify common issues

3. **Emergency Services Analytics**
   - Track emergency service requests
   - Monitor response patterns
   - Identify high-demand services

4. **Tourism Insights**
   - Track homestay queries by location
   - Monitor cab booking patterns
   - Analyze tourist preferences

## 🔒 Security & Privacy

- All data is stored in your private Google Sheet
- User IDs are Telegram user IDs (not personal information)
- No sensitive personal data is logged without consent
- API key has read/write access only to your specific spreadsheet

## 🚨 Troubleshooting

### Common Issues

1. **"Google Sheets service not initialized"**
   - Check if API key is correct
   - Verify spreadsheet ID is set
   - Ensure GOOGLE_SHEETS_ENABLED is True

2. **"Error creating sheet"**
   - Check spreadsheet permissions
   - Verify API key has write access
   - Ensure spreadsheet ID is correct

3. **"Authentication failed"**
   - Verify API key is valid
   - Check Google Cloud Console for API restrictions
   - Ensure Google Sheets API is enabled

### Debug Mode

Enable debug logging in `config.py`:
```python
DEBUG = True
```

## 📞 Support

If you encounter issues:

1. Check the bot logs for detailed error messages
2. Run the test script to isolate the problem
3. Verify your Google Sheets API setup
4. Check spreadsheet permissions and sharing settings

## 🎯 Next Steps

Once integration is working:

1. **Set up automated reports** using Google Sheets formulas
2. **Create dashboards** for real-time monitoring
3. **Set up alerts** for high-priority interactions
4. **Export data** for further analysis in other tools

---

**Note**: This integration uses the Google Sheets API with API key authentication, which is simpler than OAuth2 for server-to-server applications. 
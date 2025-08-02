# 📋 Data Management Guide for Sajilo Sewak Bot

This guide explains how to update and manage the bot's data files, including emergency contacts, CSC details, and other important information.

## 🚀 Quick Start

### Option 1: Interactive Data Manager (Recommended)
```bash
python data_manager.py
```

### Option 2: Simple Update Script
```bash
python update_data.py
```

### Option 3: Excel Templates (For Non-Technical Users)
```bash
python create_excel_template.py
```

## 📁 Data Files Structure

### Core Data Files
```
data/
├── emergency_services_text_responses.json  # Emergency service responses
├── csc_details.csv                         # CSC operator details
├── important_contacts.json                 # Important contact numbers
├── blo_details.csv                         # BLO details
├── scheme.csv                              # Government schemes
├── home_stay.csv                           # Homestay information
├── health.csv                              # Health services
├── fair_price_shop.csv                     # Fair price shops
└── backups/                                # Automatic backups
```

## 🔧 How to Update Different Data Types

### 1. 🚨 Emergency Contacts

**File:** `data/emergency_services_text_responses.json`

**What it contains:**
- Emergency service responses (medical, police, fire, disaster)
- Multilingual responses (English, Hindi, Nepali)
- Contact numbers and response times

**How to update:**
```bash
python data_manager.py
# Choose option 1: Update Emergency Contacts
```

**Or manually edit the JSON file:**
```json
{
    "medical": {
        "english": "**Emergency Medical Services**\n\n**Ambulance Services**:\n- Call 102 for Ambulance\n- Call 108 for Advanced Life Support",
        "hindi": "**आपातकालीन चिकित्सा सेवाएं**...",
        "nepali": "**आपतकालीन चिकित्सा सेवाहरू**..."
    }
}
```

### 2. 🏢 CSC (Common Service Center) Details

**File:** `data/csc_details.csv`

**What it contains:**
- CSC operator names and contact numbers
- Block and GPU (Gram Panchayat Unit) information
- Block and Sub-division single window contacts

**How to update:**
```bash
python data_manager.py
# Choose option 2: Update CSC Details
```

**Or use Excel template:**
1. Run `python create_excel_template.py`
2. Open the generated Excel file
3. Edit the data
4. Save as CSV in the data folder

**CSV Structure:**
```csv
Sl,BLOCK,GPU Name,Name,Contact No.,Block Single Window,SubDivision Single Window
1,Chongrang,Dhupidara Narkhola,Mohan Singh Subba,8389939355,"7908189770, 7029073911","9832007465, 7719254415"
```

### 3. 📞 Important Contacts

**File:** `data/important_contacts.json`

**What it contains:**
- Emergency contact categories
- Contact numbers and locations
- Service descriptions

**How to update:**
```bash
python data_manager.py
# Choose option 3: Update Important Contacts
```

**JSON Structure:**
```json
{
    "ambulance": {
        "numbers": ["102", "108"],
        "hospitals": [
            {"name": "STNM Hospital, Gangtok", "contact": "03592-201158"},
            {"name": "CRH Manipal, 5th Mile", "contact": "03592-270666"}
        ]
    }
}
```

## 📊 Excel Template Method (For Non-Technical Users)

### Step 1: Generate Templates
```bash
python create_excel_template.py
```

### Step 2: Edit Templates
1. Open the generated Excel files
2. Replace example data with actual information
3. Follow instructions in the "Instructions" sheet
4. Save as CSV files

### Step 3: Update Bot
1. Copy CSV files to the `data/` folder
2. Restart the bot to load new data

## 🔄 Automatic Backup System

The data manager automatically creates backups before making changes:

- **Backup Location:** `data/backups/`
- **Backup Format:** `filename_YYYYMMDD_HHMMSS.backup`
- **Automatic:** Backups are created before any file modification

## 📝 Manual File Editing

### Emergency Services JSON
```json
{
    "service_name": {
        "english": "**Service Title**\n\n**Emergency Numbers**:\n- Number 1\n- Number 2\n\n**Locations**:\n- Location 1: Contact\n- Location 2: Contact\n\n**Response Time**: 10-15 minutes\n\n**What to Share**:\n- Your exact location\n- Nature of emergency\n- Contact number",
        "hindi": "Hindi translation here",
        "nepali": "Nepali translation here"
    }
}
```

### CSC Details CSV
```csv
Sl,BLOCK,GPU Name,Name,Contact No.,Block Single Window,SubDivision Single Window
1,BlockName,GPUName,OperatorName,ContactNumber,"BlockContacts","SubDivContacts"
```

### Important Contacts JSON
```json
{
    "category_name": {
        "numbers": ["number1", "number2"],
        "stations": [
            {"name": "Station Name", "contact": "Contact Number"}
        ]
    }
}
```

## 🚨 Adding New Emergency Services

### Method 1: Using Data Manager
1. Run `python data_manager.py`
2. Choose "Update Emergency Contacts"
3. Choose "Add new emergency service"
4. Follow the prompts

### Method 2: Manual JSON Editing
1. Open `data/emergency_services_text_responses.json`
2. Add new service entry
3. Include English, Hindi, and Nepali responses
4. Save and restart bot

### Example New Service:
```json
{
    "roadside_assistance": {
        "english": "**Roadside Assistance Services**\n\n**Emergency Numbers**:\n- Call 1033 for Roadside Assistance\n- Call 1800-XXX-XXXX for Towing\n\n**Response Time**: 20-30 minutes\n\n**What to Share**:\n- Your exact location\n- Vehicle details\n- Nature of problem",
        "hindi": "**सड़क किनारे सहायता सेवाएं**...",
        "nepali": "**सडक छेउ सहयोग सेवाहरू**..."
    }
}
```

## 🏢 Adding New CSC Operators

### Method 1: Using Data Manager
1. Run `python data_manager.py`
2. Choose "Update CSC Details"
3. Choose "Add new CSC operator"
4. Fill in the details

### Method 2: Excel Template
1. Generate Excel template
2. Add new rows with operator details
3. Save as CSV
4. Replace existing `csc_details.csv`

### Required Fields:
- **Sl:** Serial number (auto-increment)
- **BLOCK:** Block name
- **GPU Name:** Gram Panchayat Unit name
- **Name:** Operator's full name
- **Contact No.:** Operator's contact number
- **Block Single Window:** Block office contacts (comma separated)
- **SubDivision Single Window:** Sub-division office contacts (comma separated)

## 📞 Adding New Contact Categories

### Method 1: Using Data Manager
1. Run `python data_manager.py`
2. Choose "Update Important Contacts"
3. Choose "Add new contact category"
4. Follow the prompts

### Method 2: Manual JSON Editing
```json
{
    "new_category": {
        "numbers": ["emergency_number"],
        "stations": [
            {"name": "Station Name", "contact": "Contact Number"}
        ]
    }
}
```

## 🔍 Troubleshooting

### Common Issues:

1. **Bot not loading new data:**
   - Restart the bot after updating files
   - Check file permissions
   - Verify JSON/CSV format is correct

2. **JSON syntax errors:**
   - Use a JSON validator
   - Check for missing commas or brackets
   - Ensure proper escaping of special characters

3. **CSV format issues:**
   - Ensure column headers match exactly
   - Use comma separation for multiple values
   - Check for extra spaces or special characters

4. **Backup not created:**
   - Check if `data/backups/` directory exists
   - Verify write permissions
   - Check available disk space

### Validation Commands:
```bash
# Validate JSON files
python -m json.tool data/emergency_services_text_responses.json

# Check CSV format
python -c "import pandas as pd; pd.read_csv('data/csc_details.csv')"

# Test data loading
python -c "from data_manager import DataManager; dm = DataManager(); print('Data manager initialized successfully')"
```

## 📋 Best Practices

1. **Always backup before changes:**
   - Use the automatic backup system
   - Keep manual backups of important files

2. **Test changes:**
   - Restart the bot after updates
   - Test the updated functionality
   - Verify multilingual responses

3. **Maintain consistency:**
   - Use consistent naming conventions
   - Keep contact numbers in standard format
   - Maintain multilingual support

4. **Document changes:**
   - Keep a changelog of updates
   - Document new services or contacts
   - Note any special requirements

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs:** Look at `bot.log` for error messages
2. **Validate files:** Use the validation commands above
3. **Restore backup:** Use the automatic backup files
4. **Contact support:** Reach out with specific error messages

## 📚 Additional Resources

- **Bot Configuration:** See `config.py` for bot settings
- **Main Bot Code:** See `comprehensive_smartgov_bot.py` for implementation
- **Google Sheets Integration:** See `google_sheets_service.py` for analytics
- **API Integration:** See `nc_exgratia_api.py` for external services

---

**Remember:** Always test your changes and keep backups before making modifications! 
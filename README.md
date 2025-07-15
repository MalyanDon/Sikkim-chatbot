# Enhanced SmartGov Assistant Bot 🏛️

A comprehensive multilingual Telegram chatbot for Sikkim government services with LLM-powered intent detection and rule-based workflows.

## 🌟 Features

### 🎯 Core Services

#### 🚨 Disaster Management
- **Ex-gratia Assistance Application**: Complete workflow for disaster relief applications
- **Application Status Check**: Track application progress with ID lookup
- **Ex-gratia Norms**: Detailed information about assistance amounts and eligibility
- **Application Process Guide**: Step-by-step instructions for applying
- **Disaster Reporting**: File disaster-related complaints

#### 🚑 Emergency Services
- **Ambulance (102)**: Medical emergency contacts and guidance
- **Police (100)**: Police emergency services
- **Fire (101)**: Fire emergency services
- **Women Helpline**: Support for women in distress
- **Suicide Prevention**: Mental health crisis support
- **Health Helpline**: General health emergency services
- **Disaster Emergency**: Natural disaster emergency contacts

#### 🏔️ Tourism & Homestays
- **Location-based Search**: Find homestays by tourist destination
- **Ratings & Prices**: View homestay ratings and pricing
- **Direct Booking**: Contact homestay owners directly
- **Multiple Destinations**: Gangtok, Pelling, Yuksom, and more

#### 🏢 Common Service Centers (CSC)
- **CSC Finder**: Locate nearest CSC by GPU number
- **Operator Contacts**: Direct contact with CSC operators
- **Service Information**: Complete list of available services
- **Certificate Applications**: Guide for applying through CSC

### 🌐 Multilingual Support
- **English**: Complete interface and responses
- **Hindi (हिंदी)**: Full translation for Hindi speakers
- **Nepali (नेपाली)**: Complete Nepali language support
- **Persistent Language**: User language preference is remembered

### 🤖 Smart Features
- **LLM Intent Detection**: Natural language understanding using Ollama/Qwen2
- **Card-based UI**: Visual service cards for better user experience
- **Rule-based Workflows**: Structured forms and data collection
- **Data Validation**: Input validation with helpful error messages
- **State Management**: Multi-step form handling with session persistence
- **Google Sheets Integration**: Automatic logging of complaints, queries, and applications

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Ollama with Qwen2 model (optional, for LLM features)
- Google Cloud Project with Sheets API (optional, for data logging)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/sikkim-chatbot.git
cd sikkim-chatbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the bot**
Edit `config.py` with your bot token:
```python
BOT_TOKEN = "your_telegram_bot_token_here"
```

4. **Set up Google Sheets (Optional)**
Follow the setup guide in `GOOGLE_SHEETS_SETUP.md` to enable automatic data logging.

4. **Run the bot**
```bash
python comprehensive_smartgov_bot.py
```

5. **Test the bot**
```bash
python test_enhanced_bot.py
```

6. **Test Google Sheets integration (if enabled)**
```bash
python test_google_sheets.py
```

## 📁 Project Structure

```
Sikkim-chatbot/
├── smartgov_bot_fixed.py           # Main bot implementation with Google Sheets
├── google_sheets_service.py        # Google Sheets integration service
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── test_google_sheets.py           # Google Sheets integration tests
├── GOOGLE_SHEETS_SETUP.md          # Google Sheets setup guide
├── .gitignore                      # Git ignore file
├── data/                          # Data files
│   ├── emergency_services_text_responses.json
│   ├── homestays_by_place.csv
│   ├── csc_contacts.csv
│   ├── status.csv
│   ├── exgratia_applications.csv
│   ├── info_opt1.txt             # Ex-gratia norms
│   └── info_opt2.txt             # Application process
└── tests/                        # Test files
    └── comprehensive_test.py
```

## 🔧 Configuration

### Bot Token
Set your Telegram bot token in `config.py`:
```python
BOT_TOKEN = "your_bot_token"
```

### LLM Configuration
Configure Ollama endpoint in the bot file:
```python
LLM_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2"
```

### Google Sheets Configuration
Set up Google Sheets integration in your `.env` file:
```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
```

### Data Files
Ensure all CSV and JSON files are in the `data/` directory:
- `emergency_services_text_responses.json`: Emergency service responses
- `homestays_by_place.csv`: Homestay listings by location
- `csc_contacts.csv`: CSC operator contact information
- `status.csv`: Application status database
- `exgratia_applications.csv`: Ex-gratia application records

## 🎯 Usage Examples

### Basic Commands
- `/start` - Initialize bot and select language
- Send any message to trigger intent detection

### Service Access
- **Disaster Management**: "I need ex-gratia assistance" or "Disaster relief help"
- **Emergency Services**: "Emergency ambulance" or "Police help needed"
- **Tourism**: "Show homestays in Gangtok" or "Tourism information"
- **CSC Services**: "Find CSC operator" or "Certificate application"

### Form Workflows
1. **Ex-gratia Application**:
   - Name → Father's Name → Village → Contact → Damage Type → Description
   - Automatic ID generation and data storage

2. **Status Check**:
   - Enter application ID to check current status

3. **CSC Finder**:
   - Enter GPU number to find nearest CSC operator

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_enhanced_bot.py
```

Tests include:
- ✅ Bot initialization
- ✅ Language functions
- ✅ LLM integration
- ✅ Data file loading
- ✅ Response templates
- ✅ Emergency numbers
- ✅ Service card creation

## 📊 Data Management

### Ex-gratia Applications
Applications are stored in `data/exgratia_applications.csv` with fields:
- Application ID (auto-generated)
- Personal details (name, father's name, village, contact)
- Damage information (type, description)
- Submission metadata (date, language, status)

### Google Sheets Logging
When enabled, the bot automatically logs:
- **Complaints**: General queries and complaints from users
- **Certificate Queries**: Certificate-related questions and responses
- **Ex-gratia Applications**: Complete application data with user details
- **Status Checks**: Application status check requests and results

Each sheet includes timestamps, user information, and relevant data for tracking and analysis.

### Status Tracking
Application status can be checked using the stored application ID.

### CSC Integration
CSC operators are listed with:
- Operator name and contact
- GPU coverage area
- Available timings

## 🌟 Advanced Features

### LLM Integration
- Uses Ollama with Qwen2 model for natural language understanding
- Fallback to keyword-based detection if LLM unavailable
- Intent classification for routing to appropriate services

### Multilingual Support
- Dynamic language switching
- Persistent user language preferences
- Complete translation of forms and responses

### UI Enhancements
- Service cards with visual elements
- Inline keyboards for easy navigation
- Progress indicators for multi-step forms

## 🔒 Security & Privacy

- User data is stored locally in CSV files
- No external data transmission (except Telegram API)
- Application IDs are generated securely
- Input validation prevents injection attacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For technical support or questions:
- **Helpline**: 1077
- **Email**: smartgov@sikkim.gov.in
- **GitHub Issues**: Create an issue for bug reports

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Sikkim Government for data and requirements
- Telegram Bot API for messaging platform
- Ollama community for LLM integration
- Python ecosystem for development tools

## 🚀 Deployment

### Local Deployment
```bash
python comprehensive_smartgov_bot.py
```

### Production Deployment
1. Set up environment variables
2. Configure reverse proxy (nginx)
3. Use process manager (systemd, supervisor)
4. Set up monitoring and logging

### Docker Deployment
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "comprehensive_smartgov_bot.py"]
```

## 📈 Monitoring & Analytics

The bot logs all interactions and can be extended with:
- User analytics dashboard
- Service usage statistics
- Performance monitoring
- Error tracking and alerting

---

**Made with ❤️ for the people of Sikkim** 
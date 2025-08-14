# 🐳 Docker Deployment Guide for Sikkim Chatbot

This guide will help you deploy the Sikkim Chatbot using Docker for easy hosting and management.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (usually comes with Docker Desktop)
- **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
- **Git** (to clone the repository)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Sikkim-chatbot

# Copy environment file
cp env.example .env
```

### 2. Configure Environment

Edit the `.env` file with your actual values:

```bash
# Required: Your Telegram Bot Token
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional: Ollama LLM Configuration
OLLAMA_API_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b

# Optional: Google Sheets Integration
GOOGLE_SHEETS_ENABLED=false
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Optional: NC Exgratia API Integration
NC_EXGRATIA_ENABLED=false
NC_EXGRATIA_BASE_URL=https://api.example.com
NC_EXGRATIA_USERNAME=your_username
NC_EXGRATIA_PASSWORD=your_password

# Optional: Support Contact
SUPPORT_PHONE=1800-XXX-XXXX

# Optional: Logging Level
LOG_LEVEL=INFO
```

### 3. Deploy Using Scripts

#### Linux/Mac:
```bash
# Make script executable
chmod +x docker-deploy.sh

# Build and start
./docker-deploy.sh build
./docker-deploy.sh start

# Check status
./docker-deploy.sh status

# View logs
./docker-deploy.sh logs
```

#### Windows:
```cmd
# Run the batch file
docker-deploy.bat

# Then follow the interactive menu
```

### 4. Manual Docker Commands

```bash
# Build the image
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Configuration Options

### Required Configuration

- **BOT_TOKEN**: Your Telegram bot token from @BotFather

### Optional Configurations

#### LLM Integration
```bash
# If using local Ollama
OLLAMA_API_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b

# If using remote Ollama
OLLAMA_API_URL=http://your-server:11434
LLM_MODEL=qwen2.5:7b
```

#### Google Sheets Integration
```bash
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_CREDENTIALS_FILE=./credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

#### NC Exgratia API
```bash
NC_EXGRATIA_ENABLED=true
NC_EXGRATIA_BASE_URL=https://your-api-server.com
NC_EXGRATIA_USERNAME=your_username
NC_EXGRATIA_PASSWORD=your_password
```

## 📊 Monitoring and Management

### Check Container Status
```bash
docker-compose ps
```

### View Real-time Logs
```bash
docker-compose logs -f
```

### Monitor Resource Usage
```bash
docker stats
```

### Access Container Shell
```bash
docker-compose exec sikkim-chatbot bash
```

## 🔄 Updating the Bot

### 1. Pull Latest Code
```bash
git pull origin main
```

### 2. Rebuild and Restart
```bash
# Stop current services
docker-compose down

# Rebuild with latest code
docker-compose build --no-cache

# Start services
docker-compose up -d
```

### 3. Or Use the Script
```bash
./docker-deploy.sh restart
```

## 🗄️ Data Persistence

The bot stores data in the following locations:

- **Application Data**: `./data/` (mounted as volume)
- **Photos**: `./data/photos/` (mounted as volume)
- **Logs**: `./logs/` (mounted as volume)
- **Backups**: `./data/backups/` (mounted as volume)

### Backup Data
```bash
# Create backup
docker-compose exec sikkim-chatbot tar -czf /app/data/backups/backup-$(date +%Y%m%d).tar.gz /app/data/

# Copy backup to host
docker cp sikkim-chatbot:/app/data/backups/backup-20250101.tar.gz ./
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Bot Not Responding
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs sikkim-chatbot

# Restart container
docker-compose restart sikkim-chatbot
```

#### 2. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./data ./logs
```

#### 3. Port Conflicts
```bash
# Check if port 8080 is in use
netstat -tulpn | grep :8080

# Change port in docker-compose.yml if needed
```

#### 4. Memory Issues
```bash
# Check container resource usage
docker stats

# Adjust memory limits in docker-compose.yml
```

### Log Analysis
```bash
# View error logs
docker-compose logs sikkim-chatbot | grep ERROR

# View recent logs
docker-compose logs --tail=100 sikkim-chatbot

# Follow logs in real-time
docker-compose logs -f sikkim-chatbot
```

## 🌐 Production Deployment

### 1. Environment Variables
```bash
# Use production values
BOT_TOKEN=your_production_bot_token
LOG_LEVEL=WARNING
OLLAMA_API_URL=https://your-production-ollama-server.com
```

### 2. Resource Limits
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### 3. Health Checks
```yaml
# Health check is already configured
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. Logging
```bash
# Configure log rotation
docker-compose exec sikkim-chatbot logrotate -f /etc/logrotate.conf
```

## 🔐 Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate API keys regularly

### 2. Container Security
- Container runs as non-root user (`botuser`)
- Limited resource allocation
- Health checks for monitoring

### 3. Network Security
- Only expose necessary ports (8080)
- Use internal Docker networks
- Consider VPN for sensitive deployments

## 📱 Telegram Bot Setup

### 1. Create Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow instructions to create bot
4. Copy the bot token

### 2. Configure Webhook (Optional)
```bash
# Set webhook URL
curl -F "url=https://your-domain.com:8080/webhook" \
     -F "certificate=@/path/to/cert.pem" \
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook
```

### 3. Test Bot
1. Start the bot: `./docker-deploy.sh start`
2. Send `/start` to your bot on Telegram
3. Check logs: `./docker-deploy.sh logs`

## 🎯 Next Steps

1. **Test the deployment** with basic commands
2. **Configure integrations** (Google Sheets, NC Exgratia API)
3. **Set up monitoring** and alerting
4. **Plan backup strategy** for data persistence
5. **Consider scaling** for production workloads

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify configuration in `.env` file
3. Check Docker and Docker Compose versions
4. Review this documentation
5. Check GitHub issues for known problems

---

**Happy Deploying! 🚀**

Your Sikkim Chatbot is now ready to serve citizens with Docker-powered reliability and ease of management.


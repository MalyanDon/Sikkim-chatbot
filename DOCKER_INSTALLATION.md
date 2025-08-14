# 🐳 Docker Installation Guide for Windows

This guide will help you install Docker Desktop on Windows to run the Sikkim Chatbot.

## 📋 System Requirements

- **Windows 10/11** (64-bit)
- **WSL 2** (Windows Subsystem for Linux 2)
- **Virtualization enabled** in BIOS
- **At least 4GB RAM**

## 🚀 Installation Steps

### 1. Enable WSL 2

Open PowerShell as Administrator and run:

```powershell
# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart your computer
Restart-Computer
```

After restart, open PowerShell as Administrator again and run:

```powershell
# Set WSL 2 as default
wsl --set-default-version 2

# Install Ubuntu (or your preferred Linux distribution)
wsl --install -d Ubuntu
```

### 2. Download Docker Desktop

1. Go to [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Click "Download from Docker Hub"
3. Download the latest version for Windows

### 3. Install Docker Desktop

1. **Run the installer** as Administrator
2. **Follow the installation wizard**
3. **Restart your computer** when prompted
4. **Start Docker Desktop** from the Start menu

### 4. Verify Installation

Open PowerShell and run:

```powershell
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Run test container
docker run hello-world
```

## 🔧 Configuration

### 1. Docker Desktop Settings

1. **Open Docker Desktop**
2. **Go to Settings** (gear icon)
3. **Resources > WSL Integration**
4. **Enable integration with Ubuntu**
5. **Apply & Restart**

### 2. WSL 2 Backend

Docker Desktop should automatically use WSL 2. If not:

1. **Settings > General**
2. **Check "Use WSL 2 based engine"**
3. **Apply & Restart**

## 🚨 Troubleshooting

### Common Issues

#### 1. "Docker Desktop is starting..."
- Wait a few minutes for first startup
- Check Windows Defender Firewall settings
- Ensure virtualization is enabled in BIOS

#### 2. WSL 2 Installation Issues
```powershell
# Update WSL
wsl --update

# Set WSL 2 as default
wsl --set-default-version 2
```

#### 3. Virtualization Not Enabled
1. **Restart computer and enter BIOS**
2. **Look for:**
   - Virtualization Technology
   - Intel VT-x
   - AMD-V
   - SVM Mode
3. **Enable and save**

#### 4. Port Conflicts
```powershell
# Check what's using port 8080
netstat -ano | findstr :8080

# Kill process if needed
taskkill /PID <PID> /F
```

### Performance Optimization

#### 1. Memory Allocation
1. **Docker Desktop Settings > Resources**
2. **Increase memory to 4GB+**
3. **Increase CPUs to 2+**

#### 2. WSL 2 Memory Limit
Create `%UserProfile%\.wslconfig`:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

## ✅ Post-Installation Test

After installation, test with:

```powershell
# Navigate to your project
cd C:\Sikkim\Sikkim-chatbot

# Test Docker
docker run --rm hello-world

# Test Docker Compose
docker-compose --version
```

## 🔗 Useful Commands

```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force

# Restart Docker service
Restart-Service docker

# View Docker logs
Get-EventLog -LogName Application -Source "Docker Desktop"
```

## 📚 Additional Resources

- [Docker Desktop Documentation](https://docs.docker.com/desktop/)
- [WSL 2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Hub](https://hub.docker.com/)

## 🎯 Next Steps

Once Docker is installed:

1. **Return to** `DOCKER_DEPLOYMENT.md`
2. **Follow the deployment guide**
3. **Build and run** your Sikkim Chatbot

---

**Happy Docker-ing! 🐳**

If you encounter issues, check the troubleshooting section or refer to the official Docker documentation.


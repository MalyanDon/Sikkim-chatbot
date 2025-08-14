@echo off
setlocal enabledelayedexpansion

REM Sikkim Chatbot Docker Deployment Script for Windows
REM This script helps you deploy the chatbot using Docker

echo 🚀 Sikkim Chatbot Docker Deployment Script
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo [INFO] Docker and Docker Compose are installed

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from example...
    if exist env.example (
        copy env.example .env >nul
        echo [WARNING] Please edit .env file with your actual configuration values
        echo [WARNING] Especially BOT_TOKEN is required!
        pause
        exit /b 1
    ) else (
        echo [ERROR] env.example file not found. Please create .env file manually.
        pause
        exit /b 1
    )
)

REM Check if BOT_TOKEN is set
findstr /C:"BOT_TOKEN=your_telegram_bot_token_here" .env >nul
if not errorlevel 1 (
    echo [ERROR] Please set your actual BOT_TOKEN in .env file
    pause
    exit /b 1
)

echo [INFO] .env file is properly configured

:menu
echo.
echo Available commands:
echo   build    - Build Docker image
echo   start    - Start services
echo   stop     - Stop services
echo   restart  - Restart services
echo   logs     - Show logs
echo   status   - Show status
echo   cleanup  - Clean up everything
echo   help     - Show this help
echo   exit     - Exit script
echo.

set /p command="Enter command: "

if /i "%command%"=="build" goto build
if /i "%command%"=="start" goto start
if /i "%command%"=="stop" goto stop
if /i "%command%"=="restart" goto restart
if /i "%command%"=="logs" goto logs
if /i "%command%"=="status" goto status
if /i "%command%"=="cleanup" goto cleanup
if /i "%command%"=="help" goto help
if /i "%command%"=="exit" goto exit
goto menu

:build
echo [INFO] Building Docker image...
docker-compose build --no-cache
echo [INFO] Docker image built successfully
pause
goto menu

:start
echo [INFO] Starting Sikkim Chatbot services...
docker-compose up -d
echo [INFO] Services started successfully
pause
goto menu

:stop
echo [INFO] Stopping Sikkim Chatbot services...
docker-compose down
echo [INFO] Services stopped successfully
pause
goto menu

:restart
echo [INFO] Restarting Sikkim Chatbot services...
docker-compose down
timeout /t 2 /nobreak >nul
docker-compose up -d
echo [INFO] Services restarted successfully
pause
goto menu

:logs
echo [INFO] Showing logs (Press Ctrl+C to exit)...
docker-compose logs -f
pause
goto menu

:status
echo [INFO] Container status:
docker-compose ps
echo.
echo [INFO] Resource usage:
docker stats --no-stream
pause
goto menu

:cleanup
echo [WARNING] This will remove all containers, images, and volumes. Are you sure? (Y/N)
set /p response=
if /i "%response%"=="Y" (
    echo [INFO] Cleaning up...
    docker-compose down -v --rmi all
    docker system prune -f
    echo [INFO] Cleanup completed
) else (
    echo [INFO] Cleanup cancelled
)
pause
goto menu

:help
echo.
echo Usage: %0 [command]
echo Run '%0 help' for more information
echo.
echo Commands:
echo   build    - Build Docker image
echo   start    - Start services
echo   stop     - Stop services
echo   restart  - Restart services
echo   logs     - Show logs
echo   status   - Show status
echo   cleanup  - Clean up everything
echo   help     - Show this help
echo   exit     - Exit script
pause
goto menu

:exit
echo [INFO] Goodbye!
exit /b 0


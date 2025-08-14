#!/bin/bash

# Sikkim Chatbot Docker Deployment Script
# This script helps you deploy the chatbot using Docker

set -e

echo "🚀 Sikkim Chatbot Docker Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from example..."
        if [ -f env.example ]; then
            cp env.example .env
            print_warning "Please edit .env file with your actual configuration values"
            print_warning "Especially BOT_TOKEN is required!"
            exit 1
        else
            print_error "env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    # Check if BOT_TOKEN is set
    if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=your_telegram_bot_token_here" .env; then
        print_error "Please set your actual BOT_TOKEN in .env file"
        exit 1
    fi
    
    print_status ".env file is properly configured"
}

# Build the Docker image
build_image() {
    print_status "Building Docker image..."
    docker-compose build --no-cache
    print_status "Docker image built successfully"
}

# Start the services
start_services() {
    print_status "Starting Sikkim Chatbot services..."
    docker-compose up -d
    print_status "Services started successfully"
}

# Stop the services
stop_services() {
    print_status "Stopping Sikkim Chatbot services..."
    docker-compose down
    print_status "Services stopped successfully"
}

# Show logs
show_logs() {
    print_status "Showing logs (Press Ctrl+C to exit)..."
    docker-compose logs -f
}

# Show status
show_status() {
    print_status "Container status:"
    docker-compose ps
    
    echo ""
    print_status "Resource usage:"
    docker stats --no-stream
}

# Clean up
cleanup() {
    print_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --rmi all
        docker system prune -f
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Available commands:"
    echo "  build    - Build Docker image"
    echo "  start    - Start services"
    echo "  stop     - Stop services"
    echo "  restart  - Restart services"
    echo "  logs     - Show logs"
    echo "  status   - Show status"
    echo "  cleanup  - Clean up everything"
    echo "  help     - Show this help"
    echo "  exit     - Exit script"
}

# Main function
main() {
    check_docker
    check_env
    
    case "${1:-}" in
        "build")
            build_image
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_menu
            ;;
        "exit")
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            show_menu
            echo ""
            echo "Usage: $0 [command]"
            echo "Run '$0 help' for more information"
            ;;
    esac
}

# Run main function with all arguments
main "$@"


#!/bin/bash

# Guardian Lite - Simple Deploy Script
# Creates and starts the Guardian Lite container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="guardian-lite"
CONTAINER_NAME="guardian"
IMAGE_NAME="guardian-lite"
PORT="8080"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "🚀 Guardian Lite - Simple Deploy"
print_status "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "Dockerfile" ] || [ ! -f "guardian.py" ]; then
    print_error "Please run this script from the Guardian Lite project directory."
    print_error "Required files: Dockerfile, guardian.py"
    exit 1
fi

# Stop and remove existing container if running
print_status "🛑 Stopping existing Guardian container..."
if docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
    docker stop ${CONTAINER_NAME} > /dev/null 2>&1 || true
    print_status "Stopped existing container"
fi

if docker ps -aq --filter "name=${CONTAINER_NAME}" | grep -q .; then
    docker rm ${CONTAINER_NAME} > /dev/null 2>&1 || true
    print_status "Removed existing container"
fi

# Build the image
print_status "🔨 Building Guardian Lite image..."
docker build -t ${IMAGE_NAME} .

if [ $? -ne 0 ]; then
    print_error "Build failed!"
    exit 1
fi
print_success "Image built successfully"

# Create necessary directories
print_status "📁 Creating necessary directories..."
mkdir -p state logs
print_success "Directories created"

# Run the container
print_status "🚀 Starting Guardian Lite..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/state:/app/state \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  ${IMAGE_NAME}

if [ $? -eq 0 ]; then
    print_success "Guardian Lite is now running!"
    echo ""
    print_status "🌐 Access the GUI at: http://localhost:${PORT}"
    
    # Get the actual IP if available
    if command -v hostname > /dev/null 2>&1; then
        LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
        if [ "$LOCAL_IP" != "localhost" ]; then
            print_status "📱 Or from another device: http://${LOCAL_IP}:${PORT}"
        fi
    fi
    
    echo ""
    print_status "📋 Next steps:"
    echo "1. Open the web interface"
    echo "2. Configure your Telegram bot token and chat ID"
    echo "3. Add your containers to monitor"
    echo "4. Enable cron scheduling"
    echo ""
    print_status "📜 View logs: docker logs ${CONTAINER_NAME}"
    print_status "🛑 Stop: ./destroy.sh"
    print_status "📊 Status: docker ps --filter name=${CONTAINER_NAME}"
    
    # Show container status
    echo ""
    print_status "Container Status:"
    docker ps --filter name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
else
    print_error "Failed to start Guardian Lite!"
    exit 1
fi
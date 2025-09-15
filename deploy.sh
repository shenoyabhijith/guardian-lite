#!/bin/bash

# Guardian Lite Deployment Script
# Quick setup for Raspberry Pi

echo "🚀 Guardian Lite - Container Auto-Updater Setup"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the image
echo "🔨 Building Guardian Lite image..."
docker build -t guardian-lite .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Stop existing container if running
echo "🛑 Stopping existing Guardian container..."
docker stop guardian 2>/dev/null || true
docker rm guardian 2>/dev/null || true

# Run the container
echo "🚀 Starting Guardian Lite..."
docker run -d \
  --name guardian \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  --restart unless-stopped \
  guardian-lite

if [ $? -eq 0 ]; then
    echo "✅ Guardian Lite is now running!"
    echo ""
    echo "🌐 Access the GUI at: http://localhost:8080"
    echo "📱 Or from another device: http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📋 Next steps:"
    echo "1. Open the web interface"
    echo "2. Configure your Telegram bot token and chat ID"
    echo "3. Add your containers to monitor"
    echo "4. Enable cron scheduling"
    echo ""
    echo "📜 View logs: docker logs guardian"
    echo "🛑 Stop: docker stop guardian"
else
    echo "❌ Failed to start Guardian Lite!"
    exit 1
fi

#!/bin/bash

# Guardian Lite Docker Compose Deployment Script
# Supports development, production, and custom environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
COMPOSE_FILE="docker-compose.dev.yml"
BUILD_IMAGE=true

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

# Function to show usage
show_usage() {
    echo "Guardian Lite Docker Compose Deployment Script"
    echo "=============================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV     Environment (dev|prod|custom) [default: dev]"
    echo "  -f, --file FILE   Custom compose file"
    echo "  --no-build        Skip building the image"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy in development mode"
    echo "  $0 -e prod            # Deploy in production mode"
    echo "  $0 -f custom.yml      # Use custom compose file"
    echo "  $0 --no-build         # Skip building, use existing image"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --no-build)
            BUILD_IMAGE=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set compose file based on environment
case $ENVIRONMENT in
    dev)
        COMPOSE_FILE="docker-compose.dev.yml"
        print_status "Using development configuration"
        ;;
    prod)
        COMPOSE_FILE="docker-compose.prod.yml"
        print_status "Using production configuration"
        ;;
    custom)
        if [[ ! -f "$COMPOSE_FILE" ]]; then
            print_error "Custom compose file '$COMPOSE_FILE' not found!"
            exit 1
        fi
        print_status "Using custom configuration: $COMPOSE_FILE"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        print_error "Valid environments: dev, prod, custom"
        exit 1
        ;;
esac

print_status "🚀 Guardian Lite - Container Auto-Updater Setup"
print_status "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed or not available."
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_status "Using: $COMPOSE_CMD"

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_error "Compose file '$COMPOSE_FILE' not found!"
    exit 1
fi

# Stop existing containers
print_status "🛑 Stopping existing Guardian containers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true

# Build image if requested
if [[ "$BUILD_IMAGE" == true ]]; then
    print_status "🔨 Building Guardian Lite image..."
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" build
    else
        docker build -t guardian-lite .
    fi
    
    if [[ $? -ne 0 ]]; then
        print_error "Build failed!"
        exit 1
    fi
    print_success "Image built successfully"
fi

# Start the services
print_status "🚀 Starting Guardian Lite..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

if [[ $? -eq 0 ]]; then
    print_success "Guardian Lite is now running!"
    echo ""
    print_status "🌐 Access the GUI at: http://localhost:8080"
    
    # Get the actual IP if available
    if command -v hostname &> /dev/null; then
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        if [[ "$LOCAL_IP" != "localhost" ]]; then
            print_status "📱 Or from another device: http://$LOCAL_IP:8080"
        fi
    fi
    
    echo ""
    print_status "📋 Next steps:"
    echo "1. Open the web interface"
    echo "2. Configure your Telegram bot token and chat ID"
    echo "3. Add your containers to monitor"
    echo "4. Enable cron scheduling"
    echo ""
    print_status "📜 View logs: $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    print_status "🛑 Stop: $COMPOSE_CMD -f $COMPOSE_FILE down"
    print_status "📊 Status: $COMPOSE_CMD -f $COMPOSE_FILE ps"
    
    # Show container status
    echo ""
    print_status "Container Status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    
else
    print_error "Failed to start Guardian Lite!"
    exit 1
fi

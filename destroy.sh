#!/bin/bash

# Guardian Lite - Destroy Script
# Stops and removes Guardian Lite containers and cleans up project resources

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
ARCHIVE_DIR="archives"

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

print_status "🗑️ Guardian Lite - Destroy & Cleanup"
print_status "===================================="

# Ask for confirmation before proceeding
echo ""
print_warning "⚠️  WARNING: This will destroy all Guardian Lite containers and resources!"
print_warning "⚠️  This action cannot be undone!"
echo ""
print_status "The following will be removed:"
echo "  • All Guardian Lite containers (with optional archiving)"
echo "  • Guardian Lite Docker images"
echo "  • Guardian Lite networks and volumes"
echo "  • Guardian Lite cron jobs"
echo "  • Optional: Orphaned containers and unused images"
echo ""

read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Operation cancelled by user."
    exit 0
fi

echo ""
print_status "Starting cleanup process..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Function to create archive directory
create_archive_dir() {
    if [[ ! -d "$ARCHIVE_DIR" ]]; then
        mkdir -p "$ARCHIVE_DIR"
        print_status "Created archive directory: $ARCHIVE_DIR"
    fi
}

# Function to archive container configuration
archive_container() {
    local container_id="$1"
    local container_name="$2"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local archive_file="${ARCHIVE_DIR}/${container_name}_${timestamp}.json"
    
    print_status "📦 Archiving container: ${container_name} (${container_id})"
    
    # Get container configuration
    local container_config=$(docker inspect "${container_id}" 2>/dev/null || echo "{}")
    
    if [[ "$container_config" != "{}" ]]; then
        # Save container configuration
        echo "$container_config" > "$archive_file"
        
        # Also save a human-readable summary
        local summary_file="${ARCHIVE_DIR}/${container_name}_${timestamp}_summary.txt"
        {
            echo "Container Archive Summary"
            echo "========================="
            echo "Container ID: ${container_id}"
            echo "Container Name: ${container_name}"
            echo "Archived: $(date)"
            echo ""
            echo "Image: $(echo "$container_config" | jq -r '.[0].Config.Image // "unknown"')"
            echo "Status: $(echo "$container_config" | jq -r '.[0].State.Status // "unknown"')"
            echo "Created: $(echo "$container_config" | jq -r '.[0].Created // "unknown"')"
            echo "Ports: $(echo "$container_config" | jq -r '.[0].NetworkSettings.Ports // {}')"
            echo "Volumes: $(echo "$container_config" | jq -r '.[0].Mounts // []')"
            echo "Environment: $(echo "$container_config" | jq -r '.[0].Config.Env // []')"
        } > "$summary_file"
        
        print_success "Archived to: $archive_file"
        print_success "Summary saved to: $summary_file"
    else
        print_warning "Could not inspect container ${container_id}, skipping archive"
    fi
}

# Function to stop and remove containers with archiving
cleanup_containers() {
    local container_pattern="$1"
    local description="$2"
    local should_archive="$3"
    
    print_status "🔍 Looking for ${description}..."
    
    # Find containers matching the pattern
    local containers=$(docker ps -aq --filter "name=${container_pattern}" 2>/dev/null || true)
    
    if [[ -n "$containers" ]]; then
        print_status "Found containers: $(echo $containers | tr '\n' ' ')"
        
        # Create archive directory if needed
        if [[ "$should_archive" == "true" ]]; then
            create_archive_dir
        fi
        
        # Stop running containers and archive if requested
        for container in $containers; do
            if docker ps -q --filter "id=${container}" | grep -q .; then
                print_status "Stopping container: ${container}"
                docker stop ${container} > /dev/null 2>&1 || true
            fi
            
            # Archive container configuration before removal
            if [[ "$should_archive" == "true" ]]; then
                local container_name=$(docker inspect --format='{{.Name}}' "${container}" 2>/dev/null | sed 's/^\///' || echo "unknown_${container}")
                archive_container "${container}" "${container_name}"
            fi
            
            # Remove container
            print_status "Removing container: ${container}"
            docker rm ${container} > /dev/null 2>&1 || true
        done
        
        print_success "Cleaned up ${description}"
    else
        print_status "No ${description} found"
    fi
}

# Function to clean up images
cleanup_images() {
    print_status "🔍 Looking for Guardian Lite images..."
    
    # Find images matching our project
    local images=$(docker images -q --filter "reference=${IMAGE_NAME}" 2>/dev/null || true)
    
    if [[ -n "$images" ]]; then
        print_status "Found images: $(echo $images | tr '\n' ' ')"
        
        for image in $images; do
            print_status "Removing image: ${image}"
            docker rmi ${image} > /dev/null 2>&1 || true
        done
        
        print_success "Cleaned up Guardian Lite images"
    else
        print_status "No Guardian Lite images found"
    fi
}

# Function to clean up networks
cleanup_networks() {
    print_status "🔍 Looking for Guardian Lite networks..."
    
    # Find networks created by our project
    local networks=$(docker network ls -q --filter "name=guardian" 2>/dev/null || true)
    
    if [[ -n "$networks" ]]; then
        print_status "Found networks: $(echo $networks | tr '\n' ' ')"
        
        for network in $networks; do
            print_status "Removing network: ${network}"
            docker network rm ${network} > /dev/null 2>&1 || true
        done
        
        print_success "Cleaned up Guardian Lite networks"
    else
        print_status "No Guardian Lite networks found"
    fi
}

# Function to clean up volumes
cleanup_volumes() {
    print_status "🔍 Looking for Guardian Lite volumes..."
    
    # Find volumes created by our project
    local volumes=$(docker volume ls -q --filter "name=guardian" 2>/dev/null || true)
    
    if [[ -n "$volumes" ]]; then
        print_status "Found volumes: $(echo $volumes | tr '\n' ' ')"
        
        for volume in $volumes; do
            print_status "Removing volume: ${volume}"
            docker volume rm ${volume} > /dev/null 2>&1 || true
        done
        
        print_success "Cleaned up Guardian Lite volumes"
    else
        print_status "No Guardian Lite volumes found"
    fi
}

# Function to clean up cron jobs
cleanup_cron() {
    print_status "🔍 Looking for Guardian Lite cron jobs..."
    
    # Check if cron is available
    if ! command -v crontab &> /dev/null; then
        print_status "Crontab not available, skipping cron cleanup"
        return
    fi
    
    # Get current crontab
    local current_cron=$(crontab -l 2>/dev/null || echo "")
    
    if [[ -n "$current_cron" ]] && echo "$current_cron" | grep -q "guardian"; then
        print_status "Found Guardian Lite cron jobs"
        
        # Remove guardian-related cron entries
        echo "$current_cron" | grep -v "guardian" | crontab - 2>/dev/null || true
        
        print_success "Cleaned up Guardian Lite cron jobs"
    else
        print_status "No Guardian Lite cron jobs found"
    fi
}

# Function to list archived containers
list_archives() {
    if [[ -d "$ARCHIVE_DIR" ]] && [[ -n "$(ls -A "$ARCHIVE_DIR" 2>/dev/null)" ]]; then
        print_status "📦 Archived containers:"
        ls -la "$ARCHIVE_DIR"/*.json 2>/dev/null | while read -r line; do
            local file=$(echo "$line" | awk '{print $NF}')
            local size=$(echo "$line" | awk '{print $5}')
            local date=$(echo "$line" | awk '{print $6, $7, $8}')
            local filename=$(basename "$file")
            echo "  • $filename ($size bytes) - $date"
        done
        echo ""
        print_status "To restore a container, use: docker run with the archived configuration"
    else
        print_status "No archived containers found"
    fi
}

# Main cleanup process
# 1. Stop and remove main container (with archiving)
cleanup_containers "${CONTAINER_NAME}" "main Guardian Lite container" "true"

# 2. Stop and remove any containers with 'guardian' in the name (with archiving)
cleanup_containers "guardian" "all Guardian Lite containers" "true"

# 3. Clean up images
cleanup_images

# 4. Clean up networks
cleanup_networks

# 5. Clean up volumes
cleanup_volumes

# 6. Clean up cron jobs
cleanup_cron

# 7. Clean up any orphaned containers (containers without images)
print_status "🔍 Looking for orphaned containers..."
orphaned=$(docker ps -aq --filter "dangling=true" 2>/dev/null || true)

if [[ -n "$orphaned" ]]; then
    print_warning "Found orphaned containers: $(echo $orphaned | tr '\n' ' ')"
    read -p "Do you want to remove orphaned containers? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for container in $orphaned; do
            print_status "Removing orphaned container: ${container}"
            docker rm ${container} > /dev/null 2>&1 || true
        done
        print_success "Cleaned up orphaned containers"
    else
        print_status "Skipped orphaned container cleanup"
    fi
else
    print_status "No orphaned containers found"
fi

# 8. Clean up unused images
print_status "🔍 Looking for unused images..."
unused_images=$(docker images -f "dangling=true" -q 2>/dev/null || true)

if [[ -n "$unused_images" ]]; then
    print_warning "Found unused images: $(echo $unused_images | tr '\n' ' ')"
    read -p "Do you want to remove unused images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for image in $unused_images; do
            print_status "Removing unused image: ${image}"
            docker rmi ${image} > /dev/null 2>&1 || true
        done
        print_success "Cleaned up unused images"
    else
        print_status "Skipped unused image cleanup"
    fi
else
    print_status "No unused images found"
fi

# Final status
echo ""
print_success "🎉 Guardian Lite cleanup completed!"
echo ""
print_status "Summary of cleanup:"
echo "✅ Stopped and removed all Guardian Lite containers"
echo "✅ Archived container configurations for future reference"
echo "✅ Removed Guardian Lite images"
echo "✅ Cleaned up Guardian Lite networks"
echo "✅ Cleaned up Guardian Lite volumes"
echo "✅ Removed Guardian Lite cron jobs"
echo ""

# List archived containers
list_archives

print_status "To redeploy Guardian Lite, run: ./deploy.sh"
print_status "To check Docker status: docker ps -a"

# Guardian Lite

🚀 **A featherweight container auto-updater with GUI, Telegram alerts, and ARM support for Raspberry Pi**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org/)
[![ARM](https://img.shields.io/badge/ARM-Raspberry%20Pi-red?logo=raspberry-pi)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🖥️ **Modern Web GUI** - Apple Music-inspired design with responsive interface
- 📱 **Telegram alerts** - Real-time notifications for all events
- 🔄 **Auto-update + rollback** - Smart container management with automatic rollback on failure
- 🍓 **Raspberry Pi compatible** - ARM-optimized Docker image
- ⚡ **Zero bloat** - Just Flask + vanilla JS/CSS (no heavy frameworks)
- ⏰ **GUI-based Cron scheduling** - User-friendly interface with automatic expression generation
- 🩺 **Health checks** - Optional URL monitoring for container health with retry mechanism
- 🧹 **Cleanup** - Automatic unused image removal
- 📊 **Live logs** - Real-time log viewing with clear functionality
- 🔧 **Robust Docker integration** - Multiple fallback methods for Docker operations
- 🎨 **Consistent UI** - Beautiful, modern interface with smooth animations
- 🚀 **Container management** - Add/remove containers with visual feedback
- 🔍 **External update checking** - Docker Hub API integration to check for image updates
- 📈 **Version comparison** - Display current vs latest available image versions
- 🏷️ **Update indicators** - Visual badges showing when updates are available

## 📁 Project Structure

```
guardian-lite/
├── deploy.sh              # Simple deployment script
├── destroy.sh             # Cleanup script with archiving
├── Dockerfile             # Container definition
├── requirements.txt        # Python dependencies
├── guardian.py            # Core update/rollback logic
├── web.py                 # Flask GUI server
├── config.json            # Configuration file
├── static/
│   ├── style.css          # GUI styles
│   └── script.js          # GUI functionality
├── templates/
│   └── index.html         # Web interface
├── state/                 # Container backups for rollback
├── logs/                  # Application logs
├── archives/              # Archived container configurations
└── README.md
```

## 🚀 Quick Start

```bash
git clone https://github.com/shenoyabhijith/guardian-lite.git
cd guardian-lite

# Deploy Guardian Lite
./deploy.sh

# Destroy and cleanup everything
./destroy.sh
```

### Access GUI

Open your browser and go to: `http://your-pi-ip:8082`

### 3. Configure

1. Set up your Telegram bot token and chat ID
2. Add containers to monitor
3. Enable cron scheduling
4. Save and enjoy automated updates!

## 📋 Requirements

- Docker
- Raspberry Pi (or any ARM/x86 system)
- Internet connection for Telegram notifications

## 🔧 Configuration

The GUI allows you to configure:

- **Telegram Settings**: Bot token and chat ID for notifications
- **Global Settings**: Cleanup options, dry run mode, check intervals
- **Cron Scheduler**: Automatic update scheduling
- **Containers**: Add/remove containers to monitor and update

## ⏰ GUI-Based Cron Scheduling

The GUI provides an intuitive interface for scheduling updates:

- **Every Hour**: Simple hourly updates
- **Daily**: Choose specific time of day (12:00 AM - 11:00 PM)
- **Weekly**: Select day of week and time
- **Custom Interval**: Set custom minutes (1-59 minutes)
- **Manual**: Advanced users can still enter cron expressions
- **Real-time Preview**: See generated cron expression as you configure
- **Automatic Installation**: Cron jobs are automatically installed/removed

## 📱 Telegram Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Get your chat ID (send a message to your bot, then visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`)
4. Enter both in the GUI

## 🐳 Docker Support

Guardian Lite runs in Docker and manages other Docker containers. It requires:

- Access to Docker socket (`/var/run/docker.sock`)
- Persistent volume for configuration and logs
- Network access for Telegram API and health checks

### Manual Docker Commands

```bash
# Build image
docker build -t guardian-lite .

# Run container
docker run -d --name guardian -p 8082:8082 -v /var/run/docker.sock:/var/run/docker.sock guardian-lite

# View logs
docker logs guardian

# Stop container
docker stop guardian && docker rm guardian
```

## 📊 Monitoring

- **GUI Logs**: Real-time log viewing in the web interface with clear functionality
- **File Logs**: Detailed logs in `logs/guardian.log`
- **Telegram**: Instant notifications for all events
- **Container Status**: Live monitoring of all Docker containers
- **Health Checks**: Automatic health monitoring with retry mechanisms

## 🔧 Recent Improvements

- **Fixed Docker Client Issues**: Robust fallback mechanisms for Docker operations
- **Enhanced UI**: Apple Music-inspired design with consistent theming
- **Improved Health Checks**: Retry mechanism with proper timing for container startup
- **Clear Logs Functionality**: Web interface now includes log clearing capability
- **Port Optimization**: Updated to use port 8082 to avoid conflicts
- **Better Error Handling**: Comprehensive error handling throughout the application
- **External Update Checking**: Docker Hub API integration for real-time update detection
- **Version Comparison**: Visual display of current vs latest available image versions
- **Update Indicators**: Animated badges showing when container updates are available

## 🔍 External Update Checking

Guardian Lite now includes real-time container image update detection using Docker Hub API:

### **How It Works:**
1. **API Integration**: Queries Docker Hub v2 API for latest image tags
2. **Version Comparison**: Compares current container tags with latest available
3. **Visual Indicators**: Shows update badges and version information
4. **Real-time Updates**: Checks for updates every time containers are loaded

### **Features:**
- **Update Badges**: Orange pulsing badges when updates are available
- **Version Display**: Shows current vs latest version tags
- **Tag Information**: Displays available tags with timestamps
- **Error Handling**: Graceful fallback when API calls fail
- **Performance**: Efficient caching and timeout handling

### **Supported Registries:**
- ✅ Docker Hub (docker.io) - Full support
- 🔄 Other registries - Planned for future releases

### **Example Display:**
```
Container: nginx-web
Image: nginx:latest
Status: Up 2 hours
Update Available: ✅
Current: latest
Latest: stable-perl
```

## 🤝 Contributing

Contributions welcome! This is designed to be simple and lightweight.

## 📄 License

MIT License - feel free to use and modify!

---

**Your Pi now has a brain 🧠 — and it speaks Telegram.**  
Update containers. Sleep well.
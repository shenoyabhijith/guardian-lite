# Guardian Lite

🚀 **A featherweight container auto-updater with GUI, Telegram alerts, and ARM support for Raspberry Pi**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org/)
[![ARM](https://img.shields.io/badge/ARM-Raspberry%20Pi-red?logo=raspberry-pi)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🖥️ **Ultra-simple GUI** - Configure everything via web interface
- 📱 **Telegram alerts** - Real-time notifications for all events
- 🔄 **Auto-update + rollback** - Smart container management with automatic rollback on failure
- 🍓 **Raspberry Pi compatible** - ARM-optimized Docker image
- ⚡ **Zero bloat** - Just Flask + vanilla JS/CSS (no heavy frameworks)
- ⏰ **Cron scheduling** - Automatic updates with customizable schedules
- 🩺 **Health checks** - Optional URL monitoring for container health
- 🧹 **Cleanup** - Automatic unused image removal
- 📊 **Live logs** - Real-time log viewing in the web interface

## 🚀 Quick Start

### 1. Clone and Deploy

```bash
git clone https://github.com/shenoyabhijith/guardian-lite.git
cd guardian-lite
./deploy.sh
```

### 2. Access GUI

Open your browser and go to: `http://your-pi-ip:8080`

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

## 📊 Monitoring

- **GUI Logs**: Real-time log viewing in the web interface
- **File Logs**: Detailed logs in `logs/guardian.log`
- **Telegram**: Instant notifications for all events

## 🤝 Contributing

Contributions welcome! This is designed to be simple and lightweight.

## 📄 License

MIT License - feel free to use and modify!

---

**Your Pi now has a brain 🧠 — and it speaks Telegram.**  
Update containers. Sleep well.
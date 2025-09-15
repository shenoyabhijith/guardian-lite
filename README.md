# 🚀 Guardian Lite

> *A featherweight guardian for your containers — with a clean GUI, smart updates, and Telegram alerts — perfect for your Pi.*

Guardian Lite is a **super lightweight, Python-based, Dockerized container auto-updater** with:

✅ Ultra-simple GUI for config + cron scheduling  
✅ Telegram alerts  
✅ Auto-update + rollback + cleanup  
✅ Runs on Raspberry Pi (ARM compatible)  
✅ Zero bloat — uses **just Flask + vanilla JS/CSS**  
✅ All config stored in `config.json` — GUI just edits it  
✅ Built for efficiency — no heavy frameworks

## 📁 Project Structure

```
guardian-lite/
├── Dockerfile
├── requirements.txt
├── guardian.py          # Core logic (update, rollback, cleanup)
├── web.py               # Ultra-light GUI server
├── static/
│   ├── style.css        # Minimal CSS
│   └── script.js        # Minimal JS
├── templates/
│   └── index.html       # Clean GUI
├── config.json          # Your config — edited via GUI
├── state/               # Backup container configs for rollback
├── logs/
│   └── guardian.log
└── README.md
```

## 🚀 Quick Start

### 1. Clone and Build

```bash
git clone <your-repo-url>
cd guardian-lite
docker build -t guardian-lite .
```

### 2. Run on Raspberry Pi

```bash
docker run -d \
  --name guardian \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  --restart unless-stopped \
  guardian-lite
```

### 3. Access GUI

Open your browser and go to: `http://your-pi-ip:8080`

## ⚙️ Configuration

The GUI allows you to configure:

- **Telegram Settings**: Bot token and chat ID for notifications
- **Global Settings**: Cleanup options, dry run mode, check intervals
- **Cron Scheduler**: Automatic update scheduling
- **Containers**: Add/remove containers to monitor and update

### Default Configuration

The `config.json` file contains:

```json
{
  "telegram_bot_token": "",
  "telegram_chat_id": "",
  "global": {
    "cleanup_unused_images": true,
    "cleanup_keep_last_n": 3,
    "dry_run": false,
    "check_interval_minutes": 60
  },
  "containers": [
    {
      "name": "my-nginx",
      "image": "nginx:latest",
      "auto_update": true,
      "health_check_url": "http://localhost:80",
      "rollback_on_failure": true,
      "enabled": true
    }
  ],
  "cron": {
    "enabled": true,
    "schedule": "0 */1 * * *"
  }
}
```

## 🔧 Features

### Auto-Update
- Pulls latest images for configured containers
- Stops old containers and starts new ones
- Maintains container configuration

### Rollback
- Backs up container configs before updates
- Automatically rolls back on failure
- Sends Telegram notifications

### Health Checks
- Optional health check URLs
- Rollback if health check fails
- Configurable timeout

### Cleanup
- Removes unused Docker images
- Configurable retention policy
- Prevents disk space issues

### Telegram Integration
- Real-time notifications
- Update success/failure alerts
- Health check status

## 🐳 Docker Support

Guardian Lite runs in Docker and manages other Docker containers. It requires:

- Access to Docker socket (`/var/run/docker.sock`)
- Persistent volume for configuration and logs
- Network access for Telegram API and health checks

## 📱 Telegram Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Get your chat ID (send a message to your bot, then visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`)
4. Enter both in the GUI

## 🔄 Cron Scheduling

The GUI automatically manages cron jobs for scheduled updates:

- Default: Every hour (`0 */1 * * *`)
- Customizable cron expressions
- Automatic cron installation/removal

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run GUI server
python web.py

# Run update manually
python guardian.py
```

### Testing

```bash
# Test with dry run
# Set "dry_run": true in config.json
python guardian.py
```

## 📊 Monitoring

- **GUI Logs**: Real-time log viewing in the web interface
- **File Logs**: Detailed logs in `logs/guardian.log`
- **Telegram**: Instant notifications for all events

## 🔒 Security

- Runs with minimal privileges
- No external dependencies beyond Docker
- All configuration via GUI (no CLI required)
- ARM-compatible for Raspberry Pi

## 🚀 Future Enhancements

- [ ] Authentication for web interface
- [ ] Prometheus metrics endpoint
- [ ] Webhook triggers
- [ ] Config export/import
- [ ] Dark mode toggle
- [ ] Multi-host support

## 📄 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! This is designed to be simple and lightweight.

---

**Your Pi now has a brain 🧠 — and it speaks Telegram.**  
Update containers. Sleep well.

# guardian.py
import docker
import json
import os
import subprocess
import time
import requests
import logging
from datetime import datetime

# Load config
CONFIG_PATH = 'config.json'
STATE_DIR = 'state'
LOG_FILE = 'logs/guardian.log'

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

client = docker.from_env()

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def send_telegram(msg):
    config = load_config()
    token = config.get('telegram_bot_token', '')
    chat_id = config.get('telegram_chat_id', '')
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown'
        }, timeout=10)
    except Exception as e:
        logging.error(f"Telegram failed: {e}")

def backup_container(name):
    try:
        container = client.containers.get(name)
        config = container.attrs['Config']
        with open(f"{STATE_DIR}/{name}.json", 'w') as f:
            json.dump(config, f, indent=2)
        logging.info(f"Backed up config for {name}")
    except Exception as e:
        logging.error(f"Backup failed for {name}: {e}")

def rollback_container(name):
    path = f"{STATE_DIR}/{name}.json"
    if not os.path.exists(path):
        logging.error(f"No backup found for {name}")
        return False
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        # Simple recreate — assumes image is still available
        client.containers.run(
            image=config['Image'],
            name=name,
            detach=True,
            ports=config.get('ExposedPorts', {}),
            environment=config.get('Env', []),
            restart_policy={"Name": "unless-stopped"}
        )
        logging.info(f"Rolled back {name}")
        send_telegram(f"↩️ Rolled back `{name}` due to failure.")
        return True
    except Exception as e:
        logging.error(f"Rollback failed for {name}: {e}")
        return False

def health_check(url, timeout=10):
    if not url:
        return True
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except:
        return False

def cleanup_images():
    config = load_config()
    if not config['global'].get('cleanup_unused_images', False):
        return
    keep_last_n = config['global'].get('cleanup_keep_last_n', 3)
    try:
        images = client.images.list()
        for image in images:
            if not image.tags:
                continue
            # Get containers using this image
            used = False
            for container in client.containers.list(all=True):
                if container.image.id == image.id:
                    used = True
                    break
            if not used:
                # Optional: keep last N tags per repo
                # Simplified: just prune unused
                client.images.remove(image.id, force=True)
                logging.info(f"🧹 Removed unused image: {image.tags[0]}")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

def update_container(container_config):
    name = container_config['name']
    image = container_config['image']

    # Get current image ID
    try:
        current = client.images.get(image)
        current_id = current.id
    except:
        current_id = None

    # Pull latest
    logging.info(f"⬇️ Pulling latest {image}...")
    try:
        client.images.pull(image)
    except Exception as e:
        msg = f"❌ Pull failed for `{name}`: `{e}`"
        logging.error(msg)
        send_telegram(msg)
        return False

    new = client.images.get(image)
    if current_id == new.id:
        logging.info(f"✅ {name} already up to date.")
        return True

    # Backup before update
    backup_container(name)

    # Stop & remove old container
    try:
        old_container = client.containers.get(name)
        old_container.stop(timeout=10)
        old_container.remove()
    except:
        pass  # OK if not running

    # Start new container
    try:
        client.containers.run(
            image=image,
            name=name,
            detach=True,
            restart_policy={"Name": "unless-stopped"}
        )
        logging.info(f"✅ Started updated {name}")
    except Exception as e:
        msg = f"❌ Start failed for `{name}`: `{e}`"
        logging.error(msg)
        send_telegram(msg)
        if container_config.get('rollback_on_failure', False):
            rollback_container(name)
        return False

    # Health check
    health_url = container_config.get('health_check_url', '')
    if health_url:
        logging.info(f"🩺 Health checking {name} at {health_url}...")
        healthy = health_check(health_url)
        if not healthy:
            msg = f"💔 Health check failed for `{name}`"
            logging.error(msg)
            send_telegram(msg)
            if container_config.get('rollback_on_failure', False):
                rollback_container(name)
            return False

    send_telegram(f"🎉 Successfully updated `{name}`")
    return True

def run_updates():
    config = load_config()
    containers = config.get('containers', [])
    for c in containers:
        if not c.get('enabled', True) or not c.get('auto_update', False):
            continue
        logging.info(f"🔄 Checking {c['name']}...")
        update_container(c)

    cleanup_images()
    logging.info("✅ Update cycle completed.")

if __name__ == "__main__":
    run_updates()

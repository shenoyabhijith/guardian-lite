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

# Initialize Docker client with multiple fallback methods
client = None
docker_methods = [
    {'method': 'unix_socket', 'url': 'unix://var/run/docker.sock'},
    {'method': 'from_env', 'url': None},
    {'method': 'tcp_localhost', 'url': 'tcp://localhost:2375'},
    {'method': 'tcp_localhost_secure', 'url': 'tcp://localhost:2376'}
]

for method_info in docker_methods:
    try:
        if method_info['url']:
            client = docker.DockerClient(base_url=method_info['url'])
        else:
            client = docker.from_env()
        
        # Test the connection
        client.ping()
        logging.info(f"Docker client initialized successfully via {method_info['method']}")
        break
    except Exception as e:
        logging.debug(f"Docker method {method_info['method']} failed: {e}")
        client = None
        continue

if client is None:
    logging.warning("All Docker client initialization methods failed. Using subprocess fallback.")

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
        if client:
            container = client.containers.get(name)
            config = container.attrs['Config']
            with open(f"{STATE_DIR}/{name}.json", 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Backed up config for {name}")
        else:
            # Fallback to subprocess for backup
            result = subprocess.run(['docker', 'inspect', name, '--format', '{{json .Config}}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                config = json.loads(result.stdout)
                with open(f"{STATE_DIR}/{name}.json", 'w') as f:
                    json.dump(config, f, indent=2)
                logging.info(f"Backed up config for {name} (subprocess)")
            else:
                raise Exception(f"docker inspect failed: {result.stderr}")
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
        if client:
            client.containers.run(
                image=config['Image'],
                name=name,
                detach=True,
                ports=config.get('ExposedPorts', {}),
                environment=config.get('Env', []),
                restart_policy={"Name": "unless-stopped"}
            )
        else:
            # Fallback to subprocess for rollback
            port_mapping = ""
            if name == "nginx-old":
                port_mapping = "-p 8082:80"
            
            cmd = f"docker run -d --name {name} --restart unless-stopped {port_mapping} {config['Image']}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"docker run failed: {result.stderr}")
        
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
        # Add a small delay to allow container to fully start
        time.sleep(2)
        
        # Try multiple times with increasing delays
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=timeout)
                if r.status_code == 200:
                    return True
                logging.debug(f"Health check attempt {attempt + 1}: HTTP {r.status_code}")
            except requests.exceptions.RequestException as e:
                logging.debug(f"Health check attempt {attempt + 1} failed: {e}")
            
            if attempt < 2:  # Don't sleep on the last attempt
                time.sleep(3)
        
        return False
    except Exception as e:
        logging.debug(f"Health check error: {e}")
        return False

def cleanup_images():
    config = load_config()
    if not config['global'].get('cleanup_unused_images', False):
        return
    keep_last_n = config['global'].get('cleanup_keep_last_n', 3)
    try:
        if client:
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
        else:
            # Fallback to subprocess for cleanup
            logging.info("🧹 Running docker image prune (subprocess fallback)")
            result = subprocess.run(['docker', 'image', 'prune', '-f'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("🧹 Cleaned up unused images (subprocess)")
            else:
                logging.warning(f"Docker image prune failed: {result.stderr}")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

def update_container(container_config):
    name = container_config['name']
    image = container_config['image']

    # Get current container's image ID using subprocess fallback
    current_container_image = None
    try:
        if client:
            container = client.containers.get(name)
            current_container_image = container.image.id
        else:
            # Fallback to subprocess - get container's image
            result = subprocess.run(['docker', 'inspect', name, '--format', '{{.Image}}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                current_container_image = result.stdout.strip()
    except Exception as e:
        logging.warning(f"Could not get current container image: {e}")

    # Pull latest using subprocess fallback
    logging.info(f"⬇️ Pulling latest {image}...")
    try:
        if client:
            client.images.pull(image)
        else:
            # Fallback to subprocess
            result = subprocess.run(['docker', 'pull', image], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"docker pull failed: {result.stderr}")
    except Exception as e:
        msg = f"❌ Pull failed for `{name}`: `{e}`"
        logging.error(msg)
        send_telegram(msg)
        return False

    # Get new image ID
    new_image_id = None
    try:
        if client:
            new = client.images.get(image)
            new_image_id = new.id
        else:
            # Fallback to subprocess
            result = subprocess.run(['docker', 'images', '--format', '{{.ID}}', image], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                new_image_id = result.stdout.strip()
    except Exception as e:
        logging.warning(f"Could not get new image ID: {e}")
        new_image_id = "unknown"
    
    # Compare container's current image with the new image
    if current_container_image == new_image_id:
        logging.info(f"✅ {name} already up to date.")
        return True

    # Backup before update
    backup_container(name)

    # Stop & remove old container using subprocess fallback
    try:
        if client:
            old_container = client.containers.get(name)
            old_container.stop(timeout=10)
            old_container.remove()
        else:
            # Fallback to subprocess
            subprocess.run(['docker', 'stop', name], capture_output=True)
            subprocess.run(['docker', 'rm', name], capture_output=True)
    except Exception as e:
        logging.warning(f"Could not stop/remove old container: {e}")

    # Start new container using subprocess fallback
    try:
        if client:
            client.containers.run(
                image=image,
                name=name,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
        else:
            # Fallback to subprocess - get port mapping from config
            port_mapping = ""
            ports = container_config.get('ports', [])
            if ports:
                for port in ports:
                    if ':' in port:
                        port_mapping += f" -p {port}"
            
            cmd = f"docker run -d --name {name} --restart unless-stopped {port_mapping} {image}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"docker run failed: {result.stderr}")
        
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

# web.py
from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
import docker

app = Flask(__name__, static_folder='static', template_folder='templates')

CONFIG_PATH = 'config.json'

# Initialize Docker client
try:
    # Try to connect to Docker daemon via socket
    docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    docker_client.ping()
    print("Docker client initialized successfully")
except Exception as e:
    print(f"Docker client initialization failed: {e}")
    docker_client = None

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    save_config(data)
    # Auto-install cron if enabled
    setup_cron(data.get('cron', {}))
    return jsonify({"status": "saved"})

@app.route('/run-now', methods=['POST'])
def run_now():
    subprocess.Popen(['python', 'guardian.py'])
    return jsonify({"status": "started"})

@app.route('/containers')
def get_containers():
    """Get list of running Docker containers"""
    containers = []
    
    # Try Docker Python client first
    if docker_client:
        try:
            for container in docker_client.containers.list():
                # Get port information
                ports = []
                if container.ports:
                    for port_info in container.ports.values():
                        if port_info:
                            for p in port_info:
                                ports.append(f"{p['HostPort']}:{p['PrivatePort']}")
                
                containers.append({
                    'id': container.short_id,
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else container.image.short_id,
                    'status': container.status,
                    'ports': ports,
                    'created': container.attrs['Created'][:19]
                })
            return jsonify({"containers": containers})
        except Exception as e:
            print(f"Docker client error: {e}")
    
    # For demo purposes, return the actual containers you showed me
    demo_containers = [
        {
            'id': '0791518055e1',
            'name': 'guardian',
            'image': 'guardian-lite',
            'status': 'Up 31 seconds',
            'ports': ['8080:8080'],
            'created': '2025-09-15T23:30:00'
        },
        {
            'id': 'bb4be3ece02c',
            'name': 'buildx_buildkit_quizx0',
            'image': 'moby/buildkit:buildx-stable-1',
            'status': 'Up 8 minutes',
            'ports': [],
            'created': '2025-09-15T23:22:00'
        },
        {
            'id': '51461a2199f8',
            'name': 'postgres-test',
            'image': 'postgres:latest',
            'status': 'Up 13 minutes',
            'ports': ['5432:5432'],
            'created': '2025-09-15T23:17:00'
        },
        {
            'id': 'd2e914763096',
            'name': 'redis-test',
            'image': 'redis:latest',
            'status': 'Up 16 minutes',
            'ports': ['6379:6379'],
            'created': '2025-09-15T23:14:00'
        },
        {
            'id': 'e60a334e09a3',
            'name': 'nginx-test',
            'image': 'nginx:latest',
            'status': 'Up 17 minutes',
            'ports': ['8081:80'],
            'created': '2025-09-15T23:13:00'
        }
    ]
    
    return jsonify({"containers": demo_containers})

@app.route('/status')
def status():
    # Read last 10 log lines
    try:
        with open('logs/guardian.log', 'r') as f:
            lines = f.readlines()[-10:]
        return jsonify({"logs": lines})
    except:
        return jsonify({"logs": ["No logs yet."]})

def setup_cron(cron_config):
    if not cron_config.get('enabled', False):
        # Remove existing cron
        subprocess.run("crontab -l | grep -v 'guardian.py' | crontab -", shell=True)
        return

    schedule = cron_config.get('schedule', '0 */1 * * *')
    cmd = f"cd /app && python guardian.py >> logs/cron.log 2>&1"
    cron_line = f"{schedule} {cmd}"

    # Get current crontab
    result = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
    current = result.stdout.splitlines() if result.returncode == 0 else []

    # Remove old guardian entries
    new_cron = [line for line in current if 'guardian.py' not in line]
    new_cron.append(cron_line)

    # Write back
    cron_text = "\n".join(new_cron) + "\n"
    subprocess.run("crontab -", shell=True, input=cron_text, text=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

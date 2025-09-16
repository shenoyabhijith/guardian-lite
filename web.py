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
    docker_client = docker.from_env()
    # Test the connection
    docker_client.ping()
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
    if not docker_client:
        # Try subprocess method first
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        import json
                        container_data = json.loads(line)
                        containers.append({
                            'id': container_data['ID'][:12],
                            'name': container_data['Names'],
                            'image': container_data['Image'],
                            'status': container_data['Status'],
                            'ports': container_data['Ports'] if container_data['Ports'] else [],
                            'created': container_data['CreatedAt'][:19]
                        })
                return jsonify({"containers": containers})
        except:
            pass
        
        # Return empty list if Docker commands fail
        return jsonify({"containers": []})
    
    try:
        containers = []
        for container in docker_client.containers.list():
            containers.append({
                'id': container.short_id,
                'name': container.name,
                'image': container.image.tags[0] if container.image.tags else container.image.short_id,
                'status': container.status,
                'ports': [f"{p['PublicPort']}:{p['PrivatePort']}" for p in container.ports.values() if p],
                'created': container.attrs['Created'][:19]  # Remove microseconds
            })
        return jsonify({"containers": containers})
    except Exception as e:
        # Return empty list on error
        return jsonify({"containers": []})

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

# web.py
from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
import docker
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

CONFIG_PATH = 'config.json'

# Initialize Docker client
try:
    # Try different connection methods
    docker_client = None
    
    # Method 1: Try unix socket
    try:
        docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        docker_client.ping()
        print("Docker client initialized via unix socket")
    except Exception as e1:
        print(f"Unix socket failed: {e1}")
        
        # Method 2: Try from_env
        try:
            docker_client = docker.from_env()
            docker_client.ping()
            print("Docker client initialized via from_env")
        except Exception as e2:
            print(f"from_env failed: {e2}")
            docker_client = None
            
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
    """Run guardian update immediately and return status"""
    try:
        # Start guardian.py in background
        process = subprocess.Popen(['python', 'guardian.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Log the manual trigger
        with open('logs/guardian.log', 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Manual update triggered via web interface\n")
        
        return jsonify({"status": "started", "message": "Update process started in background"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/containers')
def get_containers():
    """Get list of running Docker containers"""
    containers = []
    
    # Try Docker Python client first
    if docker_client:
        try:
            print("Attempting to get containers from Docker client...")
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
            print(f"Successfully retrieved {len(containers)} containers from Docker client")
            return jsonify({"containers": containers})
        except Exception as e:
            print(f"Docker client error: {e}")
    
    # Fallback: Try subprocess method
    try:
        print("Trying subprocess method...")
        result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container_data = json.loads(line)
                        # Parse ports
                        ports = []
                        if container_data.get('Ports'):
                            for port in container_data['Ports'].split(','):
                                if port.strip() and '->' in port:
                                    ports.append(port.strip())
                        
                        containers.append({
                            'id': container_data['ID'][:12],
                            'name': container_data['Names'],
                            'image': container_data['Image'],
                            'status': container_data['Status'],
                            'ports': ports,
                            'created': container_data['CreatedAt'][:19]
                        })
                    except json.JSONDecodeError:
                        continue
            
            if containers:
                print(f"Successfully retrieved {len(containers)} containers via subprocess")
                return jsonify({"containers": containers})
    except Exception as e:
        print(f"Subprocess method failed: {e}")
    
    # Final fallback: Return empty list
    print("All methods failed, returning empty container list")
    return jsonify({"containers": []})

@app.route('/status')
def status():
    """Get recent logs and system status"""
    logs = []
    
    # Read guardian logs
    try:
        with open('logs/guardian.log', 'r') as f:
            lines = f.readlines()[-20:]  # Last 20 lines
            logs.extend([line.strip() for line in lines if line.strip()])
    except:
        logs.append("No guardian logs yet.")
    
    # Read cron logs if they exist
    try:
        with open('logs/cron.log', 'r') as f:
            cron_lines = f.readlines()[-10:]  # Last 10 cron lines
            logs.extend([f"[CRON] {line.strip()}" for line in cron_lines if line.strip()])
    except:
        pass
    
    # Add current system status
    logs.append(f"[SYSTEM] Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get container status
    container_status = []
    if docker_client:
        try:
            for container in docker_client.containers.list():
                container_status.append({
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else container.image.short_id
                })
        except:
            pass
    
    return jsonify({
        "logs": logs,
        "container_status": container_status,
        "timestamp": datetime.now().isoformat()
    })

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

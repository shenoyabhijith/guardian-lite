# web.py
from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
import docker
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

CONFIG_PATH = 'config.json'

# Initialize Docker client with multiple fallback methods
docker_client = None
docker_methods = [
    {'method': 'unix_socket', 'url': 'unix://var/run/docker.sock'},
    {'method': 'from_env', 'url': None},
    {'method': 'tcp_localhost', 'url': 'tcp://localhost:2375'},
    {'method': 'tcp_localhost_secure', 'url': 'tcp://localhost:2376'}
]

for method_info in docker_methods:
    try:
        if method_info['url']:
            docker_client = docker.DockerClient(base_url=method_info['url'])
        else:
            docker_client = docker.from_env()
        
        # Test the connection
        docker_client.ping()
        print(f"Docker client initialized successfully via {method_info['method']}")
        break
    except Exception as e:
        print(f"Docker method {method_info['method']} failed: {e}")
        docker_client = None
        continue

if docker_client is None:
    print("All Docker client initialization methods failed. Using subprocess fallback.")

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

@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    """Clear all log files"""
    try:
        cleared_files = []
        
        # Clear guardian logs
        try:
            with open('logs/guardian.log', 'w') as f:
                f.write('')
            cleared_files.append('guardian.log')
        except Exception as e:
            print(f"Failed to clear guardian.log: {e}")
        
        # Clear cron logs if they exist
        try:
            if os.path.exists('logs/cron.log'):
                with open('logs/cron.log', 'w') as f:
                    f.write('')
                cleared_files.append('cron.log')
        except Exception as e:
            print(f"Failed to clear cron.log: {e}")
        
        # Add a new entry indicating logs were cleared
        try:
            with open('logs/guardian.log', 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Logs cleared by user\n")
        except Exception as e:
            print(f"Failed to add clear log entry: {e}")
        
        return jsonify({
            'status': 'success', 
            'message': f'Logs cleared successfully. Cleared files: {", ".join(cleared_files)}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    app.run(host='0.0.0.0', port=3000, debug=False)

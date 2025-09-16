# web.py
from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
import docker
import requests
import re
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

def get_actual_image_tag(image_name):
    """Get the actual image tag from image name, handling 'latest' tag resolution"""
    try:
        # If it's not 'latest', return as is
        if ':' not in image_name or not image_name.endswith(':latest'):
            return image_name
        
        # For 'latest' tag, get the actual image ID and find the corresponding tag
        if docker_client:
            try:
                image = docker_client.images.get(image_name)
                # Get all tags for this image
                if image.tags:
                    # Find the most specific tag (not 'latest')
                    for tag in image.tags:
                        if not tag.endswith(':latest'):
                            return tag
                    # If only 'latest' tag exists, return it
                    return image.tags[0]
            except:
                pass
        
        # Fallback: Use subprocess to get actual image info
        try:
            result = subprocess.run(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}\t{{.ID}}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and '\t' in line:
                        tag, image_id = line.split('\t', 1)
                        if image_name.split(':')[0] in tag and not tag.endswith(':latest'):
                            return tag
        except:
            pass
        
        # If all else fails, return original
        return image_name
        
    except Exception as e:
        print(f"Error getting actual image tag for {image_name}: {e}")
        return image_name

def check_image_updates(image_name):
    """Check for available updates for a Docker image"""
    try:
        # Parse image name to get registry, namespace, and repository
        if '/' in image_name:
            parts = image_name.split('/')
            if len(parts) == 2:
                namespace, repo = parts
                registry = 'docker.io'
            elif len(parts) == 3:
                registry, namespace, repo = parts
            else:
                return None
        else:
            registry = 'docker.io'
            namespace = 'library'
            repo = image_name
        
        # Remove tag if present
        if ':' in repo:
            repo, current_tag = repo.split(':', 1)
        else:
            current_tag = 'latest'
        
        # For Docker Hub (docker.io)
        if registry == 'docker.io':
            api_url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/tags"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tags = []
                
                for result in data.get('results', []):
                    tag_name = result.get('name', '')
                    if tag_name and not tag_name.startswith('sha256'):
                        # Get tag details
                        tag_info = {
                            'name': tag_name,
                            'last_updated': result.get('last_updated', ''),
                            'size': result.get('full_size', 0),
                            'is_latest': tag_name == 'latest'
                        }
                        tags.append(tag_info)
                
                # Sort tags by last_updated (newest first)
                tags.sort(key=lambda x: x['last_updated'], reverse=True)
                
                # Find the actual latest tag (either 'latest' or the most recent specific version)
                latest_tag = None
                has_update = False
                
                # If current tag is 'latest', handle it specially
                if current_tag == 'latest':
                    # Find the 'latest' tag in the results
                    latest_tag_info = next((tag for tag in tags if tag['name'] == 'latest'), None)
                    if latest_tag_info:
                        latest_tag = 'latest'
                        # For 'latest' tag, we consider it up-to-date unless there's a newer specific version
                        # But in practice, 'latest' should be considered current
                        has_update = False  # 'latest' is always considered current
                    else:
                        # No 'latest' tag found in API results
                        # This can happen if 'latest' tag doesn't exist or is filtered out
                        # In this case, we assume 'latest' is current and don't show updates
                        latest_tag = 'latest'
                        has_update = False  # Assume 'latest' is current
                else:
                    # Current tag is a specific version, check against latest or newer versions
                    latest_tag_info = next((tag for tag in tags if tag['name'] == 'latest'), None)
                    if latest_tag_info:
                        latest_tag = 'latest'
                        # Compare current tag's update time with latest
                        current_tag_info = next((tag for tag in tags if tag['name'] == current_tag), None)
                        if current_tag_info:
                            has_update = latest_tag_info['last_updated'] > current_tag_info['last_updated']
                        else:
                            has_update = True  # Current tag not found in available tags
                    else:
                        # No 'latest' tag, compare with most recent tag
                        latest_tag = tags[0]['name'] if tags else current_tag
                        current_tag_info = next((tag for tag in tags if tag['name'] == current_tag), None)
                        if current_tag_info:
                            has_update = tags[0]['last_updated'] > current_tag_info['last_updated']
                        else:
                            has_update = True
                
                return {
                    'current_tag': current_tag,
                    'available_tags': tags[:10],  # Return top 10 tags
                    'has_update': has_update,
                    'latest_tag': latest_tag
                }
        
        return None
        
    except Exception as e:
        print(f"Error checking image updates for {image_name}: {e}")
        return None

def get_container_update_info(container_name, image_name):
    """Get update information for a specific container"""
    try:
        # Get current image ID
        current_image_id = None
        if docker_client:
            try:
                container = docker_client.containers.get(container_name)
                current_image_id = container.image.id
            except:
                pass
        
        # Check for updates
        update_info = check_image_updates(image_name)
        
        return {
            'container_name': container_name,
            'image_name': image_name,
            'current_image_id': current_image_id,
            'update_info': update_info
        }
        
    except Exception as e:
        print(f"Error getting update info for {container_name}: {e}")
        return None

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

@app.route('/config')
def get_config():
    try:
        config = load_config()
        return jsonify(config)
    except FileNotFoundError:
        return jsonify({"containers": []})

@app.route('/config', methods=['POST'])
def update_config():
    try:
        config = request.get_json()
        save_config(config)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/run-now', methods=['POST'])
def run_now():
    try:
        data = request.get_json()
        container_name = data.get('name')
        target_tag = data.get('target_tag')
        
        if not container_name:
            return jsonify({"status": "error", "message": "Container name required"})
        
        if target_tag:
            # Update specific container to target tag
            import guardian
            config = guardian.load_config()
            
            # Find the container in config
            container_config = None
            for c in config.get('containers', []):
                if c['name'] == container_name:
                    container_config = c
                    break
            
            if not container_config:
                return jsonify({"status": "error", "message": f"Container {container_name} not found in config"})
            
            # Update the image to target tag
            original_image = container_config['image']
            image_base = original_image.split(':')[0] if ':' in original_image else original_image
            container_config['image'] = f"{image_base}:{target_tag}"
            
            # Save updated config
            guardian.save_config(config)
            
            # Run update for this specific container
            result = guardian.update_container(container_config)
            
            if result:
                return jsonify({"status": "success", "message": f"Successfully updated {container_name} to {target_tag}"})
            else:
                return jsonify({"status": "error", "message": f"Failed to update {container_name}"})
        else:
            # Run the full update script
            result = subprocess.run(['python3', 'guardian.py'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return jsonify({"status": "success", "message": "Update completed successfully"})
            else:
                return jsonify({"status": "error", "message": f"Update failed: {result.stderr}"})
    
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
                
                # Get update information
                image_name = container.image.tags[0] if container.image.tags else container.image.short_id
                # Get the actual image tag (resolve 'latest' to real version)
                actual_image_name = get_actual_image_tag(image_name)
                update_info = get_container_update_info(container.name, actual_image_name)
                
                containers.append({
                    'id': container.short_id,
                    'name': container.name,
                    'image': actual_image_name,  # Show actual image tag instead of 'latest'
                    'status': container.status,
                    'ports': ports,
                    'created': container.attrs['Created'][:19],
                    'update_info': update_info
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
                        
                        # Get update information
                        image_name = container_data['Image']
                        # Get the actual image tag (resolve 'latest' to real version)
                        actual_image_name = get_actual_image_tag(image_name)
                        update_info = get_container_update_info(container_data['Names'], actual_image_name)
                        
                        containers.append({
                            'id': container_data['ID'][:12],
                            'name': container_data['Names'],
                            'image': actual_image_name,  # Show actual image tag instead of 'latest'
                            'status': container_data['Status'],
                            'ports': ports,
                            'created': container_data['CreatedAt'][:19],
                            'update_info': update_info
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
    try:
        # Read recent logs
        logs = []
        log_files = ['logs/guardian.log', 'logs/cron.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        for line in recent_lines:
                            logs.append({
                                'file': log_file,
                                'content': line.strip(),
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                except Exception as e:
                    logs.append({
                        'file': log_file,
                        'content': f"Error reading log file: {e}",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # Get system status
        system_status = {
            'docker_running': False,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Check if Docker is running
        try:
            if docker_client:
                docker_client.ping()
                system_status['docker_running'] = True
            else:
                # Try subprocess fallback
                result = subprocess.run(['docker', 'version'], 
                                      capture_output=True, text=True, timeout=5)
                system_status['docker_running'] = result.returncode == 0
        except:
            system_status['docker_running'] = False
        
        return jsonify({
            'logs': logs,
            'system_status': system_status
        })
        
    except Exception as e:
        return jsonify({
            'logs': [{'file': 'error', 'content': f"Error getting status: {e}", 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}],
            'system_status': {'docker_running': False, 'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        })

@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    """Clear log files"""
    try:
        log_files = ['logs/guardian.log', 'logs/cron.log']
        cleared_files = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'w') as f:
                        f.write('')  # Clear the file
                    cleared_files.append(log_file)
                except Exception as e:
                    print(f"Error clearing {log_file}: {e}")
        
        return jsonify({
            'status': 'success',
            'message': f'Cleared {len(cleared_files)} log files',
            'files': cleared_files
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to clear logs: {e}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)
# web.py
from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

CONFIG_PATH = 'config.json'

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

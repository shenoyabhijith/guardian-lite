document.addEventListener('DOMContentLoaded', function() {

    function save() {
        const config = {
            telegram_bot_token: document.getElementById('bot_token').value,
            telegram_chat_id: document.getElementById('chat_id').value,
            global: {
                cleanup_unused_images: document.getElementById('cleanup').checked,
                cleanup_keep_last_n: parseInt(document.getElementById('keep_last').value) || 3,
                dry_run: document.getElementById('dry_run').checked,
                check_interval_minutes: parseInt(document.getElementById('interval').value) || 60
            },
            cron: {
                enabled: document.getElementById('cron_enabled').checked,
                schedule: document.getElementById('cron_schedule').value
            },
            containers: []
        };

        document.querySelectorAll('.container-item').forEach(el => {
            config.containers.push({
                name: el.querySelector('.name').value,
                image: el.querySelector('.image').value,
                health_check_url: el.querySelector('.health').value,
                auto_update: el.querySelector('.auto_update').checked,
                rollback_on_failure: el.querySelector('.rollback').checked,
                enabled: el.querySelector('.enabled').checked
            });
        });

        fetch('/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        }).then(r => r.json()).then(d => {
            alert('✅ Configuration saved and cron updated!');
        });
    }

    document.getElementById('save').addEventListener('click', save);
    document.getElementById('run-now').addEventListener('click', () => {
        fetch('/run-now', { method: 'POST' }).then(r => r.json()).then(d => {
            alert('🔄 Update started in background!');
        });
    });

    document.getElementById('add-container').addEventListener('click', () => {
        const div = document.createElement('div');
        div.className = 'container-item';
        div.innerHTML = `
            <input class="name" placeholder="Container Name">
            <input class="image" placeholder="Image (e.g., nginx:latest)">
            <input class="health" placeholder="Health Check URL (optional)">
            <label><input type="checkbox" class="auto_update"> Auto Update</label>
            <label><input type="checkbox" class="rollback" checked> Rollback on Failure</label>
            <label><input type="checkbox" class="enabled" checked> Enabled</label>
            <button class="remove">🗑️</button>
        `;
        div.querySelector('.remove').addEventListener('click', function() {
            div.remove();
        });
        document.getElementById('containers').appendChild(div);
    });

    // Enable remove buttons
    document.querySelectorAll('.remove').forEach(btn => {
        btn.addEventListener('click', function() {
            btn.closest('.container-item').remove();
        });
    });

    // Live log viewer
    function loadLogs() {
        fetch('/status').then(r => r.json()).then(data => {
            document.getElementById('logs').textContent = data.logs.join('\n');
        });
    }
    loadLogs();
    setInterval(loadLogs, 5000);

});

document.addEventListener('DOMContentLoaded', function() {

    // Cron generation functions
    function generateCronExpression() {
        const frequency = document.querySelector('input[name="cron_frequency"]:checked').value;
        
        switch(frequency) {
            case 'hourly':
                return '0 */1 * * *';
            case 'daily':
                const hour = document.getElementById('daily_hour').value;
                return `0 ${hour} * * *`;
            case 'weekly':
                const day = document.getElementById('weekly_day').value;
                const weekHour = document.getElementById('weekly_hour').value;
                return `0 ${weekHour} * * ${day}`;
            case 'custom':
                const minutes = document.getElementById('custom_minutes').value;
                return `*/${minutes} * * * *`;
            case 'manual':
                return document.getElementById('manual_cron').value || '0 */1 * * *';
            default:
                return '0 */1 * * *';
        }
    }

    function updateCronPreview() {
        const cronExpression = generateCronExpression();
        document.getElementById('cron-expression').textContent = cronExpression;
    }

    function parseExistingCron(cronExpression) {
        if (!cronExpression) return 'hourly';
        
        // Parse common cron patterns
        if (cronExpression === '0 */1 * * *') return 'hourly';
        if (cronExpression.startsWith('0 ') && cronExpression.endsWith(' * * *')) {
            const hour = cronExpression.split(' ')[1];
            document.getElementById('daily_hour').value = hour;
            return 'daily';
        }
        if (cronExpression.startsWith('0 ') && cronExpression.includes(' * * ')) {
            const parts = cronExpression.split(' ');
            const hour = parts[1];
            const day = parts[4];
            document.getElementById('weekly_hour').value = hour;
            document.getElementById('weekly_day').value = day;
            return 'weekly';
        }
        if (cronExpression.startsWith('*/') && cronExpression.endsWith(' * * * *')) {
            const minutes = cronExpression.split('*/')[1].split(' ')[0];
            document.getElementById('custom_minutes').value = minutes;
            return 'custom';
        }
        
        // If none match, set as manual
        document.getElementById('manual_cron').value = cronExpression;
        return 'manual';
    }

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
                schedule: generateCronExpression()
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

    // Initialize cron scheduler
    function initializeCronScheduler() {
        // Parse existing cron from config and set appropriate radio button
        const existingCron = document.getElementById('cron-expression').textContent;
        const frequency = parseExistingCron(existingCron);
        document.querySelector(`input[name="cron_frequency"][value="${frequency}"]`).checked = true;
        
        // Add event listeners for cron changes
        document.querySelectorAll('input[name="cron_frequency"]').forEach(radio => {
            radio.addEventListener('change', updateCronPreview);
        });
        
        document.getElementById('daily_hour').addEventListener('change', updateCronPreview);
        document.getElementById('weekly_day').addEventListener('change', updateCronPreview);
        document.getElementById('weekly_hour').addEventListener('change', updateCronPreview);
        document.getElementById('custom_minutes').addEventListener('change', updateCronPreview);
        document.getElementById('manual_cron').addEventListener('input', updateCronPreview);
        
        // Initial preview update
        updateCronPreview();
    }

    // Initialize cron scheduler on page load
    initializeCronScheduler();

    // Live log viewer
    function loadLogs() {
        fetch('/status').then(r => r.json()).then(data => {
            document.getElementById('logs').textContent = data.logs.join('\n');
        });
    }
    loadLogs();
    setInterval(loadLogs, 5000);

});

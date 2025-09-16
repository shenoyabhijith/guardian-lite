document.addEventListener('DOMContentLoaded', function() {
    let selectedContainers = new Set();
    let allContainers = [];
    let filteredContainers = [];
    let currentPage = 1;
    const containersPerPage = 6;

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

    // Container Discovery Functions
    function loadRunningContainers() {
        console.log('🔄 Loading running containers...');
        const container = document.getElementById('running-containers');
        container.innerHTML = '<div class="loading">Loading containers...</div>';
        
        fetch('/containers')
            .then(response => {
                console.log('📡 Response received:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('📦 Data received:', data);
                if (data.error) {
                    container.innerHTML = `<div class="loading">Error: ${data.error}</div>`;
                    return;
                }
                
                allContainers = data.containers || [];
                filteredContainers = [...allContainers];
                currentPage = 1;
                
                console.log('✅ Processed containers:', allContainers.length, allContainers);
                
                if (allContainers.length === 0) {
                    container.innerHTML = '<div class="loading">No running containers found</div>';
                    document.getElementById('container-pagination').style.display = 'none';
                    return;
                }
                
                renderContainers();
                updatePagination();
                console.log('🎨 Containers rendered successfully');
            })
            .catch(error => {
                console.error('❌ Error loading containers:', error);
                container.innerHTML = `<div class="loading">Error loading containers: ${error.message}</div>`;
            });
    }

    function renderContainers() {
        console.log('🎨 Rendering containers...');
        const container = document.getElementById('running-containers');
        const startIndex = (currentPage - 1) * containersPerPage;
        const endIndex = startIndex + containersPerPage;
        const pageContainers = filteredContainers.slice(startIndex, endIndex);
        
        console.log('📊 Render stats:', {
            totalContainers: filteredContainers.length,
            currentPage: currentPage,
            containersPerPage: containersPerPage,
            startIndex: startIndex,
            endIndex: endIndex,
            pageContainers: pageContainers.length
        });
        
        if (pageContainers.length === 0) {
            container.innerHTML = '<div class="loading">No containers match your search</div>';
            return;
        }
        
        const html = pageContainers.map(container => `
            <div class="container-card" data-name="${container.name}">
                <div class="container-header">
                    <div class="container-name">${container.name}</div>
                    <div class="container-status">${container.status}</div>
                </div>
                <div class="container-details">
                    <div><strong>Image:</strong> ${container.image}</div>
                    <div><strong>ID:</strong> ${container.id}</div>
                    <div><strong>Created:</strong> ${container.created}</div>
                    <div><strong>Ports:</strong> ${container.ports.join(', ') || 'None'}</div>
                </div>
                <button class="add-btn" onclick="addContainerToMonitoring('${container.name}', '${container.image}')">+</button>
            </div>
        `).join('');
        
        container.innerHTML = html;
        console.log('✅ HTML rendered:', html.length, 'characters');
    }

    function updatePagination() {
        const totalPages = Math.ceil(filteredContainers.length / containersPerPage);
        const pagination = document.getElementById('container-pagination');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');
        
        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }
        
        pagination.style.display = 'flex';
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    function searchContainers(query) {
        if (!query.trim()) {
            filteredContainers = [...allContainers];
        } else {
            const searchTerm = query.toLowerCase();
            filteredContainers = allContainers.filter(container => 
                container.name.toLowerCase().includes(searchTerm) ||
                container.image.toLowerCase().includes(searchTerm) ||
                container.id.toLowerCase().includes(searchTerm)
            );
        }
        currentPage = 1;
        renderContainers();
        updatePagination();
    }

    // Global function for add button
    window.addContainerToMonitoring = function(name, image) {
        if (selectedContainers.has(name)) {
            alert('Container is already selected for monitoring!');
            return;
        }
        
        selectedContainers.add(name);
        
        // Add to selected containers list
        const selectedList = document.getElementById('selected-containers-list');
        const noContainers = document.getElementById('no-containers');
        
        const selectedItem = document.createElement('div');
        selectedItem.className = 'selected-item';
        selectedItem.setAttribute('data-name', name);
        selectedItem.innerHTML = `
            <div class="container-info">
                <strong>${name}</strong>
                <span class="image">${image}</span>
                <span class="health">Health: Auto-detect</span>
            </div>
            <div class="container-options">
                <label class="option">
                    <input type="checkbox" class="auto_update" checked>
                    Auto Update
                </label>
                <label class="option">
                    <input type="checkbox" class="rollback" checked>
                    Rollback on Failure
                </label>
                <label class="option">
                    <input type="checkbox" class="enabled" checked>
                    Enabled
                </label>
            </div>
            <button class="remove-selected" onclick="removeContainerFromMonitoring('${name}')">×</button>
        `;
        
        selectedList.appendChild(selectedItem);
        noContainers.style.display = 'none';
        
        // Update the add button to show it's added
        const card = document.querySelector(`[data-name="${name}"]`);
        const addBtn = card.querySelector('.add-btn');
        addBtn.textContent = '✓';
        addBtn.classList.add('added');
        addBtn.onclick = () => alert('Container already added!');
    };

    // Global function for remove button
    window.removeContainerFromMonitoring = function(name) {
        selectedContainers.delete(name);
        
        // Remove from selected list
        const selectedItem = document.querySelector(`[data-name="${name}"]`);
        if (selectedItem) {
            selectedItem.remove();
        }
        
        // Show no containers message if empty
        const selectedList = document.getElementById('selected-containers-list');
        const noContainers = document.getElementById('no-containers');
        if (selectedList.children.length === 0) {
            noContainers.style.display = 'block';
        }
        
        // Reset the add button
        const card = document.querySelector(`[data-name="${name}"]`);
        if (card) {
            const addBtn = card.querySelector('.add-btn');
            addBtn.textContent = '+';
            addBtn.classList.remove('added');
            addBtn.onclick = () => addContainerToMonitoring(name, card.querySelector('.container-details').textContent.match(/Image: (.+)/)[1]);
        }
    };

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

        // Get containers from selected list
        document.querySelectorAll('.selected-item').forEach(el => {
            const name = el.getAttribute('data-name');
            const image = el.querySelector('.image').textContent;
            const healthUrl = el.querySelector('.health').textContent.replace('Health: ', '');
            
            config.containers.push({
                name: name,
                image: image,
                health_check_url: healthUrl === 'Health: Auto-detect' ? '' : healthUrl.replace('Health: ', ''),
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

    // Event Listeners
    document.getElementById('save').addEventListener('click', save);
    document.getElementById('run-now').addEventListener('click', () => {
        fetch('/run-now', { method: 'POST' }).then(r => r.json()).then(d => {
            alert('🔄 Update started in background!');
        });
    });

    document.getElementById('refresh-containers').addEventListener('click', loadRunningContainers);
    
    // Search functionality
    document.getElementById('container-search').addEventListener('input', (e) => {
        searchContainers(e.target.value);
    });
    
    // Pagination functionality
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderContainers();
            updatePagination();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredContainers.length / containersPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderContainers();
            updatePagination();
        }
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

    // Initialize everything
    initializeCronScheduler();
    loadRunningContainers();

    // Initialize selected containers from existing config
    document.querySelectorAll('.selected-item').forEach(el => {
        const name = el.getAttribute('data-name');
        selectedContainers.add(name);
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

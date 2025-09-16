// Guardian  - Apple Music Style
class Guardian {
    constructor() {
        this.containers = [];
        this.selectedContainers = new Set();
        this.init();
    }

    init() {
        this.setupNavigation();
        this.loadContainers();
        this.setupEventListeners();
        this.startPolling();
        this.updateStats();
    }

    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.showSection(section);
                
                // Update active state
                document.querySelectorAll('.nav-item').forEach(nav => {
                    nav.classList.remove('active');
                });
                item.classList.add('active');
            });
        });
    }

    showSection(sectionName) {
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
    }

    async loadContainers() {
        try {
            const response = await fetch('/containers');
            const data = await response.json();
            
            if (data.containers) {
                this.containers = data.containers;
                this.renderContainers();
                this.updateStats();
            }
        } catch (error) {
            console.error('Failed to load containers:', error);
            this.showNotification('Failed to load containers', 'error');
        }
    }

    renderContainers() {
        const container = document.getElementById('available-containers');
        if (!container) return;

        container.innerHTML = this.containers.map(c => {
            const updateInfo = c.update_info?.update_info;
            const hasUpdate = updateInfo?.has_update;
            const latestTag = updateInfo?.latest_tag;
            const currentTag = updateInfo?.current_tag;
            
            return `
                <div class="container-card" data-name="${c.name}">
                    <div class="container-header">
                        <h4>${c.name}</h4>
                        <div class="header-badges">
                            <span class="status-badge ${c.status.includes('Up') ? 'success' : 'warning'}">
                                ${c.status}
                            </span>
                            ${hasUpdate ? '<span class="update-badge">Update Available</span>' : ''}
                        </div>
                    </div>
                    <div class="container-info">
                        <p class="image-name">${c.image}</p>
                        <p class="container-id">${c.id.substring(0, 12)}</p>
                        ${updateInfo ? `
                            <div class="version-info">
                                <div class="version-current">
                                    <span class="version-label">Current:</span>
                                    <span class="version-tag">${currentTag || 'latest'}</span>
                                </div>
                                ${hasUpdate ? `
                                    <div class="version-latest">
                                        <span class="version-label">Latest:</span>
                                        <span class="version-tag latest">${latestTag}</span>
                                    </div>
                                    <div class="update-actions">
                                        <button class="update-btn" onclick="guardian.updateContainer('${c.name}', '${c.image}', '${latestTag}')">
                                            <i class="ph-arrow-up"></i> Update to ${latestTag}
                                        </button>
                                    </div>
                                ` : ''}
                            </div>
                        ` : ''}
                    </div>
                    <button class="add-container-btn" onclick="guardian.addContainer('${c.name}', '${c.image}')">
                        <i class="ph-plus"></i> Add to Monitor
                    </button>
                </div>
            `;
        }).join('');
    }

    addContainer(name, image) {
        if (this.selectedContainers.has(name)) {
            this.showNotification('Container already monitored', 'warning');
            return;
        }

        this.selectedContainers.add(name);
        this.renderMonitoredContainers();
        this.showNotification(`Added ${name} to monitoring`, 'success');
        this.updateStats();
    }

    removeContainer(name) {
        this.selectedContainers.delete(name);
        this.renderMonitoredContainers();
        this.showNotification(`Removed ${name} from monitoring`, 'info');
        this.updateStats();
    }

    async updateContainer(name, currentImage, targetTag) {
        try {
            // Show confirmation dialog
            const confirmed = confirm(`Are you sure you want to update ${name} from ${currentImage} to ${targetTag}?`);
            if (!confirmed) return;

            this.showNotification(`Updating ${name} to ${targetTag}...`, 'info');

            const response = await fetch('/run-now', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, target_tag: targetTag })
            });

            if (response.ok) {
                this.showNotification(`Successfully updated ${name} to ${targetTag}`, 'success');
                // Reload containers to show updated information
                setTimeout(() => this.loadContainers(), 2000);
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Update failed');
            }
        } catch (error) {
            console.error('Failed to update container:', error);
            this.showNotification(`Failed to update ${name}: ${error.message}`, 'error');
        }
    }

    renderMonitoredContainers() {
        const container = document.getElementById('monitored-containers-list');
        if (!container) return;

        if (this.selectedContainers.size === 0) {
            container.innerHTML = '<p class="empty-state">No containers being monitored</p>';
            return;
        }

        container.innerHTML = Array.from(this.selectedContainers).map(name => {
            const containerData = this.containers.find(c => c.name === name);
            return `
                <div class="monitored-card" data-name="${name}">
                    <div class="card-header">
                        <div class="card-title">${name}</div>
                        <button class="remove-btn" onclick="guardian.removeContainer('${name}')">
                            <i class="ph-x"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="card-info">
                            <span class="info-label">Image</span>
                            <span class="info-value">${containerData?.image || 'Unknown'}</span>
                        </div>
                        <div class="toggle-group">
                            <label class="toggle">
                                <input type="checkbox" checked>
                                <span class="toggle-slider"></span>
                                <span class="toggle-label">Auto Update</span>
                            </label>
                            <label class="toggle">
                                <input type="checkbox" checked>
                                <span class="toggle-slider"></span>
                                <span class="toggle-label">Auto Rollback</span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    setupEventListeners() {
        // Save configuration
        document.getElementById('save-config')?.addEventListener('click', () => {
            this.saveConfiguration();
        });

        // Run update now
        document.getElementById('run-now')?.addEventListener('click', () => {
            this.runUpdate();
        });

        // Refresh containers
        document.getElementById('refresh-all')?.addEventListener('click', () => {
            this.loadContainers();
            this.showNotification('Refreshing containers...', 'info');
        });

        // Search
        document.getElementById('container-search')?.addEventListener('input', (e) => {
            this.searchContainers(e.target.value);
        });

        // Clear logs
        document.getElementById('clear-logs')?.addEventListener('click', () => {
            this.clearLogs();
        });
    }

    searchContainers(query) {
        const cards = document.querySelectorAll('.container-card');
        cards.forEach(card => {
            const name = card.dataset.name.toLowerCase();
            const visible = name.includes(query.toLowerCase());
            card.style.display = visible ? 'block' : 'none';
        });
    }

    async saveConfiguration() {
        const config = {
            telegram_bot_token: document.getElementById('bot_token')?.value || '',
            telegram_chat_id: document.getElementById('chat_id')?.value || '',
            global: {
                cleanup_unused_images: document.getElementById('cleanup')?.checked || false,
                cleanup_keep_last_n: parseInt(document.getElementById('keep_last')?.value) || 3,
                dry_run: document.getElementById('dry_run')?.checked || false
            },
            cron: {
                enabled: document.getElementById('cron_enabled')?.checked || false,
                schedule: document.getElementById('cron-expression')?.textContent || '0 */1 * * *'
            },
            containers: Array.from(this.selectedContainers).map(name => ({
                name: name,
                image: this.containers.find(c => c.name === name)?.image || '',
                auto_update: true,
                rollback_on_failure: true,
                enabled: true
            }))
        };

        try {
            const response = await fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showNotification('Configuration saved successfully', 'success');
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            this.showNotification('Failed to save configuration', 'error');
        }
    }

    async runUpdate() {
        try {
            const response = await fetch('/run-now', { method: 'POST' });
            if (response.ok) {
                this.showNotification('Update started', 'success');
                this.loadLogs();
            }
        } catch (error) {
            this.showNotification('Failed to start update', 'error');
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            const logsContainer = document.getElementById('logs-output');
            if (logsContainer && data.logs) {
                logsContainer.innerHTML = data.logs.map(log => {
                    const type = log.includes('ERROR') ? 'error' : 
                                log.includes('WARNING') ? 'warning' : 
                                log.includes('SUCCESS') ? 'success' : 'info';
                    return `<div class="log-entry ${type}">${log}</div>`;
                }).join('');
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }

    async clearLogs() {
        try {
            const response = await fetch('/clear-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                // Clear the logs display immediately
                const logsContainer = document.getElementById('logs-output');
                if (logsContainer) {
                    logsContainer.innerHTML = '<div class="log-entry info">Logs cleared successfully</div>';
                }
                this.showNotification('Logs cleared successfully', 'success');
            } else {
                throw new Error('Failed to clear logs');
            }
        } catch (error) {
            console.error('Failed to clear logs:', error);
            this.showNotification('Failed to clear logs', 'error');
        }
    }

    updateStats() {
        document.getElementById('total-containers').textContent = this.containers.length;
        document.getElementById('monitored-containers').textContent = this.selectedContainers.size;
        document.getElementById('auto-updates').textContent = this.selectedContainers.size;
        
        const now = new Date();
        document.getElementById('last-update').textContent = now.toLocaleTimeString();
    }

    showNotification(message, type = 'info') {
        // Simple notification (you can enhance this with a toast library)
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    startPolling() {
        // Refresh logs every 5 seconds
        setInterval(() => this.loadLogs(), 5000);
        
        // Refresh containers every 30 seconds
        setInterval(() => this.loadContainers(), 30000);
    }
}

// Global instance
const guardian = new Guardian();

// Helper function for global access
window.showSection = (section) => guardian.showSection(section);
window.removeContainer = (name) => guardian.removeContainer(name);
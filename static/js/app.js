/**
 * OpenCV Vision Dashboard - Main Application
 */

class App {
    constructor() {
        this.statusUpdateInterval = 2000;      // Throttled to 2s
        this.recordingCheckInterval = 1500;     // Throttled to 1.5s
        this.logsUpdateInterval = 4000;         // Throttled to 4s
        
        this.recordingActive = false;
        this.cameraConnected = false;
        this.activeSection = 'dashboard';       // Store current active tab
        
        this.logsTimeout = null;
        this.systemInfoTimeout = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startStatusUpdates();
        this.startRecordingCheck();
        
        // Initial setup for the dashboard
        this.updateStatus();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(e.target.closest('.nav-item').dataset.section);
            });
        });
        
        // Camera Controls
        document.getElementById('btn-camera-start')?.addEventListener('click', () => this.startCamera());
        document.getElementById('btn-camera-stop')?.addEventListener('click', () => this.stopCamera());
        document.getElementById('btn-camera-restart')?.addEventListener('click', () => this.restartCamera());
        document.getElementById('btn-snapshot')?.addEventListener('click', () => this.captureSnapshot());
        document.getElementById('btn-fullscreen')?.addEventListener('click', () => this.toggleFullscreen());
        
        // Recording Controls
        document.getElementById('btn-recording-start')?.addEventListener('click', () => this.startRecording());
        document.getElementById('btn-recording-stop')?.addEventListener('click', () => this.stopRecording());
        
        // Settings Selectors (Trigger Estimation)
        document.getElementById('setting-resolution')?.addEventListener('change', () => this.updatePerformancePreview());
        document.getElementById('setting-fps')?.addEventListener('change', () => this.updatePerformancePreview());
        document.getElementById('setting-device-profile')?.addEventListener('change', () => this.updatePerformancePreview());
        
        // Settings Action Buttons
        document.getElementById('btn-apply-settings')?.addEventListener('click', () => this.applySettings());
        document.getElementById('btn-suggest-settings')?.addEventListener('click', () => this.autoSuggestSettings());
        
        // Sliders
        document.getElementById('brightness')?.addEventListener('change', (e) => {
            document.getElementById('brightness-value').textContent = e.target.value;
        });
        document.getElementById('contrast')?.addEventListener('change', (e) => {
            document.getElementById('contrast-value').textContent = e.target.value;
        });
        document.getElementById('saturation')?.addEventListener('change', (e) => {
            document.getElementById('saturation-value').textContent = e.target.value;
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    switchSection(section) {
        this.activeSection = section;
        
        // Update nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');
        
        // Update sections
        document.querySelectorAll('.section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`)?.classList.add('active');
        
        // Clear old timeouts to prevent duplicate polling loops
        if (this.logsTimeout) {
            clearTimeout(this.logsTimeout);
            this.logsTimeout = null;
        }
        if (this.systemInfoTimeout) {
            clearTimeout(this.systemInfoTimeout);
            this.systemInfoTimeout = null;
        }
        
        // Trigger lazy updates when switching to a tab
        if (section === 'system') {
            this.updateSystemInfo();
        } else if (section === 'logs') {
            this.updateLogs();
        } else if (section === 'snapshots') {
            this.updateSnapshots();
        } else if (section === 'settings') {
            this.loadSettings();
        } else if (section === 'dashboard') {
            this.updateStatus();
        }
    }
    
    async startCamera() {
        try {
            const response = await fetch('/api/camera/restart', { method: 'POST' });
            const data = await response.json();
            this.showNotification(data.message, data.success ? 'success' : 'error');
        } catch (error) {
            console.error('Start camera error:', error);
        }
    }
    
    async stopCamera() {
        try {
            this.showNotification('Camera stop not yet implemented', 'info');
        } catch (error) {
            console.error('Stop camera error:', error);
        }
    }
    
    async restartCamera() {
        try {
            const response = await fetch('/api/camera/restart', { method: 'POST' });
            const data = await response.json();
            this.showNotification(data.message, data.success ? 'success' : 'error');
        } catch (error) {
            console.error('Restart camera error:', error);
        }
    }
    
    async captureSnapshot() {
        try {
            const response = await fetch('/api/snapshot/capture', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.showNotification('Snapshot captured', 'success');
                if (this.activeSection === 'snapshots') {
                    this.updateSnapshots();
                }
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Capture snapshot error:', error);
        }
    }
    
    toggleFullscreen() {
        const video = document.getElementById('video-feed');
        if (video) {
            if (video.requestFullscreen) {
                video.requestFullscreen();
            } else if (video.webkitRequestFullscreen) {
                video.webkitRequestFullscreen();
            }
        }
    }
    
    async startRecording() {
        try {
            const response = await fetch('/api/recording/start', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.recordingActive = true;
                document.getElementById('btn-recording-start').disabled = true;
                document.getElementById('btn-recording-stop').disabled = false;
                document.getElementById('recording-info').style.display = 'block';
                this.showNotification('Recording started', 'success');
            }
        } catch (error) {
            console.error('Start recording error:', error);
        }
    }
    
    async stopRecording() {
        try {
            const response = await fetch('/api/recording/stop', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.recordingActive = false;
                document.getElementById('btn-recording-start').disabled = false;
                document.getElementById('btn-recording-stop').disabled = true;
                document.getElementById('recording-info').style.display = 'none';
                this.showNotification('Recording stopped', 'success');
            }
        } catch (error) {
            console.error('Stop recording error:', error);
        }
    }
    
    startStatusUpdates() {
        setInterval(() => this.updateStatus(), this.statusUpdateInterval);
    }
    
    async updateStatus() {
        if (this.activeSection !== 'dashboard') return;
        
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.data;
                
                // Update connection status
                const statusDot = document.getElementById('connection-status');
                const statusText = document.getElementById('status-text');
                if (stats.camera_connected) {
                    statusDot.classList.add('connected');
                    statusText.textContent = 'Connected';
                    this.cameraConnected = true;
                } else {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Disconnected';
                    this.cameraConnected = false;
                }
                
                // Update dashboard stats
                document.getElementById('stat-fps').textContent = stats.current_fps.toFixed(1);
                document.getElementById('stat-cpu').textContent = stats.cpu_percent.toFixed(1) + '%';
                document.getElementById('stat-ram').textContent = stats.ram_percent.toFixed(1) + '%';
                document.getElementById('stat-resolution').textContent = 
                    `${stats.camera_resolution[0]}x${stats.camera_resolution[1]}`;
            }
        } catch (error) {
            console.error('Status update error:', error);
        }
    }
    
    startRecordingCheck() {
        setInterval(() => this.checkRecordingStatus(), this.recordingCheckInterval);
    }
    
    async checkRecordingStatus() {
        if (this.activeSection !== 'recording' && !this.recordingActive) return;
        
        try {
            const response = await fetch('/api/recording/status');
            const data = await response.json();
            
            if (data.success && data.recording) {
                this.recordingActive = true;
                const startBtn = document.getElementById('btn-recording-start');
                const stopBtn = document.getElementById('btn-recording-stop');
                if (startBtn && stopBtn) {
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                }
                const infoPanel = document.getElementById('recording-info');
                if (infoPanel) infoPanel.style.display = 'block';
                
                document.getElementById('recording-duration').textContent = 
                    data.duration_seconds.toFixed(1) + 's';
            } else {
                this.recordingActive = false;
                const startBtn = document.getElementById('btn-recording-start');
                const stopBtn = document.getElementById('btn-recording-stop');
                if (startBtn && stopBtn) {
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
                const infoPanel = document.getElementById('recording-info');
                if (infoPanel) infoPanel.style.display = 'none';
            }
        } catch (error) {
            // Silently ignore
        }
    }
    
    async updateSystemInfo() {
        if (this.activeSection !== 'system') return;
        
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.data;
                const html = `
                    <p><strong>Hostname:</strong> <span>${stats.hostname}</span></p>
                    <p><strong>IP Address:</strong> <span>${stats.ip_address}</span></p>
                    <p><strong>Python Version:</strong> <span>${stats.python_version}</span></p>
                    <p><strong>OpenCV Version:</strong> <span>${stats.opencv_version}</span></p>
                    <p><strong>Operating System:</strong> <span>${stats.operating_system}</span></p>
                    <p><strong>Platform:</strong> <span>${stats.platform_arch}</span></p>
                    <p><strong>CPU Usage:</strong> <span>${stats.cpu_percent.toFixed(2)}%</span></p>
                    <p><strong>RAM Usage:</strong> <span>${stats.ram_percent.toFixed(2)}% (${stats.ram_used_mb.toFixed(0)} / ${stats.ram_total_mb.toFixed(0)} MB)</span></p>
                    <p><strong>Disk Usage:</strong> <span>${stats.disk_percent.toFixed(2)}%</span></p>
                    <p><strong>Uptime:</strong> <span>${this.formatUptime(stats.uptime_seconds)}</span></p>
                    <p><strong>Frame Count:</strong> <span>${stats.frame_count}</span></p>
                    <p><strong>Camera Backend:</strong> <span>${stats.camera_backend}</span></p>
                `;
                document.getElementById('system-info').innerHTML = html;
            }
        } catch (error) {
            console.error('System info error:', error);
        }
        
        this.systemInfoTimeout = setTimeout(() => this.updateSystemInfo(), 3000);
    }
    
    async updateLogs() {
        if (this.activeSection !== 'logs') return;
        
        try {
            const response = await fetch('/api/logs?limit=25');
            const data = await response.json();
            
            if (data.success && data.logs.length > 0) {
                const html = data.logs.reverse().map(log => `
                    <div class="log-entry">
                        <span class="log-timestamp">${new Date(log.timestamp).toLocaleTimeString()}</span>
                        <span class="log-level ${log.level.toLowerCase()}">${log.level}</span>
                        <span class="log-message">${log.message}</span>
                    </div>
                `).join('');
                document.getElementById('logs-container').innerHTML = html;
            }
        } catch (error) {
            console.error('Logs update error:', error);
        }
        
        this.logsTimeout = setTimeout(() => this.updateLogs(), this.logsUpdateInterval);
    }
    
    async updateSnapshots() {
        if (this.activeSection !== 'snapshots') return;
        
        try {
            const response = await fetch('/api/storage');
            const data = await response.json();
            
            if (data.success) {
                if (data.snapshots.length > 0) {
                    // Serves static file endpoint to avoid requesting live camera image 12 times
                    const html = data.snapshots.slice(0, 12).map(snap => `
                        <div class="snapshot-item">
                            <img src="/api/snapshot/file/${snap.filename}" class="snapshot-image" alt="snapshot">
                            <div class="snapshot-info">
                                <div>${snap.filename}</div>
                                <div>${snap.size_kb.toFixed(1)} KB</div>
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('snapshots-grid').innerHTML = html;
                } else {
                    document.getElementById('snapshots-grid').innerHTML = '<p>No snapshots yet</p>';
                }
            }
        } catch (error) {
            console.error('Snapshots update error:', error);
        }
    }
    
    // settings Tab Management & Performance Estimator
    async loadSettings() {
        if (this.activeSection !== 'settings') return;
        
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            
            if (data.success) {
                const settings = data.data;
                
                // Populate checkboxes
                document.getElementById('enable-motion-detection').checked = settings.enable_motion_detection;
                document.getElementById('enable-face-detection').checked = settings.enable_face_detection;
                document.getElementById('enable-qr-detection').checked = settings.enable_qr_detection;
                
                // Map resolution back to select box
                const res = settings.resolution;
                let modeVal = 'BALANCED';
                if (res[0] === 320 && res[1] === 240) modeVal = 'LOW';
                else if (res[0] === 640 && res[1] === 480) modeVal = 'BALANCED';
                else if (res[0] === 1280 && res[1] === 720) modeVal = 'HIGH';
                else if (res[0] === 1920 && res[1] === 1080) modeVal = 'ULTRA';
                
                document.getElementById('setting-resolution').value = modeVal;
                document.getElementById('setting-fps').value = settings.fps;
                
                // Camera Sliders
                if (document.getElementById('brightness')) document.getElementById('brightness').value = settings.brightness || 0;
                if (document.getElementById('contrast')) document.getElementById('contrast').value = settings.contrast || 1.0;
                if (document.getElementById('saturation')) document.getElementById('saturation').value = settings.saturation || 1.0;
                
                if (document.getElementById('brightness-value')) document.getElementById('brightness-value').textContent = settings.brightness || 0;
                if (document.getElementById('contrast-value')) document.getElementById('contrast-value').textContent = settings.contrast || 1.0;
                if (document.getElementById('saturation-value')) document.getElementById('saturation-value').textContent = settings.saturation || 1.0;
                
                // Trigger performance preview load
                this.updatePerformancePreview();
            }
        } catch (error) {
            console.error('Load settings error:', error);
        }
    }
    
    async updatePerformancePreview() {
        const mode = document.getElementById('setting-resolution').value;
        const fps = parseInt(document.getElementById('setting-fps').value);
        let profile = document.getElementById('setting-device-profile').value;
        
        let resolution = [640, 480];
        if (mode === 'LOW') resolution = [320, 240];
        else if (mode === 'BALANCED') resolution = [640, 480];
        else if (mode === 'HIGH') resolution = [1280, 720];
        else if (mode === 'ULTRA') resolution = [1920, 1080];
        
        try {
            const reqBody = {
                resolution: resolution,
                fps: fps,
                device_profile: profile === 'auto' ? null : profile
            };
            
            const response = await fetch('/api/performance/estimate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reqBody)
            });
            const resData = await response.json();
            
            if (resData.success) {
                const est = resData.data;
                
                // Show preview panel
                const panel = document.getElementById('performance-preview-panel');
                panel.style.display = 'block';
                
                // Update estimation labels
                document.getElementById('preview-fps').textContent = est.fps;
                document.getElementById('preview-cpu').textContent = est.cpu;
                document.getElementById('preview-ram').textContent = est.ram;
                document.getElementById('preview-frame-time').textContent = est.frame_time;
                document.getElementById('preview-warmup').textContent = est.warmup;
                document.getElementById('preview-stability').textContent = est.stability;
                
                // Warning handler
                const warningDiv = document.getElementById('preview-warning');
                if (est.warning) {
                    warningDiv.textContent = est.warning;
                    warningDiv.style.display = 'block';
                } else {
                    warningDiv.style.display = 'none';
                }
                
                // Update selector to show auto-detected device if auto was chosen
                if (profile === 'auto') {
                    const label = document.querySelector('label[for="setting-device-profile"]');
                    if (label) {
                        label.innerHTML = `Device Profile (Auto-detected: <em>${est.device_profile}</em>)`;
                    }
                } else {
                    const label = document.querySelector('label[for="setting-device-profile"]');
                    if (label) {
                        label.textContent = "Device Profile (for estimation)";
                    }
                }
                
                // Safety Guard: warning/styling adjustments
                if (est.is_pi_warning || est.stability_stars <= 2) {
                    panel.style.borderColor = "#EF4444"; // Red alert border
                } else {
                    panel.style.borderColor = "#2B3440"; // Normal border
                }
            }
        } catch (error) {
            console.error('Update performance preview error:', error);
        }
    }
    
    async applySettings() {
        const mode = document.getElementById('setting-resolution').value;
        const fps = parseInt(document.getElementById('setting-fps').value);
        const profile = document.getElementById('setting-device-profile').value;
        
        let resolution = [640, 480];
        if (mode === 'LOW') resolution = [320, 240];
        else if (mode === 'BALANCED') resolution = [640, 480];
        else if (mode === 'HIGH') resolution = [1280, 720];
        else if (mode === 'ULTRA') resolution = [1920, 1080];
        
        // Confirmation Warning logic
        if (mode === 'HIGH' || mode === 'ULTRA') {
            const profileStr = profile === 'auto' ? 'low-end/Raspberry Pi' : profile;
            const message = `WARNING: Selecting ${mode} mode (${resolution[0]}x${resolution[1]}) is resource-intensive.\n\nOn devices like the Raspberry Pi, this can cause thermal throttling, camera freezes, and latency.\n\nDo you explicitly confirm applying this resolution?`;
            
            const confirmed = confirm(message);
            if (!confirmed) return;
        }
        
        const settings = {
            enable_motion_detection: document.getElementById('enable-motion-detection').checked,
            enable_face_detection: document.getElementById('enable-face-detection').checked,
            enable_qr_detection: document.getElementById('enable-qr-detection').checked,
            resolution: resolution,
            fps: fps,
            // Capture slider settings
            brightness: parseInt(document.getElementById('brightness')?.value || 0),
            contrast: parseFloat(document.getElementById('contrast')?.value || 1.0),
            saturation: parseFloat(document.getElementById('saturation')?.value || 1.0)
        };
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Settings saved and applied successfully', 'success');
                // Reload to sync settings state
                this.loadSettings();
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Apply settings error:', error);
            this.showNotification('Failed to apply settings', 'error');
        }
    }
    
    async autoSuggestSettings() {
        try {
            const response = await fetch('/api/performance/suggest');
            const data = await response.json();
            
            if (data.success) {
                const suggest = data.data;
                
                // Apply suggested values to input selectors
                document.getElementById('setting-resolution').value = suggest.suggested_mode;
                document.getElementById('setting-fps').value = suggest.fps;
                document.getElementById('setting-device-profile').value = suggest.device_profile;
                
                this.showNotification(`Suggested mode: ${suggest.suggested_mode} (${suggest.resolution[0]}x${suggest.resolution[1]} @ ${suggest.fps} FPS) for detected platform: ${suggest.device_profile}`, 'info');
                
                // Re-evaluate preview
                this.updatePerformancePreview();
            }
        } catch (error) {
            console.error('Auto-suggest settings error:', error);
            this.showNotification('Failed to get suggestions', 'error');
        }
    }
    
    handleKeyboard(e) {
        switch (e.key.toLowerCase()) {
            case 'f':
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
                break;
            case 's':
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.captureSnapshot();
                }
                break;
            case 'r':
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.restartCamera();
                }
                break;
            case ' ':
                if (e.target === document.body) {
                    e.preventDefault();
                }
                break;
        }
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hours}h ${minutes}m ${secs}s`;
    }
    
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Dynamic notification toast implementation
        const container = document.body;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.position = 'fixed';
        toast.style.bottom = '2rem';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.background = type === 'success' ? '#00F5D4' : type === 'error' ? '#EF4444' : '#3B82F6';
        toast.style.color = type === 'success' ? '#07090D' : '#FFFFFF';
        toast.style.padding = '0.75rem 1.5rem';
        toast.style.borderRadius = '4px';
        toast.style.fontSize = '0.9rem';
        toast.style.fontWeight = '600';
        toast.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
        toast.style.zIndex = '9999';
        toast.style.transition = 'opacity 0.3s ease, bottom 0.3s ease';
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

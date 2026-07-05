# Quick Start Guide

## 🚀 For Raspberry Pi

### First Time Setup
```bash
# 1. Clone or navigate to project directory
cd ~/FUN_WITH_CV

# 2. Run automated setup (installs everything)
bash setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start the application
python app.py
```

### Open in Browser
```
http://localhost:8888
```

You should see the live camera feed immediately.

## 🖥️ For Ubuntu/Debian Linux

```bash
# Same steps as Raspberry Pi
bash setup.sh
source venv/bin/activate
python app.py
```

## ⚙️ Configuration

Edit `.env` file to customize:
- Port: `FLASK_PORT=8888`
- Resolution: `CAMERA_RESOLUTION_WIDTH=1280`
- FPS: `CAMERA_FPS=30`
- Enable/disable features

## 🎮 Using the Dashboard

### Main Dashboard
- View live camera stream
- See real-time FPS, CPU, RAM stats
- Quick action buttons

### Camera Controls
- Adjust brightness, contrast, saturation
- Flip, rotate camera view
- Reset to defaults

### Recording
- Start/stop video recording
- Files saved to `recordings/` folder
- View recording duration

### Snapshots
- Capture images
- Browse snapshot gallery
- View image properties

### System Monitor
- CPU, RAM, disk usage
- System information
- Python & OpenCV versions
- Uptime tracking

### Event Logs
- Real-time system events
- Color-coded by level
- Auto-scrolling feed

### Settings
- Enable/disable detectors
- Save preferences
- Reset to defaults

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F | Toggle fullscreen |
| S | Capture snapshot |
| R | Restart camera |
| Space | Pause/resume stream |
| ESC | Exit fullscreen |

## 🔧 Common Tasks

### Stop the Application
```bash
Ctrl + C
```

### Deactivate Virtual Environment
```bash
deactivate
```

### View Application Logs
```bash
tail -f logs/application.log
```

### Check Recordings
```bash
ls -lh recordings/
```

### Check Snapshots
```bash
ls -lh snapshots/
```

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check connected cameras
ls /dev/video*

# Test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### High Memory Usage
- Lower resolution in `.env`
- Reduce FPS
- Disable face detection in Settings
- Restart application

### Slow Streaming
- Reduce MJPEG quality
- Lower resolution
- Reduce FPS
- Check network bandwidth

### Port Already in Use
Edit `.env`:
```env
FLASK_PORT=8889
```

## 📊 Performance Tips for Raspberry Pi 4 (1GB RAM)

1. Use 640x480 resolution instead of 1280x720
2. Set FPS to 24 instead of 30
3. Disable face detection if not needed
4. Use low recording bitrate (already configured)
5. Monitor RAM usage in System Monitor
6. Restart if RAM exceeds 80%

## 🆘 Getting Help

1. Check `logs/application.log` for errors
2. Read README.md for detailed documentation
3. Check TROUBLESHOOTING section in README
4. Verify all dependencies installed: `pip list`

## ✅ Verification Checklist

After setup, verify these work:

- [ ] Camera stream displays
- [ ] FPS counter shows live value
- [ ] Snapshot button captures image
- [ ] Recording starts/stops
- [ ] System stats update
- [ ] Logs are visible
- [ ] API health check: `curl http://localhost:8888/api/health`

## 📞 Support

```bash
# Check app version
grep VERSION config.py

# Test API
curl http://localhost:8888/api/status

# Check camera status
curl http://localhost:8888/api/camera/status
```

---

**Happy monitoring! 🎥**

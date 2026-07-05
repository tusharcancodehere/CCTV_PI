# VisionCV — OpenCV Vision Dashboard

> A production-grade, real-time computer vision dashboard built with Flask, OpenCV, and React.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-38BDF8?logo=tailwindcss)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Overview

VisionCV streams a live MJPEG camera feed to a modern SaaS-style web dashboard. It includes an adaptive performance engine that dynamically adjusts resolution and frame rate based on host CPU load, motion and face detection, JPEG quality controls, and a real-time analytics view — all configurable from the browser.

---

## Features

| Area | Details |
|------|---------|
| **Streaming** | MJPEG over HTTP — works in any browser with zero plugins |
| **Adaptive Engine** | Auto-scales FPS and quality based on CPU load |
| **Detectors** | Motion (frame diff), Face (Haar cascade), QR (OpenCV) |
| **Recording** | MP4 video capture to disk |
| **Snapshots** | JPEG frame capture with storage management |
| **Analytics** | Live graphs — FPS, CPU, RAM, temperature (Recharts) |
| **Settings** | Resolution, FPS, JPEG quality — applied without restart |
| **Offline mode** | Boots cleanly if no camera is attached; shows placeholder |
| **Raspberry Pi** | Auto-detects Pi and drops to 480p/15fps defaults |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Browser                                                       │
│  React (Vite) + TailwindCSS + Zustand + Recharts              │
│     │                                                          │
│     │ HTTP / MJPEG                                             │
│     ▼                                                          │
│  Flask (app.py)                                                │
│  ├── routes/dashboard.py     → serves React SPA               │
│  ├── routes/api.py           → JSON API                       │
│  └── routes/streaming.py     → /api/stream (MJPEG)            │
│                                                                │
│  camera/                                                       │
│  ├── manager.py    CameraManager singleton                     │
│  ├── stream.py     MJPEG frame generator (condition var)       │
│  ├── detectors.py  Motion / Face / QR                          │
│  ├── controls.py   Brightness / Contrast / Flip               │
│  ├── adaptive.py   CPU-based performance brain                 │
│  ├── recorder.py   MP4 writer                                  │
│  └── snapshots.py  JPEG capture                               │
│                                                                │
│  services/                                                     │
│  ├── analytics.py  Ring-buffer metrics + watchdog              │
│  ├── logger.py     Centralised logging                         │
│  ├── storage.py    File management                             │
│  └── watchdog.py   Camera recovery (max 3 restarts/min)       │
│                                                                │
│  config/                                                       │
│  ├── system_config.py   Server + path constants                │
│  └── camera_config.py  Camera hardware defaults               │
└────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourname/FUN_WITH_CV.git
cd FUN_WITH_CV

# 2. Setup (installs system deps + Python venv + Node deps)
chmod +x setup.sh run.sh verify.sh
./setup.sh

# 3. Launch everything
./run.sh
```

Open **http://localhost:8888**

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |
| OpenCV | 4.8+ |
| Camera device | `/dev/video0` or Pi Camera |

---

## Installation (manual)

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install Python deps
pip install -r requirements.txt

# Install and build frontend
cd frontend
npm install
npm run build
cd ..

# Start backend
python app.py
```

---

## Configuration

All runtime configuration lives in `config/system_config.py`:

```python
HOST          = "0.0.0.0"   # bind address
PORT          = 8888         # HTTP port
CAMERA_FPS    = 30           # starting FPS
CAMERA_RESOLUTION = (1280, 720)
MJPEG_QUALITY = 80           # 1–95 JPEG quality
```

Settings can also be changed at runtime via the Settings tab in the UI, which calls `POST /api/settings`.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/status` | System health (CPU, RAM, FPS, OpenCV version) |
| `GET`  | `/api/camera/status` | Camera state + resolution + frame count |
| `POST` | `/api/camera/restart` | Restart the camera pipeline |
| `GET`  | `/api/stream` | **MJPEG live stream** |
| `GET`  | `/snapshot` | Current frame as JPEG |
| `POST` | `/snapshot/capture` | Save snapshot to disk |
| `POST` | `/recording/start` | Begin MP4 recording |
| `POST` | `/recording/stop` | Stop recording + return file path |
| `GET`  | `/api/analytics` | Historical FPS/CPU/RAM data |
| `GET`  | `/api/logs?limit=N` | Recent log entries |
| `GET`  | `/api/settings` | Current settings |
| `POST` | `/api/settings` | Update settings (applied live) |
| `GET`  | `/api/health` | Simple health-check (`{"status":"healthy"}`) |

---

## Folder Structure

```
FUN_WITH_CV/
├── app.py                  # Flask entry point
├── run.sh                  # One-command launcher
├── setup.sh                # Environment installer
├── verify.sh               # Health checker
├── requirements.txt        # Python deps
│
├── config/
│   ├── system_config.py    # Server constants
│   └── camera_config.py    # Camera defaults
│
├── camera/                 # Camera pipeline
│   ├── manager.py
│   ├── stream.py
│   ├── adaptive.py
│   ├── detectors.py
│   ├── controls.py
│   ├── recorder.py
│   ├── snapshots.py
│   └── overlays.py
│
├── routes/                 # Flask blueprints
│   ├── api.py
│   ├── dashboard.py
│   └── streaming.py
│
├── services/               # Background services
│   ├── analytics.py
│   ├── logger.py
│   ├── watchdog.py
│   └── storage.py
│
├── frontend/               # React app (Vite)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css       # Design system
│   │   ├── components/
│   │   └── store/
│   └── tailwind.config.js
│
├── static/                 # Compiled frontend assets
├── templates/              # Flask HTML templates
├── logs/                   # Runtime logs
├── recordings/             # MP4 recordings
└── snapshots/              # JPEG snapshots
```

---

## Scripts

### `./run.sh`
Starts the full stack: kills stale processes, launches Flask, waits for readiness, builds React, runs verification.

### `./setup.sh`
Installs system packages (Arch / Debian), creates venv, installs Python and Node deps.

### `./verify.sh`
Read-only diagnostics: Python version, camera device, API health, frontend assets. Never installs anything.

---

## Troubleshooting

**Camera not detected**
```bash
ls /dev/video*          # check device exists
sudo usermod -aG video $USER   # add yourself to video group
```

**Port 8888 already in use**
```bash
./run.sh               # automatically kills the stale process
```

**Frontend shows blank page**
```bash
cd frontend && npm run build   # rebuild assets
```

**Backend fails to start**
```bash
cat logs/backend.log   # run.sh prints this automatically on failure
```

---

## Roadmap

- [ ] WebSocket streaming (lower latency)
- [ ] YOLO object detection integration
- [ ] Multi-camera switching
- [ ] JWT authentication
- [ ] Docker + Docker Compose
- [ ] Prometheus metrics export
- [ ] Timeline-based recording browser

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Run `./verify.sh` before committing
4. Open a pull request

---

## License

MIT — see `LICENSE` for details.

# OpenCV Vision Edge: Production-Grade IoT Camera Streaming System

An ultra-low resource, highly reliable, and self-healing real-time camera streaming and computer vision pipeline optimized for Raspberry Pi and Linux edge devices.

---

## 1. System Overview

OpenCV Vision Edge is a production-ready edge vision server that captures, processes, and streams real-time video feeds with negligible resource footprints. Designed to operate continuously on resource-constrained hardware such as the Raspberry Pi 4/5 (1GB RAM) as well as Linux desktops, the system implements a strict single-frame lifecycle to achieve deterministic latency, avoid memory leaks, and eliminate frame queue buildup. 

The web-based dashboard displays live stream feeds, tracks event logs, lists captures, and charts system telemetry (CPU, RAM, Core Temperature, and Pipeline FPS) updated dynamically based on view status.

---

## 2. Real-Time Architecture

The architecture enforces a strict decoupling of concerns across a multi-layered design:

```
[ Camera Hardware ] 
       │ (Picamera2 / OpenCV Capture)
       ▼
[ Camera Pipeline (camera/manager.py) ] ── (Single-Frame Overwrite)
       │ 
       ▼
[ Processing Layer (detectors.py, overlays.py) ] ── (In-place Drawing / Downsizer)
       │
       ▼
[ Streaming Handler (stream.py) ] ── (Single JPEG pre-encoding / Condition Variable)
       │
       ▼
[ Flask HTTP Layer (routes/streaming.py) ] ── (Stateless Multiclient yield)
       │
       ▼
[ Frontend Web Dashboard (static/js/app.js) ] ── (Lazy Tab Polling / Static Snapshots)
```

### Core Execution Design
1. **Producer-Consumer Model**: A dedicated capture thread polls the camera hardware continuously, updating a single reference to the latest frame.
2. **Single-Frame Lifecycle**: Raw frames are modified in-place with HUD overlays to prevent memory allocation overhead and garbage collection churn. No queues or buffers are used. Old frames are immediately overwritten and discarded.
3. **Pre-Encoded Shared Buffers**: Frames are encoded to JPEG exactly *once* in the capture thread. Connected HTTP streaming workers block using a thread-safe `threading.Condition` variable and yield the pre-encoded bytes to clients, preventing per-client encoding duplication.

---

## 3. Features

### Streaming Features
* **Stateless MJPEG Distribution**: High-efficiency HTTP video feed serving multiple concurrent clients without CPU degradation.
* **Shared Cached Frame Output**: Subscribing workers stream from the same pre-encoded buffer, eliminating CPU encoding bottlenecks.
* **Emergency Placeholder Frame**: Automatically renders a dynamic "CAMERA OFFLINE" image with timestamps if hardware captures are interrupted.

### AI / Vision Features
* **Frame-Differenced Motion Detection**: Lightweight motion evaluation using frame difference matrices.
* **Face Detection**: Haar Cascade classifier optimized for embedded hardware.
* **QR Code Decodification**: Integrated QR code detection and reading.
* **Internal Resolution Scaling**: Image buffers downscale to a configurable target width (`320px` to `640px`) before classification to maintain stable processing frame rates.

### System Reliability Features
* **Auto-Reconnection Retry Loop**: If a camera is unplugged or `/dev/video0` is locked on boot, a background thread retries hardware initialization every 10 seconds.
* **Watchdog Frame Verification**: Monitors frame sequence numbers and automatically restarts the capture loop if frames stall for more than 5 seconds.
* **Daemon thread control**: Start, stop, and restart operations are serialized under a lifecycle lock, preventing duplicate threads and deadlocks.
* **Process Exit Cleanup**: Uses the python `atexit` module to cleanly release hardware and terminate child threads on process shutdowns.

### Performance Features
* **Adaptive FPS Throttling**: Capture loop dynamically skips frame processing (reads and discards raw buffers to clear OS camera cache) if average CPU usage exceeds `60%`, `75%`, or `90%`.
* **Dynamic Pi Optimization**: Auto-tunes resolution to `640x480` and limits FPS to `15` when a Raspberry Pi is detected.
* **Lazy UI Polling**: The frontend dashboard pauses background status, log, and snapshot AJAX calls if their respective tabs are inactive.

---

## 4. Performance Design

To ensure continuous execution over 24 to 72 hours, the codebase employs the following optimizations:

* **Sustained Load Throttling**: Rather than reacting to transient spikes, the throttling logic measures a moving average CPU percentage to adjust frame skips and toggle detectors.
* **Memory Growth Prevention**: Historical metrics in `analytics.py` are capped strictly between 30 and 60 entries using ring buffers (`collections.deque` with `maxlen`). Snapshot and recording directories returned as JSON are capped to the 100 most recent items to avoid API payload bloating.
* **Periodic Garbage Collection**: Explicitly triggers `gc.collect()` in the background analytics loop every 30 seconds to reclaim memory blocks and combat fragmentation.
* **Non-Blocking Telemetry**: Replaced blocking `psutil` CPU percent queries with immediate, non-blocking calls (`interval=None`), eliminating Flask route latency.

---

## 5. System Requirements

* **Hardware**: Raspberry Pi 4/5 (1GB RAM minimum) or standard x86/ARM Linux laptops.
* **Operating System**: Raspberry Pi OS, Ubuntu, Debian, or Arch Linux.
* **Python**: Version 3.9, 3.10, or 3.11.

---

## 6. Tech Stack

* **Core**: Python 3
* **Web Server**: Flask
* **Computer Vision**: OpenCV (headless optimized for Pi)
* **Matrix Operations**: NumPy
* **System Telemetry**: psutil
* **Image Processing**: Pillow

---

## 7. Installation

The installation is fully automated via `setup.sh`, which detects your operating system, configures a virtual environment, installs system libraries, compiles/installs Python dependencies, and runs step-by-step checks.

```bash
# Clone the repository
git clone https://github.com/tusharcancodehere/CCTV_PI.git
cd CCTV_PI

# Make installer executable
chmod +x setup.sh

# Run the installer (requires sudo for apt packages)
./setup.sh
```

---

## 8. Usage

1. Run the installation script to start the server, or run the app manually:
   ```bash
   source venv/bin/activate
   python app.py
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:8888
   ```
3. Use the web interface to view the live feed, adjust brightness/contrast, start MP4 video recording, or capture snapshot images.
4. Settings, performance estimator evaluations, and system diagnostic logs are available under their respective tabs.

---

## 9. Use Cases

* **Edge CCTV Camera**: Deployment on remote low-power Raspberry Pi hardware as a surveillance camera.
* **Robotics Vision Feed**: Real-time video processing pipeline for mobile robotics or automated vehicles.
* **Edge AI Prototype**: A foundation for embedding more complex object classifiers or models without UI blocking.
* **System Diagnostics Dashboard**: General-purpose hardware telemetry monitoring system.

---

## 10. Performance Notes

* **Zero Queue Design**: Traditional queues buffer frames when clients get slow, leading to memory growth and stream lag. This system utilizes a condition variable to notify clients immediately, dropping frames automatically if a client's thread is blocked.
* **Single-Frame Overwrite**: Python memory allocations are kept low by reusing a single variable reference for the raw capture frame. No history is kept in memory.
* **Capped Log Ring Buffers**: System diagnostics log events are pushed to a `RingBuffer` capped at 100 entries, preventing memory expansion.

---

## 11. Final Summary

OpenCV Vision Edge is a production-grade edge vision streaming system designed from the ground up for low-memory efficiency and long-term deployment reliability on embedded edge hardware.

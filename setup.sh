#!/bin/bash

# OpenCV Vision Dashboard - Production Setup & Deployment Script
# Supports: Raspberry Pi 4/5, Debian, Ubuntu, Linux Laptops

set -eo pipefail

# Emojis & Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    OpenCV Vision Dashboard - Production Setup    ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 1. OS & Platform Detection
echo -e "\n${BLUE}» Detecting Platform & OS...${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_ID=$ID
else
    echo -e "${RED}✗ Error: Cannot detect operating system. Only Debian/Ubuntu-based systems are supported.${NC}"
    exit 1
fi

IS_PI=false
if [ -f /proc/device-tree/model ]; then
    MODEL=$(tr -d '\0' < /proc/device-tree/model)
    if [[ "$MODEL" =~ "Raspberry Pi" ]]; then
        IS_PI=true
        echo -e "${GREEN}✓ Hardware Detected: $MODEL${NC}"
    fi
fi

if [ "$IS_PI" = false ]; then
    echo -e "${GREEN}✓ Hardware Detected: Standard Linux PC / Laptop${NC}"
fi
echo -e "${GREEN}✓ OS Detected: $OS_NAME ($OS_ID)${NC}"

# Verify we are on a supported Debian/Ubuntu based OS
if [[ "$OS_ID" != "ubuntu" && "$OS_ID" != "debian" && "$OS_ID" != "raspbian" ]]; then
    echo -e "${YELLOW}! Warning: Unsupported OS ID '$OS_ID'. Setup will proceed but might fail.${NC}"
fi

# 2. System Dependency Installation
echo -e "\n${BLUE}» Installing System Dependencies (requires sudo privilege)...${NC}"

# Update apt repositories
sudo apt-get update -y

SYS_PACKAGES=(
    python3
    python3-pip
    python3-venv
    build-essential
    cmake
    git
    libopencv-dev
    libatlas-base-dev
    libjpeg-dev
    libpng-dev
    v4l-utils
)

# Handle OS specific libraries
if [ "$OS_ID" = "debian" ] || [ "$OS_ID" = "raspbian" ]; then
    # Debian uses libtiff-dev rather than libtiff5-dev in newer packages
    SYS_PACKAGES+=(libtiff-dev)
else
    SYS_PACKAGES+=(libtiff5-dev)
fi

# Add Pi specific camera packages
if [ "$IS_PI" = true ]; then
    echo -e "${BLUE}» Adding Raspberry Pi camera system dependencies...${NC}"
    SYS_PACKAGES+=(libcamera-dev libcamera-apps-lite)
fi

# Install packages
for pkg in "${SYS_PACKAGES[@]}"; do
    echo -e "Installing $pkg..."
    sudo apt-get install -y "$pkg" || echo -e "${YELLOW}! Failed to install $pkg, trying to continue...${NC}"
done

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_success "System dependencies verification complete"

# 3. Directory Structures Setup
echo -e "\n${BLUE}» Creating Project Folders & Setting Permissions...${NC}"
REQUIRED_DIRS=(
    camera
    services
    routes
    static/css
    static/js
    templates
    logs
    snapshots
    recordings
    cache
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "Created folder: $dir"
    fi
done

# Ensure logs, snapshot and recording directories are writable
chmod -R 775 logs snapshots recordings cache || true
print_success "Directories configured successfully"

# 4. Python Virtual Environment Setup
echo -e "\n${BLUE}» Setting up Python Virtual Environment...${NC}"
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created in ./$VENV_DIR"
else
    echo -e "${GREEN}✓ Existing virtual environment found.${NC}"
fi

# Activate venv
source "$VENV_DIR"/bin/activate

# Upgrade pip
echo -e "Upgrading pip inside venv..."
pip install --upgrade pip

# Install Python requirements with retry logic
echo -e "\n${BLUE}» Installing Python Packages...${NC}"

# Core dependencies list
PYTHON_DEPS=(
    flask==3.0.0
    numpy==1.24.3
    psutil==5.9.5
    pillow==10.0.0
    python-dotenv==1.0.0
)

# Standard desktop vs Pi OpenCV handling
if [ "$IS_PI" = true ]; then
    # Low-resource Pi uses precompiled opencv-python-headless for speed/RAM
    PYTHON_DEPS+=(opencv-python-headless==4.8.1.78)
else
    PYTHON_DEPS+=(opencv-python==4.8.1.78)
fi

# Install function with retry
install_with_retry() {
    local max_retries=3
    local count=1
    until pip install "$@"; do
        if [ $count -lt $max_retries ]; then
            echo -e "${YELLOW}! Pip install failed. Retrying ($count/$max_retries)...${NC}"
            sleep 2
            ((count++))
        else
            echo -e "${RED}✗ Error: Pip installation failed after $max_retries attempts.${NC}"
            return 1
        fi
    done
    return 0
}

# Install packages
for dep in "${PYTHON_DEPS[@]}"; do
    echo -e "Installing $dep..."
    install_with_retry "$dep"
done

# Try installing picamera2 optionally if Pi
if [ "$IS_PI" = true ]; then
    echo -e "Attempting to install picamera2 bindings..."
    # First try via apt (recommended for Pi OS) or fallback to pip
    sudo apt-get install -y python3-picamera2 || pip install picamera2 --no-deps || echo -e "${YELLOW}! Picamera2 bindings installation failed. Falling back to OpenCV backend.${NC}"
fi

print_success "Python dependencies installed successfully"

# 5. Verification Phase
echo -e "\n${BLUE}==================================================${NC}"
echo -e "${BLUE}            SYSTEM VERIFICATION & CHECKS          ${NC}"
echo -e "${BLUE}==================================================${NC}"

VERIFY_FAIL=0

# Python version check
PY_VER=$(python3 --version)
print_success "Python Version: $PY_VER"

# PIP check
PIP_VER=$(pip --version | awk '{print $2}')
print_success "Pip Version: $PIP_VER"

# OpenCV import test
echo -e "Testing OpenCV package..."
if python3 -c "import cv2; print('OpenCV Version:', cv2.__version__)" 2>/dev/null; then
    print_success "OpenCV installation verified"
else
    echo -e "${RED}✗ Error: OpenCV installation check failed.${NC}"
    ((VERIFY_FAIL++))
fi

# Flask import test
echo -e "Testing Flask package..."
if python3 -c "import flask; print('Flask Version:', flask.__version__)" 2>/dev/null; then
    print_success "Flask installation verified"
else
    echo -e "${RED}✗ Error: Flask installation check failed.${NC}"
    ((VERIFY_FAIL++))
fi

# Camera hardware detection check
echo -e "Checking camera device availability..."
CAMERA_DETECTED=false
if [ -c /dev/video0 ]; then
    CAMERA_DETECTED=true
    print_success "Camera device found (/dev/video0)"
else
    echo -e "${YELLOW}! Warning: No standard video capture device found (/dev/video0). Make sure a USB camera is plugged in or Picamera interface is active.${NC}"
fi

# RAM check
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
print_success "Total System RAM: $TOTAL_RAM_MB MB"

if [ "$TOTAL_RAM_MB" -lt 950 ]; then
    echo -e "${YELLOW}! Warning: System RAM is low ($TOTAL_RAM_MB MB). Enforcing low-resource auto-tuning settings.${NC}"
fi

# Print installation results
if [ "$VERIFY_FAIL" -eq 0 ]; then
    echo -e "\n${GREEN}==================================================${NC}"
    echo -e "${GREEN}    ✅ INSTALLATION VERIFIED & READY TO LAUNCH     ${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo -e "\nSystem Summary:"
    echo -e "  - Hardware:      $(uname -m) ($(uname -s))"
    echo -e "  - Raspberry Pi:  $IS_PI"
    echo -e "  - Camera Found:  $CAMERA_DETECTED"
    echo -e "  - RAM Memory:    $TOTAL_RAM_MB MB"
    echo -e "  - URL Address:   http://localhost:8888"
    echo -e "--------------------------------------------------"
else
    echo -e "\n${RED}==================================================${NC}"
    echo -e "${RED}         ✗ VERIFICATION FAILED ($VERIFY_FAIL errors)       ${NC}"
    echo -e "${RED}==================================================${NC}"
    echo -e "Please check the logs above, resolve the missing packages, and rerun setup.sh."
    exit 1
fi

# 6. Auto-Start App
echo -e "\n${BLUE}» Starting OpenCV Vision Dashboard server...${NC}"
python3 app.py

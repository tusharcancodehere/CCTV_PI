#!/bin/bash

# OpenCV Vision Dashboard - Production Setup & Deployment Script
# Supports: Raspberry Pi 4/5, Debian, Ubuntu, Arch Linux, Linux Laptops

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
    echo -e "${RED}✗ Error: Cannot detect operating system.${NC}"
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

# 2. System Dependency Installation
echo -e "\n${BLUE}» Installing System Dependencies (requires sudo privilege)...${NC}"

if [[ "$OS_ID" == "ubuntu" || "$OS_ID" == "debian" || "$OS_ID" == "raspbian" ]]; then
    sudo apt-get update -y
    SYS_PACKAGES=(python3 python3-pip python3-venv build-essential cmake git libopencv-dev libatlas-base-dev libjpeg-dev libpng-dev v4l-utils)
    if [ "$OS_ID" = "debian" ] || [ "$OS_ID" = "raspbian" ]; then
        SYS_PACKAGES+=(libtiff-dev)
    else
        SYS_PACKAGES+=(libtiff5-dev)
    fi
    if [ "$IS_PI" = true ]; then
        SYS_PACKAGES+=(libcamera-dev libcamera-apps-lite python3-picamera2 nodejs npm)
    else
        SYS_PACKAGES+=(nodejs npm)
    fi
    for pkg in "${SYS_PACKAGES[@]}"; do
        sudo apt-get install -y "$pkg" || echo -e "${YELLOW}! Failed to install $pkg${NC}"
    done

elif [[ "$OS_ID" == "arch" || "$OS_ID" == "manjaro" || "$OS_ID" == "endeavouros" ]]; then
    SYS_PACKAGES=(python python-pip python-virtualenv base-devel cmake git opencv hdf5 v4l-utils nodejs npm)
    sudo pacman -Sy --noconfirm --needed "${SYS_PACKAGES[@]}" || echo -e "${YELLOW}! Pacman install failed${NC}"
else
    echo -e "${YELLOW}! Warning: Unsupported OS '$OS_ID'. Please install python, pip, venv, opencv, and nodejs manually.${NC}"
fi

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_success "System dependencies verification complete"

# Check camera permissions
echo -e "\n${BLUE}» Verifying Camera Permissions...${NC}"
if groups $USER | grep -q '\bvideo\b'; then
    print_success "User is in 'video' group."
else
    echo -e "${YELLOW}! User is not in 'video' group. Adding...${NC}"
    sudo usermod -aG video $USER
    echo -e "${YELLOW}! You may need to log out and back in for permissions to apply.${NC}"
fi

# 3. Directory Structures & .env
echo -e "\n${BLUE}» Creating Project Folders & Files...${NC}"
REQUIRED_DIRS=(camera services routes static/css static/js static/assets templates logs snapshots recordings cache)

for dir in "${REQUIRED_DIRS[@]}"; do
    mkdir -p "$dir"
done
chmod -R 775 logs snapshots recordings cache || true

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
    else
        touch .env
        print_success "Created blank .env"
    fi
else
    print_success ".env already exists"
fi

# Make scripts executable
chmod +x run.sh setup.sh verify.sh

print_success "Directories and files configured successfully"

# 4. Python Virtual Environment Setup
echo -e "\n${BLUE}» Setting up Python Virtual Environment...${NC}"
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    if command -v python3 &>/dev/null; then
        python3 -m venv "$VENV_DIR"
    else
        python -m venv "$VENV_DIR"
    fi
    print_success "Virtual environment created"
fi

source "$VENV_DIR"/bin/activate
pip install --upgrade pip

echo -e "\n${BLUE}» Installing Python Packages...${NC}"
PYTHON_DEPS=(flask==3.0.0 numpy==1.24.3 psutil==5.9.5 pillow==10.0.0 python-dotenv==1.0.0)

if [ "$IS_PI" = true ]; then
    PYTHON_DEPS+=(opencv-python-headless==4.8.1.78)
else
    PYTHON_DEPS+=(opencv-python==4.8.1.78)
fi

install_with_retry() {
    local max=3 count=1
    until pip install "$@"; do
        if [ $count -lt $max ]; then
            sleep 2; ((count++))
        else
            return 1
        fi
    done
    return 0
}

for dep in "${PYTHON_DEPS[@]}"; do
    install_with_retry "$dep" || echo -e "${YELLOW}! Failed to install $dep${NC}"
done

# Try installing picamera2 optionally if Pi via pip if apt failed
if [ "$IS_PI" = true ]; then
    python3 -c "import picamera2" 2>/dev/null || pip install picamera2 --no-deps || true
fi

print_success "Python dependencies installed"

# 5. Node.js & React Build
echo -e "\n${BLUE}» Installing Frontend Dependencies...${NC}"
if command -v npm &>/dev/null; then
    if [ -d "frontend" ]; then
        cd frontend
        npm install --silent
        print_success "NPM dependencies installed"
        cd ..
    fi
else
    echo -e "${YELLOW}! npm not found. Skipping frontend dependencies.${NC}"
fi

# 6. Verification Phase
echo -e "\n${BLUE}==================================================${NC}"
echo -e "${BLUE}            SYSTEM VERIFICATION & CHECKS          ${NC}"
echo -e "${BLUE}==================================================${NC}"

VERIFY_FAIL=0

PY_VER=$(python --version)
print_success "Python Version: $PY_VER"

if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    print_success "Node.js Version: $NODE_VER"
else
    echo -e "${RED}✗ Error: Node.js is missing.${NC}"
    ((VERIFY_FAIL++))
fi

if python -c "import cv2" 2>/dev/null; then
    print_success "OpenCV installation verified"
else
    echo -e "${RED}✗ Error: OpenCV check failed.${NC}"
    ((VERIFY_FAIL++))
fi

if python -c "import flask" 2>/dev/null; then
    print_success "Flask installation verified"
else
    echo -e "${RED}✗ Error: Flask check failed.${NC}"
    ((VERIFY_FAIL++))
fi

CAMERA_DETECTED=false
if ls /dev/video* 1> /dev/null 2>&1 || [ "$IS_PI" = true ]; then
    CAMERA_DETECTED=true
    print_success "Camera device found or PiCamera interface available"
else
    echo -e "${YELLOW}! Warning: No standard video capture device found (/dev/video*).${NC}"
fi

if [ "$VERIFY_FAIL" -eq 0 ]; then
    echo -e "\n${GREEN}==================================================${NC}"
    echo -e "${GREEN}    ✅ INSTALLATION VERIFIED & READY TO LAUNCH     ${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo -e "You can now start the application by running:"
    echo -e "  ${YELLOW}./run.sh${NC}"
else
    echo -e "\n${RED}==================================================${NC}"
    echo -e "${RED}         ✗ VERIFICATION FAILED ($VERIFY_FAIL errors)       ${NC}"
    echo -e "${RED}==================================================${NC}"
    echo -e "Please check the logs above, resolve missing packages, and rerun setup.sh."
    exit 1
fi

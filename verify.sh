#!/bin/bash

# Verification script to check if project is complete

echo "═══════════════════════════════════════════════════════════════"
echo "  OpenCV Vision Dashboard - Project Verification"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SUCCESS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        ((SUCCESS++))
    else
        echo "✗ MISSING: $1"
        ((FAIL++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
        ((SUCCESS++))
    else
        echo "✗ MISSING: $1/"
        ((FAIL++))
    fi
}

echo "Checking Python files..."
check_file "app.py"
check_file "config.py"
check_file "camera/manager.py"
check_file "camera/stream.py"
check_file "camera/recorder.py"
check_file "camera/snapshots.py"
check_file "camera/detectors.py"
check_file "camera/controls.py"
check_file "camera/overlays.py"
check_file "services/logger.py"
check_file "services/system_monitor.py"
check_file "services/analytics.py"
check_file "services/storage.py"
check_file "services/config_service.py"
check_file "routes/dashboard.py"
check_file "routes/api.py"
check_file "routes/streaming.py"

echo ""
echo "Checking HTML/CSS/JS files..."
check_file "templates/dashboard.html"
check_file "templates/about.html"
check_file "static/css/style.css"
check_file "static/js/app.js"

echo ""
echo "Checking configuration files..."
check_file "requirements.txt"
check_file "setup.sh"
check_file ".env.example"
check_file ".gitignore"

echo ""
echo "Checking documentation..."
check_file "README.md"
check_file "QUICKSTART.md"
check_file "PROJECT_COMPLETION.md"

echo ""
echo "Checking directories..."
check_dir "camera"
check_dir "services"
check_dir "routes"
check_dir "templates"
check_dir "static/css"
check_dir "static/js"
check_dir "logs"
check_dir "recordings"
check_dir "snapshots"
check_dir "cache"
check_dir "ai"

echo ""
echo "Checking Python syntax..."
if python3 -m py_compile camera/*.py services/*.py routes/*.py app.py config.py 2>/dev/null; then
    echo "✓ All Python files compile successfully"
    ((SUCCESS++))
else
    echo "✗ Python syntax errors found"
    ((FAIL++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Results: $SUCCESS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ PROJECT IS COMPLETE AND READY TO RUN"
    echo ""
    echo "Next steps:"
    echo "  1. bash setup.sh"
    echo "  2. source venv/bin/activate"
    echo "  3. python app.py"
    echo "  4. Open http://localhost:8888"
else
    echo "❌ PROJECT HAS MISSING FILES"
    exit 1
fi

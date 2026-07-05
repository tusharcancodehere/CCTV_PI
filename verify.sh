#!/usr/bin/env bash
# =============================================================================
# verify.sh — Read-only diagnostic health checker
# Does NOT install anything. Does NOT require root.
# =============================================================================

# ── Colours ──────────────────────────────────────────────────────────────────
GRN='\033[0;32m'; RED='\033[0;31m'; YLW='\033[0;33m'; BLU='\033[0;34m'; RST='\033[0m'
ok()   { echo -e "${GRN}  ✓${RST} $*"; ((PASS++)); }
fail() { echo -e "${RED}  ✗${RST} $*"; ((FAIL++)); }
info() { echo -e "${BLU}  ·${RST} $*"; }

PASS=0; FAIL=0

echo ""
echo -e "${BLU}═══════════════════════════════════════════════════════${RST}"
echo -e "${BLU}  VisionCV — System Verification${RST}"
echo -e "${BLU}═══════════════════════════════════════════════════════${RST}"
echo ""

# ── 1. Python version ─────────────────────────────────────────────────────────
section() { echo -e "\n${YLW}▸ $*${RST}"; }

section "Python environment"
if command -v python3 &>/dev/null; then
    VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$(echo "$VER" | cut -d. -f1)
    MINOR=$(echo "$VER" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
        ok "Python $VER"
    else
        fail "Python $VER (need ≥ 3.10)"
    fi
else
    fail "python3 not found"
fi

# ── 2. Virtual environment ────────────────────────────────────────────────────
section "Virtual environment"
if [ -d "venv" ]; then
    ok "venv/ exists"
    if [ -f "venv/bin/activate" ]; then
        ok "venv/bin/activate"
    else
        fail "venv is corrupt"
    fi
else
    fail "venv/ not found — run ./setup.sh"
fi

# ── 3. Python packages ────────────────────────────────────────────────────────
section "Python packages"
if [ -f "venv/bin/python" ]; then
    PYBIN="venv/bin/python"
else
    PYBIN="python3"
fi

for pkg in flask cv2 numpy psutil; do
    if $PYBIN -c "import $pkg" 2>/dev/null; then
        VER=$($PYBIN -c "import $pkg; print(getattr($pkg,'__version__','?'))" 2>/dev/null)
        ok "$pkg $VER"
    else
        fail "$pkg not installed"
    fi
done

# ── 4. Critical Python files ──────────────────────────────────────────────────
section "Backend source files"
REQUIRED_PY=(
    app.py
    config/system_config.py
    config/camera_config.py
    camera/manager.py
    camera/stream.py
    camera/detectors.py
    camera/controls.py
    camera/recorder.py
    camera/snapshots.py
    services/analytics.py
    services/logger.py
    services/storage.py
    services/system_monitor.py
    routes/api.py
    routes/dashboard.py
    routes/streaming.py
)
for f in "${REQUIRED_PY[@]}"; do
    [ -f "$f" ] && ok "$f" || fail "$f missing"
done

# ── 5. Python syntax ──────────────────────────────────────────────────────────
section "Python syntax"
SYNTAX_ERR=0
for f in "${REQUIRED_PY[@]}"; do
    if [ -f "$f" ]; then
        if ! $PYBIN -m py_compile "$f" 2>/dev/null; then
            fail "Syntax error in $f"
            SYNTAX_ERR=1
        fi
    fi
done
[ "$SYNTAX_ERR" -eq 0 ] && ok "All Python files compile cleanly"

# ── 6. Frontend assets ────────────────────────────────────────────────────────
section "Frontend assets"
[ -f "templates/dashboard.html" ] && ok "templates/dashboard.html" || fail "templates/dashboard.html missing"
[ -f "static/assets/index.js"  ] && ok "static/assets/index.js"  || fail "static/assets/index.js missing — run frontend build"
[ -f "static/assets/index.css" ] && ok "static/assets/index.css" || fail "static/assets/index.css missing — run frontend build"

# ── 7. Configuration files ────────────────────────────────────────────────────
section "Configuration"
for f in requirements.txt setup.sh run.sh verify.sh .gitignore README.md; do
    [ -f "$f" ] && ok "$f" || fail "$f missing"
done

# ── 8. Runtime directories ────────────────────────────────────────────────────
section "Runtime directories"
for d in logs recordings snapshots cache; do
    [ -d "$d" ] && ok "$d/" || { mkdir -p "$d" && ok "$d/ (created)"; }
done

# ── 9. Camera device ──────────────────────────────────────────────────────────
section "Camera hardware"
if ls /dev/video* &>/dev/null 2>&1; then
    for dev in /dev/video*; do
        ok "$dev"
    done
else
    info "No /dev/video* found (camera may be a Pi camera or USB unplugged)"
fi

# ── 10. Backend API (if running) ─────────────────────────────────────────────
section "Backend API"
if curl -sf http://127.0.0.1:8888/api/health >/dev/null 2>&1; then
    ok "GET /api/health → OK"
    if curl -sf http://127.0.0.1:8888/api/status >/dev/null 2>&1; then
        ok "GET /api/status → OK"
    fi
    # Check stream endpoint returns correct content-type
    CT=$(curl -sI http://127.0.0.1:8888/api/stream 2>/dev/null | grep -i content-type | head -1)
    if echo "$CT" | grep -qi "multipart"; then
        ok "GET /api/stream → multipart/x-mixed-replace"
    else
        info "GET /api/stream → backend running but camera may be offline"
    fi
else
    info "Backend not running — start with ./run.sh"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLU}═══════════════════════════════════════════════════════${RST}"
echo -e "  Results: ${GRN}$PASS passed${RST}, ${RED}$FAIL failed${RST}"
echo -e "${BLU}═══════════════════════════════════════════════════════${RST}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GRN}  ✅ All checks passed — ready to launch${RST}"
    exit 0
else
    echo -e "${RED}  ❌ $FAIL check(s) failed${RST}"
    exit 1
fi

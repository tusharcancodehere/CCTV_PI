#!/usr/bin/env bash
# =============================================================================
# run.sh — OpenCV Vision Dashboard Launcher
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[0;33m'
BLU='\033[0;34m'; CYN='\033[0;36m'; RST='\033[0m'
info()  { echo -e "${BLU}[·]${RST} $*"; }
ok()    { echo -e "${GRN}[✓]${RST} $*"; }
warn()  { echo -e "${YLW}[!]${RST} $*"; }
error() { echo -e "${RED}[✗]${RST} $*"; }

PID_FILE=".backend.pid"
BACKEND_PID=""

# ── Cleanup on exit ───────────────────────────────────────────────────────────
cleanup() {
    echo ""
    info "Shutting down…"
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    ok "Clean exit."
}
trap cleanup INT TERM EXIT

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BLU}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║     OpenCV Vision Dashboard v1.0     ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${RST}"

# ── 1. Verify virtual environment ─────────────────────────────────────────────
if [[ ! -d "venv" ]]; then
    error "Virtual environment not found. Run ./setup.sh first."
    exit 1
fi
source venv/bin/activate
ok "Virtual environment active"

# ── 2. Kill any stale process ─────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        warn "Killing stale backend (PID $OLD_PID)…"
        kill -9 "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

STALE=$(lsof -ti:8888 2>/dev/null || true)
if [[ -n "$STALE" ]]; then
    warn "Freeing port 8888 (PID $STALE)…"
    kill -9 $STALE 2>/dev/null || true
    sleep 0.5
fi

# ── 3. Start Flask backend ────────────────────────────────────────────────────
mkdir -p logs
info "Starting Flask backend…"
python app.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"

# ── 4. Wait for API readiness (30 s) ─────────────────────────────────────────
info "Waiting for backend (up to 30 s)…"
READY=0
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8888/api/status >/dev/null 2>&1; then
        READY=1
        break
    fi
    # Bail early if the process already died
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

if [[ "$READY" -eq 0 ]]; then
    error "Backend failed to start. Last 20 log lines:"
    echo "──────────────────────────────────────────"
    tail -n 20 logs/backend.log 2>/dev/null || echo "(log empty)"
    echo "──────────────────────────────────────────"
    exit 1
fi
ok "Backend is alive (PID $BACKEND_PID)"

# ── 5. Build React frontend ───────────────────────────────────────────────────
if [[ -d "frontend" ]]; then
    info "Building React frontend…"
    (
        cd frontend

        # Only run npm install when node_modules is missing or package.json changed
        if [[ ! -d "node_modules" ]] || [[ "package.json" -nt "node_modules/.install_stamp" ]]; then
            npm install --silent
            touch node_modules/.install_stamp
        fi

        # Only build if src/ or package.json is newer than static/index.js
        if [[ ! -f "../static/index.js" ]] || [[ $(find src package.json -type f -newer ../static/index.js -print -quit) ]]; then
            info "Building React frontend (changes detected)…"
            if npm run build --silent 2>&1; then
                # Vite outputs index.js, index.css, index.html directly to dist/
                # Template references /static/index.js and /static/index.css
                cp dist/index.js  ../static/index.js
                cp dist/index.css ../static/index.css
                # Also keep a copy in static/assets/ for verify.sh
                mkdir -p ../static/assets
                cp dist/index.js  ../static/assets/index.js
                cp dist/index.css ../static/assets/index.css
                # Always regenerate the template from the fresh Vite output
                cp dist/index.html ../templates/dashboard.html
                echo -e "${GRN}[✓] React frontend built and linked${RST}" >&2
            else
                warn "Frontend build failed — backend still running" >&2
            fi
        else
            echo -e "${GRN}[✓] Frontend up to date (no changes detected)${RST}" >&2
        fi
    )
fi

# ── 6. System verification ───────────────────────────────────────────────────
info "Running system checks…"
bash verify.sh || warn "Some checks failed (non-fatal)"

# ── 7. Ready ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GRN}  ╔══════════════════════════════════════╗${RST}"
echo -e "${GRN}  ║        Dashboard is LIVE ✓           ║${RST}"
echo -e "${GRN}  ╚══════════════════════════════════════╝${RST}"
echo -e "  ${CYN}URL  :${RST} http://localhost:8888"
echo -e "  ${CYN}PID  :${RST} $BACKEND_PID"
echo -e "  ${CYN}Logs :${RST} logs/backend.log"
echo -e "  ${YLW}Press Ctrl+C to stop${RST}"
echo ""

# ── Keep alive ───────────────────────────────────────────────────────────────
wait "$BACKEND_PID"

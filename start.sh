#!/usr/bin/env bash
# JAL-RAKSHA AI — one-command local startup (Git Bash / Linux / macOS).
# Starts backend :8000 and frontend :5173. Ctrl+C stops both.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Backend: installing deps + starting FastAPI on :8000"
python -m pip install -q -r "$ROOT/backend/requirements.txt"
(cd "$ROOT/backend" && python -m uvicorn main:app --port 8000) &
BACK_PID=$!

echo "==> Frontend: installing deps + starting Vite on :5173"
(cd "$ROOT/frontend" && npm install --no-audit --no-fund && npm run dev) &
FRONT_PID=$!

echo "Backend PID $BACK_PID | Frontend PID $FRONT_PID"
echo "Open http://localhost:5173 (API at http://localhost:8000/docs)"
trap "kill $BACK_PID $FRONT_PID 2>/dev/null" INT TERM
wait

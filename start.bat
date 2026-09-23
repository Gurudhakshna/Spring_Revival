@echo off
REM JAL-RAKSHA AI — one-command local startup (Windows).
REM Opens backend :8000 and frontend :5173 in two windows.
set ROOT=%~dp0
echo ==^> Backend: installing deps + starting FastAPI on :8000
start "jal-raksha-backend" cmd /k "cd /d %ROOT%backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --port 8000"
echo ==^> Frontend: installing deps + starting Vite on :5173
start "jal-raksha-frontend" cmd /k "cd /d %ROOT%frontend && npm install && npm run dev"
echo Open http://localhost:5173 (API docs at http://localhost:8000/docs)

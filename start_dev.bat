@echo off
setlocal

if not exist ".venv\\Scripts\\python.exe" (
  echo [Horticalc] .venv nicht gefunden. Bitte Setup aus README.md ausfuehren.
  exit /b 1
)

start "Horticalc API" .\.venv\Scripts\python -m uvicorn api.app:app --host 127.0.0.1 --port 8000

echo.
echo [Horticalc] Frontend: http://127.0.0.1:8000/
echo [Horticalc] API:      http://127.0.0.1:8000/
echo [Horticalc] Health:   http://127.0.0.1:8000/health
echo.

@echo off
rem One-time setup (Windows). Double-click or run: scripts\setup.bat
cd /d "%~dp0.."
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example. Fill in your own keys.
)
if not exist .venv (
  python -m venv .venv || goto :error
)
.venv\Scripts\python -m pip install --upgrade pip || goto :error
.venv\Scripts\pip install -r api\requirements.txt || goto :error
pushd web
call npm install || goto :error
popd
.venv\Scripts\python scripts\check_env.py
echo.
echo Setup done. Next: scripts\run_api.bat, scripts\run_bot.bat, scripts\run_web.bat (three terminals).
exit /b 0
:error
echo.
echo Setup FAILED. Read the error above.
exit /b 1

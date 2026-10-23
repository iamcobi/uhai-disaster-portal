@echo off
setlocal
cd /d "%~dp0"
title UHAI Portal - keep this window open
if exist ".venv\Scripts\python.exe" goto ready
echo Preparing your private Python environment. First setup needs internet.
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" setup_portal.py
) else (
  py -3 setup_portal.py
)
if errorlevel 1 goto failed
:ready
echo Opening UHAI Portal. Keep this window open while using the app.
echo All calculations run on this laptop. Press Ctrl+C to stop.
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo The portal could not start. Check Python and run SETUP_PORTAL.cmd.
echo Copy any error above if you need help.
pause
exit /b 1

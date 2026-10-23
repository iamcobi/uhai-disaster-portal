@echo off
setlocal
cd /d "%~dp0"
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" setup_portal.py
) else (
  py -3 setup_portal.py
)
pause

@echo off
setlocal
title TEACHERF _SIM
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
set "PYTHONUTF8=1"
set "QT_QPA_PLATFORM="
if /i "%~1"=="--check" goto check
if not exist "data\simulation\logs" mkdir "data\simulation\logs"
echo Opening the local teacher panel. Reports: data\simulation.
echo [%date% %time%] Teacher started >> "data\simulation\logs\teacher.log"
".venv\Scripts\python.exe" -u tools\run_sim.py teacher >> "data\simulation\logs\teacher.log" 2>&1
if errorlevel 1 goto failed
exit /b 0
:check
".venv\Scripts\python.exe" tools\run_sim.py teacher --check
exit /b %errorlevel%
:missing
echo Create .venv and install requirements.txt first. See README.md.
pause
exit /b 1
:failed
echo Startup failed. Details: %CD%\data\simulation\logs\teacher.log
pause
exit /b 1

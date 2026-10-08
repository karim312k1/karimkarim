@echo off
setlocal
title STUDENT-sim
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
set "PYTHONUTF8=1"
set "QT_QPA_PLATFORM="
if /i "%~1"=="--check" goto check
if not exist "data\simulation\logs" mkdir "data\simulation\logs"
echo Opening the local student test. Please wait for the window.
echo Emergency release: Ctrl+Alt+F12. Protection releases after 60 seconds.
echo F8 saves a screenshot. Reports stay in data\simulation.
echo [%date% %time%] Student started >> "data\simulation\logs\student.log"
".venv\Scripts\python.exe" -u tools\run_sim.py student >> "data\simulation\logs\student.log" 2>&1
if errorlevel 1 goto failed
exit /b 0
:check
".venv\Scripts\python.exe" tools\run_sim.py student --check
exit /b %errorlevel%
:missing
echo Create .venv and install requirements.txt first. See README.md.
pause
exit /b 1
:failed
echo Startup failed. Details: %CD%\data\simulation\logs\student.log
pause
exit /b 1

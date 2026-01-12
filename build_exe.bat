@echo off
REM Build the executable with PyInstaller

REM Change to the script directory
cd /d %~dp0

REM Activate virtual environment
call venv\Scripts\activate

REM Build the executable
pyinstaller --onefile run.py

pause

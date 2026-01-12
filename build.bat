@echo off
cd /d %~dp0
pyinstaller app.spec
pause

@echo off
cd /d %~dp0
echo Flaskアプリを起動中...
start "" cmd /k python app.py
timeout /t 3 >nul
start "" http://127.0.0.1:5000

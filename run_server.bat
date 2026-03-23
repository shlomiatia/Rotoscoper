@echo off
echo Starting Animation Server...
start "" python server.py
timeout /t 3 /nobreak >nul
start http://localhost:5000
echo Server started and browser opened.
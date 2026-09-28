@echo off
title News Tracker
cd /d "%~dp0"
where py >nul 2>nul && (py -3 app\server.py & goto :end)
where python >nul 2>nul && (python app\server.py & goto :end)
echo Python is not installed.
echo Please install it from https://www.python.org/downloads/
echo (tick "Add Python to PATH" during install), then double-click Start.bat again.
pause
:end

@echo off
title ELEVIX Backend API
echo Starting ELEVIX Backend...
cd /d %~dp0
..\.venv\Scripts\python.exe src\api\main.py
pause

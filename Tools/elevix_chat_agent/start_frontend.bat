@echo off
title ELEVIX Frontend UI
echo Starting ELEVIX Frontend...
cd /d %~dp0
..\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
pause

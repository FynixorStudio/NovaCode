@echo off
chcp 65001 >nul
title NovaCode Launcher
cd /d "%~dp0"

echo Memeriksa dependensi...
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo Menginstall customtkinter...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

echo Menjalankan NovaCode...
python main.py
if errorlevel 1 pause

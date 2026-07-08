@echo off
chcp 65001 >nul
title Helium
echo.
echo  ====================================
echo    Helium - 音频变速变调工具
echo  ====================================
echo.
echo  Press Ctrl+C to stop the server
echo.
python "%~dp0app.py"
echo.
pause

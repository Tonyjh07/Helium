@echo off
chcp 65001 >nul
title Helium
python "%~dp0app.py"
pause

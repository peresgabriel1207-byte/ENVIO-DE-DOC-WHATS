@echo off
chcp 65001 >nul
cd /d "%~dp0"
python cadastrar_cliente.py
pause

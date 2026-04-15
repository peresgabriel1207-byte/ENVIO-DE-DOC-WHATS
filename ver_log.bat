@echo off
chcp 65001 >nul
REM ============================================================
REM VER LOG DE ENVIOS - Abre no Excel ou no terminal
REM ============================================================

cd /d "%~dp0"

if exist "logs\log_envios.csv" (
    echo.
    echo Abrindo log de envios...
    echo.
    start "" "logs\log_envios.csv"
) else (
    echo.
    echo Nenhum log encontrado ainda.
    echo O log sera criado apos o primeiro envio.
    echo.
)

pause

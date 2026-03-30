@echo off
chcp 65001 >nul
REM ============================================================
REM INICIAR ROBO DE ENVIO DE DOCUMENTOS
REM Clique duas vezes para iniciar o monitoramento
REM ============================================================

set DIR=%~dp0
cd /d "%DIR%"

echo.
echo Iniciando Robo de Envio de Documentos...
echo Nao feche esta janela enquanto o robo estiver rodando!
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu um erro ao iniciar o robo.
    echo Verifique se o Python esta instalado e as dependencias foram instaladas.
    echo.
)

pause

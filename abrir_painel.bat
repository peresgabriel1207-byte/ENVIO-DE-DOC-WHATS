@echo off
chcp 65001 >nul
REM ============================================================
REM ABRIR PAINEL WEB - Robo de Envio de Documentos
REM Inicia o servidor web e abre no navegador
REM ============================================================

cd /d "%~dp0"

echo.
echo  ===================================================
echo     PAINEL WEB - Envio de Documentos
echo  ===================================================
echo.
echo  Abrindo no navegador...
echo  Endereco: http://localhost:5000
echo.
echo  NAO FECHE ESTA JANELA enquanto estiver usando!
echo  Pressione Ctrl+C para parar.
echo.

REM Abrir navegador automaticamente apos 2 segundos
start "" "http://localhost:5000"

REM Iniciar o servidor
python app.py

pause

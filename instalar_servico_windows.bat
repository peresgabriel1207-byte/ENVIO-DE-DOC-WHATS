@echo off
chcp 65001 >nul
REM ============================================================
REM INSTALAR ROBO COMO TAREFA AGENDADA DO WINDOWS
REM Assim ele inicia automaticamente quando o servidor ligar
REM Execute como Administrador!
REM ============================================================

echo.
echo ══════════════════════════════════════════════════════════
echo   INSTALANDO ROBO COMO TAREFA AUTOMATICA DO WINDOWS
echo ══════════════════════════════════════════════════════════
echo.

set DIR=%~dp0

REM --- Criar tarefa agendada que inicia com o Windows ---
schtasks /create /tn "RoboEnvioDocumentos" /tr "pythonw \"%DIR%main.py\"" /sc onstart /ru SYSTEM /rl HIGHEST /f >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [OK] Tarefa agendada criada com sucesso!
    echo.
    echo O robo vai iniciar automaticamente quando o servidor ligar.
    echo.
    echo Comandos uteis:
    echo   Iniciar agora:   schtasks /run /tn "RoboEnvioDocumentos"
    echo   Parar:           schtasks /end /tn "RoboEnvioDocumentos"
    echo   Remover:         schtasks /delete /tn "RoboEnvioDocumentos" /f
    echo   Ver status:      schtasks /query /tn "RoboEnvioDocumentos"
) else (
    echo [ERRO] Nao foi possivel criar a tarefa agendada.
    echo Certifique-se de executar como Administrador.
)

echo.
pause

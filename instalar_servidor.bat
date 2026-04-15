@echo off
chcp 65001 >nul
REM ============================================================
REM INSTALACAO DO ROBO DE ENVIO DE DOCUMENTOS NO SERVIDOR WINDOWS
REM Execute como Administrador (botao direito > Executar como administrador)
REM ============================================================

echo.
echo ══════════════════════════════════════════════════════════
echo    INSTALACAO - ROBO DE ENVIO DE DOCUMENTOS
echo    Servidor Windows com pasta compartilhada para 5 PCs
echo ══════════════════════════════════════════════════════════
echo.

set DIR_INSTALACAO=%~dp0

REM --- Criar pastas ---
echo [1/5] Criando estrutura de pastas...
if not exist "%DIR_INSTALACAO%documentos_envio" mkdir "%DIR_INSTALACAO%documentos_envio"
if not exist "%DIR_INSTALACAO%documentos_enviados" mkdir "%DIR_INSTALACAO%documentos_enviados"
if not exist "%DIR_INSTALACAO%logs" mkdir "%DIR_INSTALACAO%logs"
echo   [OK] Pastas criadas

REM --- Verificar Python ---
echo.
echo [2/5] Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [ERRO] Python nao encontrado!
    echo   Baixe e instale: https://www.python.org/downloads/
    echo   IMPORTANTE: Marque "Add Python to PATH" na instalacao!
    pause
    exit /b 1
)
echo   [OK] Python encontrado

REM --- Instalar dependencias ---
echo.
echo [3/5] Instalando dependencias...
python -m pip install -r "%DIR_INSTALACAO%requirements.txt" --quiet
echo   [OK] Dependencias instaladas

REM --- Configurar .env ---
echo.
echo [4/5] Verificando configuracao...
if not exist "%DIR_INSTALACAO%.env" (
    copy "%DIR_INSTALACAO%.env.example" "%DIR_INSTALACAO%.env" >nul
    echo   [ATENCAO] Arquivo .env criado. EDITE COM SUAS CREDENCIAIS!
) else (
    echo   [OK] Arquivo .env ja existe
)

REM --- Compartilhar pasta na rede ---
echo.
echo [5/5] Compartilhando pasta na rede...
echo.
set /p COMPARTILHAR="Deseja compartilhar a pasta documentos_envio na rede? (S/N): "
if /i "%COMPARTILHAR%"=="S" (
    net share DocumentosContabilidade="%DIR_INSTALACAO%documentos_envio" /GRANT:Todos,CHANGE >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] Pasta compartilhada como: \\%COMPUTERNAME%\DocumentosContabilidade
        echo.
        echo   Nos outros computadores, acesse:
        echo   \\%COMPUTERNAME%\DocumentosContabilidade
    ) else (
        echo   [AVISO] Nao foi possivel compartilhar automaticamente.
        echo   Compartilhe manualmente: botao direito na pasta ^> Propriedades ^> Compartilhamento
    )
)

REM --- Testar ---
echo.
echo Testando configuracao...
python "%DIR_INSTALACAO%main.py" --testar

echo.
echo ══════════════════════════════════════════════════════════
echo    INSTALACAO CONCLUIDA!
echo.
echo    Proximos passos:
echo    1. Edite o .env com suas credenciais reais
echo    2. Cadastre clientes no clientes.json
echo    3. Execute: iniciar_robo.bat
echo ══════════════════════════════════════════════════════════
echo.
pause

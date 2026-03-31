@echo off
chcp 65001 >nul
REM ============================================================
REM INSTALADOR COMPLETO - ROBO DE ENVIO DE DOCUMENTOS
REM Instala TUDO que precisa no servidor Windows
REM Execute como Administrador!
REM ============================================================

cd /d "%~dp0"
set DIR=%~dp0

echo.
echo  ===================================================
echo   INSTALADOR COMPLETO - ROBO DE ENVIO DE DOCUMENTOS
echo  ===================================================
echo.
echo  Este instalador vai configurar:
echo    1. Python e dependencias
echo    2. Docker Desktop (WhatsApp API local)
echo    3. Pasta compartilhada na rede
echo    4. Inicio automatico
echo.
echo  IMPORTANTE: Execute como Administrador!
echo.
pause

REM --- PASSO 1: Verificar Python ---
echo.
echo  [1/5] Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    [ERRO] Python nao encontrado!
    echo.
    echo    Baixe e instale o Python:
    echo    https://www.python.org/downloads/
    echo.
    echo    IMPORTANTE: Marque "Add Python to PATH" na instalacao!
    echo.
    pause
    exit /b 1
)
echo    [OK] Python encontrado
python -m pip install -r "%DIR%requirements.txt" --quiet 2>nul
echo    [OK] Dependencias Python instaladas

REM --- PASSO 2: Verificar Docker ---
echo.
echo  [2/5] Verificando Docker...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    [AVISO] Docker nao encontrado!
    echo.
    echo    O Docker e necessario para rodar o WhatsApp local.
    echo    Baixe o Docker Desktop:
    echo    https://www.docker.com/products/docker-desktop/
    echo.
    echo    Apos instalar o Docker, execute este instalador novamente.
    echo.
    set /p CONTINUAR="    Continuar sem Docker? O email funcionara, mas o WhatsApp nao. (S/N): "
    if /i not "%CONTINUAR%"=="S" (
        pause
        exit /b 1
    )
) else (
    echo    [OK] Docker encontrado
    echo    [INFO] Iniciando WhatsApp API local...
    docker compose up -d 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo    [OK] WhatsApp API iniciada!
    ) else (
        echo    [AVISO] Erro ao iniciar Docker. Verifique se o Docker Desktop esta aberto.
    )
)

REM --- PASSO 3: Criar pastas ---
echo.
echo  [3/5] Criando pastas...
if not exist "%DIR%documentos_envio" mkdir "%DIR%documentos_envio"
if not exist "%DIR%documentos_enviados" mkdir "%DIR%documentos_enviados"
if not exist "%DIR%logs" mkdir "%DIR%logs"
echo    [OK] Pastas criadas

REM --- PASSO 4: Configurar .env ---
echo.
echo  [4/5] Configurando...
if not exist "%DIR%.env" (
    copy "%DIR%.env.example" "%DIR%.env" >nul
    REM Atualizar .env com a chave da API local
    powershell -Command "(Get-Content '%DIR%.env') -replace 'sua_api_key', 'SuaChaveSegura123' -replace 'sua_instancia', 'robo-contabilidade' | Set-Content '%DIR%.env'" 2>nul
    echo    [OK] Arquivo .env criado com configuracoes locais
    echo    [ATENCAO] Edite o .env para configurar seu EMAIL
) else (
    echo    [OK] Arquivo .env ja existe
)

REM --- PASSO 5: Compartilhar pasta ---
echo.
echo  [5/5] Compartilhamento de rede...
set /p COMPARTILHAR="    Compartilhar pasta na rede para os outros PCs? (S/N): "
if /i "%COMPARTILHAR%"=="S" (
    net share DocumentosContabilidade="%DIR%documentos_envio" /GRANT:Todos,CHANGE >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    [OK] Pasta compartilhada!
        echo    [INFO] Nos outros PCs, acesse: \\%COMPUTERNAME%\DocumentosContabilidade
    ) else (
        echo    [AVISO] Nao foi possivel compartilhar automaticamente.
        echo    Compartilhe manualmente: botao direito na pasta, Propriedades, Compartilhamento
    )
) else (
    echo    [OK] Compartilhamento pulado
)

echo.
echo  ===================================================
echo   INSTALACAO CONCLUIDA!
echo  ===================================================
echo.
echo   O que fazer agora:
echo.
echo   1. Edite o .env com seu EMAIL (Gmail, Outlook, etc)
echo   2. Clique em: abrir_painel.bat
echo      (o painel web abre no navegador)
echo   3. No painel, conecte seu WhatsApp pelo QR Code
echo   4. Cadastre seus clientes
echo   5. Comece a enviar!
echo.
echo   Nos outros PCs:
echo   Mapeie \\%COMPUTERNAME%\DocumentosContabilidade como Z:
echo.
echo  ===================================================
echo.
pause

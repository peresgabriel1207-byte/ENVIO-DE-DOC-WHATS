#!/bin/bash
# ============================================================
# INSTALACAO DO ROBO DE ENVIO DE DOCUMENTOS NO SERVIDOR
# Execute como administrador: sudo bash instalar_servidor.sh
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   INSTALACAO - ROBO DE ENVIO DE DOCUMENTOS              ║"
echo "║   Servidor com pasta compartilhada para 5 PCs           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# --- Detectar sistema operacional ---
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ -f /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    SO="windows"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SO="linux"
else
    SO="outro"
fi

echo "[INFO] Sistema detectado: $SO"

# --- Diretorio de instalacao ---
DIR_INSTALACAO="$(cd "$(dirname "$0")" && pwd)"
echo "[INFO] Diretorio de instalacao: $DIR_INSTALACAO"

# --- Criar pastas ---
echo ""
echo "[1/4] Criando estrutura de pastas..."
mkdir -p "$DIR_INSTALACAO/documentos_envio"
mkdir -p "$DIR_INSTALACAO/documentos_enviados"
mkdir -p "$DIR_INSTALACAO/logs"
echo "  [OK] Pastas criadas"

# --- Instalar dependencias Python ---
echo ""
echo "[2/4] Instalando dependencias Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "  [ERRO] Python nao encontrado! Instale Python 3.10+ primeiro."
    echo "  Download: https://www.python.org/downloads/"
    exit 1
fi

echo "  [INFO] Python encontrado: $($PYTHON --version)"
$PYTHON -m pip install -r "$DIR_INSTALACAO/requirements.txt" --quiet
echo "  [OK] Dependencias instaladas"

# --- Configurar .env ---
echo ""
echo "[3/4] Verificando configuracao..."
if [ ! -f "$DIR_INSTALACAO/.env" ]; then
    cp "$DIR_INSTALACAO/.env.example" "$DIR_INSTALACAO/.env"
    echo "  [ATENCAO] Arquivo .env criado a partir do exemplo."
    echo "  VOCE PRECISA EDITAR O .env COM SUAS CREDENCIAIS REAIS!"
else
    echo "  [OK] Arquivo .env ja existe"
fi

# --- Testar configuracao ---
echo ""
echo "[4/4] Testando configuracao..."
$PYTHON "$DIR_INSTALACAO/main.py" --testar

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   INSTALACAO CONCLUIDA!                                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║   Proximos passos:                                       ║"
echo "║   1. Edite o .env com suas credenciais reais             ║"
echo "║   2. Cadastre clientes no clientes.json                  ║"
echo "║   3. Compartilhe a pasta documentos_envio na rede        ║"
echo "║   4. Execute: python main.py                             ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

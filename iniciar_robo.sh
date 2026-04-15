#!/bin/bash
# Iniciar Robo de Envio de Documentos
# Execute: bash iniciar_robo.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo ""
echo "Iniciando Robo de Envio de Documentos..."
echo "Pressione Ctrl+C para parar."
echo ""

python3 main.py

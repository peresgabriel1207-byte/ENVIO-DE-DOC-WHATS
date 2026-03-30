#!/usr/bin/env python3
"""
Robo de Envio Automatico de Documentos da Contabilidade.

Monitora uma pasta e envia documentos automaticamente por WhatsApp e Email.
O CNPJ no nome do arquivo identifica o destinatario.

Uso:
    python main.py              # Inicia o monitoramento
    python main.py --enviar     # Envia todos os arquivos ja na pasta (sem monitorar)
    python main.py --testar     # Testa a configuracao sem enviar nada
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

from src.watcher import iniciar_monitoramento
from src.cnpj_extractor import identificar_destinatario, carregar_clientes


def testar_configuracao():
    """Testa se a configuracao esta correta."""
    print("\n[TESTE] Verificando configuracao...\n")
    erros = 0

    # Verificar .env
    if not os.path.exists(".env"):
        print("  [FALHA] Arquivo .env nao encontrado. Copie .env.example para .env e configure.")
        erros += 1
    else:
        print("  [OK] Arquivo .env encontrado")

    # Verificar credenciais de email
    if os.getenv("EMAIL_REMETENTE") and os.getenv("EMAIL_SENHA"):
        print(f"  [OK] Email configurado: {os.getenv('EMAIL_REMETENTE')}")
    else:
        print("  [FALHA] Email nao configurado no .env")
        erros += 1

    # Verificar credenciais do WhatsApp
    if os.getenv("WHATSAPP_API_KEY") and os.getenv("WHATSAPP_INSTANCE"):
        print(f"  [OK] WhatsApp configurado: instancia '{os.getenv('WHATSAPP_INSTANCE')}'")
    else:
        print("  [FALHA] WhatsApp nao configurado no .env")
        erros += 1

    # Verificar clientes
    try:
        clientes = carregar_clientes("clientes.json")
        ativos = [c for c in clientes if c.get("ativo", True)]
        print(f"  [OK] {len(ativos)} cliente(s) ativo(s) cadastrado(s)")
        for c in ativos:
            print(f"       - {c['nome']} (CNPJ: {c['cnpj']})")
    except FileNotFoundError:
        print("  [FALHA] Arquivo clientes.json nao encontrado")
        erros += 1

    # Verificar pastas
    pasta_entrada = os.getenv("PASTA_ENTRADA", "./documentos_envio")
    pasta_enviados = os.getenv("PASTA_ENVIADOS", "./documentos_enviados")

    for pasta in [pasta_entrada, pasta_enviados]:
        if os.path.exists(pasta):
            print(f"  [OK] Pasta existe: {pasta}")
        else:
            print(f"  [INFO] Pasta sera criada: {pasta}")

    print(f"\n{'='*50}")
    if erros == 0:
        print("  TUDO OK! Pronto para iniciar.")
    else:
        print(f"  {erros} problema(s) encontrado(s). Corrija antes de iniciar.")
    print(f"{'='*50}\n")

    return erros == 0


def enviar_existentes():
    """Envia todos os arquivos que ja estao na pasta de entrada."""
    from src.email_sender import enviar_email
    from src.whatsapp_sender import enviar_whatsapp
    from src.audit_log import registrar_envio, registrar_erro

    pasta_entrada = os.getenv("PASTA_ENTRADA", "./documentos_envio")

    if not os.path.exists(pasta_entrada):
        print(f"[ERRO] Pasta nao encontrada: {pasta_entrada}")
        return

    arquivos = [f for f in os.listdir(pasta_entrada) if not f.startswith(".") and os.path.isfile(os.path.join(pasta_entrada, f))]

    if not arquivos:
        print(f"[INFO] Nenhum arquivo encontrado em {pasta_entrada}")
        return

    print(f"\n[INFO] {len(arquivos)} arquivo(s) encontrado(s). Processando...\n")

    for nome_arquivo in arquivos:
        caminho = os.path.join(pasta_entrada, nome_arquivo)
        print(f"\n{'='*60}")
        print(f"[PROCESSANDO] {nome_arquivo}")

        cliente = identificar_destinatario(nome_arquivo, "clientes.json")

        if not cliente:
            print(f"  [ERRO] Cliente nao identificado para: {nome_arquivo}")
            registrar_erro(nome_arquivo, "CNPJ nao encontrado ou cliente nao cadastrado")
            continue

        print(f"  [OK] Cliente: {cliente['nome']}")

        # Enviar Email
        resultado_email = enviar_email(
            destinatario_email=cliente["email"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        print(f"  [EMAIL] {resultado_email['mensagem']}")

        # Enviar WhatsApp
        resultado_whatsapp = enviar_whatsapp(
            numero_whatsapp=cliente["whatsapp"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        print(f"  [WHATSAPP] {resultado_whatsapp['mensagem']}")

        # Log
        registrar_envio(
            arquivo=nome_arquivo,
            cnpj=cliente["cnpj_extraido"],
            nome_cliente=cliente["nome"],
            email_destino=cliente["email"],
            resultado_email=resultado_email,
            whatsapp_destino=cliente["whatsapp"],
            resultado_whatsapp=resultado_whatsapp,
        )

        # Mover se enviado
        if resultado_email["sucesso"] or resultado_whatsapp["sucesso"]:
            pasta_enviados = os.getenv("PASTA_ENVIADOS", "./documentos_enviados")
            os.makedirs(pasta_enviados, exist_ok=True)
            import shutil
            import time
            destino = os.path.join(pasta_enviados, nome_arquivo)
            if os.path.exists(destino):
                base, ext = os.path.splitext(nome_arquivo)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                destino = os.path.join(pasta_enviados, f"{base}_{timestamp}{ext}")
            shutil.move(caminho, destino)
            print(f"  [MOVIDO] {destino}")

    print(f"\n{'='*60}")
    print("[CONCLUIDO] Verifique o log em logs/log_envios.csv")


def main():
    parser = argparse.ArgumentParser(description="Robo de Envio de Documentos da Contabilidade")
    parser.add_argument("--testar", action="store_true", help="Testar configuracao")
    parser.add_argument("--enviar", action="store_true", help="Enviar arquivos existentes na pasta")
    args = parser.parse_args()

    if args.testar:
        testar_configuracao()
        return

    if args.enviar:
        enviar_existentes()
        return

    # Modo padrao: monitoramento continuo
    pasta_entrada = os.getenv("PASTA_ENTRADA", "./documentos_envio")
    pasta_enviados = os.getenv("PASTA_ENVIADOS", "./documentos_enviados")

    iniciar_monitoramento(pasta_entrada, pasta_enviados, "clientes.json")


if __name__ == "__main__":
    main()

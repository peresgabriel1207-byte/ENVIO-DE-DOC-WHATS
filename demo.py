#!/usr/bin/env python3
"""
DEMO - Simulacao completa do robo de envio de documentos.

Este script simula todo o fluxo SEM enviar nada de verdade.
Ele substitui os modulos de envio por versoes fake para voce
ver como o sistema funciona.
"""

import os
import sys
import time
import shutil
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# MOCK dos modulos de envio (simula sem enviar de verdade)
# ============================================================

import src.email_sender
import src.whatsapp_sender


def mock_enviar_email(destinatario_email, nome_cliente, caminho_arquivo, **kwargs):
    """Simula envio de email com sucesso."""
    time.sleep(0.5)  # Simula tempo de envio
    return {
        "sucesso": True,
        "mensagem": f"[SIMULADO] Email enviado para {destinatario_email}"
    }


def mock_enviar_whatsapp(numero_whatsapp, nome_cliente, caminho_arquivo, **kwargs):
    """Simula envio de WhatsApp com sucesso."""
    time.sleep(0.5)  # Simula tempo de envio
    return {
        "sucesso": True,
        "mensagem": f"[SIMULADO] WhatsApp enviado para {numero_whatsapp}"
    }


# Substituir funcoes reais pelas simuladas
src.email_sender.enviar_email = mock_enviar_email
src.whatsapp_sender.enviar_whatsapp = mock_enviar_whatsapp

# Agora importar o restante (usara os mocks)
from src.cnpj_extractor import identificar_destinatario, carregar_clientes, extrair_cnpj_do_nome
from src.audit_log import registrar_envio, registrar_erro


def criar_arquivos_demo():
    """Cria arquivos PDF falsos para demonstracao."""
    pasta = os.getenv("PASTA_ENTRADA", "./documentos_envio")
    os.makedirs(pasta, exist_ok=True)

    arquivos_demo = [
        "12345678000199_balanco_anual_2024.pdf",
        "guia_DAS_98765432000111_marco2025.pdf",
        "relatorio_00000000000000_desconhecido.pdf",  # CNPJ nao cadastrado
    ]

    criados = []
    for nome in arquivos_demo:
        caminho = os.path.join(pasta, nome)
        with open(caminho, "w") as f:
            f.write(f"[DOCUMENTO DEMO] {nome}\nEste e um arquivo de demonstracao.")
        criados.append(nome)

    return criados


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║          DEMO - ROBO DE ENVIO DE DOCUMENTOS             ║
║                                                          ║
║   Este modo simula o envio SEM enviar nada de verdade.   ║
║   Serve para voce ver como o sistema funciona.           ║
╚══════════════════════════════════════════════════════════╝
    """)

    # ---- PASSO 1: Mostrar clientes cadastrados ----
    print("=" * 60)
    print("  PASSO 1: CLIENTES CADASTRADOS")
    print("=" * 60)

    try:
        clientes = carregar_clientes("clientes.json")
        for c in clientes:
            status = "ATIVO" if c.get("ativo", True) else "INATIVO"
            print(f"""
  [{status}] {c['nome']}
     CNPJ:     {c['cnpj']}
     Email:    {c['email']}
     WhatsApp: {c['whatsapp']}""")
    except Exception as e:
        print(f"  ERRO: {e}")
        return

    # ---- PASSO 2: Criar arquivos demo ----
    print(f"\n{'=' * 60}")
    print("  PASSO 2: CRIANDO ARQUIVOS DE DEMONSTRACAO")
    print("=" * 60)

    arquivos = criar_arquivos_demo()
    for arq in arquivos:
        print(f"  [CRIADO] documentos_envio/{arq}")

    input("\n  Pressione ENTER para iniciar o envio...")

    # ---- PASSO 3: Processar cada arquivo ----
    print(f"\n{'=' * 60}")
    print("  PASSO 3: PROCESSANDO ARQUIVOS")
    print("=" * 60)

    pasta_entrada = os.getenv("PASTA_ENTRADA", "./documentos_envio")
    pasta_enviados = os.getenv("PASTA_ENVIADOS", "./documentos_enviados")
    os.makedirs(pasta_enviados, exist_ok=True)

    for nome_arquivo in arquivos:
        caminho = os.path.join(pasta_entrada, nome_arquivo)

        if not os.path.exists(caminho):
            continue

        print(f"\n  {'─' * 56}")
        print(f"  ARQUIVO: {nome_arquivo}")
        print(f"  {'─' * 56}")

        # Extrair CNPJ
        cnpj = extrair_cnpj_do_nome(nome_arquivo)
        if cnpj:
            print(f"  [1/5] CNPJ extraido: {cnpj}")
        else:
            print(f"  [1/5] CNPJ nao encontrado no nome do arquivo!")
            registrar_erro(nome_arquivo, "CNPJ nao encontrado no nome do arquivo")
            continue

        # Buscar cliente
        cliente = identificar_destinatario(nome_arquivo, "clientes.json")
        if cliente:
            print(f"  [2/5] Cliente encontrado: {cliente['nome']}")
        else:
            print(f"  [2/5] Cliente com CNPJ {cnpj} NAO CADASTRADO!")
            registrar_erro(nome_arquivo, f"Cliente com CNPJ {cnpj} nao cadastrado")
            print(f"        >>> Adicione este CNPJ no clientes.json <<<")
            continue

        # Enviar Email (simulado)
        print(f"  [3/5] Enviando Email para {cliente['email']}...", end=" ", flush=True)
        resultado_email = mock_enviar_email(
            destinatario_email=cliente["email"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        print(f"OK!" if resultado_email["sucesso"] else "FALHA!")

        # Enviar WhatsApp (simulado)
        print(f"  [4/5] Enviando WhatsApp para {cliente['whatsapp']}...", end=" ", flush=True)
        resultado_whatsapp = mock_enviar_whatsapp(
            numero_whatsapp=cliente["whatsapp"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        print(f"OK!" if resultado_whatsapp["sucesso"] else "FALHA!")

        # Registrar no log
        registrar_envio(
            arquivo=nome_arquivo,
            cnpj=cliente["cnpj_extraido"],
            nome_cliente=cliente["nome"],
            email_destino=cliente["email"],
            resultado_email=resultado_email,
            whatsapp_destino=cliente["whatsapp"],
            resultado_whatsapp=resultado_whatsapp,
        )
        print(f"  [5/5] Registrado no log de auditoria")

        # Mover arquivo
        destino = os.path.join(pasta_enviados, nome_arquivo)
        shutil.move(caminho, destino)
        print(f"  [OK]  Movido para documentos_enviados/")

    # ---- PASSO 4: Resumo ----
    print(f"\n{'=' * 60}")
    print("  PASSO 4: RESUMO")
    print("=" * 60)

    # Mostrar arquivos enviados
    enviados = os.listdir(pasta_enviados)
    print(f"\n  Arquivos enviados ({len(enviados)}):")
    for e in enviados:
        if not e.startswith("."):
            print(f"    [OK] {e}")

    # Mostrar arquivos que ficaram na entrada
    restantes = [f for f in os.listdir(pasta_entrada) if not f.startswith(".")]
    if restantes:
        print(f"\n  Arquivos NAO enviados ({len(restantes)}):")
        for r in restantes:
            print(f"    [!!] {r}")

    # Mostrar log
    log_path = "logs/log_envios.csv"
    if os.path.exists(log_path):
        print(f"\n  Log de auditoria ({log_path}):")
        with open(log_path, "r") as f:
            linhas = f.readlines()
            print(f"  {'─' * 56}")
            for linha in linhas:
                campos = linha.strip().split(";")
                if campos[0] == "data_hora":
                    # cabecalho
                    print(f"  DATA/HORA           | ARQUIVO                | STATUS")
                    print(f"  {'─' * 56}")
                else:
                    data = campos[0] if len(campos) > 0 else ""
                    arq = campos[1][:22] if len(campos) > 1 else ""
                    status_e = campos[5] if len(campos) > 5 else ""
                    status_w = campos[8] if len(campos) > 8 else ""
                    print(f"  {data} | {arq:<22} | E:{status_e} W:{status_w}")

    print(f"""
{'=' * 60}
  DEMONSTRACAO CONCLUIDA!

  Para usar de verdade:
  1. Configure o .env com suas credenciais reais
  2. Cadastre seus clientes no clientes.json
  3. Execute: python main.py
  4. Coloque arquivos na pasta documentos_envio/
{'=' * 60}
    """)


if __name__ == "__main__":
    main()

"""
Modulo de log de auditoria.
Registra todos os envios em um arquivo CSV para controle e seguranca.
"""

import csv
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "log_envios.csv")

COLUNAS = [
    "data_hora",
    "arquivo",
    "cnpj",
    "nome_cliente",
    "email_destino",
    "email_status",
    "email_detalhe",
    "whatsapp_destino",
    "whatsapp_status",
    "whatsapp_detalhe",
]


def _garantir_cabecalho():
    """Cria o arquivo CSV com cabecalho se nao existir."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(COLUNAS)


def registrar_envio(
    arquivo: str,
    cnpj: str,
    nome_cliente: str,
    email_destino: str,
    resultado_email: dict,
    whatsapp_destino: str,
    resultado_whatsapp: dict,
):
    """
    Registra um envio no log de auditoria.

    Args:
        arquivo: Nome do arquivo enviado
        cnpj: CNPJ do cliente
        nome_cliente: Nome do cliente
        email_destino: Email do destinatario
        resultado_email: Dict com 'sucesso' (bool) e 'mensagem' (str)
        whatsapp_destino: Numero do WhatsApp
        resultado_whatsapp: Dict com 'sucesso' (bool) e 'mensagem' (str)
    """
    _garantir_cabecalho()

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linha = [
        agora,
        arquivo,
        cnpj,
        nome_cliente,
        email_destino,
        "ENVIADO" if resultado_email.get("sucesso") else "FALHA",
        resultado_email.get("mensagem", ""),
        whatsapp_destino,
        "ENVIADO" if resultado_whatsapp.get("sucesso") else "FALHA",
        resultado_whatsapp.get("mensagem", ""),
    ]

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(linha)

    print(f"  [LOG] Registro salvo em {LOG_FILE}")


def registrar_erro(arquivo: str, motivo: str):
    """Registra um erro (arquivo nao identificado, cliente nao encontrado, etc.)."""
    _garantir_cabecalho()

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linha = [
        agora,
        arquivo,
        "",
        "",
        "",
        "ERRO",
        motivo,
        "",
        "ERRO",
        motivo,
    ]

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(linha)

    print(f"  [LOG] Erro registrado: {motivo}")

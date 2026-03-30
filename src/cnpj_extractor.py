"""
Modulo para extrair CNPJ do nome do arquivo e buscar cliente correspondente.

Formatos aceitos no nome do arquivo:
  - 12.345.678/0001-99_documento.pdf
  - 12345678000199_documento.pdf
  - documento_12345678000199.pdf
  - qualquer arquivo que contenha 14 digitos consecutivos de CNPJ
"""

import re
import json
import os


def limpar_cnpj(cnpj: str) -> str:
    """Remove formatacao do CNPJ, mantendo apenas digitos."""
    return re.sub(r"[^0-9]", "", cnpj)


def extrair_cnpj_do_nome(nome_arquivo: str) -> str | None:
    """
    Extrai o CNPJ do nome do arquivo.
    Tenta primeiro formato com pontuacao, depois apenas digitos.
    Retorna o CNPJ limpo (14 digitos) ou None.
    """
    # Formato com pontuacao: 12.345.678/0001-99
    padrao_formatado = r"\d{2}\.?\d{3}\.?\d{3}/?(\d{4})-?\d{2}"
    match = re.search(padrao_formatado, nome_arquivo)
    if match:
        return limpar_cnpj(match.group())

    # Formato apenas digitos: 14 digitos consecutivos
    padrao_digitos = r"\d{14}"
    match = re.search(padrao_digitos, nome_arquivo)
    if match:
        return match.group()

    return None


def carregar_clientes(caminho_json: str = "clientes.json") -> list[dict]:
    """Carrega a lista de clientes do arquivo JSON."""
    if not os.path.exists(caminho_json):
        raise FileNotFoundError(f"Arquivo de clientes nao encontrado: {caminho_json}")

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    return dados.get("clientes", [])


def buscar_cliente_por_cnpj(cnpj: str, clientes: list[dict]) -> dict | None:
    """Busca um cliente pelo CNPJ na lista de clientes."""
    cnpj_limpo = limpar_cnpj(cnpj)
    for cliente in clientes:
        if limpar_cnpj(cliente["cnpj"]) == cnpj_limpo:
            if cliente.get("ativo", True):
                return cliente
    return None


def identificar_destinatario(nome_arquivo: str, caminho_clientes: str = "clientes.json") -> dict | None:
    """
    Fluxo completo: extrai CNPJ do nome do arquivo e retorna o cliente.
    Retorna None se nao encontrar CNPJ ou cliente.
    """
    cnpj = extrair_cnpj_do_nome(nome_arquivo)
    if not cnpj:
        return None

    clientes = carregar_clientes(caminho_clientes)
    cliente = buscar_cliente_por_cnpj(cnpj, clientes)

    if cliente:
        cliente["cnpj_extraido"] = cnpj

    return cliente

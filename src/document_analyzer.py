"""
Analisador inteligente de documentos.

Le o conteudo de PDFs e documentos para extrair o CNPJ de dentro do arquivo,
nao apenas do nome. Isso permite enviar documentos mesmo que o nome do arquivo
nao contenha o CNPJ.

Ordem de busca:
  1. Nome do arquivo (mais rapido)
  2. Conteudo do PDF (texto extraido)
  3. Conteudo de arquivos de texto (.txt, .csv, .xml)
"""

import os
import re


def limpar_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", cnpj)


def extrair_todos_cnpjs(texto: str) -> list[str]:
    """Extrai todos os CNPJs encontrados em um texto."""
    cnpjs = set()

    # Formato com pontuacao: 12.345.678/0001-99
    for match in re.finditer(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", texto):
        cnpj = limpar_cnpj(match.group())
        if len(cnpj) == 14:
            cnpjs.add(cnpj)

    # Formato so digitos: sequencias de 14 digitos
    for match in re.finditer(r"(?<!\d)\d{14}(?!\d)", texto):
        cnpjs.add(match.group())

    return list(cnpjs)


def extrair_texto_pdf(caminho: str) -> str:
    """Extrai texto de um arquivo PDF."""
    try:
        import pdfplumber
        texto = ""
        with pdfplumber.open(caminho) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
        return texto
    except ImportError:
        # Fallback para PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(caminho)
            texto = ""
            for pagina in reader.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto
        except ImportError:
            return ""
    except Exception:
        return ""


def extrair_texto_arquivo(caminho: str) -> str:
    """Extrai texto de arquivos de texto (.txt, .csv, .xml, etc.)."""
    extensoes_texto = {".txt", ".csv", ".xml", ".html", ".htm", ".json"}
    ext = os.path.splitext(caminho)[1].lower()

    if ext not in extensoes_texto:
        return ""

    try:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def analisar_documento(caminho: str) -> dict:
    """
    Analisa um documento e retorna informacoes extraidas.

    Retorna dict com:
      - cnpjs: lista de CNPJs encontrados
      - cnpj_principal: CNPJ mais provavel (primeiro encontrado)
      - fonte: onde o CNPJ foi encontrado ('nome_arquivo', 'conteudo_pdf', 'conteudo_texto')
      - preview: trecho do documento onde o CNPJ aparece
      - tipo_arquivo: extensao do arquivo
      - tamanho: tamanho em bytes
    """
    nome_arquivo = os.path.basename(caminho)
    ext = os.path.splitext(caminho)[1].lower()
    tamanho = os.path.getsize(caminho) if os.path.exists(caminho) else 0

    resultado = {
        "cnpjs": [],
        "cnpj_principal": None,
        "fonte": None,
        "preview": "",
        "tipo_arquivo": ext,
        "tamanho": tamanho,
        "nome_arquivo": nome_arquivo,
    }

    # 1. Tentar extrair do nome do arquivo
    cnpjs_nome = extrair_todos_cnpjs(nome_arquivo)
    if cnpjs_nome:
        resultado["cnpjs"] = cnpjs_nome
        resultado["cnpj_principal"] = cnpjs_nome[0]
        resultado["fonte"] = "nome_arquivo"
        resultado["preview"] = f"CNPJ encontrado no nome: {nome_arquivo}"
        return resultado

    # 2. Tentar extrair do conteudo do PDF
    if ext == ".pdf":
        texto_pdf = extrair_texto_pdf(caminho)
        if texto_pdf:
            cnpjs_pdf = extrair_todos_cnpjs(texto_pdf)
            if cnpjs_pdf:
                resultado["cnpjs"] = cnpjs_pdf
                resultado["cnpj_principal"] = cnpjs_pdf[0]
                resultado["fonte"] = "conteudo_pdf"
                # Encontrar trecho com o CNPJ para preview
                resultado["preview"] = _extrair_preview(texto_pdf, cnpjs_pdf[0])
                return resultado

    # 3. Tentar extrair de arquivos de texto
    texto_arquivo = extrair_texto_arquivo(caminho)
    if texto_arquivo:
        cnpjs_texto = extrair_todos_cnpjs(texto_arquivo)
        if cnpjs_texto:
            resultado["cnpjs"] = cnpjs_texto
            resultado["cnpj_principal"] = cnpjs_texto[0]
            resultado["fonte"] = "conteudo_texto"
            resultado["preview"] = _extrair_preview(texto_arquivo, cnpjs_texto[0])
            return resultado

    # Nenhum CNPJ encontrado
    resultado["fonte"] = "nao_encontrado"
    resultado["preview"] = "Nenhum CNPJ encontrado no arquivo"
    return resultado


def _extrair_preview(texto: str, cnpj: str) -> str:
    """Extrai um trecho do texto ao redor do CNPJ encontrado."""
    # Buscar formato com pontuacao ou so digitos
    padrao_fmt = rf"\d{{2}}\.?\d{{3}}\.?\d{{3}}/?\d{{4}}-?\d{{2}}"
    for match in re.finditer(padrao_fmt, texto):
        if limpar_cnpj(match.group()) == cnpj:
            inicio = max(0, match.start() - 80)
            fim = min(len(texto), match.end() + 80)
            trecho = texto[inicio:fim].replace("\n", " ").strip()
            return f"...{trecho}..."

    return f"CNPJ {cnpj} encontrado no conteudo"

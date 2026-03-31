#!/usr/bin/env python3
"""
Interface Web do Robo de Envio de Documentos.

Acesse http://localhost:5000 no navegador.

Funcionalidades:
  - Dashboard com status do robo e estatisticas
  - Upload e analise de documentos
  - Cadastro de clientes
  - Visualizacao do log de envios
  - Envio manual de documentos
"""

import os
import csv
import json
import shutil
import time
import threading
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

from src.cnpj_extractor import (
    identificar_destinatario,
    carregar_clientes,
    limpar_cnpj,
    extrair_cnpj_do_nome,
)
from src.document_analyzer import analisar_documento
from src.email_sender import enviar_email
from src.whatsapp_sender import enviar_whatsapp
from src.audit_log import registrar_envio, registrar_erro, obter_registros, obter_registro_por_id, obter_estatisticas

app = Flask(__name__)
app.secret_key = os.urandom(24)

PASTA_ENTRADA = os.getenv("PASTA_ENTRADA", "./documentos_envio")
PASTA_ENVIADOS = os.getenv("PASTA_ENVIADOS", "./documentos_enviados")
ARQUIVO_CLIENTES = "clientes.json"
LOG_FILE = "logs/log_envios.csv"

# Estado global do robo
robo_estado = {
    "ativo": False,
    "iniciado_em": None,
    "thread": None,
}


# =============================================================
# ROTAS PRINCIPAIS
# =============================================================


@app.route("/")
def dashboard():
    """Pagina principal - Dashboard."""
    stats = obter_estatisticas()
    ultimos_envios = obter_registros(10)
    arquivos_pendentes = _obter_arquivos_pendentes()
    clientes = _carregar_clientes_safe()

    return render_template(
        "dashboard.html",
        stats=stats,
        ultimos_envios=ultimos_envios,
        arquivos_pendentes=arquivos_pendentes,
        total_clientes=len(clientes),
        robo_ativo=robo_estado["ativo"],
        robo_iniciado=robo_estado["iniciado_em"],
    )


@app.route("/clientes")
def clientes_page():
    """Pagina de gerenciamento de clientes."""
    clientes = _carregar_clientes_safe()
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/adicionar", methods=["POST"])
def adicionar_cliente():
    """Adiciona um novo cliente."""
    cnpj = limpar_cnpj(request.form.get("cnpj", ""))
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    whatsapp = limpar_cnpj(request.form.get("whatsapp", ""))

    if len(cnpj) != 14:
        flash("CNPJ invalido. Deve conter 14 digitos.", "danger")
        return redirect(url_for("clientes_page"))

    if not nome or not email or not whatsapp:
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for("clientes_page"))

    dados = _carregar_dados_clientes()
    # Verificar duplicidade
    for c in dados["clientes"]:
        if limpar_cnpj(c["cnpj"]) == cnpj:
            flash(f"CNPJ {cnpj} ja cadastrado!", "warning")
            return redirect(url_for("clientes_page"))

    dados["clientes"].append({
        "cnpj": cnpj,
        "nome": nome,
        "email": email,
        "whatsapp": whatsapp,
        "ativo": True,
    })
    _salvar_dados_clientes(dados)
    flash(f"Cliente '{nome}' cadastrado com sucesso!", "success")
    return redirect(url_for("clientes_page"))


@app.route("/clientes/remover/<cnpj>", methods=["POST"])
def remover_cliente(cnpj):
    """Remove um cliente."""
    dados = _carregar_dados_clientes()
    dados["clientes"] = [c for c in dados["clientes"] if limpar_cnpj(c["cnpj"]) != cnpj]
    _salvar_dados_clientes(dados)
    flash("Cliente removido.", "success")
    return redirect(url_for("clientes_page"))


@app.route("/clientes/toggle/<cnpj>", methods=["POST"])
def toggle_cliente(cnpj):
    """Ativa/desativa um cliente."""
    dados = _carregar_dados_clientes()
    for c in dados["clientes"]:
        if limpar_cnpj(c["cnpj"]) == cnpj:
            c["ativo"] = not c.get("ativo", True)
            status = "ativado" if c["ativo"] else "desativado"
            flash(f"Cliente {status}.", "success")
            break
    _salvar_dados_clientes(dados)
    return redirect(url_for("clientes_page"))


@app.route("/enviar", methods=["GET", "POST"])
def enviar_page():
    """Pagina de envio/upload de documentos."""
    clientes = _carregar_clientes_safe()

    if request.method == "POST":
        return _processar_upload()

    arquivos_pendentes = _obter_arquivos_pendentes()
    return render_template("enviar.html", clientes=clientes, arquivos_pendentes=arquivos_pendentes)


@app.route("/analisar", methods=["POST"])
def analisar_arquivo():
    """Analisa um arquivo enviado por upload e retorna os CNPJs encontrados."""
    if "arquivo" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files["arquivo"]
    if arquivo.filename == "":
        return jsonify({"erro": "Nenhum arquivo selecionado"}), 400

    # Salvar temporariamente
    nome_seguro = secure_filename(arquivo.filename)
    os.makedirs(PASTA_ENTRADA, exist_ok=True)
    caminho_temp = os.path.join(PASTA_ENTRADA, nome_seguro)
    arquivo.save(caminho_temp)

    # Analisar
    resultado = analisar_documento(caminho_temp)

    # Buscar clientes correspondentes
    clientes_encontrados = []
    clientes = _carregar_clientes_safe()
    for cnpj in resultado["cnpjs"]:
        for c in clientes:
            if limpar_cnpj(c["cnpj"]) == cnpj and c.get("ativo", True):
                clientes_encontrados.append({
                    "cnpj": cnpj,
                    "nome": c["nome"],
                    "email": c["email"],
                    "whatsapp": c["whatsapp"],
                })

    resultado["clientes_encontrados"] = clientes_encontrados
    resultado["caminho"] = caminho_temp
    return jsonify(resultado)


@app.route("/enviar/processar", methods=["POST"])
def processar_envio():
    """Processa o envio de um documento para um cliente especifico."""
    caminho = request.form.get("caminho", "")
    cnpj = request.form.get("cnpj", "")
    enviar_por_email = request.form.get("email") == "on"
    enviar_por_whatsapp = request.form.get("whatsapp") == "on"

    if not caminho or not os.path.exists(caminho):
        flash("Arquivo nao encontrado.", "danger")
        return redirect(url_for("enviar_page"))

    nome_arquivo = os.path.basename(caminho)
    cliente = None
    clientes = _carregar_clientes_safe()
    for c in clientes:
        if limpar_cnpj(c["cnpj"]) == limpar_cnpj(cnpj):
            cliente = c
            break

    if not cliente:
        flash("Cliente nao encontrado.", "danger")
        return redirect(url_for("enviar_page"))

    resultado_email = {"sucesso": False, "mensagem": "Envio por email nao selecionado"}
    resultado_whatsapp = {"sucesso": False, "mensagem": "Envio por WhatsApp nao selecionado"}

    if enviar_por_email:
        resultado_email = enviar_email(
            destinatario_email=cliente["email"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )

    if enviar_por_whatsapp:
        resultado_whatsapp = enviar_whatsapp(
            numero_whatsapp=cliente["whatsapp"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )

    registrar_envio(
        arquivo=nome_arquivo,
        cnpj=cnpj,
        nome_cliente=cliente["nome"],
        email_destino=cliente["email"],
        resultado_email=resultado_email,
        whatsapp_destino=cliente["whatsapp"],
        resultado_whatsapp=resultado_whatsapp,
    )

    # Mover para enviados
    if resultado_email["sucesso"] or resultado_whatsapp["sucesso"]:
        os.makedirs(PASTA_ENVIADOS, exist_ok=True)
        destino = os.path.join(PASTA_ENVIADOS, nome_arquivo)
        if os.path.exists(destino):
            base, ext = os.path.splitext(nome_arquivo)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            destino = os.path.join(PASTA_ENVIADOS, f"{base}_{timestamp}{ext}")
        shutil.move(caminho, destino)
        flash(f"Documento enviado para {cliente['nome']}!", "success")
    else:
        flash(f"Falha no envio. Verifique o log.", "danger")

    return redirect(url_for("enviar_page"))


@app.route("/log")
def log_page():
    """Pagina de visualizacao do log de envios."""
    envios = obter_registros(100)
    return render_template("log.html", envios=envios)


@app.route("/relatorio/<registro_id>")
def relatorio_page(registro_id):
    """Pagina de relatorio detalhado de um envio."""
    registro = obter_registro_por_id(registro_id)
    if not registro:
        flash("Registro nao encontrado.", "danger")
        return redirect(url_for("log_page"))
    return render_template("relatorio.html", r=registro)


@app.route("/robo/toggle", methods=["POST"])
def toggle_robo():
    """Inicia ou para o robo de monitoramento."""
    if robo_estado["ativo"]:
        robo_estado["ativo"] = False
        robo_estado["iniciado_em"] = None
        flash("Robo parado.", "warning")
    else:
        _iniciar_robo_background()
        flash("Robo iniciado!", "success")

    return redirect(url_for("dashboard"))


# =============================================================
# FUNCOES AUXILIARES
# =============================================================


def _processar_upload():
    """Processa upload de arquivo."""
    if "arquivo" not in request.files:
        flash("Nenhum arquivo selecionado.", "danger")
        return redirect(url_for("enviar_page"))

    arquivo = request.files["arquivo"]
    if arquivo.filename == "":
        flash("Nenhum arquivo selecionado.", "danger")
        return redirect(url_for("enviar_page"))

    nome_seguro = secure_filename(arquivo.filename)
    os.makedirs(PASTA_ENTRADA, exist_ok=True)
    caminho = os.path.join(PASTA_ENTRADA, nome_seguro)
    arquivo.save(caminho)

    flash(f"Arquivo '{nome_seguro}' salvo na pasta de entrada.", "success")
    return redirect(url_for("enviar_page"))


def _carregar_clientes_safe() -> list[dict]:
    try:
        return carregar_clientes(ARQUIVO_CLIENTES)
    except Exception:
        return []


def _carregar_dados_clientes() -> dict:
    if os.path.exists(ARQUIVO_CLIENTES):
        with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"clientes": []}


def _salvar_dados_clientes(dados: dict):
    with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def _obter_arquivos_pendentes() -> list[dict]:
    """Lista arquivos na pasta de entrada."""
    os.makedirs(PASTA_ENTRADA, exist_ok=True)
    arquivos = []
    for nome in os.listdir(PASTA_ENTRADA):
        caminho = os.path.join(PASTA_ENTRADA, nome)
        if os.path.isfile(caminho) and not nome.startswith(".") and nome != ".gitkeep":
            cnpj = extrair_cnpj_do_nome(nome)
            arquivos.append({
                "nome": nome,
                "caminho": caminho,
                "tamanho": os.path.getsize(caminho),
                "cnpj": cnpj,
                "data": datetime.fromtimestamp(os.path.getmtime(caminho)).strftime("%d/%m/%Y %H:%M"),
            })
    return arquivos


def _iniciar_robo_background():
    """Inicia o monitoramento em background."""
    from src.watcher import iniciar_monitoramento

    robo_estado["ativo"] = True
    robo_estado["iniciado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def _rodar():
        try:
            iniciar_monitoramento(PASTA_ENTRADA, PASTA_ENVIADOS, ARQUIVO_CLIENTES)
        except Exception:
            robo_estado["ativo"] = False

    t = threading.Thread(target=_rodar, daemon=True)
    t.start()
    robo_estado["thread"] = t


if __name__ == "__main__":
    os.makedirs(PASTA_ENTRADA, exist_ok=True)
    os.makedirs(PASTA_ENVIADOS, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print("\n  Acesse no navegador: http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

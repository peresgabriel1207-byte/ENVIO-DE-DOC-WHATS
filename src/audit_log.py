"""
Modulo de log de auditoria.
Registra todos os envios em JSON para facil leitura e geracao de relatorios visuais.
Tambem mantem o CSV para quem quiser abrir no Excel.
"""

import csv
import json
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE_CSV = os.path.join(LOG_DIR, "log_envios.csv")
LOG_FILE_JSON = os.path.join(LOG_DIR, "log_envios.json")

CSV_COLUNAS = [
    "data_hora", "arquivo", "cnpj", "nome_cliente",
    "email_destino", "email_status", "email_detalhe",
    "whatsapp_destino", "whatsapp_status", "whatsapp_detalhe",
]

# Mensagens de erro amigaveis
ERROS_AMIGAVEIS = {
    "Erro de autenticacao SMTP": {
        "titulo": "Senha do email incorreta",
        "explicacao": "A senha configurada no .env esta errada ou expirou.",
        "solucao": "Gere uma nova senha de app no Gmail e atualize EMAIL_SENHA no arquivo .env",
    },
    "Erro SMTP": {
        "titulo": "Problema no servidor de email",
        "explicacao": "O servidor de email recusou a conexao ou esta fora do ar.",
        "solucao": "Verifique se o EMAIL_SMTP_HOST e EMAIL_SMTP_PORT estao corretos no .env",
    },
    "Nao foi possivel conectar a API do WhatsApp": {
        "titulo": "WhatsApp desconectado",
        "explicacao": "A API do WhatsApp (Evolution API) nao esta respondendo.",
        "solucao": "Verifique se o servidor da Evolution API esta rodando e se o WHATSAPP_API_URL esta correto",
    },
    "Timeout": {
        "titulo": "Conexao demorou demais",
        "explicacao": "O servidor nao respondeu a tempo.",
        "solucao": "Verifique a conexao de internet do servidor",
    },
    "CNPJ nao encontrado": {
        "titulo": "CNPJ nao detectado",
        "explicacao": "Nao foi possivel encontrar um CNPJ no nome nem no conteudo do arquivo.",
        "solucao": "Renomeie o arquivo incluindo o CNPJ (ex: 12345678000199_documento.pdf) ou cadastre o CNPJ no conteudo",
    },
    "cliente nao cadastrado": {
        "titulo": "Cliente nao cadastrado",
        "explicacao": "O CNPJ foi encontrado no arquivo, mas nao existe no cadastro de clientes.",
        "solucao": "Cadastre o cliente na pagina de Clientes com este CNPJ",
    },
    "Credenciais de email nao configuradas": {
        "titulo": "Email nao configurado",
        "explicacao": "As credenciais de email nao foram preenchidas no arquivo .env",
        "solucao": "Edite o arquivo .env e preencha EMAIL_REMETENTE e EMAIL_SENHA",
    },
    "Credenciais do WhatsApp nao configuradas": {
        "titulo": "WhatsApp nao configurado",
        "explicacao": "As credenciais do WhatsApp nao foram preenchidas no arquivo .env",
        "solucao": "Edite o arquivo .env e preencha WHATSAPP_API_KEY e WHATSAPP_INSTANCE",
    },
    "Envio por email nao selecionado": {
        "titulo": "Email nao selecionado",
        "explicacao": "O envio por email nao foi marcado.",
        "solucao": "Marque a opcao de envio por email antes de enviar",
    },
    "Envio por WhatsApp nao selecionado": {
        "titulo": "WhatsApp nao selecionado",
        "explicacao": "O envio por WhatsApp nao foi marcado.",
        "solucao": "Marque a opcao de envio por WhatsApp antes de enviar",
    },
}


def _traduzir_erro(mensagem_erro: str) -> dict:
    """Traduz uma mensagem de erro tecnica para uma explicacao amigavel."""
    for chave, info in ERROS_AMIGAVEIS.items():
        if chave.lower() in mensagem_erro.lower():
            return info
    return {
        "titulo": "Erro no envio",
        "explicacao": mensagem_erro,
        "solucao": "Verifique o log ou entre em contato com o suporte",
    }


def _carregar_log_json() -> list[dict]:
    """Carrega o log JSON existente."""
    if os.path.exists(LOG_FILE_JSON):
        try:
            with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return []
    return []


def _salvar_log_json(registros: list[dict]):
    """Salva o log JSON."""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)


def _salvar_csv(linha: list):
    """Salva uma linha no CSV (backup)."""
    os.makedirs(LOG_DIR, exist_ok=True)
    criar_cabecalho = not os.path.exists(LOG_FILE_CSV)
    with open(LOG_FILE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        if criar_cabecalho:
            writer.writerow(CSV_COLUNAS)
        writer.writerow(linha)


def registrar_envio(
    arquivo: str,
    cnpj: str,
    nome_cliente: str,
    email_destino: str,
    resultado_email: dict,
    whatsapp_destino: str,
    resultado_whatsapp: dict,
):
    """Registra um envio no log."""
    agora = datetime.now()

    # Traduzir erros
    erro_email = None
    if not resultado_email.get("sucesso"):
        erro_email = _traduzir_erro(resultado_email.get("mensagem", ""))

    erro_whatsapp = None
    if not resultado_whatsapp.get("sucesso"):
        erro_whatsapp = _traduzir_erro(resultado_whatsapp.get("mensagem", ""))

    # Determinar status geral
    if resultado_email.get("sucesso") and resultado_whatsapp.get("sucesso"):
        status_geral = "sucesso"
    elif resultado_email.get("sucesso") or resultado_whatsapp.get("sucesso"):
        status_geral = "parcial"
    else:
        status_geral = "falha"

    registro = {
        "id": agora.strftime("%Y%m%d%H%M%S") + f"_{cnpj[-4:]}",
        "data_hora": agora.strftime("%d/%m/%Y %H:%M:%S"),
        "data_iso": agora.isoformat(),
        "arquivo": arquivo,
        "cnpj": cnpj,
        "nome_cliente": nome_cliente,
        "status_geral": status_geral,
        "email": {
            "destino": email_destino,
            "enviado": resultado_email.get("sucesso", False),
            "mensagem": resultado_email.get("mensagem", ""),
            "erro": erro_email,
        },
        "whatsapp": {
            "destino": whatsapp_destino,
            "enviado": resultado_whatsapp.get("sucesso", False),
            "mensagem": resultado_whatsapp.get("mensagem", ""),
            "erro": erro_whatsapp,
        },
    }

    # Salvar JSON
    registros = _carregar_log_json()
    registros.append(registro)
    _salvar_log_json(registros)

    # Salvar CSV (backup)
    _salvar_csv([
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        arquivo, cnpj, nome_cliente, email_destino,
        "ENVIADO" if resultado_email.get("sucesso") else "FALHA",
        resultado_email.get("mensagem", ""),
        whatsapp_destino,
        "ENVIADO" if resultado_whatsapp.get("sucesso") else "FALHA",
        resultado_whatsapp.get("mensagem", ""),
    ])

    print(f"  [LOG] Registro salvo")
    return registro


def registrar_erro(arquivo: str, motivo: str):
    """Registra um erro."""
    agora = datetime.now()
    erro_info = _traduzir_erro(motivo)

    registro = {
        "id": agora.strftime("%Y%m%d%H%M%S") + "_erro",
        "data_hora": agora.strftime("%d/%m/%Y %H:%M:%S"),
        "data_iso": agora.isoformat(),
        "arquivo": arquivo,
        "cnpj": "",
        "nome_cliente": "",
        "status_geral": "erro",
        "email": {
            "destino": "",
            "enviado": False,
            "mensagem": motivo,
            "erro": erro_info,
        },
        "whatsapp": {
            "destino": "",
            "enviado": False,
            "mensagem": motivo,
            "erro": erro_info,
        },
    }

    registros = _carregar_log_json()
    registros.append(registro)
    _salvar_log_json(registros)

    _salvar_csv([
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        arquivo, "", "", "", "ERRO", motivo, "", "ERRO", motivo,
    ])

    print(f"  [LOG] Erro registrado: {motivo}")
    return registro


def obter_registros(limite: int = 100) -> list[dict]:
    """Retorna os registros do log, mais recentes primeiro."""
    registros = _carregar_log_json()
    return list(reversed(registros[-limite:]))


def obter_registro_por_id(registro_id: str) -> dict | None:
    """Busca um registro pelo ID."""
    registros = _carregar_log_json()
    for r in registros:
        if r.get("id") == registro_id:
            return r
    return None


def obter_estatisticas() -> dict:
    """Calcula estatisticas dos envios."""
    registros = _carregar_log_json()
    total = len(registros)
    sucesso = sum(1 for r in registros if r.get("status_geral") == "sucesso")
    parcial = sum(1 for r in registros if r.get("status_geral") == "parcial")
    falha = sum(1 for r in registros if r.get("status_geral") in ("falha", "erro"))
    email_ok = sum(1 for r in registros if r.get("email", {}).get("enviado"))
    whats_ok = sum(1 for r in registros if r.get("whatsapp", {}).get("enviado"))

    return {
        "total_envios": total,
        "sucesso": sucesso,
        "parcial": parcial,
        "falha": falha,
        "email_enviados": email_ok,
        "whatsapp_enviados": whats_ok,
    }

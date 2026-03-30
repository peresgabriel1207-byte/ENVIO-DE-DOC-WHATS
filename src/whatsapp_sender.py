"""
Modulo de envio de documentos por WhatsApp.

Suporta:
  - Evolution API (gratuita, self-hosted)
  - Facilmente adaptavel para Z-API, Twilio, etc.
"""

import os
import base64
import mimetypes
import requests


def enviar_whatsapp(
    numero_whatsapp: str,
    nome_cliente: str,
    caminho_arquivo: str,
    mensagem: str | None = None,
) -> dict:
    """
    Envia documento pelo WhatsApp via Evolution API.

    Retorna dict com:
      - sucesso: bool
      - mensagem: str (descricao do resultado)
    """
    api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
    api_key = os.getenv("WHATSAPP_API_KEY", "")
    instancia = os.getenv("WHATSAPP_INSTANCE", "")

    if not api_key or not instancia:
        return {"sucesso": False, "mensagem": "Credenciais do WhatsApp nao configuradas no .env"}

    if not mensagem:
        mensagem = os.getenv(
            "MENSAGEM_WHATSAPP",
            "Ola! Segue em anexo o documento da contabilidade."
        )
        mensagem = mensagem.replace("{nome_cliente}", nome_cliente)

    # Formatar numero (remover caracteres especiais, garantir formato correto)
    numero = numero_whatsapp.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

    try:
        # 1. Enviar mensagem de texto primeiro
        url_texto = f"{api_url}/message/sendText/{instancia}"
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
        payload_texto = {
            "number": numero,
            "text": mensagem
        }

        resp_texto = requests.post(url_texto, json=payload_texto, headers=headers, timeout=30)

        if resp_texto.status_code not in (200, 201):
            return {
                "sucesso": False,
                "mensagem": f"Erro ao enviar mensagem de texto: {resp_texto.status_code} - {resp_texto.text}"
            }

        # 2. Enviar documento
        nome_arquivo = os.path.basename(caminho_arquivo)
        mime_type = mimetypes.guess_type(caminho_arquivo)[0] or "application/octet-stream"

        with open(caminho_arquivo, "rb") as f:
            arquivo_base64 = base64.b64encode(f.read()).decode("utf-8")

        url_media = f"{api_url}/message/sendMedia/{instancia}"
        payload_media = {
            "number": numero,
            "mediatype": "document",
            "mimetype": mime_type,
            "caption": f"Documento: {nome_arquivo}",
            "media": arquivo_base64,
            "fileName": nome_arquivo
        }

        resp_media = requests.post(url_media, json=payload_media, headers=headers, timeout=60)

        if resp_media.status_code in (200, 201):
            return {"sucesso": True, "mensagem": f"WhatsApp enviado para {numero}"}
        else:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao enviar documento: {resp_media.status_code} - {resp_media.text}"
            }

    except requests.exceptions.ConnectionError:
        return {"sucesso": False, "mensagem": "Nao foi possivel conectar a API do WhatsApp. Verifique se esta rodando."}
    except requests.exceptions.Timeout:
        return {"sucesso": False, "mensagem": "Timeout ao conectar a API do WhatsApp."}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao enviar WhatsApp: {e}"}

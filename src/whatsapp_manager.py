"""
Gerenciador da conexao WhatsApp local (Evolution API).

Cria instancia, gera QR Code, verifica status da conexao.
Tudo roda local no servidor - sem nuvem.
"""

import os
import requests


def _get_config():
    return {
        "url": os.getenv("WHATSAPP_API_URL", "http://localhost:8080"),
        "key": os.getenv("WHATSAPP_API_KEY", "SuaChaveSegura123"),
        "instance": os.getenv("WHATSAPP_INSTANCE", "robo-contabilidade"),
    }


def _headers():
    cfg = _get_config()
    return {"apikey": cfg["key"], "Content-Type": "application/json"}


def verificar_api_online() -> bool:
    """Verifica se a Evolution API esta rodando."""
    cfg = _get_config()
    try:
        r = requests.get(f"{cfg['url']}/", headers=_headers(), timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def criar_instancia() -> dict:
    """Cria a instancia do WhatsApp na Evolution API."""
    cfg = _get_config()
    try:
        payload = {
            "instanceName": cfg["instance"],
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        }
        r = requests.post(
            f"{cfg['url']}/instance/create",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        if r.status_code in (200, 201):
            data = r.json()
            return {"sucesso": True, "dados": data}
        else:
            return {"sucesso": False, "mensagem": f"Erro {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError:
        return {"sucesso": False, "mensagem": "Evolution API nao esta rodando. Execute: docker compose up -d"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}


def obter_qrcode() -> dict:
    """Obtem o QR Code para conectar o WhatsApp."""
    cfg = _get_config()
    try:
        r = requests.get(
            f"{cfg['url']}/instance/connect/{cfg['instance']}",
            headers=_headers(),
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            # O QR Code pode vir como base64 ou como code
            qr_base64 = data.get("base64", "")
            qr_code = data.get("code", "")
            return {
                "sucesso": True,
                "qr_base64": qr_base64,
                "qr_code": qr_code,
            }
        else:
            return {"sucesso": False, "mensagem": f"Erro {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError:
        return {"sucesso": False, "mensagem": "Evolution API nao esta rodando"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}


def verificar_conexao() -> dict:
    """Verifica o status da conexao do WhatsApp."""
    cfg = _get_config()
    try:
        r = requests.get(
            f"{cfg['url']}/instance/connectionState/{cfg['instance']}",
            headers=_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            state = data.get("instance", {}).get("state", "unknown")
            conectado = state == "open"
            return {
                "sucesso": True,
                "conectado": conectado,
                "estado": state,
                "detalhes": data,
            }
        elif r.status_code == 404:
            return {"sucesso": True, "conectado": False, "estado": "nao_criada", "detalhes": {}}
        else:
            return {"sucesso": False, "conectado": False, "estado": "erro", "detalhes": {}}
    except requests.exceptions.ConnectionError:
        return {"sucesso": False, "conectado": False, "estado": "api_offline", "detalhes": {}}
    except Exception as e:
        return {"sucesso": False, "conectado": False, "estado": "erro", "detalhes": {"erro": str(e)}}


def desconectar() -> dict:
    """Desconecta o WhatsApp."""
    cfg = _get_config()
    try:
        r = requests.delete(
            f"{cfg['url']}/instance/logout/{cfg['instance']}",
            headers=_headers(),
            timeout=10,
        )
        return {"sucesso": r.status_code in (200, 201)}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

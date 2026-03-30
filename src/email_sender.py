"""
Modulo de envio de documentos por Email via SMTP.
Suporta Gmail, Outlook, e qualquer servidor SMTP.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


def enviar_email(
    destinatario_email: str,
    nome_cliente: str,
    caminho_arquivo: str,
    assunto: str | None = None,
    mensagem: str | None = None,
) -> dict:
    """
    Envia um email com o documento em anexo.

    Retorna dict com:
      - sucesso: bool
      - mensagem: str (descricao do resultado)
    """
    smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    remetente = os.getenv("EMAIL_REMETENTE", "")
    senha = os.getenv("EMAIL_SENHA", "")
    nome_remetente = os.getenv("EMAIL_NOME_REMETENTE", "Contabilidade")

    if not remetente or not senha:
        return {"sucesso": False, "mensagem": "Credenciais de email nao configuradas no .env"}

    # Montar assunto e mensagem
    if not assunto:
        assunto_template = os.getenv("ASSUNTO_EMAIL", "Documento Contabil - {nome_cliente}")
        assunto = assunto_template.replace("{nome_cliente}", nome_cliente)

    if not mensagem:
        mensagem_template = os.getenv(
            "MENSAGEM_EMAIL",
            "Prezado(a) {nome_cliente},\n\nSegue em anexo o documento contabil.\n\nAtenciosamente,\nContabilidade"
        )
        mensagem = mensagem_template.replace("{nome_cliente}", nome_cliente)
        mensagem = mensagem.replace("\\n", "\n")

    try:
        # Criar email
        msg = MIMEMultipart()
        msg["From"] = f"{nome_remetente} <{remetente}>"
        msg["To"] = destinatario_email
        msg["Subject"] = assunto

        # Corpo do email
        msg.attach(MIMEText(mensagem, "plain", "utf-8"))

        # Anexo
        nome_arquivo = os.path.basename(caminho_arquivo)
        with open(caminho_arquivo, "rb") as f:
            anexo = MIMEBase("application", "octet-stream")
            anexo.set_payload(f.read())
            encoders.encode_base64(anexo)
            anexo.add_header("Content-Disposition", f"attachment; filename={nome_arquivo}")
            msg.attach(anexo)

        # Enviar
        with smtplib.SMTP(smtp_host, smtp_port) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)

        return {"sucesso": True, "mensagem": f"Email enviado para {destinatario_email}"}

    except smtplib.SMTPAuthenticationError:
        return {"sucesso": False, "mensagem": "Erro de autenticacao SMTP. Verifique email e senha no .env"}
    except smtplib.SMTPException as e:
        return {"sucesso": False, "mensagem": f"Erro SMTP: {e}"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao enviar email: {e}"}

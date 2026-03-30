"""
Modulo de monitoramento de pasta.
Detecta novos arquivos e dispara o processo de envio.
"""

import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.cnpj_extractor import identificar_destinatario
from src.email_sender import enviar_email
from src.whatsapp_sender import enviar_whatsapp
from src.audit_log import registrar_envio, registrar_erro


class DocumentHandler(FileSystemEventHandler):
    """Handler que processa novos arquivos na pasta monitorada."""

    def __init__(self, pasta_enviados: str, caminho_clientes: str):
        self.pasta_enviados = pasta_enviados
        self.caminho_clientes = caminho_clientes
        self._processando = set()

    def on_created(self, event):
        if event.is_directory:
            return

        caminho = event.src_path
        nome_arquivo = os.path.basename(caminho)

        # Ignorar arquivos temporarios e ocultos
        if nome_arquivo.startswith(".") or nome_arquivo.startswith("~"):
            return

        # Evitar processar o mesmo arquivo duas vezes
        if caminho in self._processando:
            return
        self._processando.add(caminho)

        # Aguardar arquivo terminar de ser copiado
        self._aguardar_copia(caminho)

        try:
            self._processar_arquivo(caminho, nome_arquivo)
        finally:
            self._processando.discard(caminho)

    def _aguardar_copia(self, caminho: str, tentativas: int = 10):
        """Aguarda o arquivo terminar de ser copiado verificando se o tamanho estabilizou."""
        tamanho_anterior = -1
        for _ in range(tentativas):
            try:
                tamanho_atual = os.path.getsize(caminho)
                if tamanho_atual == tamanho_anterior and tamanho_atual > 0:
                    return
                tamanho_anterior = tamanho_atual
            except OSError:
                pass
            time.sleep(1)

    def _processar_arquivo(self, caminho: str, nome_arquivo: str):
        """Processa um arquivo: identifica cliente e envia por email e WhatsApp."""
        print(f"\n{'='*60}")
        print(f"[NOVO ARQUIVO] {nome_arquivo}")
        print(f"{'='*60}")

        # 1. Identificar destinatario pelo CNPJ no nome do arquivo
        cliente = identificar_destinatario(nome_arquivo, self.caminho_clientes)

        if not cliente:
            msg = f"CNPJ nao encontrado ou cliente nao cadastrado para: {nome_arquivo}"
            print(f"  [ERRO] {msg}")
            registrar_erro(nome_arquivo, msg)
            return

        print(f"  [OK] Cliente: {cliente['nome']} (CNPJ: {cliente['cnpj_extraido']})")
        print(f"  [OK] Email: {cliente['email']}")
        print(f"  [OK] WhatsApp: {cliente['whatsapp']}")

        # 2. Enviar por Email
        print(f"\n  [ENVIANDO] Email para {cliente['email']}...")
        resultado_email = enviar_email(
            destinatario_email=cliente["email"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        status_email = "OK" if resultado_email["sucesso"] else "FALHA"
        print(f"  [{status_email}] {resultado_email['mensagem']}")

        # 3. Enviar por WhatsApp
        print(f"\n  [ENVIANDO] WhatsApp para {cliente['whatsapp']}...")
        resultado_whatsapp = enviar_whatsapp(
            numero_whatsapp=cliente["whatsapp"],
            nome_cliente=cliente["nome"],
            caminho_arquivo=caminho,
        )
        status_whats = "OK" if resultado_whatsapp["sucesso"] else "FALHA"
        print(f"  [{status_whats}] {resultado_whatsapp['mensagem']}")

        # 4. Registrar no log de auditoria
        registrar_envio(
            arquivo=nome_arquivo,
            cnpj=cliente["cnpj_extraido"],
            nome_cliente=cliente["nome"],
            email_destino=cliente["email"],
            resultado_email=resultado_email,
            whatsapp_destino=cliente["whatsapp"],
            resultado_whatsapp=resultado_whatsapp,
        )

        # 5. Mover arquivo para pasta de enviados (se pelo menos um envio deu certo)
        if resultado_email["sucesso"] or resultado_whatsapp["sucesso"]:
            destino = os.path.join(self.pasta_enviados, nome_arquivo)
            # Se ja existe arquivo com mesmo nome, adicionar timestamp
            if os.path.exists(destino):
                base, ext = os.path.splitext(nome_arquivo)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                destino = os.path.join(self.pasta_enviados, f"{base}_{timestamp}{ext}")

            shutil.move(caminho, destino)
            print(f"\n  [MOVIDO] Arquivo movido para: {destino}")
        else:
            print(f"\n  [ATENCAO] Arquivo mantido na pasta de entrada (ambos envios falharam)")

        print(f"{'='*60}\n")


def iniciar_monitoramento(pasta_entrada: str, pasta_enviados: str, caminho_clientes: str):
    """Inicia o monitoramento da pasta de entrada."""
    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_enviados, exist_ok=True)

    handler = DocumentHandler(pasta_enviados, caminho_clientes)
    observer = Observer()
    observer.schedule(handler, pasta_entrada, recursive=False)
    observer.start()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║     ROBO DE ENVIO DE DOCUMENTOS - CONTABILIDADE        ║
╠══════════════════════════════════════════════════════════╣
║  Status: ATIVO                                          ║
║  Monitorando: {pasta_entrada:<41s} ║
║  Enviados:    {pasta_enviados:<41s} ║
║  Log:         logs/log_envios.csv                       ║
╠══════════════════════════════════════════════════════════╣
║  Coloque arquivos na pasta monitorada.                  ║
║  O CNPJ no nome do arquivo identifica o cliente.        ║
║  Pressione Ctrl+C para parar.                           ║
╚══════════════════════════════════════════════════════════╝
    """)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[PARADO] Monitoramento encerrado.")

    observer.join()

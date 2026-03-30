"""
Modulo de monitoramento de pasta.
Detecta novos arquivos e dispara o processo de envio.

Usa PollingObserver no Windows para funcionar com pastas de rede (UNC paths).
O watchdog padrao usa eventos do sistema de arquivos que NAO funcionam
com pastas compartilhadas (\\SERVIDOR\\pasta). O polling verifica a cada
poucos segundos se tem arquivo novo - mais confiavel em rede.
"""

import os
import sys
import time
import shutil
from datetime import datetime

from watchdog.events import FileSystemEventHandler

# Usar PollingObserver no Windows para compatibilidade com pastas de rede
if sys.platform == "win32":
    from watchdog.observers.polling import PollingObserver as Observer
else:
    from watchdog.observers import Observer

from src.cnpj_extractor import identificar_destinatario
from src.email_sender import enviar_email
from src.whatsapp_sender import enviar_whatsapp
from src.audit_log import registrar_envio, registrar_erro


# Intervalo de verificacao da pasta (em segundos)
POLLING_INTERVAL = 5


class DocumentHandler(FileSystemEventHandler):
    """Handler que processa novos arquivos na pasta monitorada."""

    def __init__(self, pasta_enviados: str, caminho_clientes: str):
        self.pasta_enviados = pasta_enviados
        self.caminho_clientes = caminho_clientes
        self._processando = set()
        self._contador_envios = 0
        self._contador_erros = 0

    def on_created(self, event):
        if event.is_directory:
            return

        caminho = event.src_path
        nome_arquivo = os.path.basename(caminho)

        # Ignorar arquivos temporarios, ocultos e thumbs.db do Windows
        if nome_arquivo.startswith(".") or nome_arquivo.startswith("~"):
            return
        if nome_arquivo.lower() in ("thumbs.db", "desktop.ini", ".ds_store"):
            return

        # Evitar processar o mesmo arquivo duas vezes
        if caminho in self._processando:
            return
        self._processando.add(caminho)

        # Aguardar arquivo terminar de ser copiado pela rede
        self._aguardar_copia(caminho)

        try:
            self._processar_arquivo(caminho, nome_arquivo)
        finally:
            self._processando.discard(caminho)

    def _aguardar_copia(self, caminho: str, tentativas: int = 30):
        """
        Aguarda o arquivo terminar de ser copiado verificando se o tamanho estabilizou.
        Em rede, a copia pode demorar mais, por isso tentativas=30 (30 segundos).
        """
        tamanho_anterior = -1
        for _ in range(tentativas):
            try:
                tamanho_atual = os.path.getsize(caminho)
                if tamanho_atual == tamanho_anterior and tamanho_atual > 0:
                    # Tenta abrir o arquivo para confirmar que nao esta travado
                    try:
                        with open(caminho, "rb") as f:
                            f.read(1)
                        return
                    except (PermissionError, OSError):
                        pass  # Arquivo ainda sendo escrito
                tamanho_anterior = tamanho_atual
            except OSError:
                pass
            time.sleep(1)

    def _processar_arquivo(self, caminho: str, nome_arquivo: str):
        """Processa um arquivo: identifica cliente e envia por email e WhatsApp."""
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        print(f"\n{'='*60}")
        print(f"  NOVO ARQUIVO DETECTADO - {agora}")
        print(f"  Arquivo: {nome_arquivo}")
        print(f"{'='*60}")

        # 1. Identificar destinatario pelo CNPJ no nome do arquivo
        cliente = identificar_destinatario(nome_arquivo, self.caminho_clientes)

        if not cliente:
            msg = f"CNPJ nao encontrado ou cliente nao cadastrado para: {nome_arquivo}"
            print(f"  [ERRO] {msg}")
            registrar_erro(nome_arquivo, msg)
            self._contador_erros += 1
            self._mostrar_status()
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
            print(f"\n  [MOVIDO] Arquivo movido para pasta de enviados")
            self._contador_envios += 1
        else:
            print(f"\n  [ATENCAO] Arquivo mantido na pasta de entrada (ambos envios falharam)")
            self._contador_erros += 1

        self._mostrar_status()

    def _mostrar_status(self):
        """Mostra contadores de envio."""
        print(f"\n  --- Enviados: {self._contador_envios} | Erros: {self._contador_erros} | Aguardando novos arquivos... ---\n")


def iniciar_monitoramento(pasta_entrada: str, pasta_enviados: str, caminho_clientes: str):
    """Inicia o monitoramento da pasta de entrada."""
    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_enviados, exist_ok=True)

    handler = DocumentHandler(pasta_enviados, caminho_clientes)

    # No Windows, o PollingObserver aceita o intervalo de polling
    if sys.platform == "win32":
        observer = Observer(timeout=POLLING_INTERVAL)
    else:
        observer = Observer()

    observer.schedule(handler, pasta_entrada, recursive=False)
    observer.start()

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print(f"""
  ===========================================================
  |     ROBO DE ENVIO DE DOCUMENTOS - CONTABILIDADE         |
  ===========================================================
  |  Status:      ATIVO                                     |
  |  Iniciado em: {agora:<41s} |
  |  Monitorando: {pasta_entrada:<41s} |
  |  Enviados:    {pasta_enviados:<41s} |
  |  Log:         logs/log_envios.csv                       |
  |  Verificando: a cada {POLLING_INTERVAL} segundos{' ' * 29}|
  ===========================================================
  |  Coloque arquivos na pasta monitorada.                  |
  |  O CNPJ no nome do arquivo identifica o cliente.        |
  |  Pressione Ctrl+C para parar.                           |
  ===========================================================
    """)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[PARADO] Monitoramento encerrado.")

    observer.join()

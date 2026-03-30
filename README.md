# Robo de Envio Automatico de Documentos - Contabilidade

Automacao para envio de documentos contabeis por **WhatsApp** e **Email**.
Basta colocar o arquivo na pasta monitorada e o robo faz o resto.

## Como Funciona

1. Voce coloca o arquivo na pasta `documentos_envio/`
2. O robo detecta o novo arquivo automaticamente
3. Extrai o **CNPJ** do nome do arquivo
4. Busca o cliente no cadastro (`clientes.json`)
5. Envia por **Email** e **WhatsApp**
6. Move o arquivo para `documentos_enviados/`
7. Registra tudo no log de auditoria (`logs/log_envios.csv`)

## Estrutura do Projeto

```
ENVIO-DE-DOC-WHATS/
├── main.py                  # Script principal
├── clientes.json            # Cadastro de clientes (CNPJ, email, WhatsApp)
├── .env                     # Configuracoes (copiar de .env.example)
├── requirements.txt         # Dependencias Python
├── documentos_envio/        # Pasta monitorada (coloque arquivos aqui)
├── documentos_enviados/     # Arquivos ja enviados
├── logs/
│   └── log_envios.csv       # Log de auditoria
└── src/
    ├── cnpj_extractor.py    # Extrai CNPJ do nome do arquivo
    ├── email_sender.py      # Envio por email (SMTP)
    ├── whatsapp_sender.py   # Envio por WhatsApp (Evolution API)
    ├── watcher.py           # Monitor da pasta
    └── audit_log.py         # Log de auditoria CSV
```

## Instalacao

### 1. Instalar Python 3.10+

Baixe em https://www.python.org/downloads/

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar o .env

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

- **Email**: Configure SMTP (Gmail, Outlook, etc.)
- **WhatsApp**: Configure a Evolution API (veja abaixo)

### 4. Cadastrar clientes

Edite o `clientes.json` e adicione seus clientes:

```json
{
  "clientes": [
    {
      "cnpj": "12345678000199",
      "nome": "Empresa Exemplo LTDA",
      "whatsapp": "5511999999999",
      "email": "contato@empresa.com.br",
      "ativo": true
    }
  ]
}
```

### 5. Configurar WhatsApp (Evolution API)

A Evolution API e gratuita e voce hospeda no seu proprio servidor:

1. Instale via Docker: https://doc.evolution-api.com/
2. Crie uma instancia e conecte seu WhatsApp
3. Copie a API Key e o nome da instancia para o `.env`

## Uso

### Monitoramento continuo (modo principal)

```bash
python main.py
```

O robo fica rodando e envia automaticamente quando detecta um novo arquivo.

### Enviar arquivos existentes

```bash
python main.py --enviar
```

Envia todos os arquivos que ja estao na pasta `documentos_envio/`.

### Testar configuracao

```bash
python main.py --testar
```

Verifica se tudo esta configurado corretamente sem enviar nada.

## Nome dos Arquivos

O CNPJ precisa estar no nome do arquivo. Formatos aceitos:

| Formato | Exemplo |
|---------|---------|
| CNPJ formatado | `12.345.678/0001-99_balanco.pdf` |
| CNPJ so numeros | `12345678000199_balanco.pdf` |
| CNPJ no meio | `balanco_12345678000199_2024.pdf` |

## Log de Auditoria

Todos os envios sao registrados em `logs/log_envios.csv` com:

- Data e hora do envio
- Nome do arquivo
- CNPJ do cliente
- Status do email (ENVIADO/FALHA)
- Status do WhatsApp (ENVIADO/FALHA)
- Detalhes de erro (se houver)

## Configuracao de Email (Gmail)

Para usar com Gmail, voce precisa de uma **Senha de App**:

1. Acesse https://myaccount.google.com/security
2. Ative a verificacao em duas etapas
3. Gere uma "Senha de app" para "Outro (nome personalizado)"
4. Use essa senha no `.env` (campo `EMAIL_SENHA`)

## Dicas

- Mantenha o `clientes.json` atualizado com os CNPJs corretos
- Verifique o log (`logs/log_envios.csv`) regularmente
- Se um envio falhar, o arquivo permanece na pasta de entrada para reprocessamento
- Use `--testar` antes de iniciar para garantir que tudo esta configurado

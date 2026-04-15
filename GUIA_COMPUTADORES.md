# Guia Rapido - Computadores da Contabilidade

## Como enviar documentos pelo robo

### Passo 1: Acessar a pasta compartilhada

No seu computador, abra o Explorador de Arquivos e digite na barra de endereco:

```
\\NOME_DO_SERVIDOR\DocumentosContabilidade
```

> Substitua `NOME_DO_SERVIDOR` pelo nome ou IP do servidor (ex: `\\192.168.1.100\DocumentosContabilidade`)

**Dica:** Clique com botao direito e selecione "Mapear unidade de rede" para criar um atalho permanente (ex: unidade Z:)

### Passo 2: Colocar o arquivo na pasta

Copie ou mova o arquivo para a pasta compartilhada.

**IMPORTANTE:** O nome do arquivo DEVE conter o CNPJ do cliente.

Exemplos de nomes validos:

| Nome do Arquivo | CNPJ Detectado |
|---|---|
| `12345678000199_balanco.pdf` | 12345678000199 |
| `guia_DAS_12345678000199.pdf` | 12345678000199 |
| `12.345.678/0001-99_relatorio.pdf` | 12345678000199 |

### Passo 3: Pronto!

O robo no servidor detecta o arquivo automaticamente e:
1. Identifica o cliente pelo CNPJ
2. Envia por Email e WhatsApp
3. Move o arquivo para a pasta "enviados"

### Como saber se foi enviado?

Pergunte ao administrador do servidor. Ele pode verificar no log:
`logs/log_envios.csv`

### O arquivo nao foi enviado?

Possveis motivos:
- O CNPJ nao esta no nome do arquivo
- O cliente nao esta cadastrado no sistema
- O arquivo ficou na pasta (nao foi movido) = nao foi enviado

Avise o administrador para verificar o log de erros.

---

## Mapear unidade de rede (acesso mais facil)

### Windows:
1. Abra o Explorador de Arquivos
2. Clique em "Este Computador"
3. Clique em "Mapear unidade de rede" (no menu superior)
4. Escolha uma letra (ex: Z:)
5. Em "Pasta", digite: `\\NOME_DO_SERVIDOR\DocumentosContabilidade`
6. Marque "Reconectar na entrada"
7. Clique em "Concluir"

Agora a pasta aparece como unidade Z: no seu computador.
Basta arrastar os arquivos para la.

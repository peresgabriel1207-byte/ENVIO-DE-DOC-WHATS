#!/usr/bin/env python3
"""
Cadastro interativo de clientes.
Adiciona novos clientes ao clientes.json sem precisar editar o arquivo manualmente.

Uso:
    python cadastrar_cliente.py
"""

import json
import os
import re


ARQUIVO_CLIENTES = "clientes.json"


def limpar_cnpj(cnpj: str) -> str:
    return re.sub(r"[^0-9]", "", cnpj)


def validar_cnpj(cnpj: str) -> bool:
    cnpj = limpar_cnpj(cnpj)
    return len(cnpj) == 14 and cnpj.isdigit()


def formatar_cnpj(cnpj: str) -> str:
    c = limpar_cnpj(cnpj)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def carregar_clientes() -> dict:
    if os.path.exists(ARQUIVO_CLIENTES):
        with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"clientes": []}


def salvar_clientes(dados: dict):
    with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def listar_clientes():
    dados = carregar_clientes()
    clientes = dados.get("clientes", [])

    if not clientes:
        print("\n  Nenhum cliente cadastrado.\n")
        return

    print(f"\n  {'='*65}")
    print(f"  {'#':<4} {'NOME':<30} {'CNPJ':<20} {'STATUS'}")
    print(f"  {'='*65}")

    for i, c in enumerate(clientes, 1):
        status = "ATIVO" if c.get("ativo", True) else "INATIVO"
        cnpj_fmt = formatar_cnpj(c["cnpj"])
        print(f"  {i:<4} {c['nome']:<30} {cnpj_fmt:<20} {status}")

    print(f"  {'='*65}")
    print(f"  Total: {len(clientes)} cliente(s)\n")


def adicionar_cliente():
    print("\n  --- NOVO CLIENTE ---\n")

    # CNPJ
    while True:
        cnpj = input("  CNPJ (somente numeros): ").strip()
        cnpj = limpar_cnpj(cnpj)
        if validar_cnpj(cnpj):
            # Verificar se ja existe
            dados = carregar_clientes()
            existe = any(limpar_cnpj(c["cnpj"]) == cnpj for c in dados["clientes"])
            if existe:
                print(f"  [ERRO] CNPJ {formatar_cnpj(cnpj)} ja cadastrado!\n")
                continue
            break
        print("  [ERRO] CNPJ invalido. Digite 14 numeros.\n")

    print(f"  CNPJ: {formatar_cnpj(cnpj)}")

    # Nome
    nome = input("  Nome da empresa: ").strip()
    if not nome:
        print("  [ERRO] Nome nao pode ser vazio.")
        return

    # WhatsApp
    while True:
        whatsapp = input("  WhatsApp (com DDD, ex: 5511999999999): ").strip()
        whatsapp = re.sub(r"[^0-9]", "", whatsapp)
        if len(whatsapp) >= 12:
            break
        print("  [ERRO] Numero invalido. Use formato: 5511999999999\n")

    # Email
    while True:
        email = input("  Email: ").strip()
        if "@" in email and "." in email:
            break
        print("  [ERRO] Email invalido.\n")

    # Confirmar
    print(f"\n  --- CONFIRMAR CADASTRO ---")
    print(f"  Nome:     {nome}")
    print(f"  CNPJ:     {formatar_cnpj(cnpj)}")
    print(f"  WhatsApp: {whatsapp}")
    print(f"  Email:    {email}")

    confirma = input("\n  Confirmar? (S/N): ").strip().upper()
    if confirma != "S":
        print("  Cadastro cancelado.\n")
        return

    # Salvar
    dados = carregar_clientes()
    dados["clientes"].append({
        "cnpj": cnpj,
        "nome": nome,
        "whatsapp": whatsapp,
        "email": email,
        "ativo": True
    })
    salvar_clientes(dados)
    print(f"\n  [OK] Cliente '{nome}' cadastrado com sucesso!\n")


def remover_cliente():
    listar_clientes()
    dados = carregar_clientes()
    clientes = dados.get("clientes", [])

    if not clientes:
        return

    try:
        num = int(input("  Numero do cliente para remover (0 para cancelar): ").strip())
        if num == 0:
            return
        if 1 <= num <= len(clientes):
            cliente = clientes[num - 1]
            confirma = input(f"  Remover '{cliente['nome']}'? (S/N): ").strip().upper()
            if confirma == "S":
                clientes.pop(num - 1)
                salvar_clientes(dados)
                print(f"  [OK] Cliente removido.\n")
        else:
            print("  Numero invalido.\n")
    except ValueError:
        print("  Numero invalido.\n")


def main():
    print("""
  ===========================================================
  |     CADASTRO DE CLIENTES - ENVIO DE DOCUMENTOS          |
  ===========================================================
    """)

    while True:
        print("  1. Listar clientes")
        print("  2. Adicionar cliente")
        print("  3. Remover cliente")
        print("  4. Sair")
        print()

        opcao = input("  Escolha uma opcao: ").strip()

        if opcao == "1":
            listar_clientes()
        elif opcao == "2":
            adicionar_cliente()
        elif opcao == "3":
            remover_cliente()
        elif opcao == "4":
            print("\n  Ate logo!\n")
            break
        else:
            print("  Opcao invalida.\n")


if __name__ == "__main__":
    main()

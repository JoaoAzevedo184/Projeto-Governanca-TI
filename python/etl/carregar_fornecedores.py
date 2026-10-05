"""Carrega `dataset/demo/fornecedores_demo.csv` na API com `data_source = compras_gov` (D.2).

O importador resolve o fornecedor pela razão social e não cria nenhum, então os fornecedores das
linhas do `inventario_demo.csv` precisam existir antes. Idempotente: quem já existe (mesmo CNPJ)
é pulado, então rodar de novo não duplica nem falha.

Credenciais só por variável de ambiente (nunca no código), de um usuário ADMIN:
    ITAM_API_LOGIN, ITAM_API_SENHA   e, se a API não estiver em localhost:8000, ITAM_API_URL.

Uso (a partir de `python/`): `python -m etl.carregar_fornecedores`.
"""

import csv
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from etl.paths import DATASET_DIR

ARQUIVO = DATASET_DIR / "demo" / "fornecedores_demo.csv"
DATA_SOURCE = "compras_gov"


class ErroCarga(Exception):
    """A API recusou o login ou um cadastro; a mensagem não leva a senha nem o token."""


@dataclass
class Resultado:
    criados: list[str] = field(default_factory=list)
    existentes: list[str] = field(default_factory=list)


def ler_fornecedores(arquivo: Path = ARQUIVO) -> list[dict[str, str]]:
    with arquivo.open(encoding="utf-8", newline="") as aberto:
        return list(csv.DictReader(aberto))


def carregar(
    cliente: httpx.Client, login: str, senha: str, fornecedores: list[dict[str, str]]
) -> Resultado:
    resposta = cliente.post("/api/v1/auth/login", json={"login": login, "senha": senha})
    if resposta.status_code != 200:
        raise ErroCarga(f"login recusado (HTTP {resposta.status_code})")
    cabecalho = {"Authorization": f"Bearer {resposta.json()['access_token']}"}

    listagem = cliente.get("/api/v1/fornecedores", headers=cabecalho)
    if listagem.status_code != 200:
        raise ErroCarga(f"listagem de fornecedores recusada (HTTP {listagem.status_code})")
    cnpjs_existentes = {f["cnpj"] for f in listagem.json()}

    resultado = Resultado()
    for fornecedor in fornecedores:
        if fornecedor["cnpj"] in cnpjs_existentes:
            resultado.existentes.append(fornecedor["cnpj"])
            continue
        criado = cliente.post(
            "/api/v1/fornecedores",
            headers=cabecalho,
            json={**fornecedor, "data_source": DATA_SOURCE},
        )
        if criado.status_code != 201:
            raise ErroCarga(
                f"cadastro do CNPJ {fornecedor['cnpj']} recusado (HTTP {criado.status_code})"
            )
        resultado.criados.append(fornecedor["cnpj"])
    return resultado


def main() -> int:
    login = os.environ.get("ITAM_API_LOGIN", "")
    senha = os.environ.get("ITAM_API_SENHA", "")
    if not login or not senha:
        print("Defina ITAM_API_LOGIN e ITAM_API_SENHA (usuário ADMIN).", file=sys.stderr)
        return 2
    url = os.environ.get("ITAM_API_URL", "http://localhost:8000")
    try:
        with httpx.Client(base_url=url, timeout=30) as cliente:
            resultado = carregar(cliente, login, senha, ler_fornecedores())
    except (ErroCarga, httpx.HTTPError) as erro:
        print(f"Carga recusada: {erro}", file=sys.stderr)
        return 1
    print(
        f"Fornecedores: {len(resultado.criados)} criados, {len(resultado.existentes)} já existiam."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

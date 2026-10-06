"""Coletor `endoflife` (item D.3, ADR-011): ciclos de vida e fim de suporte de produtos de software.

Consulta `GET /api/<produto>.json` de endoflife.date (sem chave) para os produtos de `config.yaml`
e grava cada resposta como veio da API, sem transformação, em `dataset/raw/endoflife/<data>/`:

    <produto>.json     ex.: postgresql.json

Mesmas garantias do `compras_gov`: um produto só é gravado depois de a resposta chegar inteira e
no formato esperado (escrita em arquivo temporário e `os.replace`); rodar de novo no mesmo dia
pula os produtos já gravados; novas tentativas com espera crescente (respeitando `Retry-After`)
para 429, 5xx e erro de rede; intervalo fixo entre requisições. Redirecionamento (301) não é
seguido: o produto configurado precisa ter o nome certo na fonte.

Os dados alimentam só o ETL de referência (`dataset/processed/`, ver `python -m etl.normalizar`):
não são carregados no banco e não geram alerta.

Uso: `python -m collectors.endoflife` (a partir de `python/`).
"""

import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
import yaml  # type: ignore[import-untyped]

from collectors.compras_gov import ErroColeta, _pedir, gravar_atomico
from collectors.comum import ResultadoColeta, resumir
from etl.paths import DATASET_DIR

FONTE = "endoflife"
CONFIG = Path(__file__).with_name("config.yaml")


@dataclass(frozen=True)
class Configuracao:
    base_url: str
    endpoint: str  # com o marcador {produto}
    produtos: list[str]
    intervalo_segundos: float = 1.0
    timeout_segundos: float = 30.0
    tentativas: int = 4
    espera_inicial_segundos: float = 2.0
    espera_maxima_segundos: float = 60.0

    def __post_init__(self) -> None:
        if self.tentativas < 1:
            raise ErroColeta("tentativas deve ser >= 1.")
        if not self.produtos:
            raise ErroColeta("produtos vazio: nada a coletar.")
        if len(set(self.produtos)) != len(self.produtos):
            raise ErroColeta("há produto repetido em produtos.")
        if "{produto}" not in self.endpoint:
            raise ErroColeta("endpoint deve conter o marcador {produto}.")


@dataclass(frozen=True)
class _Politica:
    """A política de requisição de um produto: o endpoint já tem o produto no lugar."""

    endpoint: str
    tentativas: int
    espera_inicial_segundos: float
    espera_maxima_segundos: float


def carregar_configuracao(caminho: Path = CONFIG) -> Configuracao:
    bloco = yaml.safe_load(caminho.read_text(encoding="utf-8"))[FONTE]
    bloco["produtos"] = list(bloco.get("produtos") or [])
    if not bloco["produtos"]:
        raise ErroColeta(f"produtos vazio em {caminho.name}: nada a coletar.")
    return Configuracao(**bloco)


def _validar(corpo: bytes) -> None:
    """Recusa o que não tem o formato visto na API: lista de ciclos com `cycle` e `eol`."""
    try:
        ciclos = json.loads(corpo)
        if (
            isinstance(ciclos, list)
            and ciclos
            and all(isinstance(c, dict) and {"cycle", "eol"} <= set(c) for c in ciclos)
        ):
            return
    except ValueError:
        pass
    raise ErroColeta("resposta fora do formato esperado (lista de ciclos com cycle e eol)")


def coletar_produto(
    cliente: httpx.Client,
    configuracao: Configuracao,
    produto: str,
    dormir: Callable[[float], None] = time.sleep,
) -> bytes:
    """O corpo bruto da resposta do produto, ainda em memória: nada vai ao disco."""
    do_produto = _Politica(
        endpoint=configuracao.endpoint.format(produto=produto),
        tentativas=configuracao.tentativas,
        espera_inicial_segundos=configuracao.espera_inicial_segundos,
        espera_maxima_segundos=configuracao.espera_maxima_segundos,
    )
    corpo = _pedir(cliente, do_produto, {}, dormir)
    _validar(corpo)
    return corpo


def executar(
    configuracao: Configuracao,
    destino: Path,
    cliente: httpx.Client,
    dormir: Callable[[float], None] = time.sleep,
) -> ResultadoColeta:
    """Coleta cada produto para `destino` (`raw/endoflife/<data>/`); uma falha não para o resto."""
    resultado = ResultadoColeta()
    for indice, produto in enumerate(configuracao.produtos):
        arquivo = destino / f"{produto}.json"
        if arquivo.exists():
            resultado.pulados.append(produto)
            continue
        if indice:
            dormir(configuracao.intervalo_segundos)
        try:
            corpo = coletar_produto(cliente, configuracao, produto, dormir)
        except ErroColeta as erro:
            resultado.falhas[produto] = str(erro)
            continue
        gravar_atomico(arquivo, corpo)
        resultado.gravados.append(arquivo.name)
    return resultado


def main() -> int:
    configuracao = carregar_configuracao()
    destino = DATASET_DIR / "raw" / FONTE / date.today().isoformat()
    with httpx.Client(
        base_url=configuracao.base_url,
        timeout=configuracao.timeout_segundos,
        headers={"Accept": "application/json", "User-Agent": "itam-coletor/1.0"},
    ) as cliente:
        resultado = executar(configuracao, destino, cliente, time.sleep)
    return resumir(FONTE, destino, resultado, "produtos", "no produto")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

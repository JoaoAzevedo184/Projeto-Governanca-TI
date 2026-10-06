"""Coletor `nvd` (item D.4, ADR-011): quantas CVEs do NVD (NIST) afetam cada ciclo de um produto.

Não baixa CVEs: para cada produto e ciclo de `config.yaml` faz cinco consultas de UM registro
(`resultsPerPage=1`) e guarda a resposta como veio, porque só o `totalResults` interessa:

    <produto>_<ciclo>_<LOW|MEDIUM|HIGH|CRITICAL>.json    CVEs com aquela severidade CVSS v3
    <produto>_<ciclo>_total.json                         todas as CVEs do ciclo (com ou sem v3)

O produto e a faixa de versão de cada ciclo vêm do CPE escrito em `config.yaml`
(`virtualMatchString`, `versionStart`, `versionEnd`): nada é deduzido por semelhança de nome. O
volume é pequeno por construção (consultas de um registro, sem consulta genérica).

Garantias: as mesmas do `compras_gov` (gravação atômica, `total` por último como marcador de ciclo
completo, rodar de novo no mesmo dia pula o que está completo, novas tentativas com espera
crescente para 429 e 5xx). 403, o que o NVD devolve ao passar do limite de requisições, não é
repetido: o ciclo falha e a próxima execução o refaz. O intervalo entre consultas respeita o limite
da API: 5 por 30 s sem chave, 50 com chave.

`NVD_API_KEY` (opcional) é lida só do ambiente, vai no cabeçalho `apiKey` e não passa por
configuração, arquivo, log nem mensagem de erro.

Os dados alimentam só o ETL de referência (`dataset/processed/`): não vão ao banco nem geram alerta.

Uso: `python -m collectors.nvd` (a partir de `python/`).
"""

import json
import os
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

FONTE = "nvd"
CONFIG = Path(__file__).with_name("config.yaml")
SEVERIDADES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
LIMITE_SEM_CHAVE_SEGUNDOS = 30 / 5  # 5 requisições por janela de 30 s
LIMITE_COM_CHAVE_SEGUNDOS = 30 / 50  # 50 requisições por janela de 30 s
TAMANHO_MAXIMO_PAGINA = 10


@dataclass(frozen=True)
class Ciclo:
    ciclo: str  # o `cycle` do endoflife, como "16" ou "8.4"
    cpe: str  # `virtualMatchString`: parte do CPE 2.3 (produto, sem versão) ou o CPE do ciclo
    de: str | None = None  # `versionStart` (inclusive)
    ate: str | None = None  # `versionEnd` (exclusive)


@dataclass(frozen=True)
class Produto:
    produto: str  # o slug do endoflife
    ciclos: list[Ciclo]


@dataclass(frozen=True)
class Configuracao:
    base_url: str
    endpoint: str
    produtos: list[Produto]
    tamanho_pagina: int = 1
    intervalo_segundos: float = 6.5
    intervalo_com_chave_segundos: float = 0.7
    timeout_segundos: float = 60.0
    tentativas: int = 4
    espera_inicial_segundos: float = 2.0
    espera_maxima_segundos: float = 60.0

    def __post_init__(self) -> None:
        if self.tentativas < 1:
            raise ErroColeta("tentativas deve ser >= 1.")
        if not 1 <= self.tamanho_pagina <= TAMANHO_MAXIMO_PAGINA:  # volume por consulta
            raise ErroColeta(f"tamanho_pagina deve ficar entre 1 e {TAMANHO_MAXIMO_PAGINA}.")
        if self.intervalo_segundos < LIMITE_SEM_CHAVE_SEGUNDOS:
            raise ErroColeta("intervalo_segundos abaixo do limite do NVD sem chave (5 por 30 s).")
        if self.intervalo_com_chave_segundos < LIMITE_COM_CHAVE_SEGUNDOS:
            raise ErroColeta("intervalo_com_chave_segundos abaixo do limite do NVD (50 por 30 s).")
        if not self.produtos:
            raise ErroColeta("produtos vazio: nada a coletar.")
        nomes = [p.produto for p in self.produtos]
        if len(set(nomes)) != len(nomes):
            raise ErroColeta("há produto repetido em produtos.")
        for produto in self.produtos:
            if not produto.ciclos:
                raise ErroColeta(f"{produto.produto}: sem ciclos.")
            ciclos = [c.ciclo for c in produto.ciclos]
            if len(set(ciclos)) != len(ciclos):
                raise ErroColeta(f"{produto.produto}: há ciclo repetido.")
            for ciclo in produto.ciclos:
                if not ciclo.cpe.startswith("cpe:2.3:"):
                    raise ErroColeta(f"{produto.produto} {ciclo.ciclo}: cpe deve ser CPE 2.3.")
                if (ciclo.de is None) != (ciclo.ate is None):
                    raise ErroColeta(f"{produto.produto} {ciclo.ciclo}: informe de e ate juntos.")


def carregar_configuracao(caminho: Path = CONFIG) -> Configuracao:
    bloco = yaml.safe_load(caminho.read_text(encoding="utf-8"))[FONTE]
    produtos = bloco.pop("produtos") or {}
    if not produtos:
        raise ErroColeta(f"produtos vazio em {caminho.name}: nada a coletar.")
    return Configuracao(
        produtos=[
            Produto(nome, [Ciclo(**{str(k): str(v) for k, v in c.items()}) for c in ciclos])
            for nome, ciclos in produtos.items()
        ],
        **bloco,
    )


def parametros(
    configuracao: Configuracao, ciclo: Ciclo, severidade: str | None
) -> dict[str, str | int]:
    """Parâmetros de uma consulta: o CPE, a faixa de versão do ciclo e a severidade, se houver."""
    pedido: dict[str, str | int] = {"virtualMatchString": ciclo.cpe}
    if ciclo.de is not None and ciclo.ate is not None:
        pedido |= {
            "versionStart": ciclo.de,
            "versionStartType": "including",
            "versionEnd": ciclo.ate,
            "versionEndType": "excluding",
        }
    if severidade is not None:
        pedido["cvssV3Severity"] = severidade
    pedido["resultsPerPage"] = configuracao.tamanho_pagina
    return pedido


def nome_arquivo(produto: str, ciclo: str, severidade: str | None) -> str:
    return f"{produto}_{ciclo}_{severidade or 'total'}.json"


def _validar(corpo: bytes) -> None:
    """Recusa o que não tem o formato visto na API: `totalResults` inteiro e lista de CVEs."""
    try:
        dados = json.loads(corpo)
        total = dados["totalResults"]
        if (
            isinstance(total, int)
            and not isinstance(total, bool)
            and total >= 0
            and isinstance(dados["vulnerabilities"], list)
        ):
            return
    except (ValueError, KeyError, TypeError):
        pass
    raise ErroColeta("resposta fora do formato esperado (totalResults e vulnerabilities)")


def consultar(
    cliente: httpx.Client,
    configuracao: Configuracao,
    pedido: dict[str, str | int],
    dormir: Callable[[float], None] = time.sleep,
) -> bytes:
    corpo = _pedir(cliente, configuracao, pedido, dormir)
    _validar(corpo)
    return corpo


def coletar_ciclo(
    cliente: httpx.Client,
    configuracao: Configuracao,
    produto: str,
    ciclo: Ciclo,
    dormir: Callable[[float], None],
    intervalo_segundos: float,
) -> list[tuple[str, bytes]]:
    """As cinco respostas do ciclo, na ordem, ainda em memória: nada vai ao disco."""
    arquivos: list[tuple[str, bytes]] = []
    for indice, severidade in enumerate((*SEVERIDADES, None)):
        if indice:
            dormir(intervalo_segundos)
        corpo = consultar(
            cliente, configuracao, parametros(configuracao, ciclo, severidade), dormir
        )
        arquivos.append((nome_arquivo(produto, ciclo.ciclo, severidade), corpo))
    return arquivos


def executar(
    configuracao: Configuracao,
    destino: Path,
    cliente: httpx.Client,
    dormir: Callable[[float], None] = time.sleep,
    intervalo_segundos: float | None = None,
) -> ResultadoColeta:
    """Coleta cada ciclo para `destino` (`raw/nvd/<data>/`); uma falha não para o resto."""
    intervalo = (
        configuracao.intervalo_segundos if intervalo_segundos is None else intervalo_segundos
    )
    resultado = ResultadoColeta()
    primeiro = True
    for produto in configuracao.produtos:
        for ciclo in produto.ciclos:
            chave = f"{produto.produto}_{ciclo.ciclo}"
            if (destino / nome_arquivo(produto.produto, ciclo.ciclo, None)).exists():
                resultado.pulados.append(chave)
                continue
            if not primeiro:
                dormir(intervalo)
            primeiro = False
            try:
                arquivos = coletar_ciclo(
                    cliente, configuracao, produto.produto, ciclo, dormir, intervalo
                )
            except ErroColeta as erro:
                resultado.falhas[chave] = str(erro)
                continue
            for nome, corpo in reversed(arquivos):  # o total por último: é o marcador de completo
                gravar_atomico(destino / nome, corpo)
                resultado.gravados.append(nome)
    return resultado


def _chave_do_ambiente() -> str | None:
    chave = os.environ.get("NVD_API_KEY", "").strip()
    return chave or None


def main() -> int:
    configuracao = carregar_configuracao()
    destino = DATASET_DIR / "raw" / FONTE / date.today().isoformat()
    cabecalhos = {"Accept": "application/json", "User-Agent": "itam-coletor/1.0"}
    chave = _chave_do_ambiente()
    if chave is not None:
        cabecalhos["apiKey"] = chave
    intervalo = (
        configuracao.intervalo_segundos
        if chave is None
        else configuracao.intervalo_com_chave_segundos
    )
    with httpx.Client(
        base_url=configuracao.base_url, timeout=configuracao.timeout_segundos, headers=cabecalhos
    ) as cliente:
        resultado = executar(configuracao, destino, cliente, time.sleep, intervalo)
    return resumir(FONTE, destino, resultado, "ciclos", "em")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""Coletor `compras_gov` (item D.1, ADR-011): itens de TI comprados por órgãos públicos.

Consulta a API de Dados Abertos do Compras.gov.br pelos códigos CATMAT de `config.yaml` e grava
cada página como veio da API, sem transformação, em `dataset/raw/compras_gov/<data>/`:

    <tipo_codigo>_<codigo>_p<NNN>.json     ex.: codigoPdm_8435_p001.json

Garantias:
- Um código só é gravado depois de todas as suas páginas chegarem; falha de rede, de HTTP ou de
  formato não deixa arquivo pela metade (escrita em arquivo temporário e `os.replace`).
- A página 1 é gravada por último e marca o código como completo: rodar de novo no mesmo dia
  pula os códigos completos e refaz os que falharam (`raw/` é imutável por coleta).
- Novas tentativas com espera crescente (respeitando `Retry-After`) para 429, 5xx e erro de
  rede; um intervalo fixo entre requisições.

Uso: `python -m collectors.compras_gov` (a partir de `python/`).
"""

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx
import yaml  # type: ignore[import-untyped]

from etl.paths import DATASET_DIR

FONTE = "compras_gov"
CONFIG = Path(__file__).with_name("config.yaml")
STATUS_REPETIVEIS = {429, 500, 502, 503, 504}


class ErroColeta(Exception):
    """Falha ao coletar um código; a mensagem não leva dados da resposta além do necessário."""


@dataclass(frozen=True)
class Configuracao:
    base_url: str
    endpoint: str
    tipo_codigo: str
    codigos: list[int]
    tamanho_pagina: int = 100
    max_paginas_por_codigo: int = 2
    intervalo_segundos: float = 1.0
    timeout_segundos: float = 30.0
    tentativas: int = 4
    espera_inicial_segundos: float = 2.0
    espera_maxima_segundos: float = 60.0

    def __post_init__(self) -> None:
        if self.tentativas < 1:
            raise ErroColeta("tentativas deve ser >= 1.")
        if not 10 <= self.tamanho_pagina <= 500:  # limites da API (erro 400 fora deles)
            raise ErroColeta("tamanho_pagina deve ficar entre 10 e 500.")
        if self.max_paginas_por_codigo < 1:
            raise ErroColeta("max_paginas_por_codigo deve ser >= 1.")


@dataclass
class Resultado:
    gravados: list[str] = field(default_factory=list)
    pulados: list[int] = field(default_factory=list)
    falhas: dict[int, str] = field(default_factory=dict)


def carregar_configuracao(caminho: Path = CONFIG) -> Configuracao:
    bloco = yaml.safe_load(caminho.read_text(encoding="utf-8"))[FONTE]
    codigos = bloco.pop("catmat_codigos") or []
    if not codigos:
        raise ErroColeta(f"catmat_codigos vazio em {caminho.name}: nada a coletar.")
    return Configuracao(codigos=[int(c) for c in codigos], **bloco)


def gravar_atomico(destino: Path, conteudo: bytes) -> None:
    """Grava `conteudo` em `destino` de uma vez: ou o arquivo inteiro existe, ou não existe."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(f".{destino.name}.tmp")
    try:
        with temporario.open("wb") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)


def _espera(configuracao: Configuracao, tentativa: int, resposta: httpx.Response | None) -> float:
    espera = configuracao.espera_inicial_segundos * 2**tentativa
    pedida = resposta.headers.get("Retry-After", "") if resposta is not None else ""
    if pedida.isdigit():
        espera = max(espera, float(pedida))
    return min(espera, configuracao.espera_maxima_segundos)


def _pedir(
    cliente: httpx.Client,
    configuracao: Configuracao,
    parametros: dict[str, str | int],
    dormir: Callable[[float], None],
) -> bytes:
    """GET com novas tentativas. Devolve o corpo bruto de uma resposta 200."""
    for tentativa in range(configuracao.tentativas):
        ultima = tentativa == configuracao.tentativas - 1
        resposta: httpx.Response | None = None
        try:
            resposta = cliente.get(configuracao.endpoint, params=parametros)
        except httpx.TransportError as erro:  # timeout, conexão recusada, DNS...
            if ultima:
                raise ErroColeta(f"rede: {type(erro).__name__} após {tentativa + 1} tentativas")
        else:
            if resposta.status_code == 200:
                return resposta.content
            if resposta.status_code not in STATUS_REPETIVEIS or ultima:
                raise ErroColeta(f"HTTP {resposta.status_code} em {parametros}")
        dormir(_espera(configuracao, tentativa, resposta))
    raise ErroColeta("sem tentativas")  # pragma: no cover  (tentativas >= 1 é validado)


def _totais(corpo: bytes) -> int:
    """`totalPaginas` da resposta; recusa o que não tem o formato visto na API."""
    try:
        dados = json.loads(corpo)
        if isinstance(dados["resultado"], list) and isinstance(dados["totalPaginas"], int):
            return dados["totalPaginas"]
    except (ValueError, KeyError, TypeError):
        pass
    raise ErroColeta("resposta fora do formato esperado (resultado e totalPaginas)")


def coletar_codigo(
    cliente: httpx.Client,
    configuracao: Configuracao,
    codigo: int,
    dormir: Callable[[float], None] = time.sleep,
) -> list[tuple[str, bytes]]:
    """Todas as páginas do código (até o teto), na ordem, ainda em memória: nada vai ao disco."""
    paginas: list[tuple[str, bytes]] = []
    total = 1
    pagina = 1
    while pagina <= total:
        corpo = _pedir(
            cliente,
            configuracao,
            {
                "tipo": configuracao.tipo_codigo,
                "codigo": codigo,
                "pagina": pagina,
                "tamanhoPagina": configuracao.tamanho_pagina,
            },
            dormir,
        )
        total = min(_totais(corpo), configuracao.max_paginas_por_codigo)
        paginas.append((f"{configuracao.tipo_codigo}_{codigo}_p{pagina:03d}.json", corpo))
        if pagina < total:
            dormir(configuracao.intervalo_segundos)
        pagina += 1
    return paginas


def executar(
    configuracao: Configuracao,
    destino: Path,
    cliente: httpx.Client,
    dormir: Callable[[float], None] = time.sleep,
) -> Resultado:
    """Coleta cada código para `destino` (`raw/compras_gov/<data>/`); uma falha não para o resto."""
    resultado = Resultado()
    for indice, codigo in enumerate(configuracao.codigos):
        primeira = destino / f"{configuracao.tipo_codigo}_{codigo}_p001.json"
        if primeira.exists():
            resultado.pulados.append(codigo)
            continue
        if indice:
            dormir(configuracao.intervalo_segundos)
        try:
            paginas = coletar_codigo(cliente, configuracao, codigo, dormir)
        except ErroColeta as erro:
            resultado.falhas[codigo] = str(erro)
            continue
        for nome, corpo in reversed(paginas):  # p001 por último: é o marcador de completo
            gravar_atomico(destino / nome, corpo)
            resultado.gravados.append(nome)
    return resultado


def main() -> int:
    configuracao = carregar_configuracao()
    destino = DATASET_DIR / "raw" / FONTE / date.today().isoformat()
    with httpx.Client(
        base_url=configuracao.base_url,
        timeout=configuracao.timeout_segundos,
        headers={"Accept": "application/json", "User-Agent": "itam-coletor/1.0"},
    ) as cliente:
        resultado = executar(configuracao, destino, cliente)
    print(
        f"{FONTE}: {len(resultado.gravados)} arquivos em {destino}; "
        f"{len(resultado.pulados)} códigos já coletados; {len(resultado.falhas)} falhas"
    )
    for codigo, motivo in resultado.falhas.items():
        print(f"  falha no código {codigo}: {motivo}", file=sys.stderr)
    return 1 if resultado.falhas else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

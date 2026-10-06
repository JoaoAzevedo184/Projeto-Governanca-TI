"""Resolução de DATASET_DIR compartilhada por collectors/ e etl/, e as coletas de referência.

Fora de contêiner, o default é dataset/ na raiz do repositório (calculado a
partir deste arquivo, não do cwd). Em Docker, DATASET_DIR vem do
docker-compose.yml (montado em /dataset).

Os arquivos versionados de `dataset/demo/` e `dataset/processed/` são o retrato das **coletas de
referência** fixadas em `python/collectors/config.yaml` (bloco `referencia`). O exportador e o
normalizador usam essas datas por padrão; usar outra coleta exige parâmetro explícito e uma saída
que não seja o diretório versionado (`escolher_saida`).
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = Path(os.getenv("DATASET_DIR", REPO_ROOT / "dataset"))
CONFIG = REPO_ROOT / "python" / "collectors" / "config.yaml"
_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


class ErroReferencia(Exception):
    """A configuração da referência está errada, ou a coleta pedida não pode ir para a saída."""


def data_do_nome(nome: str) -> str | None:
    """A data AAAA-MM-DD no nome de uma pasta de coleta (`2026-10-05` ou `coleta_2026-10-05`)."""
    achada = _DATA.search(nome)
    if achada:
        try:
            return date.fromisoformat(achada.group()).isoformat()
        except ValueError:
            return None
    return None


def coleta_de_referencia(fonte: str, config: Path | None = None) -> str:
    """A data (AAAA-MM-DD) da coleta de referência da fonte, do `config.yaml`."""
    bloco = (yaml.safe_load((config or CONFIG).read_text(encoding="utf-8")) or {}).get("referencia")
    if not isinstance(bloco, dict) or fonte not in bloco:
        raise ErroReferencia(f"referencia.{fonte} ausente em {(config or CONFIG).name}")
    valor = bloco[fonte]
    data = data_do_nome(valor.isoformat() if isinstance(valor, date) else str(valor))
    if data is None:
        raise ErroReferencia(f"referencia.{fonte} deve ser uma data AAAA-MM-DD, não {valor!r}")
    return data


def escolher_saida(
    informadas: dict[str, Path], saida: Path | None, versionado: Path, config: Path | None = None
) -> Path:
    """A saída a usar, recusando o que sobrescreveria os arquivos versionados com outra coleta.

    `informadas` são as coletas que o usuário passou por parâmetro (fonte -> pasta). Sem nenhuma,
    vale a de referência e a saída padrão é `versionado`. Com alguma, `saida` é obrigatória, e só
    pode ser `versionado` se toda coleta informada tiver a data de referência da sua fonte."""
    if informadas and saida is None:
        raise ErroReferencia(
            f"usar outra coleta ({', '.join(sorted(informadas))}) exige informar --saida, com um "
            f"diretório que não seja o versionado ({versionado})"
        )
    destino = saida or versionado
    if destino.resolve() == versionado.resolve():
        for fonte, pasta in informadas.items():
            referencia = coleta_de_referencia(fonte, config)
            if data_do_nome(pasta.name) != referencia:
                raise ErroReferencia(
                    f"a coleta {pasta} não é a de referência de {fonte} ({referencia}) e não pode "
                    f"sobrescrever o diretório versionado {versionado}: informe outra --saida"
                )
    return destino


def texto_reprodutibilidade(config: Path | None = None) -> str:
    """A seção dos LEIAME gerados: os arquivos são um retrato das coletas de referência."""
    datas = {f: coleta_de_referencia(f, config) for f in ("compras_gov", "endoflife", "nvd")}
    return f"""## Reprodutibilidade: um retrato das coletas de referência

Estes arquivos correspondem às **coletas de referência** fixadas no bloco `referencia` de `python/collectors/config.yaml`: Compras.gov.br de {datas["compras_gov"]}, endoflife de {datas["endoflife"]} e NVD de {datas["nvd"]}.

A fonte muda entre coletas: medido em 2026-10-06, entre as coletas do Compras.gov.br de 2026-10-05 e de 2026-10-06, **14 dos 1705 registros** mudaram (1691 ficaram iguais) e só 5 das 18 páginas ficaram idênticas byte a byte. Por isso uma coleta nova não reproduz estes arquivos.

O exportador de demonstração e o normalizador usam por padrão a coleta de referência, mesmo que `dataset/raw/` tenha uma mais recente. Usar outra coleta exige parâmetro explícito e `--saida` com um diretório que não seja o versionado.

Para atualizar a referência de propósito (nova coleta, sanitização, fixtures, regeneração e testes), siga a seção "Atualizando a referência" de `docs/guia/coleta-de-dados.md`.
"""  # noqa: E501

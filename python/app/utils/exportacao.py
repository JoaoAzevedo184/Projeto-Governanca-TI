"""Exportação de relatórios em CSV e XLSX (FR-006, AC-036, AC-037).

Funções puras: o carimbo de geração e o solicitante vêm de quem chama. O cabeçalho traz data,
hora e usuário solicitante. Texto que começa com `=`, `+`, `-` ou `@` recebe um apóstrofo, para
a planilha não executá-lo como fórmula (CSV/XLSX injection).
"""

import csv
import io
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from openpyxl import Workbook

CSV_MEDIA_TYPE = "text/csv; charset=utf-8"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_GATILHOS_FORMULA = ("=", "+", "-", "@")


def _cabecalho(titulo: str, gerado_em: datetime, solicitante: str) -> list[list[str]]:
    return [
        [f"Relatório: {titulo}"],
        [f"Gerado em: {gerado_em.strftime('%Y-%m-%d %H:%M:%S')}"],
        [f"Solicitante: {solicitante}"],
        [],
    ]


def _texto_seguro(valor: str) -> str:
    return f"'{valor}" if valor.startswith(_GATILHOS_FORMULA) else valor


def _celula_csv(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (Decimal, int, date)):
        return str(valor)
    return _texto_seguro(str(valor))


def _celula_xlsx(valor: Any) -> Any:
    return _texto_seguro(valor) if isinstance(valor, str) else valor


def gerar_csv(
    titulo: str,
    gerado_em: datetime,
    solicitante: str,
    colunas: Sequence[str],
    linhas: Sequence[Sequence[Any]],
    rodape: Sequence[Sequence[Any]] = (),
) -> bytes:
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerows(_cabecalho(titulo, gerado_em, solicitante))
    escritor.writerow(colunas)
    for linha in [*linhas, *rodape]:
        escritor.writerow([_celula_csv(v) for v in linha])
    return saida.getvalue().encode("utf-8")


def gerar_xlsx(
    titulo: str,
    gerado_em: datetime,
    solicitante: str,
    colunas: Sequence[str],
    linhas: Sequence[Sequence[Any]],
    rodape: Sequence[Sequence[Any]] = (),
) -> bytes:
    planilha = Workbook()
    folha = planilha.active
    for linha_cabecalho in _cabecalho(titulo, gerado_em, solicitante):
        folha.append(linha_cabecalho)
    folha.append(list(colunas))
    for linha in [*linhas, *rodape]:
        folha.append([_celula_xlsx(v) for v in linha])
    saida = io.BytesIO()
    planilha.save(saida)
    return saida.getvalue()

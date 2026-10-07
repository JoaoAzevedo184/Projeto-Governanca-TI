"""Guarda: os testes não leem a data da máquina como "hoje" do domínio.

A aplicação usa `app.utils.datas.hoje()` (fuso America/Recife). `date.today()` segue o fuso da
máquina: em UTC, entre 21h e 00h de Recife, os dois diferem em um dia e o CI quebra.
"""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RELOGIOS = {"today", "utcnow", "now"}
ALVOS = {"date", "datetime"}

# arquivo (relativo a tests/) -> (chamadas permitidas, justificativa)
EXCECOES = {
    "integration/test_relatorios.py": (
        1,
        "carimbo 'Gerado em' vem de agora() (hora local da máquina), não de hoje()",
    ),
    "unit/test_endoflife.py": (1, "o coletor nomeia o diretório raw com date.today() da máquina"),
    "unit/test_nvd.py": (1, "o coletor nomeia o diretório raw com date.today() da máquina"),
    "unit/test_compras_gov.py": (
        1,
        "o coletor nomeia o diretório raw com date.today() da máquina",
    ),
}


def _chamadas_de_relogio(arquivo: Path) -> list[int]:
    linhas = []
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)):
            continue
        dono = no.func.value
        nome = dono.id if isinstance(dono, ast.Name) else getattr(dono, "attr", None)
        if no.func.attr in RELOGIOS and nome in ALVOS:
            linhas.append(no.lineno)
    return linhas


def test_testes_nao_usam_a_data_da_maquina_fora_das_excecoes():
    violacoes = []
    for arquivo in sorted(RAIZ.rglob("*.py")):
        rel = arquivo.relative_to(RAIZ).as_posix()
        if rel == Path(__file__).relative_to(RAIZ).as_posix():
            continue
        linhas = _chamadas_de_relogio(arquivo)
        if len(linhas) != EXCECOES.get(rel, (0, ""))[0]:
            violacoes.append(f"{rel}: linhas {linhas}")
    assert not violacoes, (
        "use app.utils.datas.hoje() em vez da data da máquina "
        "(ou registre a exceção justificada em EXCECOES):\n" + "\n".join(violacoes)
    )

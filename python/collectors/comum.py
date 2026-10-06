"""O que os coletores `endoflife` e `nvd` repartem (o `compras_gov` tem o seu `Resultado`).

A espera crescente, o `Retry-After`, a gravação atômica e `ErroColeta` continuam em
`compras_gov.py`, de onde os outros coletores os importam: não há segunda cópia dessa lógica.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ResultadoColeta:
    """Chaves em texto: o produto (endoflife) ou `<produto>_<ciclo>` (nvd)."""

    gravados: list[str] = field(default_factory=list)
    pulados: list[str] = field(default_factory=list)
    falhas: dict[str, str] = field(default_factory=dict)


def resumir(
    fonte: str, destino: Path, resultado: ResultadoColeta, unidade: str, rotulo_falha: str
) -> int:
    """Imprime o resumo da coleta e devolve o código de saída (1 se houve falha)."""
    print(
        f"{fonte}: {len(resultado.gravados)} arquivos em {destino}; "
        f"{len(resultado.pulados)} {unidade} já coletados; {len(resultado.falhas)} falhas"
    )
    for chave, motivo in resultado.falhas.items():
        print(f"  falha {rotulo_falha} {chave}: {motivo}", file=sys.stderr)
    return 1 if resultado.falhas else 0

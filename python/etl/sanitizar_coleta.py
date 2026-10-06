"""Copia uma coleta bruta para as fixtures trocando o CPF de razão social por zeros.

Microempreendedor individual no formato antigo vem como "NOME DA PESSOA" + 11 dígitos, e os 11
dígitos são o CPF do titular. Os zeros mantêm o formato, então o filtro do exportador
(`PESSOA_FISICA_ONZE_DIGITOS`) continua descartando o registro e a saída não muda.

Uso: python -m etl.sanitizar_coleta dataset/raw/compras_gov/AAAA-MM-DD \
        tests/fixtures/compras_gov/coleta_AAAA-MM-DD
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ZEROS = "0" * 11
# Onze dígitos soltos logo depois de uma palavra: o CPF que segue o nome na razão social.
CPF_APOS_NOME = re.compile(r"(?<=[A-Za-zÀ-ÿ.] )(?<!\d)\d{11}(?!\d)")


def sanitizar(texto: str) -> str:
    return CPF_APOS_NOME.sub(ZEROS, texto)


def copiar_sanitizado(origem: Path, destino: Path) -> int:
    """Copia os `*.json` de `origem` para `destino`; devolve quantos arquivos mudaram."""
    destino.mkdir(parents=True, exist_ok=True)
    alterados = 0
    for arquivo in sorted(origem.glob("*.json")):
        bruto = arquivo.read_bytes().decode("utf-8")
        limpo = sanitizar(bruto)
        alterados += limpo != bruto
        (destino / arquivo.name).write_bytes(limpo.encode("utf-8"))
    return alterados


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    alterados = copiar_sanitizado(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"{alterados} arquivo(s) com CPF de razão social substituído por zeros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

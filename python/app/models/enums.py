from enum import Enum


class TipoAtivo(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"


class StatusAtivo(str, Enum):
    ATIVO = "ATIVO"
    EM_MANUTENCAO = "EM_MANUTENCAO"
    BAIXADO = "BAIXADO"


class PerfilUsuario(str, Enum):
    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"
    GESTOR = "GESTOR"
    AUDITOR = "AUDITOR"


def check_in(coluna: str, enum_cls: type[Enum]) -> str:
    """Gera a expressão SQL de um CHECK (coluna IN (...)) a partir de um enum Python.

    Enums viram VARCHAR + CHECK no banco (não ENUM nativo), para portabilidade
    entre PostgreSQL e SQLite — ver docs/spec/modelo-fisico.md.
    """
    valores = ", ".join(f"'{membro.value}'" for membro in enum_cls)
    return f"{coluna} IN ({valores})"

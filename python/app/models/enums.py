from enum import Enum


class TipoAtivo(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"


class StatusAtivo(str, Enum):
    ATIVO = "ATIVO"
    EM_MANUTENCAO = "EM_MANUTENCAO"
    BAIXADO = "BAIXADO"


class MotivoBaixa(str, Enum):
    OBSOLESCENCIA = "OBSOLESCENCIA"
    DEFEITO = "DEFEITO"
    FURTO_ROUBO = "FURTO_ROUBO"
    FIM_VIDA_UTIL = "FIM_VIDA_UTIL"
    OUTRO = "OUTRO"


class DestinacaoBaixa(str, Enum):
    RECICLAGEM_CERTIFICADA = "RECICLAGEM_CERTIFICADA"
    DOACAO = "DOACAO"
    DEVOLUCAO_FORNECEDOR = "DEVOLUCAO_FORNECEDOR"
    VENDA = "VENDA"
    DESCARTE = "DESCARTE"


class TipoLicenciamento(str, Enum):
    PERPETUA = "PERPETUA"
    SUBSCRICAO = "SUBSCRICAO"
    OEM = "OEM"


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

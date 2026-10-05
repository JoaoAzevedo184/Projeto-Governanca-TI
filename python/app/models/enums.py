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


class CategoriaRisco(str, Enum):
    OPERACIONAL = "OPERACIONAL"
    FINANCEIRO = "FINANCEIRO"
    LEGAL = "LEGAL"
    SEGURANCA = "SEGURANCA"
    CONTINUIDADE = "CONTINUIDADE"


class RespostaRisco(str, Enum):
    ACEITAR = "ACEITAR"
    MITIGAR = "MITIGAR"
    TRANSFERIR = "TRANSFERIR"
    EVITAR = "EVITAR"


class StatusRisco(str, Enum):
    ABERTO = "ABERTO"
    EM_TRATAMENTO = "EM_TRATAMENTO"
    ENCERRADO = "ENCERRADO"


class ClassificacaoRisco(str, Enum):
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


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


class NomeCenario(str, Enum):
    MANTER = "MANTER"
    RENOVAR = "RENOVAR"
    MIGRAR_ASSINATURA = "MIGRAR_ASSINATURA"


class StatusRecomendacao(str, Enum):
    PROPOSTA = "PROPOSTA"
    APROVADA = "APROVADA"
    REJEITADA = "REJEITADA"
    IMPLEMENTADA = "IMPLEMENTADA"


class TipoEvidencia(str, Enum):
    INDICADOR = "INDICADOR"
    RISCO = "RISCO"
    ATIVO = "ATIVO"
    LICENCA = "LICENCA"
    SCORECARD = "SCORECARD"
    CENARIO = "CENARIO"
    PREMISSA = "PREMISSA"


# Evidências sem registro próprio no banco (indicador e cenário são derivados na hora; premissa é
# declarada): não têm `referencia_id` e a `descricao` carrega o que sustenta a recomendação.
EVIDENCIAS_SEM_REFERENCIA = frozenset(
    {TipoEvidencia.INDICADOR, TipoEvidencia.CENARIO, TipoEvidencia.PREMISSA}
)

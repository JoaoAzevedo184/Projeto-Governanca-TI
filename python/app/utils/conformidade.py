"""Conformidade de licença e catálogo das regras de compliance (FR-004, FR-007).

Funções puras: sem sessão de banco e sem `date.today()`. A `data_referencia` é sempre injetada
por quem chama, como na depreciação. Docs: docs/spec/regras-de-calculo.md §7.2.
"""

from dataclasses import dataclass
from datetime import date

CRITICO, ALTO, MEDIO, BAIXO = "CRITICO", "ALTO", "MEDIO", "BAIXO"
SEVERIDADES = (CRITICO, ALTO, MEDIO, BAIXO)  # ordem decrescente de criticidade (AC-040)

CONFORME, ALERTA, NAO_CONFORME = "CONFORME", "ALERTA", "NAO_CONFORME"


@dataclass(frozen=True)
class RegraCompliance:
    codigo: str
    severidade: str
    descricao: str  # a regra aplicada, legível (AC-042)
    mensagem: str


REGRAS = {
    r.codigo: r
    for r in (
        RegraCompliance("CP-01", CRITICO, "Licença com data_expiracao < hoje", "Licença vencida"),
        RegraCompliance(
            "CP-02",
            CRITICO,
            "Licença com quantidade_em_uso > quantidade_contratada",
            "Uso acima do contratado — risco de autuação",
        ),
        RegraCompliance(
            "CP-03",
            ALTO,
            "Licença expirando dentro da janela de alerta (padrão 30 dias)",
            "Licença próxima do vencimento",
        ),
        RegraCompliance(
            "CP-04",
            ALTO,
            "Ativo com status ATIVO sem vínculo de responsável aberto",
            "Ativo em operação sem responsável",
        ),
    )
}


def dias_para_expiracao(data_expiracao: date, data_referencia: date) -> int:
    """Negativo quando a licença já venceu."""
    return (data_expiracao - data_referencia).days


def alertas_licenca(
    quantidade_contratada: int,
    quantidade_em_uso: int,
    data_expiracao: date,
    data_referencia: date,
    janela_dias: int,
) -> list[str]:
    """Códigos CP-01 a CP-03 que a licença dispara na data de referência."""
    dias = dias_para_expiracao(data_expiracao, data_referencia)
    codigos = []
    if dias < 0:
        codigos.append("CP-01")
    if quantidade_em_uso > quantidade_contratada:
        codigos.append("CP-02")
    if 0 <= dias <= janela_dias:
        codigos.append("CP-03")
    return codigos


def status_conformidade(codigos: list[str]) -> str:
    """CRITICO → NAO_CONFORME; só ALTO → ALERTA; nenhum → CONFORME. KPI-03 conta como
    conforme tudo o que não é NAO_CONFORME (uso ≤ contratado e não vencida)."""
    severidades = {REGRAS[c].severidade for c in codigos}
    if CRITICO in severidades:
        return NAO_CONFORME
    return ALERTA if severidades else CONFORME

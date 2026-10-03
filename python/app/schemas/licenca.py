from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import TipoLicenciamento


def _validar_nao_futura(valor: date | None) -> date | None:
    if valor is not None and valor > date.today():
        raise ValueError("data_inicio_vigencia não pode ser posterior à data corrente (FR-004).")
    return valor


class LicencaCreate(BaseModel):
    """Corpo de `POST /licencas` (FR-004, contrato §6.4).

    A forma por tipo segue `ck_licenca_tipo`: PERPETUA aponta para o ativo SOFTWARE; SUBSCRICAO e
    OEM guardam o nome do software, e só a subscrição tem `valor_total`. A ordem das datas
    (BR-019) e o ativo que não é SOFTWARE em PERPETUA (BR-035) são recusados pelo serviço com 409 e
    `regra`, registrada na auditoria (NFR-AUD-05).
    """

    tipo_licenciamento: TipoLicenciamento
    ativo_id: int | None = None
    software: str | None = Field(default=None, min_length=3, max_length=120)
    fornecedor_id: int
    chave_licenca: str = Field(min_length=1, max_length=200)
    quantidade_contratada: int = Field(ge=1)
    data_inicio_vigencia: date
    data_expiracao: date
    valor_total: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _validar_forma_por_tipo(self) -> "LicencaCreate":
        tipo = self.tipo_licenciamento
        if tipo == TipoLicenciamento.PERPETUA:
            if self.ativo_id is None:
                raise ValueError("ativo_id é obrigatório em licença PERPETUA.")
            if self.software is not None or self.valor_total is not None:
                raise ValueError("Licença PERPETUA não tem software nem valor_total (ADR-012).")
            return self
        if self.ativo_id is not None:
            raise ValueError(f"Licença {tipo.value} não aponta para ativo (ADR-012).")
        if self.software is None:
            raise ValueError(f"software é obrigatório em licença {tipo.value}.")
        if tipo == TipoLicenciamento.SUBSCRICAO and self.valor_total is None:
            raise ValueError("valor_total é obrigatório em licença SUBSCRICAO.")
        if tipo == TipoLicenciamento.OEM and self.valor_total is not None:
            raise ValueError("Licença OEM não tem valor_total: o valor está no hardware.")
        return self

    @model_validator(mode="after")
    def _validar_inicio_nao_futuro(self) -> "LicencaCreate":
        _validar_nao_futura(self.data_inicio_vigencia)
        return self


class LicencaUpdate(BaseModel):
    """Corpo de `PATCH /licencas/{id}`: só o que muda ao longo do contrato. Tipo, ativo, nome do
    software e valor não mudam (alterariam `ck_licenca_tipo`)."""

    fornecedor_id: int | None = None
    chave_licenca: str | None = Field(default=None, min_length=1, max_length=200)
    quantidade_contratada: int | None = Field(default=None, ge=1)
    data_inicio_vigencia: date | None = None
    data_expiracao: date | None = None

    @model_validator(mode="after")
    def _validar_inicio_nao_futuro(self) -> "LicencaUpdate":
        _validar_nao_futura(self.data_inicio_vigencia)
        return self


class LicencaResponse(BaseModel):
    """Licença com o bloco derivado do contrato §6.4, calculado na hora (nada é armazenado):
    `alertas` são os códigos CP-01 a CP-03 disparados hoje e `status_conformidade` resume-os.
    A chave sai mascarada, salvo no detalhe para ADMIN (RI-08)."""

    id: int
    tipo_licenciamento: TipoLicenciamento
    ativo_id: int | None
    software: str | None
    fornecedor_id: int
    chave_licenca: str
    quantidade_contratada: int
    quantidade_em_uso: int = Field(description="COUNT dos vínculos ativos (BR-021, ADR-008).")
    saldo: int = Field(description="quantidade_contratada − quantidade_em_uso.")
    data_inicio_vigencia: date
    data_expiracao: date
    dias_para_expiracao: int = Field(description="Negativo quando a licença já venceu.")
    valor_total: Decimal | None
    data_source: str
    status_conformidade: str = Field(description="CONFORME, ALERTA (só CP-03) ou NAO_CONFORME.")
    alertas: list[str] = Field(description="Códigos CP-01 a CP-03 disparados na data de hoje.")


class ListaLicencasResponse(BaseModel):
    itens: list[LicencaResponse]
    pagina: int
    tamanho: int
    total: int
    total_paginas: int


class VinculoLicencaCreate(BaseModel):
    """Corpo de `POST /licencas/{id}/vinculos`: `ativo_id` é a máquina hospedeira.

    Recusas com 409 e `regra`: BR-018, BR-020, BR-032 (máquina baixada), BR-037 (ativo SOFTWARE
    da licença baixado), BR-033 (máquina que não é HARDWARE) e BR-034 (licença já vinculada à
    máquina).
    """

    ativo_id: int
    data_vinculo: date | None = Field(default=None, description="Padrão: hoje.")

    @model_validator(mode="after")
    def _validar_data_nao_futura(self) -> "VinculoLicencaCreate":
        if self.data_vinculo is not None and self.data_vinculo > date.today():
            raise ValueError("data_vinculo não pode ser posterior à data corrente (FR-004).")
        return self


class VinculoLicencaResponse(BaseModel):
    id: int
    licenca_id: int
    ativo_id: int
    data_vinculo: date
    ativo_vinculo: bool
    data_source: str

    model_config = {"from_attributes": True}

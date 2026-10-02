# Modelo de Dados — Diagrama de Entidade-Relacionamento

Parte de [Modelo de Dados — ITAM](README.md).

## 1. Diagrama de Entidade-Relacionamento

```mermaid
erDiagram
    CATEGORIA ||--o{ ATIVO : classifica
    FORNECEDOR ||--o{ ATIVO : fornece
    FORNECEDOR ||--o{ LICENCA : fornece
    FORNECEDOR ||--o{ FORNECEDOR_AVALIACAO : recebe

    SETOR ||--o{ RESPONSAVEL : lota
    SETOR ||--o{ HISTORICO_TRANSFERENCIA : destina

    ATIVO ||--o{ HISTORICO_TRANSFERENCIA : possui
    RESPONSAVEL ||--o{ HISTORICO_TRANSFERENCIA : recebe

    ATIVO ||--o| BAIXA_ATIVO : encerra
    ATIVO ||--o{ LICENCA_VINCULO : hospeda_instalacao
    LICENCA ||--o{ LICENCA_VINCULO : concede_assento
    ATIVO |o--o{ LICENCA : "perpetua_de (tipo SOFTWARE)"

    LOTE_IMPORTACAO ||--o{ ERRO_IMPORTACAO : registra
    LOTE_IMPORTACAO ||--o{ ATIVO : origina

    RECOMENDACAO ||--|{ EVIDENCIA : sustenta
    RISCO ||--o{ EVIDENCIA : fundamenta

    USUARIO ||--o{ HISTORICO_TRANSFERENCIA : registra
    USUARIO ||--o{ BAIXA_ATIVO : registra
    USUARIO ||--o{ AUDIT_LOG : gera

    PRODUTO_SOFTWARE ||--o{ VULNERABILIDADE : afetado_por
    PRODUTO_SOFTWARE ||--o{ ATIVO_SOFTWARE : instalado_em
    ATIVO ||--o{ ATIVO_SOFTWARE : possui
    PRODUTO_SOFTWARE |o--o{ ATIVO : cataloga
```

**Software e licença** (ADR-012 e itens 4 a 6 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)): em `LICENCA_VINCULO`, o `ATIVO` é a **máquina hospedeira**, e o software é alcançado pela `LICENCA`. A licença perpétua aponta para o ativo `SOFTWARE`, que tem o valor patrimonial; subscrição e OEM não têm ativo. `PRODUTO_SOFTWARE` é catálogo de referência; `ATIVO_SOFTWARE` é a instalação observada e continua separada de `LICENCA_VINCULO` (ver [dicionário §3.11](dicionario-de-dados.md#311-ciclo-de-vida-de-software-e-vulnerabilidades)).

A cardinalidade `RECOMENDACAO ||--|{ EVIDENCIA` é **um para um-ou-muitos**, não um para zero-ou-muitos. Essa é a expressão no modelo da regra BR-027: recomendação sem evidência não existe.


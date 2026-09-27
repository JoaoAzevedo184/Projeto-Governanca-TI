# PRD — ITAM: Gestão de Ativos de TI

| Campo | Valor |
|---|---|
| **Produto** | ITAM — Gestão de Ativos de TI |
| **Versão do documento** | 1.0 |
| **Tipo** | Product Requirements Document (PRD) |
| **Disciplina** | Governança de TI — Sistemas de Informação — UNINASSAU Olinda |
| **Baseline técnica** | Guia de Orquestração para 3 Projetos de MVPs (dual Python + Java) |
| **Status** | Aprovado para especificação técnica (SDD) |
| **Idioma** | Português (Brasil) |

Este PRD foi dividido em arquivos menores por responsabilidade. Índice:

| Arquivo | Conteúdo |
|---|---|
| [`visao-geral.md`](visao-geral.md) | Executive summary, visão de produto, problema, objetivos e métricas de sucesso (KPI-) |
| [`stakeholders-personas.md`](stakeholders-personas.md) | Stakeholders e personas |
| [`escopo.md`](escopo.md) | Escopo do MVP — incluído (IN-) e fora de escopo (OUT-) |
| [`jornadas-historias.md`](jornadas-historias.md) | Jornadas do usuário e histórias de usuário (US-) |
| [`requisitos-funcionais.md`](requisitos-funcionais.md) | Requisitos funcionais completos (FR-001 a FR-015) |
| [`regras-de-negocio.md`](regras-de-negocio.md) | Regras de negócio (BR-) |
| [`criterios-de-aceitacao.md`](criterios-de-aceitacao.md) | Critérios de aceitação (AC-) |
| [`requisitos-nao-funcionais.md`](requisitos-nao-funcionais.md) | Requisitos não funcionais (NFR-) |
| [`modelo-conceitual.md`](modelo-conceitual.md) | Modelo conceitual de dados (entidades e relacionamentos, nível de produto — dicionário físico completo em [`docs/modelo-de-dados/`](../modelo-de-dados/README.md)) |
| [`fluxos-de-negocio.md`](fluxos-de-negocio.md) | Fluxos de negócio (cadastro, transferência, baixa, renovação, compliance) |
| [`dashboard-relatorios.md`](dashboard-relatorios.md) | Dashboard, gráficos e relatórios |
| [`planejamento.md`](planejamento.md) | Riscos (RI-), restrições (RE-), roadmap e perguntas em aberto (QA-) |
| [`anexos.md`](anexos.md) | Matriz de aderência a frameworks de governança, matriz de rastreabilidade e glossário |

Todo identificador (`FR-`, `BR-`, `AC-`, `NFR-`, `US-`, `KPI-`, `IN-`, `OUT-`, `RI-`, `RE-`, `QA-`) é estável e vive inteiro em um único arquivo acima — toda alteração posterior deve preservar os identificadores existentes e adicionar novos ao final da sequência de sua família.

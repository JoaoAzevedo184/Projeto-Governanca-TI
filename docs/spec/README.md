# SPEC — ITAM: Especificação Técnica

| Campo | Valor |
|---|---|
| **Produto** | ITAM — Gestão de Ativos de TI |
| **Documento** | Especificação técnica de implementação |
| **Versão** | 1.0 |
| **Stack** | Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL |
| **Documento de origem** | [`docs/prd/`](../prd/README.md) |
| **Disciplina** | Governança de TI — UNINASSAU Olinda |

> Este documento define **como** construir. O **o quê** e o **por quê** estão no PRD. Todo identificador citado aqui (FR, BR, AC, NFR, US, KPI) refere-se ao PRD e é estável: implementações devem preservá-lo em comentários, nomes de teste e mensagens de erro.

Dividido em arquivos menores por responsabilidade. Índice:

| Arquivo | Conteúdo |
|---|---|
| [`escopo-e-premissas.md`](escopo-e-premissas.md) | Escopo técnico e premissas arquiteturais (P1–P6) |
| [`arquitetura.md`](arquitetura.md) | Camadas e módulos transversais (visão resumida — visão completa em [`docs/ARQUITETURA.md`](../ARQUITETURA.md)) |
| [`stack.md`](stack.md) | Stack e dependências de runtime e desenvolvimento |
| [`estrutura-diretorios.md`](estrutura-diretorios.md) | Estrutura de diretórios do repositório |
| [`modelo-fisico.md`](modelo-fisico.md) | Modelo físico de dados — enumerações, tabelas, constraints, imutabilidade |
| [`contrato-api.md`](contrato-api.md) | Contrato da API — endpoints, payloads, envelopes |
| [`regras-de-calculo.md`](regras-de-calculo.md) | Regras de cálculo — depreciação, licença, risco, scorecard, TCO |
| [`padrao-de-erros.md`](padrao-de-erros.md) | Padrão de erros da API |
| [`seguranca.md`](seguranca.md) | Autenticação, autorização e demais controles de segurança |
| [`pipeline-importacao.md`](pipeline-importacao.md) | Pipeline de importação de inventário (FR-008) |
| [`observabilidade.md`](observabilidade.md) | Métricas, log estruturado e Grafana |
| [`estrategia-de-testes.md`](estrategia-de-testes.md) | Estratégia de testes por camada |
| [`configuracao.md`](configuracao.md) | Configuração (`.env.example`), migrações e carga inicial |
| [`plano-de-sprints.md`](plano-de-sprints.md) | Plano de sprints |
| [`adrs-e-rastreabilidade.md`](adrs-e-rastreabilidade.md) | ADR-001 a ADR-011 resumidas e mapa requisito → módulo → teste |

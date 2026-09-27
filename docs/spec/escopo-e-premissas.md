# SPEC — Escopo Técnico e Premissas Arquiteturais

Parte de [SPEC — ITAM](README.md).

## 1. Escopo Técnico

### 1.1 O que este documento cobre

Arquitetura, modelo físico de dados, contrato da API, regras de cálculo, padrão de erros, segurança, pipeline de importação, observabilidade, estratégia de testes e plano de sprints.

### 1.2 Premissas arquiteturais

| # | Premissa | Consequência |
|---|---|---|
| P1 | Monólito modular, não microsserviços | Um único processo; separação por pacote, não por rede |
| P2 | Contrato OpenAPI é a fonte de verdade da API | Qualquer implementação alternativa deve passar na mesma suíte de contrato (NFR-MAN-01) |
| P3 | Regra de negócio vive na camada de serviço, nunca no router nem no modelo | Routers só orquestram; testes de regra não precisam subir HTTP |
| P4 | Depreciação é função pura, não estado persistido | Recalculável a qualquer momento; exceção única no registro de baixa (BR-015) |
| P5 | Tabelas históricas são *append-only* garantidas no banco | Imutabilidade não depende de disciplina de código (NFR-AUD-01) |
| P6 | SQLite para execução local, PostgreSQL para o ambiente orquestrado | Seleção por variável de ambiente, mesma suíte de testes nos dois perfis |


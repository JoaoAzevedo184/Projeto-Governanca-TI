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
| P3 | Regra de negócio vive na camada de serviço, nunca no router nem no modelo | Routers só orquestram; testes de regra não precisam subir HTTP. *Revisado:* não há camada de repositório; serviços usam a `Session` direto, e leituras sem regra (listagens de cadastro, login, consultas de importação) acessam o modelo direto no router — ver [`arquitetura.md`](arquitetura.md) §2.1 |
| P4 | Depreciação é função pura, não estado persistido | Recalculável a qualquer momento; exceção única no registro de baixa (BR-015) |
| P5 | Tabelas históricas são *append-only* garantidas no banco | Imutabilidade não depende de disciplina de código (NFR-AUD-01). *Estado atual:* `historico_transferencia`, `audit_log` e `baixa_ativo` têm trigger (ver [`migracoes.md`](../modelo-de-dados/migracoes.md)) |
| P6 | SQLite para execução local, PostgreSQL para o ambiente orquestrado | Seleção por variável de ambiente. *Revisado (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)):* a aplicação continua rodando em SQLite para execução local sem Docker (`DATABASE_URL`), mas os testes rodam só em PostgreSQL 16. No SQLite não há trigger de imutabilidade, lock de linha (`FOR NO KEY UPDATE`) nem verificação de FK (`PRAGMA foreign_keys` desligado) |


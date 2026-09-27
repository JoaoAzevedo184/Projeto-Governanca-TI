# SPEC — Decisões Arquiteturais (ADR resumidas) e Rastreabilidade

Parte de [SPEC — ITAM](README.md).

## 15. Decisões Arquiteturais (ADR resumidas)

| ID | Decisão | Alternativa descartada | Motivo |
|---|---|---|---|
| ADR-001 | Monólito modular em FastAPI | Microsserviços | Escopo de MVP; complexidade operacional sem benefício proporcional |
| ADR-002 | Depreciação calculada sob demanda | Persistir valor depreciado | Evita job de recálculo e divergência entre o valor armazenado e a data corrente |
| ADR-003 | Responsável atual derivado do histórico | Coluna `responsavel_id` no ativo | Elimina fonte de verdade concorrente (seção 14.3 do PRD) |
| ADR-004 | `Decimal` com `Numeric(12,2)` | `float` | Precisão contábil exigida pelo KPI-05 |
| ADR-005 | Imutabilidade por trigger no banco | Convenção de código | Garantia independente da disciplina da equipe (NFR-AUD-01) |
| ADR-006 | Índice único parcial para vínculo aberto | Validação só na aplicação | Só o banco garante a invariante sob concorrência (BR-007) |
| ADR-007 | Enums como VARCHAR + CHECK | Tipo ENUM do PostgreSQL | Portabilidade para SQLite e migrações mais simples |
| ADR-008 | `quantidade_em_uso` derivada por COUNT | Coluna materializada | Elimina risco de dessincronização (BR-021) |
| ADR-009 | Campo `regra` no payload de erro | Mensagem livre | Rastreabilidade runtime → requisito, verificável na defesa |
| ADR-010 | Testes nomeados pelo identificador do critério | Nomes livres | Matriz de rastreabilidade verificável por comando |
| [ADR-011](../adr/0011-estrategia-dados-reais-demonstracao.md) | Dados reais de Compras.gov.br, endoflife.date e NVD para a base de demonstração; sintético só para pessoas e eventos | GLPI Agent, scraping, datasets do Kaggle, 100% sintético | Credibilidade dos indicadores exige preço, data e ciclo de vida verificáveis; pessoas não podem ser reais (LGPD) |

> A partir da ADR-011, registros de decisão completos ficam em `docs/adr/`; esta tabela permanece como resumo histórico das ADR-001 a ADR-010.


## Apêndice — Mapa Requisito → Módulo → Teste

| FR | Serviço | Módulo de teste |
|---|---|---|
| FR-001 | `ativo_service.py` | `tests/integration/test_ativos.py` |
| FR-002 | `responsavel_service.py` | `tests/integration/test_responsaveis.py` |
| FR-003 | `depreciacao_service.py`, `utils/depreciacao.py` | `tests/unit/test_depreciacao.py` |
| FR-004 | `licenca_service.py` | `tests/integration/test_licencas.py` |
| FR-005 | `baixa_service.py` | `tests/integration/test_baixas.py` |
| FR-006 | `relatorio_service.py` | `tests/integration/test_relatorios.py` |
| FR-007 | `compliance_service.py` | `tests/integration/test_compliance.py` |
| FR-008 | `importacao_service.py` | `tests/integration/test_importacao.py` |
| FR-009 | `indicador_service.py` | `tests/integration/test_indicadores.py` |
| FR-010 | `cenario_service.py` | `tests/unit/test_cenarios.py` |
| FR-011 | `scorecard_service.py` | `tests/unit/test_scorecard.py` |
| FR-012 | `risco_service.py` | `tests/unit/test_riscos.py` |
| FR-013 | `recomendacao_service.py` | `tests/integration/test_recomendacoes.py` |
| FR-014 | `core/metrics.py` | `tests/integration/test_observabilidade.py` |
| FR-015 | `core/security.py`, `api/deps.py` | `tests/integration/test_seguranca.py` |
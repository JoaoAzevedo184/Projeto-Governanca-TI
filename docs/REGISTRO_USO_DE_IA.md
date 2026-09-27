# Registro de Uso de IA — ITAM

Documento vivo. Cada uso de ferramenta de IA na construção deste projeto é registrado aqui, com o artefato gerado e a revisão humana aplicada.

**Princípio:** a ferramenta produz rascunho; a equipe produz entrega. Todo artefato aqui listado é de responsabilidade integral de quem assina a revisão, e qualquer integrante deve conseguir explicá-lo na defesa sem consultar este registro.

---

## 1. Ferramentas autorizadas pela equipe

| Ferramenta | Uso previsto | Uso vedado |
|---|---|---|
| Assistentes de chat (Claude, ChatGPT, Gemini) | Rascunho de documentação, revisão de texto, exploração de alternativas de modelagem | Gerar código que entra no repositório sem leitura linha a linha |
| Assistentes de código (Copilot, Cursor, Claude Code) | Autocompletar, gerar testes a partir de critérios de aceite, refatoração mecânica | Gerar regra de negócio sem conferência contra o `PRD-ITAM.md` |
| Geradores de dados | Produzir datasets sintéticos de demonstração | Produzir dados que a equipe não consiga explicar ou reproduzir |

---

## 2. Níveis de revisão

Todo registro classifica a revisão em um dos três níveis:

| Nível | Significado | Quando é suficiente |
|---|---|---|
| **R1 — Leitura** | Lido integralmente, sem alteração | Texto descritivo, sem afirmação técnica verificável |
| **R2 — Verificação** | Conferido contra uma fonte (PRD, norma, documentação oficial) e corrigido | Documentação técnica, decisões de modelagem, citação de frameworks |
| **R3 — Execução** | Executado, testado e o resultado conferido | Todo código, script, migração, consulta SQL e dataset |

Nenhum artefato de código pode ficar abaixo de R3. Nenhum documento que cite norma ou framework pode ficar abaixo de R2.

---

## 3. Registro

| # | Data | Ferramenta | Artefato gerado | O que foi pedido | Revisão humana aplicada | Nível | Responsável |
|---|---|---|---|---|---|---|---|
| 01 | 2026-09-20 | Claude | `docs/PRD-ITAM.md` | PRD completo a partir dos requisitos FR-001 a FR-007 definidos pela equipe | Conferida a aderência a COBIT BAI09, ITIL 4 e ISO/IEC 19770 nas fontes originais; vida útil das categorias verificada contra a IN RFB 1.700/2017; ajustadas as personas ao contexto da organização do cenário | R2 | *(preencher)* |
| 02 | 2026-09-20 | Claude | `SPEC.md` | Especificação técnica para stack Python/FastAPI | Versões das dependências verificadas na documentação oficial e fixadas; contrato da API conferido endpoint a endpoint contra o PRD | R2 | *(preencher)* |
| 03 | 2026-09-20 | Claude | `README.md` | Documentação de execução do repositório | Comandos executados em máquina limpa; seção de troubleshooting validada provocando cada erro | R3 | *(preencher)* |
| 04 | 2026-09-20 | Claude | `docs/ARQUITETURA.md`, `docs/MODELO_DE_DADOS.md`, `docs/BACKLOG_E_GATES.md` | Documentos de arquitetura, modelo de dados e planejamento | Diagramas Mermaid renderizados e conferidos; DDL das constraints e triggers executado em PostgreSQL; consultas SQL de referência executadas contra o dataset | R3 | *(preencher)* |
| 05 | 2026-09-20 | Claude | `scripts/gerar_datasets.py`, `scripts/validar_datasets.py`, `datasets/*.csv` | Gerador e validador dos datasets de demonstração | Script executado; validador apontou vínculos encerrados após a data de baixa e o gerador foi corrigido; deslocamento nos índices de fornecedor identificado e corrigido; contagem de desvios conferida manualmente | R3 | *(preencher)* |
| 06 | 2026-09-27 | Claude | `README.md`, `docs/FONTES_DE_DADOS.md`, `docs/adr/0011-estrategia-dados-reais-demonstracao.md`, `docs/MODELO_DE_DADOS.md`, `docs/ARQUITETURA.md`, `docs/SPEC.md`, `docs/PRD.md` | Atualização da documentação para refletir a estratégia de dados reais (Compras.gov.br, endoflife.date, NVD) combinados com dados sintéticos (Mockaroo + ETL) | Conferência pendente: endpoints exatos do Compras.gov.br e do NVD, e limites de requisição, marcados com `<!-- TODO: confirmar -->` nos documentos; nenhum endpoint, campo ou número foi inventado sem essa marcação | R2 | *(preencher)* |
| 07 | 2026-09-27 | Claude | Reorganização de diretórios: `collectors/`, `etl/` e `scripts/gerar_sinteticos.py` → `python/`; `data/` → `dataset/` (com `data/inventario_demo.csv` → `dataset/demo/inventario_demo.csv`); `docker/` e `infra/` unificados em `infra/`; novos `python/alembic.ini`, `python/etl/paths.py`, `dataset/README.md`; `docker-compose.yml`, `scripts/*.sh`, `.env.example` e docs correspondentes atualizados | Consolidar todo o código Python (app, collectors, etl, testes) sob `python/`, dados sob `dataset/` e provisionamento sob `infra/`, sem duplicidade nem caminho hardcoded dependente do cwd | Nenhuma lógica alterada, só movimentação de arquivo e caminho — conferido: diff entre `docker/` e `infra/` mostrou `infra/prometheus.yml` como resíduo do protótipo antigo (job `observabilidade-python`), descartado em favor do conteúdo em uso (`itam-api`); `docker compose config` validado com volume de `dataset/` e `DATASET_DIR=/dataset` no serviço `api`; links relativos dos `.md` verificados sem quebra; `pytest --collect-only` executado a partir de `python/` (venv temporária, removida depois) sem erro | R3 | *(preencher)* |
| 08 | 2026-09-27 | Claude | Conclusão do Gate 0 (Sprint 0): `.github/workflows/ci.yml` (corrigido de `.github/.workflow/`, caminho inválido para o GitHub Actions); `python/app/core/config.py`, `python/app/core/database.py`, `python/app/models/base.py` implementados (mínimo necessário para o Alembic funcionar); `python/alembic/env.py` funcional (`target_metadata`, URL via settings) e `python/alembic/script.py.mako` (faltava); migração base `8b17f25f113a`; `mypy`/`bandit` adicionados a `requirements-dev.txt`; `alembic/versions` excluído do `ruff.toml`; `docs/ROADMAP.md` e `docs/BACKLOG_E_GATES.md` corrigidos | Fechar os itens pendentes do Gate 0/Sprint 0 (CI, migração base) e corrigir o roadmap, que marcava modelos/serviços de Sprints 1–5 como "Feito" quando os arquivos estão vazios (scaffold) | Testado em venv temporária (removida depois): `alembic upgrade head` e `alembic downgrade base` executados com sucesso e revertidos (SQLite); `ruff check .`, `mypy app --ignore-missing-imports` e `bandit -r app -ll` sem erros; `docker compose config` e `docker compose build api` executados com sucesso; nenhum `test_*.py` existe ainda, então `pytest` não tem o que coletar (esperado, fora do escopo do Gate 0) | R3 | *(preencher)* |
| 09 | 2026-09-27 | Claude | Implementação da Sprint 1 (Gate 1): modelos `categoria`, `fornecedor`, `setor`, `responsavel`, `usuario`, `ativo`, `lote_importacao`, `erro_importacao`, `audit_log` (`app/models/`); `app/core/security.py` (JWT + BCrypt), `app/api/deps.py` (`require_perfil`); `app/services/ativo_service.py` e `importacao_service.py`; routers `auth`, `categorias`, `fornecedores`, `setores`, `responsaveis`, `ativos`, `importacoes`; `app/core/exceptions.py` (handler global com campo `regra`); migração `13ade34ba8a3`; 25 testes em `tests/integration/` | Implementar o backlog 1.1–1.12 (docs/BACKLOG_E_GATES.md) seguindo à risca `docs/prd/regras-de-negocio.md`, `docs/prd/criterios-de-aceitacao.md`, `docs/spec/modelo-fisico.md`, `docs/spec/contrato-api.md`, `docs/spec/padrao-de-erros.md` e `docs/spec/pipeline-importacao.md` | Cada regra de negócio (BR-001 a BR-006, BR-030) e critério de aceite (AC-001 a AC-007, AC-055 a AC-057, AC-044 a AC-046) citados no código foi verificado com teste automatizado rodando contra SQLite; `ruff check`, `mypy --ignore-missing-imports` e `bandit -ll` limpos; migração testada com `alembic upgrade head` e `downgrade base`; `docker compose build api` validado com a nova dependência `pandas`. Escopo deliberadamente fora: matriz RBAC completa do FR-015 (só ADMIN/OPERADOR/AUDITOR testados em `/ativos`), mascaramento de `chave_licenca` (RI-08, NFR não listado no backlog 1.1–1.12), depreciação no corpo de resposta do ativo (depende de `utils/depreciacao.py`, Sprint 2) | R3 | *(preencher)* |
| 10 | 2026-09-27 | Claude | Auditoria nos cadastros de apoio: `app/services/categoria_service.py`, `fornecedor_service.py`, `setor_service.py`, `responsavel_service.py` (novos, `registrar_auditoria` no mesmo padrão de `ativo_service.py`) e os 4 routers correspondentes atualizados; `GET/PATCH /categorias/{id}` implementado (faltava, previsto em `docs/spec/contrato-api.md`) | Fechar a lacuna: `POST` de categoria/fornecedor/setor/responsável não registrava auditoria (violava AC-057/BR-030); pedido explícito de manter a chamada na mesma camada do padrão já usado em `ativo_service.py` (serviço, não router) | 25 testes existentes continuam verdes após a mudança; `ruff`/`mypy` limpos | R3 | *(preencher)* |
| 11 | 2026-09-27 | Claude | RBAC de `/importacoes`: `GET /importacoes`, `/importacoes/{id}`, `/importacoes/{id}/erros` abertos aos 4 perfis (antes só ADMIN/AUDITOR); `docs/spec/contrato-api.md` §6.6 e a matriz do FR-015 em `docs/prd/requisitos-funcionais.md` atualizadas (colunas "Setores" e "Importação" acrescentadas, sem renumerar FR/AC/BR) | Alinhar o contrato ao que fazia sentido pro papel de cada perfil (OPERADOR precisa ver erro da própria importação; GESTOR é "Ler" em tudo no FR-015, não fazia sentido ficar de fora só aqui) | **Decisão pausada:** a proposta de abrir `POST /importacoes` para ADMIN+OPERADOR foi barrada por contradizer `docs/prd/jornadas-historias.md` (US-031, US-032 — histórias de importação são explicitamente "Como Administrador de TI"). `POST /importacoes` continua ADMIN-only até a equipe decidir se reescreve as user stories ou mantém a restrição | R2 | *(preencher)* |
| 12 | 2026-09-27 | Claude | `app/core/database.py` (`flush_ou_conflito`, converte `IntegrityError` em 409 — faltava, `db.flush()` deixava violação de UNIQUE virar 500 não tratado); `tests/integration/test_cadastros.py` (CRUD/404/422/unicidade/auditoria de categoria, fornecedor, setor, responsável) e `tests/integration/test_seguranca.py` (matriz RBAC parametrizada dos 4 perfis × todas as rotas existentes, mais "sem token → 401" em todas); `token_gestor` novo em `conftest.py` | Fechar os dois itens pendentes do Sprint 1: testes de cadastro e matriz RBAC completa | Ao escrever o teste de duplicidade de cadastro, a resposta vinha 500 (exceção não tratada) em vez de 409 — bug real, corrigido antes de escrever o teste, não só documentado; suíte completa (47 testes) passando após a correção; `ruff`/`mypy`/`bandit` limpos | R3 | *(preencher)* |
| 13 | — | — | — | — | — | — | — |

---

## 4. O que a equipe produziu sem IA

Esta seção existe para deixar explícito o que é autoria direta, e é tão importante quanto a tabela acima.

| Item | Autor | Descrição |
|---|---|---|
| Escolha do tema (ITAM) e definição dos requisitos FR-001 a FR-007 | Equipe | Levantamento do problema e delimitação do escopo funcional |
| Decisão de adotar Python/FastAPI como stack | Equipe | Avaliação de domínio técnico disponível na equipe |
| *(preencher)* | | |

---

## 5. Falhas encontradas em saídas de IA

Registrar erros corrigidos é a evidência mais forte de que houve revisão real. Esta seção conta a favor na defesa.

| # | Artefato | Erro na saída original | Como foi detectado | Correção |
|---|---|---|---|---|
| 01 | `gerar_datasets.py` | Vínculos de responsável encerrando após a data de baixa do ativo | Validador de coerência referencial | Datas de baixa passaram a ser calculadas antes das transferências, servindo de limite superior |
| 02 | `gerar_datasets.py` | Índices de fornecedor deslocados: Microsoft 365 atribuído à Adobe | Inspeção manual da amostra de `licencas.csv` | Índices corrigidos na lista de softwares |
| 03 | *(preencher)* | | | |

---

## 6. Como preencher

Um registro por sessão de uso, não por mensagem trocada. O critério é: **gerou artefato que entrou no repositório?** Então registra.

Campos obrigatórios:

- **Artefato gerado** — caminho do arquivo, não descrição genérica;
- **O que foi pedido** — em uma linha, o objetivo, não o prompt literal;
- **Revisão humana aplicada** — o que foi *conferido* e contra o quê. "Revisado" não é revisão; "vida útil conferida contra a IN RFB 1.700" é;
- **Nível** — R1, R2 ou R3, conforme a seção 2;
- **Responsável** — quem assina a revisão e responde pelo artefato na defesa.

---

## 7. Política de autoria

1. Nenhum artefato entra no repositório sem um responsável nomeado neste registro.
2. Código gerado por IA passa obrigatoriamente por R3 — executado e testado — antes do commit.
3. Afirmação sobre norma, framework ou taxa legal é verificada na fonte primária. Modelos de linguagem erram números e confundem versões de norma com frequência suficiente para que isso seja regra, não precaução.
4. Se um integrante não consegue explicar um trecho na defesa, o trecho é reescrito ou removido antes da entrega.
5. Este documento é entregue junto com o projeto. Omitir uso de IA é mais grave do que usá-la.

---

*Documento exigido pelo Gate 0. Mantido atualizado ao longo de todas as sprints.*
# SPEC — Estrutura de Diretórios

Parte de [SPEC — ITAM](README.md).

## 4. Estrutura de Diretórios

A árvore mostra a estrutura-alvo. Todos os módulos listados estão implementados (Sprint 5 fechada); `FornecedorAvaliacao` mora em `models/fornecedor.py`.

```
itam-api/
├── python/                           # build context da imagem da API
│   ├── collectors/                   # um coletor por fonte pública (compras_gov, endoflife, nvd)
│   │   └── config.yaml               # códigos CATMAT e produtos monitorados
│   ├── etl/                          # normalização (dataset/raw → dataset/processed) e carga no banco
│   │   ├── paths.py                  # resolução de DATASET_DIR, compartilhada com collectors/
│   │   └── gerar_sinteticos.py       # gera as entidades via Mockaroo
│   ├── app/
│   │   ├── main.py                      # criação do app, routers, handlers, métricas
│   │   ├── seed.py                      # seed mínimo: usuários de demonstração e categorias (python -m app.seed)
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── exceptions.py
│   │   │   ├── metrics.py
│   │   │   ├── audit.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── base.py                  # DeclarativeBase, mixins de timestamp
│   │   │   ├── ativo.py
│   │   │   ├── categoria.py
│   │   │   ├── fornecedor.py
│   │   │   ├── responsavel.py
│   │   │   ├── setor.py
│   │   │   ├── licenca.py               # Licenca, LicencaVinculo
│   │   │   ├── historico.py             # HistoricoTransferencia (append-only)
│   │   │   ├── baixa.py                 # BaixaAtivo (append-only)
│   │   │   ├── importacao.py            # LoteImportacao, ErroImportacao
│   │   │   ├── risco.py                 # Risco (score gerado pelo banco)
│   │   │   ├── recomendacao.py          # Recomendacao, Evidencia
│   │   │   ├── usuario.py
│   │   │   └── auditoria.py             # AuditLog (append-only)
│   │   ├── schemas/                     # um módulo por agregado (ativo, baixa, licenca, ...)
│   │   ├── repositories/            # vazio (.gitkeep): sem camada de repositório, ver arquitetura.md §2.1
│   │   ├── services/
│   │   │   ├── ativo_service.py
│   │   │   ├── categoria_service.py
│   │   │   ├── fornecedor_service.py
│   │   │   ├── setor_service.py
│   │   │   ├── responsavel_service.py
│   │   │   ├── depreciacao_service.py
│   │   │   ├── importacao_service.py
│   │   │   ├── licenca_service.py
│   │   │   ├── baixa_service.py
│   │   │   ├── relatorio_service.py     # inventário filtrado e relatório de conformidade, CSV/XLSX
│   │   │   ├── compliance_service.py    # alertas CP-01 a CP-04, derivados na hora
│   │   │   ├── indicador_service.py     # indicadores do FR-009 com fórmula e amostra
│   │   │   ├── observabilidade_service.py # saúde do banco e gauges de /metrics
│   │   │   ├── cenario_service.py       # comparação de cenários e TCO (só calcula)
│   │   │   ├── scorecard_service.py     # scorecard de fornecedores (BR-029)
│   │   │   ├── risco_service.py         # registro de riscos
│   │   │   └── recomendacao_service.py  # recomendação com evidência (BR-027)
│   │   ├── api/
│   │   │   ├── deps.py                  # get_db, get_current_user, require_perfil
│   │   │   ├── tecnico.py               # /health e /metrics (públicos, fora de /api/v1)
│   │   │   └── v1/
│   │   │       ├── router.py            # agregador
│   │   │       └── routers/             # existem: auth, categorias, fornecedores (inclui o scorecard), setores, responsaveis, ativos, importacoes, licencas, relatorios, compliance, indicadores, riscos, cenarios, recomendacoes (a baixa é POST /ativos/{id}/baixa, em ativos.py)
│   │   └── utils/
│   │       ├── depreciacao.py
│   │       ├── datas.py                 # hoje(): relógio injetável nos serviços
│   │       ├── mascaramento.py          # chave de licença mascarada (RI-08)
│   │       ├── risco.py                 # score e classificação (função pura)
│   │       ├── scorecard.py             # pontuação ponderada e ranking (BR-029)
│   │       ├── cenario.py               # TCO de 5 anos e ordenação (BR-028)
│   │       ├── conformidade.py          # CP-01 a CP-04 e status de conformidade (função pura)
│   │       ├── indicadores.py           # fórmulas dos indicadores (funções puras)
│   │       └── exportacao.py            # CSV/XLSX, com cabeçalho datado
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/                        # funções puras e serviços
│   │   ├── integration/                 # API + banco
│   │   ├── contract/                    # validação contra openapi.yaml
│   │   └── fixtures/                    # respostas gravadas das APIs, para testes de collectors/
│   ├── api/openapi.yaml                 # contrato congelado, usado nos testes
│   ├── Dockerfile
│   ├── entrypoint.sh                    # contêiner da API: alembic upgrade head e depois uvicorn
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   └── ruff.toml
├── dataset/                          # DATASET_DIR: montado em /dataset no contêiner da API
│   ├── demo/inventario_demo.csv      # modelo de importação manual (FR-008)
│   ├── raw/<fonte>/<data>/           # resposta original das APIs, imutável
│   ├── processed/                    # dados normalizados, prontos para carga
│   └── synthetic/                    # CSVs e esquemas do Mockaroo (versionados)
│       └── schemas/
├── scripts/
│   ├── start.sh
│   ├── stop.sh
│   ├── reset.sh
│   ├── seed.sh                       # alembic upgrade head + python -m app.seed (usuários de demonstração e categorias); carga de dataset/ pendente (D.9)
│   ├── collect.sh                    # coleta + normalização de todas as fontes públicas
│   └── smoke_test.sh
├── infra/
│   ├── prometheus.yml
│   └── grafana/
│       ├── datasources/prometheus.yml
│       └── dashboards/               # provider.yml e itam.json (dashboard técnico)
├── docs/
│   ├── prd/                          # dividido por responsabilidade, ver docs/prd/README.md
│   ├── spec/                         # este documento, dividido por responsabilidade
│   ├── modelo-de-dados/              # dividido por responsabilidade, ver docs/modelo-de-dados/README.md
│   ├── ARQUITETURA.md                # arquivo único, não dividido
│   ├── FONTES_DE_DADOS.md
│   ├── CRITERIOS_DE_ACEITE.md
│   ├── REGISTRO_USO_DE_IA.md
│   ├── BACKLOG_E_GATES.md
│   ├── guia/                         # execução local, coleta de dados, testes etc. — ver README.md da raiz
│   └── adr/                          # ADR-011 em diante; ADR-001 a ADR-010 resumidas em docs/spec/adrs-e-rastreabilidade.md
├── docker-compose.yml
├── .env.example
├── README.md
└── SPEC.md
```


# SPEC — Estrutura de Diretórios

Parte de [SPEC — ITAM](README.md).

## 4. Estrutura de Diretórios

```
itam-api/
├── collectors/                       # um coletor por fonte pública (compras_gov, endoflife, nvd)
│   └── config.yaml                   # códigos CATMAT e produtos monitorados
├── etl/                              # normalização (data/raw → data/processed) e carga no banco
├── app/
│   ├── main.py                      # criação do app, routers, handlers, métricas
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── metrics.py
│   │   ├── audit.py
│   │   └── logging.py
│   ├── models/
│   │   ├── base.py                  # DeclarativeBase, mixins de timestamp
│   │   ├── ativo.py
│   │   ├── categoria.py
│   │   ├── fornecedor.py
│   │   ├── responsavel.py
│   │   ├── setor.py
│   │   ├── licenca.py
│   │   ├── historico.py             # HistoricoTransferencia (append-only)
│   │   ├── baixa.py                 # BaixaAtivo (append-only)
│   │   ├── importacao.py            # LoteImportacao, ErroImportacao
│   │   ├── risco.py
│   │   ├── recomendacao.py          # Recomendacao, Evidencia
│   │   ├── usuario.py
│   │   └── auditoria.py             # AuditLog (append-only)
│   ├── schemas/                     # um módulo por agregado
│   ├── repositories/
│   ├── services/
│   │   ├── ativo_service.py
│   │   ├── responsavel_service.py
│   │   ├── depreciacao_service.py
│   │   ├── licenca_service.py
│   │   ├── baixa_service.py
│   │   ├── relatorio_service.py
│   │   ├── compliance_service.py
│   │   ├── indicador_service.py
│   │   ├── importacao_service.py
│   │   ├── cenario_service.py
│   │   ├── scorecard_service.py
│   │   ├── risco_service.py
│   │   └── recomendacao_service.py
│   ├── api/
│   │   ├── deps.py                  # get_db, get_current_user, require_perfil
│   │   └── v1/
│   │       ├── router.py            # agregador
│   │       └── routers/
│   └── utils/
│       ├── depreciacao.py
│       ├── datas.py
│       └── exportacao.py            # CSV/XLSX
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── unit/                        # funções puras e serviços
│   ├── integration/                 # API + banco
│   ├── contract/                    # validação contra openapi.yaml
│   └── fixtures/                    # respostas gravadas das APIs, para testes de collectors/
├── data/
│   ├── raw/<fonte>/<data>/           # resposta original das APIs, imutável
│   ├── processed/                    # dados normalizados, prontos para carga
│   ├── synthetic/                    # CSVs e esquemas do Mockaroo (versionados)
│   │   └── schemas/
│   └── inventario_demo.csv           # modelo de importação manual (FR-008)
├── scripts/
│   ├── start.sh
│   ├── stop.sh
│   ├── reset.sh
│   ├── seed.sh
│   ├── collect.sh                    # coleta + normalização de todas as fontes públicas
│   ├── gerar_sinteticos.py           # gera as entidades via Mockaroo
│   └── smoke_test.sh
├── docker/
│   ├── prometheus/prometheus.yml
│   └── grafana/provisioning/
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
├── api/openapi.yaml                 # contrato congelado, usado nos testes
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── pytest.ini
├── ruff.toml
├── README.md
└── SPEC.md
```


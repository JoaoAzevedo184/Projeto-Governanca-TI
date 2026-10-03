# ITAM — Gestão de Ativos de TI

Sistema de apoio à governança do parque tecnológico: inventário de hardware e software, cadeia de responsabilidade, depreciação patrimonial e alertas de conformidade — construído sobre **dados públicos reais** sempre que eles existem.

Projeto da disciplina **Governança de TI** — Bacharelado em Sistemas de Informação, UNINASSAU Olinda.

```
Python 3.12  ·  FastAPI  ·  SQLAlchemy 2.0  ·  PostgreSQL 16  ·  httpx  ·  Docker  ·  Prometheus + Grafana
```

---

## Sobre o projeto

O ITAM é uma **camada de orquestração, análise e apoio à decisão** sobre os dados de ativos da organização. Não é um sistema de descoberta automática de inventário, nem um ERP patrimonial, nem um substituto de plataformas comerciais de ITAM.

Ele resolve cinco problemas concretos:

| Problema | Resposta do sistema |
|---|---|
| Inventário espalhado em planilhas divergentes | Base única com importação validada de CSV/XLSX |
| Equipamentos sem responsável identificado | Vínculo obrigatório com histórico imutável de transferências |
| Licenças usadas acima do contratado | Bloqueio preventivo e alerta de excedente |
| Valor patrimonial congelado no valor de compra | Depreciação linear calculada automaticamente |
| Descarte sem rastreabilidade | Baixa com motivo, data e destinação registrados |

### Princípios estruturantes

1. **Nenhuma recomendação sem evidência.** Uma decisão registrada no sistema exige ao menos um dado verificável que a sustente.
2. **A decisão é humana.** O sistema ordena alternativas por custo e risco; nunca escolhe por você.
3. **O histórico não se apaga.** Transferências, baixas e auditoria são *append-only*, garantido no banco. O trigger existe nas três tabelas (transferências, auditoria e baixas).
4. **Todo dado declara sua origem.** Cada registro carrega o campo `data_source`; a fronteira entre dado real e dado sintético é consultável, nunca implícita.

---

## Origem dos dados

A base de demonstração privilegia **fontes públicas e oficiais** — Compras.gov.br, endoflife.date e NVD — e usa dado sintético apenas onde não existe, e não deveria existir, dado público: pessoas e eventos internos da organização fictícia (LGPD). Toda tabela principal carrega `data_source` (`compras_gov`, `endoflife`, `nvd`, `sintetico`, `importacao`), tornando a fronteira real × sintético consultável:

```sql
SELECT data_source, COUNT(*) FROM ativos GROUP BY data_source;
```

Detalhamento fonte a fonte, regras de uso e conformidade com a LGPD em [`docs/FONTES_DE_DADOS.md`](docs/FONTES_DE_DADOS.md).

---

## Funcionalidades

| Código | Funcionalidade |
|---|---|
| FR-001 | Cadastro de ativos de hardware e software |
| FR-002 | Vinculação de responsável com histórico de transferências |
| FR-003 | Cálculo de depreciação linear e valor residual |
| FR-004 | Controle de licenças com alerta de excedente e de vencimento |
| FR-005 | Baixa e descarte com motivo, data e destinação |
| FR-006 | Relatório de inventário com filtros combináveis e exportação |
| FR-007 | Painel de alertas de compliance |
| FR-008 | Importação de inventário em CSV/XLSX com relatório de erros |
| FR-009 | Indicadores de ITAM |
| FR-010 | Comparação de cenários com TCO de 5 anos |
| FR-011 | Scorecard ponderado de fornecedores |
| FR-012 | Registro de riscos com score probabilidade × impacto |
| FR-013 | Recomendações rastreáveis vinculadas a evidências |
| FR-014 | Dashboard gerencial e observabilidade técnica |
| FR-015 | Autenticação JWT e controle de acesso por perfil |

---

## Pré-requisitos

**Execução com Docker (recomendada):**
- Docker Engine 24+
- Docker Compose v2

**Execução local sem Docker:**
- Python 3.12+
- pip e venv

**Coleta de dados (opcional):**
- Acesso à internet
- Chave de API do NVD (gratuita, recomendada — sem ela o NVD aplica limite de requisições mais restrito). Solicite em https://nvd.nist.gov/developers/request-an-api-key e defina `NVD_API_KEY` no `.env`.

> A coleta **não é necessária** para executar o projeto: o repositório já inclui os datasets processados em `dataset/processed/`. O seed atual **não** os carrega: ele cria só os usuários de demonstração e as categorias (a carga do pipeline é a pendência D.9 do [`ROADMAP.md`](docs/ROADMAP.md)).

---

## Execução rápida com Docker

```bash
git clone <url-do-repositorio> itam-api
cd itam-api
cp .env.example .env
docker compose up -d
```

Aguarde os health checks ficarem saudáveis e carregue o seed mínimo (migrações, os quatro usuários de demonstração e as 11 categorias). Com a API no ar, o script roda dentro do contêiner `api`; as senhas vêm das variáveis `SEED_*_PASSWORD` do `.env`:

```bash
./scripts/seed.sh
```

### Endereços do ambiente

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Documentação interativa (Swagger) | http://localhost:8000/docs |
| Documentação alternativa (ReDoc) | http://localhost:8000/redoc |
| Contrato OpenAPI | http://localhost:8000/openapi.json |
| Health check | http://localhost:8000/health |
| Métricas | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

**Credenciais didáticas do Grafana:** definidas em `.env` (`GRAFANA_USER` / `GRAFANA_PASSWORD`). Altere-as em qualquer ambiente que não seja exclusivamente laboratorial.

**Usuários de demonstração** criados pelo seed — senhas nas variáveis `SEED_ADMIN_PASSWORD`, `SEED_OPERADOR_PASSWORD`, `SEED_GESTOR_PASSWORD` e `SEED_AUDITOR_PASSWORD` do `.env`, para uso apenas em laboratório. O seed é idempotente (rodar de novo não duplica nem altera o que já existe) e recusa rodar com `ENVIRONMENT=producao`:

| Login | Perfil | Pode |
|---|---|---|
| `admin` | ADMIN | tudo |
| `operador` | OPERADOR | cadastrar ativos, transferir, registrar manutenção |
| `gestor` | GESTOR | consultar e comparar cenários |
| `auditor` | AUDITOR | somente leitura |

---

Execução local sem Docker, coleta de dados reais (`python/collectors/`/`python/etl/`), verificação da instalação, importação de inventário próprio, testes e scripts operacionais estão detalhados em [`docs/guia/`](docs/guia/README.md).

Os testes rodam sempre contra PostgreSQL 16: suba o banco com `docker compose up -d db` antes do `pytest` (detalhes em [`docs/guia/testes.md`](docs/guia/testes.md)).

---

## Estrutura do repositório

```
python/
├── app/
│   ├── main.py           # aplicação, routers, handlers, métricas
│   ├── core/             # config, banco, segurança, exceções, auditoria
│   ├── models/           # mapeamento SQLAlchemy
│   ├── schemas/          # contratos Pydantic
│   ├── repositories/     # vazio (.gitkeep): não há camada de repositório
│   ├── services/         # regras de negócio (BR-001 a BR-037)
│   ├── api/v1/routers/   # endpoints
│   └── utils/            # cálculos puros (depreciação, exportação)
├── python/collectors/           # um coletor por fonte pública (compras_gov, endoflife, nvd)
├── python/etl/                  # normalização e carga no banco
├── alembic/              # migrações versionadas
├── tests/                # unit, integration, contract, fixtures das APIs
└── api/openapi.yaml      # contrato congelado, usado nos testes de contrato

dataset/
├── demo/inventario_demo.csv
├── raw/              # respostas originais das APIs, por fonte e data (imutável)
├── processed/        # dados normalizados, prontos para carga
└── synthetic/        # CSVs e esquemas do Mockaroo (versionados)

scripts/              # operação do ambiente
infra/                # configuração de Prometheus e Grafana
docs/                 # PRD, arquitetura, modelo de dados, ADRs
```

A regra de dependência entre camadas é unidirecional: router → serviço → modelo. Não existe camada de repositório: os serviços consultam e gravam pela `Session` do SQLAlchemy, direto nos modelos. Leituras sem regra de negócio também acessam o modelo direto, sem passar por serviço: as listagens de `categorias`, `fornecedores`, `setores` e `responsaveis`, o login (`auth.py`), as consultas de lote e de erros em `importacoes.py` e a dependência `get_current_user` (`api/deps.py`). Regra de negócio (BR) vive em `services/`, nunca em `routers/` nem em `models/`; os únicos desvios nos routers são autenticação, autorização e 404. Os módulos `python/collectors/` e `python/etl/` ficam fora de `app/`: a API nunca chama APIs externas durante uma requisição.

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/prd/`](docs/prd/README.md) | Visão de produto, personas, requisitos, regras de negócio, critérios de aceite |
| [`docs/spec/`](docs/spec/README.md) | Arquitetura, modelo físico, contrato da API, cálculos, testes, ADRs resumidas |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | Visão de arquitetura detalhada |
| [`docs/modelo-de-dados/`](docs/modelo-de-dados/README.md) | Diagrama e dicionário de dados |
| [`docs/FONTES_DE_DADOS.md`](docs/FONTES_DE_DADOS.md) | Fontes, endpoints, regras de normalização e fronteira real × sintético |
| [`docs/adr/`](docs/adr/) | Registros de decisão arquitetural completos (ADR-011 em diante) |
| [`docs/guia/`](docs/guia/README.md) | Execução local, coleta de dados, verificação, importação, testes, scripts, troubleshooting, contribuição, equipe/IA |
| [`docs/BACKLOG_E_GATES.md`](docs/BACKLOG_E_GATES.md) | Planejamento de execução por gate |
| [`docs/CRITERIOS_DE_ACEITE.md`](docs/CRITERIOS_DE_ACEITE.md) | Critérios de avaliação da disciplina |
| [`docs/REGISTRO_USO_DE_IA.md`](docs/REGISTRO_USO_DE_IA.md) | Registro de uso de ferramentas de IA no projeto |
| `/docs` (runtime) | Documentação interativa da API, gerada automaticamente |

Todo requisito possui identificador estável (`FR-`, `BR-`, `AC-`, `NFR-`, `US-`, `KPI-`). Esses identificadores aparecem em comentários do código, nomes de testes e no campo `regra` das respostas de erro da API — cada família vive inteira em um único arquivo dentro de `docs/prd/`, para continuar localizável por busca.

---

## Licença

Projeto acadêmico, sem fins comerciais. Uso educacional.

Os dados coletados pertencem às respectivas fontes: Compras.gov.br (dados abertos do Governo Federal), endoflife.date (licença MIT) e NVD/NIST (domínio público). Dados sintéticos gerados com Mockaroo não representam pessoas reais.

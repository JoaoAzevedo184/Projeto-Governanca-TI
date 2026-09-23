# ITAM — Gestão de Ativos de TI

Sistema de apoio à governança do parque tecnológico: inventário de hardware e software, cadeia de responsabilidade, depreciação patrimonial e alertas de conformidade.

Projeto da disciplina **Governança de TI** — Bacharelado em Sistemas de Informação, UNINASSAU Olinda.

```
Python 3.12  ·  FastAPI  ·  SQLAlchemy 2.0  ·  PostgreSQL 16  ·  Docker  ·  Prometheus + Grafana
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
3. **O histórico não se apaga.** Transferências, baixas e auditoria são *append-only*, garantido no banco.

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

---

## Execução rápida com Docker

```bash
git clone <url-do-repositorio> itam-api
cd itam-api
cp .env.example .env
docker compose up -d
```

Aguarde os health checks ficarem saudáveis e carregue os dados de demonstração:

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

**Usuários de demonstração** criados pelo seed — senhas no `.env`, para uso apenas em laboratório:

| Login | Perfil | Pode |
|---|---|---|
| `admin` | ADMIN | tudo |
| `operador` | OPERADOR | cadastrar ativos, transferir, registrar manutenção |
| `gestor` | GESTOR | consultar e comparar cenários |
| `auditor` | AUDITOR | somente leitura |

---

## Execução local sem Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env               # DATABASE_URL já aponta para SQLite

alembic upgrade head
python -m scripts.seed

uvicorn app.main:app --reload --port 8000
```

O perfil local usa **SQLite**, sem necessidade de banco externo. O perfil Docker usa **PostgreSQL**. A seleção é feita pela variável `DATABASE_URL`.

---

## Verificando a instalação

```bash
./scripts/smoke_test.sh
```

O script verifica, em sequência: health da API, disponibilidade do banco, endpoint de indicadores, endpoint de métricas, saúde do Prometheus e saúde do Grafana. Saída diferente de zero indica ambiente incompleto.

Verificação manual mínima:

```bash
# 1. Autenticar
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","senha":"admin"}' | jq -r .access_token)

# 2. Listar ativos
curl -s http://localhost:8000/api/v1/ativos \
  -H "Authorization: Bearer $TOKEN" | jq '.total'

# 3. Consultar indicadores
curl -s http://localhost:8000/api/v1/indicadores \
  -H "Authorization: Bearer $TOKEN" | jq '.indicadores[] | {codigo, nome, valor}'

# 4. Ver alertas de compliance
curl -s http://localhost:8000/api/v1/compliance/alertas \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {codigo, severidade, descricao}'
```

---

## Importando seu próprio inventário

```bash
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@meu_inventario.xlsx"
```

O arquivo deve conter as colunas `nome`, `tipo`, `categoria`, `fornecedor`, `numero_serie` ou `chave_licenca`, `data_aquisicao` e `valor_compra`. Veja `data/inventario_demo.csv` como modelo.

Linhas inválidas **não impedem** a importação das demais. Para consultar o que foi rejeitado:

```bash
curl -s http://localhost:8000/api/v1/importacoes/1/erros \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Testes

```bash
pip install -r requirements-dev.txt

pytest                              # suíte completa
pytest tests/unit -v                # apenas unitários
pytest --cov=app --cov-report=term-missing
pytest -k "test_ac015"              # um critério de aceite específico
```

Cada teste carrega o identificador do critério que valida (`test_ac015_...`, `test_ac021_...`), de modo que a matriz de rastreabilidade entre a especificação e o código é verificável por comando:

```bash
pytest --collect-only -q | grep -c "test_ac"
```

Cobertura mínima exigida: **70% global**, **100%** em `app/utils/` e `app/services/`.

---

## Scripts operacionais

| Script | Ação |
|---|---|
| `./scripts/start.sh` | Sobe todo o ambiente |
| `./scripts/stop.sh` | Encerra os contêineres preservando os dados |
| `./scripts/reset.sh` | Remove contêineres, redes e **volumes** — apaga os dados |
| `./scripts/seed.sh` | Carrega categorias, usuários e datasets de demonstração |
| `./scripts/smoke_test.sh` | Verifica se o ambiente subiu corretamente |

> `reset.sh` elimina dados persistidos. Use apenas em ambiente de laboratório.

Acompanhar logs:

```bash
docker compose logs -f              # todos os serviços
docker compose logs -f api          # apenas a API
```

---

## Estrutura do repositório

```
app/
├── main.py           # aplicação, routers, handlers, métricas
├── core/             # config, banco, segurança, exceções, auditoria
├── models/           # mapeamento SQLAlchemy
├── schemas/          # contratos Pydantic
├── repositories/     # acesso a dados
├── services/         # regras de negócio (BR-001 a BR-030)
├── api/v1/routers/   # endpoints
└── utils/            # cálculos puros (depreciação, exportação)

alembic/              # migrações versionadas
tests/                # unit, integration, contract
data/                 # datasets de demonstração
scripts/              # operação do ambiente
docker/               # configuração de Prometheus e Grafana
docs/                 # PRD, arquitetura, modelo de dados, ADRs
api/openapi.yaml      # contrato congelado, usado nos testes de contrato
```

A regra de dependência entre camadas é unidirecional: router → serviço → repositório → modelo. Regra de negócio vive em `services/`, nunca em `routers/` nem em `models/`.

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Visão de produto, personas, requisitos, regras de negócio, critérios de aceite |
| [`docs/SPEC.md`](docs/SPEC.md) | Arquitetura, modelo físico, contrato da API, cálculos, testes, ADRs |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | Visão de arquitetura detalhada |
| [`docs/MODELO_DE_DADOS.md`](docs/MODELO_DE_DADOS.md) | Diagrama e dicionário de dados |
| [`docs/adr/`](docs/adr/) | Registros de decisão arquitetural |
| `/docs` (runtime) | Documentação interativa da API, gerada automaticamente |

Todo requisito possui identificador estável (`FR-`, `BR-`, `AC-`, `NFR-`, `US-`, `KPI-`). Esses identificadores aparecem em comentários do código, nomes de testes e no campo `regra` das respostas de erro da API.

---

## Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `docker compose up` falha na porta 8000 | Porta ocupada | Altere `API_PORT` no `.env` |
| API sobe mas `/health` retorna banco `DOWN` | Postgres ainda inicializando | Aguarde o health check; verifique `docker compose logs db` |
| `alembic upgrade head` falha | `DATABASE_URL` incorreta | Confira o `.env`; em Docker o host é `db`, não `localhost` |
| Aplicação recusa iniciar com erro de `SECRET_KEY` | Chave padrão fora do ambiente local | Defina `SECRET_KEY` própria quando `ENVIRONMENT != local` |
| Importação retorna 422 antes de processar | Cabeçalhos divergentes | Compare com `data/inventario_demo.csv` |
| Grafana sem dados | Prometheus não alcança a API | Verifique `docker/prometheus/prometheus.yml` e `docker compose logs prometheus` |
| Testes falham só em PostgreSQL | Índice parcial ou trigger ausente | Rode `alembic upgrade head` no banco de teste |
| HTTP 403 em operação esperada | Perfil sem permissão | Consulte a matriz do FR-015 no PRD |

---

## Contribuição

**Branches:** `main` protegida; trabalho em `feat/`, `fix/` ou `docs/`.

**Commits:** padrão Conventional Commits, referenciando o requisito.

```
feat(ativos): implementa bloqueio de número de série duplicado (FR-001, BR-001)
fix(depreciacao): corrige arredondamento para half-up (BR-017)
test(licencas): cobre AC-021 — excedente de quantitativo
```

**Definition of Done:** testes do critério passando · migração aplicada e reversível · `openapi.yaml` regenerado · `ruff check` limpo · README atualizado se a forma de execução mudou.

---

## Equipe e política de uso de IA

| Nome | Papel |
|---|---|
| *(preencher)* | Product Owner |
| *(preencher)* | Arquitetura e backend |
| *(preencher)* | Dados e indicadores |
| *(preencher)* | Infraestrutura e observabilidade |
| *(preencher)* | Documentação e qualidade |

O uso de ferramentas de IA na construção deste projeto é permitido e deve ser registrado em `docs/REGISTRO_USO_IA.md`, conforme a política da disciplina: ferramenta utilizada, artefato gerado, natureza da revisão humana aplicada. Código e documentação gerados com apoio de IA são de responsabilidade integral da equipe, e cada integrante deve ser capaz de explicar qualquer trecho na defesa.

---

## Licença

Projeto acadêmico, sem fins comerciais. Uso educacional.
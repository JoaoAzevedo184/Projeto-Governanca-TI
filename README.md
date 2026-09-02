# Projeto 3 — Observabilidade e Operação Híbrida

MVP de apoio à governança operacional para datacenter, filiais e cloud. A solução importa
eventos, mede MTTD/MTTR, identifica ruído e duplicidade, avalia acionabilidade, gerencia
SLI/SLO e error budget, associa owner e runbook, calcula custo de telemetria e produz
recomendação de tuning rastreável.

Stack: **Python (FastAPI)**, com Prometheus e Grafana para observabilidade da própria API.

## Estrutura

```
.
├── spec.md              # Especificação do MVP (contexto, funções, regras, metas)
├── docs/                # Arquitetura, modelo de dados, backlog/gates, critérios de aceite
├── material_aluno/      # Guia do aluno, checklist e rubrica de avaliação
├── datasets/            # Dados de demonstração (alertas, custos, riscos, SLOs)
├── python/              # API FastAPI — código, testes e Dockerfile
├── infra/               # Configuração de Prometheus e provisionamento do Grafana
├── scripts/             # Automação da stack (wait, load, smoke, reset)
├── docker-compose.yml   # Orquestração de API, Prometheus e Grafana
└── .env.example         # Variáveis de ambiente (copiar para .env)
```

## Execução com Docker

```bash
cp .env.example .env
docker compose up --build -d
./scripts/wait-for-stack.sh
./scripts/load-demo-data.sh
./scripts/smoke-test.sh
```

Para derrubar a stack e remover os volumes: `./scripts/reset.sh`.

## Execução local

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
pytest -q
```

## Endereços

| Serviço    | URL                            |
|------------|--------------------------------|
| API        | http://localhost:8101/docs     |
| Prometheus | http://localhost:9092          |
| Grafana    | http://localhost:3002          |

## Endpoints

| Método | Rota                                 | Descrição                                  |
|--------|--------------------------------------|--------------------------------------------|
| GET    | `/health`                            | Health check                               |
| GET    | `/metrics`                           | Métricas no formato Prometheus             |
| POST   | `/api/v1/imports/events`             | Importa eventos a partir de CSV            |
| GET    | `/api/v1/kpis`                       | KPIs, com filtros `service` e `severity`   |
| POST   | `/api/v1/slos`                       | Cadastra SLO e calcula error budget        |
| GET    | `/api/v1/slos`                       | Lista os SLOs cadastrados                  |
| POST   | `/api/v1/costs/compare`              | Compara custo de cenários de telemetria    |
| POST   | `/api/v1/tuning/recommendations`     | Registra recomendação de tuning            |

O estado é mantido em memória: reiniciar a API zera eventos e SLOs.

## Datasets

Os CSVs em `datasets/` trazem BOM, um preâmbulo de título/descrição antes do cabeçalho e
uma coluna vazia à esquerda. O parser (`rows_from_csv`, em `python/app/main.py`) trata esse
formato. O `dashboard_referencia.csv` contém o baseline esperado dos KPIs e serve de
oráculo para os testes.

## Documentação

- [Especificação](spec.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Modelo de dados](docs/MODELO_DE_DADOS.md)
- [Backlog e gates](docs/BACKLOG_E_GATES.md)
- [Critérios de aceite](docs/CRITERIOS_DE_ACEITE.md)
- [Guia do aluno](material_aluno/GUIA_DO_ALUNO.md) · [Checklist](material_aluno/CHECKLIST.md) · [Rubrica](material_aluno/RUBRICA.md)

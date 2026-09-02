# Projeto 3 — Observabilidade e Operação Híbrida

MVP de apoio à governança operacional para datacenter, filiais e cloud. A solução importa
eventos, mede MTTD/MTTR, identifica ruído e duplicidade, avalia acionabilidade, gerencia
SLI/SLO e error budget, associa owner e runbook, calcula custo de telemetria e produz
recomendação de tuning rastreável.

## Estrutura

```
.
├── spec.md              # Especificação do MVP (contexto, funções, regras, metas)
├── docs/                # Arquitetura, modelo de dados, backlog/gates, critérios de aceite
├── material_aluno/      # Guia do aluno, checklist e rubrica de avaliação
├── datasets/            # Dados de demonstração (alertas, custos, riscos, SLOs)
├── python/              # API FastAPI (porta interna 8080)
├── java/                # API Spring Boot (porta interna 8080)
├── infra/               # Configuração de Prometheus e provisionamento do Grafana
├── scripts/             # Automação da stack (wait, load, smoke, reset)
├── docker-compose.yml   # Orquestração das quatro peças
└── .env.example         # Variáveis de ambiente (copiar para .env)
```

## Execução integrada

```bash
cp .env.example .env
docker compose up --build -d
./scripts/wait-for-stack.sh
./scripts/load-demo-data.sh
./scripts/smoke-test.sh
```

Para derrubar a stack e remover os volumes: `./scripts/reset.sh`.

## Endereços

| Serviço    | URL                                    |
|------------|----------------------------------------|
| Python     | http://localhost:8101/docs             |
| Java       | http://localhost:8102/swagger-ui.html  |
| Prometheus | http://localhost:9092                  |
| Grafana    | http://localhost:3002                  |

## Execução local (sem Docker)

- **Python** — `cd python && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8080`; testes com `pytest -q`. Detalhes em [`python/README.md`](python/README.md).
- **Java** — `cd java && mvn spring-boot:run` (Java 21 e Maven 3.9+); testes com `mvn test`. Detalhes em [`java/README.md`](java/README.md).

## Documentação

- [Especificação](spec.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Modelo de dados](docs/MODELO_DE_DADOS.md)
- [Backlog e gates](docs/BACKLOG_E_GATES.md)
- [Critérios de aceite](docs/CRITERIOS_DE_ACEITE.md)
- [Guia do aluno](material_aluno/GUIA_DO_ALUNO.md) · [Checklist](material_aluno/CHECKLIST.md) · [Rubrica](material_aluno/RUBRICA.md)

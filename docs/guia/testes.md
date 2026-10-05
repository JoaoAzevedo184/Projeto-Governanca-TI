# Guia — Testes

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Testes

`audit_log` e `baixa_ativo` recusam UPDATE e DELETE por trigger: a limpeza entre testes é `TRUNCATE` (não aciona trigger de linha), e um teste não pode apagar linhas de auditoria nem de baixa; para isolar o que a operação gravou, compare os `id` antes e depois.

A suíte inteira roda contra **PostgreSQL 16**, nunca SQLite: trigger de imutabilidade, índice único parcial e `CHECK` só se comportam como em produção no banco real. Localmente o banco de teste é o `itam_test`, no mesmo contêiner `db` do `docker-compose` (criado por `infra/postgres/init/` na primeira subida); no CI é um *service container* do GitHub Actions.

```bash
docker compose up -d db
# volume postgres_data criado antes do script de init? crie o banco uma vez:
docker compose exec db createdb -U itam itam_test

cd python
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

Os testes dos coletores usam respostas gravadas das APIs (fixtures em `tests/fixtures/`) e **não acessam a internet**.

Cobertura mínima exigida: **70% global**, **100%** em `app/utils/` e `app/services/`.

**Nomes de arquivo de teste são únicos na árvore** (`tests/unit` e `tests/integration` não têm `__init__.py`): dois `test_x.py` com o mesmo nome derrubam a coleta com "import file mismatch". Por isso o teste de API dos indicadores é `test_indicadores_api.py`, ao lado de `tests/unit/test_indicadores.py`.

**Fábricas do `conftest.py`:** `novo_ativo(tipo=..., data_aquisicao=..., valor=...)` e `nova_licenca(quantidade=..., expiracao=..., inicio=...)` criam registros pela API e devolvem o id. Datas relativas a hoje (compliance, relatórios) são calculadas no teste a partir de `date.today()`; os limites exatos ficam nos testes unitários das funções puras, com data de referência injetada.

**Métricas nos testes:** os contadores do Prometheus são globais ao processo e não zeram entre testes. Compare o valor antes e depois da operação (`REGISTRY.get_sample_value`), nunca o valor absoluto.

**Testes de contrato (`tests/contract/`):** `test_contrato_schemathesis.py` gera requisições a partir do `api/openapi.yaml` e valida as respostas do app real (ASGI, PostgreSQL de teste) em todas as operações, com o token de um ADMIN. Dez exemplos por operação e semente fixa (`CONTRATO_EXEMPLOS=N` muda), cerca de 2 minutos. Checks ligados: erro de servidor, código de status e tipo de conteúdo documentados, schema da resposta, cabeçalhos e autenticação ignorada. Desligados, de propósito: `positive_data_acceptance` e `negative_data_rejection` (ver o ROADMAP, "Achados dos testes de contrato"). `test_openapi_sincronizado.py` garante que o arquivo é igual ao gerado pelo app: depois de mudar uma rota, regenere o `openapi.yaml` (ver [`contribuicao.md`](contribuicao.md)). A dependência é `schemathesis==4.10.2` no `requirements-dev.txt`, a última versão compatível com o `pytest==8.3.4` fixado.

**Smoke test do ambiente completo:** `docker compose up -d --build`, `./scripts/seed.sh` e `./scripts/smoke_test.sh` (ver [`verificacao.md`](verificacao.md)).

O banco usado vem de `TEST_DATABASE_URL` (padrão `postgresql+psycopg://itam:itam@localhost:5432/itam_test`). O `tests/conftest.py` aplica `alembic upgrade head` uma vez por sessão (o schema nunca vem de `create_all`) e trunca todas as tabelas antes de cada teste. Por segurança, recusa qualquer banco cujo nome não termine em `_test`.

## Convenção contra falso positivo

Todo teste novo ou alterado segue os critérios do item 15 de `RESOLUCAO_PENDENCIAS_SPRINT2.md`:

- **Banco real:** sem mock de banco, de sessão ou de exceção do banco. Conflitos de concorrência são provocados com uma segunda conexão real (ver `test_responsavel_vinculo.py`).
- **Efeito, não só status:** além do código HTTP, o teste consulta o banco (linha criada, vínculo encerrado, auditoria gravada ou não).
- **Ver o teste falhar:** para cada BR/AC, quem implementa quebra a regra no código uma vez, confirma que o teste falha e registra isso no resumo da entrega.
- **Valores à mão:** o esperado de um cálculo é escrito como conta no próprio teste (ex.: `6000 × 12 ÷ 36 = 2000,00`), nunca copiado do retorno da função.
- **Isolamento:** cada teste começa com o banco limpo, sem depender da ordem de execução.
- **Cobertura com asserção:** teste sem `assert` sobre comportamento não é aceito.

# Guia — Testes

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

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

Os testes dos coletores usam respostas gravadas das APIs (fixtures em `tests/fixtures/`) e **não acessam a internet**.

Cobertura mínima exigida: **70% global**, **100%** em `app/utils/` e `app/services/`.


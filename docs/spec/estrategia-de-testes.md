# SPEC — Estratégia de Testes

Parte de [SPEC — ITAM](README.md).

## 12. Estratégia de Testes

| Camada | Alvo | Ferramenta | Meta |
|---|---|---|---|
| Unitário | Funções puras (`utils/depreciacao.py`) e serviços com repositório falso | pytest | 100% das regras de cálculo |
| Integração | Endpoints com banco real (SQLite em memória ou PostgreSQL efêmero) | pytest + httpx | Um teste por critério de aceite |
| Contrato | Validação das respostas contra `api/openapi.yaml` | schemathesis | Todos os endpoints |
| Coletores | `python/collectors/` (Compras.gov.br, endoflife.date, NVD) | pytest + fixtures gravadas | Nenhum teste acessa a internet |
| Fumaça | Ambiente orquestrado no ar | `scripts/smoke_test.sh` | health, metrics, KPIs |
| Segurança | Análise estática | bandit, ruff | Zero achados de severidade alta |

Os testes de `python/collectors/` usam respostas gravadas das APIs em `tests/fixtures/` (ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md)) e nunca fazem requisição real — o teste falha se tentar abrir socket, o que é verificado por um marcador que bloqueia rede (`pytest-socket` ou equivalente <!-- TODO: confirmar -->).

**Convenção de nomenclatura.** Cada teste carrega o identificador do critério que valida:

```python
def test_ac015_depreciacao_linear_12_meses_de_60(): ...
def test_ac021_bloqueia_vinculo_acima_do_contratado(): ...
def test_ac051_recusa_recomendacao_sem_evidencia(): ...
```

Isso torna a matriz de rastreabilidade verificável por comando, não por inspeção manual:

```bash
pytest --collect-only -q | grep -c "test_ac"
```

**Cobertura mínima:** 70% global (NFR-MAN-03), com exigência de 100% em `app/utils/` e `app/services/`.

**Casos de borda obrigatórios:** ativo adquirido hoje (zero meses); ativo com vida útil esgotada; ativo com vida útil de 1 mês; transferência no mesmo dia da aquisição; licença expirando exatamente hoje; importação com arquivo vazio; importação só com linhas inválidas.


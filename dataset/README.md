# dataset/

Dados usados pelo seed e pela API do ITAM. Raiz resolvida pela variável `DATASET_DIR` (ver `.env.example`); fora de contêiner, default é este diretório.

| Pasta | Conteúdo |
|---|---|
| `demo/` | `inventario_demo.csv` — modelo de importação manual de inventário (FR-008) |
| `raw/<fonte>/<data>/` | Respostas originais das APIs (Compras.gov.br, endoflife.date, NVD), imutáveis por coleta |
| `processed/` | Referência normalizada a partir de `raw/` por `python -m etl.normalizar` (hardware do Compras.gov.br, ciclo de vida e CVEs, com `LEIAME.md`), versionada. É o retrato das coletas de referência (bloco `referencia` de `python/collectors/config.yaml`), não da coleta mais recente de `raw/`. **Não é carregada no banco** |
| `synthetic/` | CSVs gerados via Mockaroo (versionados) e `synthetic/schemas/`, os esquemas usados para gerá-los |

Detalhamento de cada fonte, regras de normalização e conformidade LGPD em [`docs/FONTES_DE_DADOS.md`](../docs/FONTES_DE_DADOS.md).

## `data_source`

Toda tabela principal do banco carrega o campo `data_source`, indicando de onde veio cada registro. `endoflife` e `nvd` **não são valores de `data_source`**: esses dados ficam só em `raw/` e `processed/`, como referência, e não vão ao banco nem geram alertas.


| Valor | Origem |
|---|---|
| `compras_gov` | Coletado de Compras.gov.br (`raw/compras_gov/` → `demo/`, importado pela API) |
| `sintetico` | Criado só para demonstração, teste ou simulação (o seed de demonstração, `DEMO-`) — usado só onde não existe, e não deveria existir, dado público (pessoas e eventos internos, LGPD) |
| `importacao` | Recebido via `POST` de importação de inventário na API (não vem de `dataset/`) |

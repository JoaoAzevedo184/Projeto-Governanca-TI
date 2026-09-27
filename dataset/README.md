# dataset/

Dados usados pelo seed e pela API do ITAM. Raiz resolvida pela variável `DATASET_DIR` (ver `.env.example`); fora de contêiner, default é este diretório.

| Pasta | Conteúdo |
|---|---|
| `demo/` | `inventario_demo.csv` — modelo de importação manual de inventário (FR-008) |
| `raw/<fonte>/<data>/` | Respostas originais das APIs (Compras.gov.br, endoflife.date, NVD), imutáveis por coleta |
| `processed/` | Dados normalizados a partir de `raw/`, prontos para carga no banco |
| `synthetic/` | CSVs gerados via Mockaroo (versionados) e `synthetic/schemas/`, os esquemas usados para gerá-los |

Detalhamento de cada fonte, regras de normalização e conformidade LGPD em [`docs/FONTES_DE_DADOS.md`](../docs/FONTES_DE_DADOS.md).

## `data_source`

Toda tabela principal do banco carrega o campo `data_source`, indicando de onde veio cada registro:

| Valor | Origem |
|---|---|
| `compras_gov` | Coletado de Compras.gov.br (`raw/compras_gov/` → `processed/`) |
| `endoflife` | Coletado de endoflife.date (`raw/endoflife/` → `processed/`) |
| `nvd` | Coletado do NVD (`raw/nvd/` → `processed/`) |
| `sintetico` | Gerado via Mockaroo (`synthetic/`) — usado só onde não existe, e não deveria existir, dado público (pessoas e eventos internos, LGPD) |
| `importacao` | Recebido via `POST` de importação de inventário na API (não vem de `dataset/`) |

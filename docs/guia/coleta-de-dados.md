# Guia — Coletando Dados Reais

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Coletando dados reais

O pipeline tem três etapas independentes: **coleta** (APIs → `dataset/raw/`), **normalização** (`dataset/raw/` → `dataset/processed/`) e **carga** (`dataset/processed/` + `dataset/synthetic/` → banco).

```bash
# Todas as fontes
python -m collectors run all

# Uma fonte específica
python -m collectors run compras_gov
python -m collectors run endoflife
python -m collectors run nvd

# Normalizar o que foi coletado
python -m etl normalize

# Carregar no banco (é o que o seed executa)
python -m etl load
```

| Coletor | Entrada | Saída bruta |
|---|---|---|
| `compras_gov` | Códigos CATMAT de TI configurados em `python/collectors/config.yaml` | `dataset/raw/compras_gov/<data>/*.json` |
| `endoflife` | Lista de produtos acompanhados em `python/collectors/config.yaml` | `dataset/raw/endoflife/<data>/*.json` |
| `nvd` | Produtos e versões presentes na base | `dataset/raw/nvd/<data>/*.json` |

A normalização classifica os itens pelo CATMAT (notebook, desktop, servidor, monitor, equipamento de rede), padroniza fabricantes e modelos e cruza software × ciclo de vida × vulnerabilidades.

Todos os coletores respeitam limites de requisição das APIs e podem ser executados novamente sem duplicar registros.


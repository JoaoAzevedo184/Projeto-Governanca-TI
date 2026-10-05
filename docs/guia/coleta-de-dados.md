# Guia — Coletando Dados Reais

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Coletando dados reais

O pipeline tem três etapas independentes: **coleta** (APIs → `dataset/raw/`), **normalização** (`dataset/raw/` → `dataset/processed/`) e **carga** (`dataset/processed/` + `dataset/synthetic/` → banco).

```bash
# Fonte implementada hoje (a partir de python/)
python -m collectors.compras_gov

# Ainda não implementadas: endoflife (D.3) e nvd (D.4)

# Normalizar o que foi coletado
python -m etl normalize

# Carregar no banco (é o que o seed executa)
python -m etl load
```

| Coletor | Entrada | Saída bruta |
|---|---|---|
| `compras_gov` | PDMs do CATMAT de TI configurados em `python/collectors/config.yaml` | `dataset/raw/compras_gov/<data>/<tipo>_<codigo>_pNNN.json`, uma página por arquivo, como a API devolveu |
| `endoflife` | Lista de produtos acompanhados em `python/collectors/config.yaml` | `dataset/raw/endoflife/<data>/*.json` |
| `nvd` | Produtos e versões presentes na base | `dataset/raw/nvd/<data>/*.json` |

A normalização classifica os itens pelo CATMAT (notebook, desktop, servidor, monitor, equipamento de rede), padroniza fabricantes e modelos e cruza software × ciclo de vida × vulnerabilidades.

Todos os coletores respeitam limites de requisição das APIs e podem ser executados novamente sem duplicar registros.

## Coletor `compras_gov` (D.1) e arquivo do Gate 1 (D.2)

O coletor usa `GET /modulo-pesquisa-preco/1_consultarMaterial` (sem chave). Cada código vira
até `max_paginas_por_codigo` páginas de `tamanho_pagina` registros, com 1 s entre requisições e
novas tentativas com espera crescente para 429, 5xx e erro de rede. Um código só é gravado
depois de todas as páginas chegarem (sem arquivo pela metade) e `raw/` não é sobrescrito: rodar
de novo no mesmo dia pula o que já está completo.

Do que foi coletado ao arquivo de demonstração (`dataset/demo/`):

```bash
cd python
python -m collectors.compras_gov            # raw/compras_gov/<data>/
python -m etl.exportar_inventario_demo      # inventario_demo.csv, fornecedores_demo.csv e o LEIAME
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores   # POST /fornecedores
```

O exportador é determinístico: com a mesma coleta, gera arquivos idênticos. A metodologia (filtros,
faixas de preço, as 8 linhas inválidas de propósito) está em `dataset/demo/inventario_demo.LEIAME.md`.
O `numero_serie` desses ativos, `CG-{idItemCompra}-001`, é um identificador técnico sintético: a
fonte pública não traz número de série.

# Guia — Importando Seu Próprio Inventário

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Importando seu próprio inventário

```bash
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@meu_inventario.xlsx"
```

O arquivo deve conter as colunas `nome`, `tipo`, `categoria`, `fornecedor`, `numero_serie` ou `chave_licenca`, `data_aquisicao` e `valor_compra`. Veja `dataset/demo/inventario_demo.csv` como modelo. Registros importados recebem `data_source = importacao`, ou o que a coluna opcional `data_source` declarar (`compras_gov`; vazia ou ausente, `importacao`).

São aceitos arquivos `.csv` (UTF-8) e `.xlsx`, até 5 MB e 5.000 linhas. Arquivo vazio, com outra extensão, CSV fora de UTF-8 ou XLSX corrompido recebem erro 422 (`/erros/arquivo-invalido`) e nenhum lote é criado.

Linhas inválidas **não impedem** a importação das demais. Para consultar o que foi rejeitado:

```bash
curl -s http://localhost:8000/api/v1/importacoes/1/erros \
  -H "Authorization: Bearer $TOKEN" | jq
```

## O arquivo do Gate 1

`dataset/demo/inventario_demo.csv` tem 100 linhas reais do Compras.gov.br: 92 válidas e 8 inválidas de propósito (coluna extra `erro_proposital`, que o importador ignora). Importado como está, dá **100 processadas, 92 aceitas e 8 rejeitadas**. Antes, com o seed aplicado, os fornecedores precisam existir (a linha referencia o fornecedor pela razão social e a importação não cria nenhum):

```bash
cd python
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores   # idempotente
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" -F "arquivo=@../dataset/demo/inventario_demo.csv"
```

O relatório esperado e a metodologia estão em `dataset/demo/inventario_demo.LEIAME.md`. Para repetir a demonstração, use um banco novo: com os ativos já importados, as 92 linhas válidas são rejeitadas por número de série já cadastrado.

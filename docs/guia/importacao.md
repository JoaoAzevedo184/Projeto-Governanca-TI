# Guia — Importando Seu Próprio Inventário

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Importando seu próprio inventário

```bash
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@meu_inventario.xlsx"
```

O arquivo deve conter as colunas `nome`, `tipo`, `categoria`, `fornecedor`, `numero_serie` ou `chave_licenca`, `data_aquisicao` e `valor_compra`. Veja `dataset/demo/inventario_demo.csv` como modelo. Registros importados recebem `data_source = importacao`.

São aceitos arquivos `.csv` (UTF-8) e `.xlsx`, até 5 MB e 5.000 linhas. Arquivo vazio, com outra extensão, CSV fora de UTF-8 ou XLSX corrompido recebem erro 422 (`/erros/arquivo-invalido`) e nenhum lote é criado.

Linhas inválidas **não impedem** a importação das demais. Para consultar o que foi rejeitado:

```bash
curl -s http://localhost:8000/api/v1/importacoes/1/erros \
  -H "Authorization: Bearer $TOKEN" | jq
```


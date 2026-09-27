# Guia — Importando Seu Próprio Inventário

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Importando seu próprio inventário

```bash
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@meu_inventario.xlsx"
```

O arquivo deve conter as colunas `nome`, `tipo`, `categoria`, `fornecedor`, `numero_serie` ou `chave_licenca`, `data_aquisicao` e `valor_compra`. Veja `data/inventario_demo.csv` como modelo. Registros importados recebem `data_source = importacao`.

Linhas inválidas **não impedem** a importação das demais. Para consultar o que foi rejeitado:

```bash
curl -s http://localhost:8000/api/v1/importacoes/1/erros \
  -H "Authorization: Bearer $TOKEN" | jq
```


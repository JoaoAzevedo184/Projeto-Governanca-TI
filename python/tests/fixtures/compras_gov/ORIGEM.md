# Fixtures do coletor `compras_gov`

Respostas reais da API de Dados Abertos do Compras.gov.br, gravadas com `curl` em 2026-10-05 e
guardadas byte a byte, sem edição. Nenhum arquivo foi escrito ou ajustado à mão. O comportamento
de cada uma foi conferido na resposta real (campos e códigos HTTP abaixo).

Endpoint: `GET https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial`
com `tipo=codigoPdm` e `codigo=237` (PDM `ROTEADOR`).

| Arquivo | Parâmetros além dos acima | HTTP | O que mostra |
|---|---|---|---|
| `codigoPdm_237_p001.json` | `pagina=1`, `tamanhoPagina=10` | 200 | 10 registros; `totalRegistros` 1515, `totalPaginas` 152 |
| `codigoPdm_237_p002.json` | `pagina=2`, `tamanhoPagina=10` | 200 | 10 registros; `paginasRestantes` 150 |
| `pagina_alem_do_fim.json` | `pagina=999999`, `tamanhoPagina=10` | 200 | `resultado` vazio, com os totais |
| `erro_tamanho_pagina_minimo.json` | `pagina=1`, `tamanhoPagina=5` | 400 | erro de validação (tamanho mínimo 10) |

Os dados mudam a cada dia na fonte; refazer a gravação gera arquivos diferentes. Os testes não
dependem dos valores de negócio, só da estrutura e da paginação (`totalPaginas`).

## `coleta_2026-10-05/`

Os 18 arquivos que `python -m collectors.compras_gov` gravou em `dataset/raw/compras_gov/2026-10-05/`
(9 PDMs, 2 páginas de 100, 1705 registros), copiados byte a byte. `dataset/raw/` não é versionado;
esta cópia é a entrada do exportador do arquivo do Gate 1 (`python/etl/exportar_inventario_demo.py`)
e permite gerar de novo, e conferir, `dataset/demo/inventario_demo.csv` sem rede.

### Sanitização (2026-10-06)

Exceção à cópia byte a byte: em 6 registros de `coleta_2026-10-05/`, a razão social (campo
`nomeFornecedor`) vinha no formato antigo de microempreendedor individual, o nome da pessoa
seguido de 11 dígitos, que são o CPF do titular. Em 2026-10-06 esses 11 dígitos foram trocados por
`00000000000`, sem outra alteração nos arquivos; o tamanho em bytes é o mesmo. O exportador
descarta esses registros pelo padrão de 11 dígitos, e os zeros mantêm o padrão, então
`dataset/demo/` sai idêntico. Isto cobre os arquivos versionados a partir desta data. Não afirma
nada sobre o histórico do git, em que a versão anterior dos arquivos continua existindo.

Coletas novas: copie de `dataset/raw/` com
`python -m etl.sanitizar_coleta dataset/raw/compras_gov/AAAA-MM-DD tests/fixtures/compras_gov/coleta_AAAA-MM-DD`
em vez de `cp`. O teste `tests/unit/test_fixtures_sem_cpf.py` falha se uma fixture versionada tiver
razão social seguida de 11 dígitos diferentes de zeros. `dataset/raw/` não é versionado e guarda a
coleta sem alteração.

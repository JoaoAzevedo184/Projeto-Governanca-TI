# `inventario_demo.csv`: arquivo do Gate 1

Gerado por `python -m etl.exportar_inventario_demo` (`python/etl/exportar_inventario_demo.py`) a
partir de `dataset/raw/compras_gov/2026-10-05/`, a coleta real do Compras.gov.br de **2026-10-05** (coletor D.1). A data
de geração é a da coleta: o gerador não grava a data de execução, para duas execuções darem
arquivos idênticos. A coleta sanitizada está em `python/tests/fixtures/compras_gov/coleta_2026-10-05/`:
é a coleta real, só com o CPF que segue o nome do microempreendedor na razão social trocado por
zeros (seção "Sanitização" de `python/tests/fixtures/compras_gov/ORIGEM.md`). O teste
`test_exportar_inventario_demo.py` confere que este arquivo é exatamente o que ela gera.

Critério de liberação do Gate 1 (`docs/BACKLOG_E_GATES.md`): **100 linhas processadas, 92 ativos
aceitos e 8 linhas rejeitadas**, com relatório de erros linha a linha.

## O que é cada coluna

Colunas do importador (`docs/spec/pipeline-importacao.md`) mais `data_source = compras_gov` e a
coluna extra `erro_proposital` (o importador ignora colunas que não conhece), preenchida só nas 8
linhas inválidas.

- `numero_serie` = `CG-{idItemCompra}-001`: **identificador técnico sintético**, derivado do
  `idItemCompra` do item de compra. A fonte pública não traz número de série real. Não é número
  de fábrica (ADR-011).
- `nome` = `nomePdm` + marca (até 120 caracteres; marca vazia ou só pontuação: só o `nomePdm`).
- `valor_compra` = `precoUnitario` arredondado a 2 casas (ROUND_HALF_UP); `data_aquisicao` =
  `dataCompra`; `tipo` = `HARDWARE`; `localizacao` vazia.
- `categoria` pelo PDM (tabela abaixo); `fornecedor` = `nomeFornecedor`, que precisa existir
  antes (`fornecedores_demo.csv` + `python -m etl.carregar_fornecedores`).

## Metodologia e números

Registros coletados: **1705**. Federais (`esfera = F`): **702**.
Descartes em sequência, sobre os federais (o que se repete é medido sobre todos os coletados):

| Filtro | Descartados |
|---|---|
| identificador de fornecedor estrangeiro | 1 |
| razão social de pessoa física (microempreendedor) | 61 |
| CNPJ com mais de uma razão social | 15 |
| razão social com mais de um CNPJ | 26 |
| item com (idCompra, idCompraItem) repetido | 8 |
| preço fora da faixa P10-P90 do PDM | 124 |
| **Elegíveis** | **467** |

Fornecedores cuja razão social é o nome de uma pessoa física (microempreendedor individual:
`64.956.713 NOME DA PESSOA`, ou o nome seguido de 11 dígitos) **não entram** no arquivo, por
decisão da equipe. O filtro é só do exportador: a coleta bruta e as fixtures não são alteradas.

Seleção determinística: o menor conjunto de fornecedores (pela ordem de volume, CNPJ como
desempate) que cobre os 9 PDMs e reúne os registros necessários, **17
fornecedores escolhidos** (17 aparecem nas 92 linhas válidas). Com ~10
fornecedores não saem as 92 linhas válidas, então a equipe aceitou o mínimo possível. Dentro do conjunto, as
linhas vêm em rodízio entre os PDMs (cobertura antes de volume). Utilizados: 100 registros (92
válidos e 8 bases das inválidas).

### Preço por PDM

Percentis por interpolação linear sobre os registros federais do PDM; "utilizados" são as 92
linhas válidas.

| PDM | CATMAT | Categoria | Federais | Mín. original | Máx. original | P10 | P90 | Válidas | Mín. usado | Máx. usado |
|---|---|---|---|---|---|---|---|---|---|---|
| 8435 | NOTEBOOK | Notebook | 85 | 1669.00 | 68000.00 | 3075.60 | 14744.52 | 13 | 3250.00 | 9950.00 |
| 6661 | MICROCOMPUTADOR | Desktop | 93 | 900.00 | 33000.00 | 2256.00 | 8430.19 | 15 | 2780.00 | 8042.00 |
| 6484 | MICROCOMPUTADOR ALL IN ONE | Desktop | 55 | 1497.90 | 1213940.00 | 2071.20 | 19990.00 | 7 | 3170.00 | 5208.00 |
| 10293 | SERVIDOR | Servidor | 110 | 11.83 | 7010980.00 | 9474.67 | 617428.60 | 19 | 11580.00 | 372400.00 |
| 6669 | MONITOR COMPUTADOR | Monitor | 87 | 265.00 | 77140.00 | 406.48 | 4964.00 | 7 | 715.00 | 1065.00 |
| 5522 | SWITCH | Switch | 124 | 60.99 | 347203.00 | 158.30 | 38950.00 | 18 | 850.00 | 28155.00 |
| 237 | ROTEADOR | Roteador | 62 | 96.49 | 230000.00 | 172.50 | 55293.19 | 4 | 450.00 | 650.00 |
| 15287 | IMPRESSORA MONOCROMÁTICA | Impressora | 20 | 772.58 | 28899.00 | 970.20 | 5040.00 | 1 | 2290.00 | 2290.00 |
| 19246 | TABLET | Tablet | 66 | 33.51 | 14775.00 | 961.50 | 5449.31 | 8 | 1254.42 | 5200.00 |

## As 8 linhas inválidas (propositais)

Uma por tipo de validação, um erro por linha (8 rejeitadas = 8 erros). Nenhuma "se conserta" com o
tempo: a data futura é 2099-12-31.

| Linha | Campo | Erro inserido | Motivo esperado no relatório |
|---|---|---|---|
| 7 | nome | nome com menos de 3 caracteres | Nome deve ter ao menos 3 caracteres. |
| 18 | tipo | tipo fora do domínio | Tipo deve ser HARDWARE ou SOFTWARE. |
| 31 | categoria | categoria inexistente | Categoria não encontrada. |
| 46 | fornecedor | fornecedor não cadastrado | Fornecedor não encontrado. |
| 58 | numero_serie | HARDWARE sem número de série | Obrigatório para ativos do tipo HARDWARE (BR-002). |
| 71 | numero_serie | número de série repetido no arquivo | Duplicado dentro do próprio arquivo (AC-046). |
| 84 | data_aquisicao | data futura | Não pode ser futura (BR-003). |
| 97 | valor_compra | valor zero | Deve ser maior que zero (BR-004). |

A linha 71 repete o `numero_serie` da linha 5, que é válida e conta nas 92.
O fornecedor da linha 46 é real, mas fica de fora de `fornecedores_demo.csv`.

Relatório esperado de `GET /importacoes/{id}/erros`:

- linha 7, campo `nome`
- linha 18, campo `tipo`
- linha 31, campo `categoria`
- linha 46, campo `fornecedor`
- linha 58, campo `numero_serie`
- linha 71, campo `numero_serie`
- linha 84, campo `data_aquisicao`
- linha 97, campo `valor_compra`

## Como usar

```bash
cd python
python -m etl.exportar_inventario_demo        # regenera os três arquivos de dataset/demo/
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores
# com o seed aplicado (categorias) e logado como ADMIN: POST /api/v1/importacoes com o arquivo
```

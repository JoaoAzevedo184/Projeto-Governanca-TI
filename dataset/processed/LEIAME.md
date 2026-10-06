# `dataset/processed/`: referência normalizada (D.6)

Gerado por `python -m etl.normalizar` (`python/etl/normalizar.py`) a partir de
`dataset/raw/compras_gov/2026-10-05/`, `dataset/raw/endoflife/2026-10-06/` e
`dataset/raw/nvd/2026-10-06/`. A data de cada coleta é a da pasta de origem: o gerador não grava
a data de execução, e duas execuções dão arquivos idênticos. As coletas gravadas estão em
`python/tests/fixtures/` (ver os `ORIGEM.md`), e o teste `test_normalizar.py` confere que estes
arquivos são exatamente o que elas geram, sem rede.

**endoflife e NVD não são carregados no banco, não aparecem nas telas do ITAM e não geram alertas na versão atual.**
Só o dataset do Compras.gov.br usado na demonstração (`dataset/demo/`) é carregado no banco, pelo seed e pela importação. Os arquivos desta pasta são referência reproduzível, não entrada do sistema.

## Fontes

| Fonte | Endereço | Coleta | O que entra aqui |
|---|---|---|---|
| Compras.gov.br | https://dadosabertos.compras.gov.br (`/modulo-pesquisa-preco/1_consultarMaterial`) | 2026-10-05 | Itens de TI de 9 PDMs do CATMAT |
| endoflife.date | https://endoflife.date (`/api/<produto>.json`) | 2026-10-06 | Ciclos de vida e fim de suporte |
| NVD (NIST) | https://services.nvd.nist.gov (`/rest/json/cves/2.0`) | 2026-10-06 | Contagem de CVEs por ciclo e severidade |

Produtos pesquisados no endoflife (8): `postgresql`, `mysql`, `nginx`, `mongodb`, `tomcat`, `redis`, `windows-server`, `office`. O slug `apache` do endoflife
redireciona (HTTP 301) e o coletor não segue redirecionamento, então o Tomcat o substituiu.

## `hardware_compras_gov.csv`: hardware do Compras.gov.br

Normalizado e classificado com as funções e os filtros do exportador de demonstração
(`etl/exportar_inventario_demo.py`), sem regra duplicada: só esfera federal; fora identificador de
fornecedor estrangeiro, razão social de pessoa física (microempreendedor), CNPJ com mais de uma razão
social e vice-versa, item repetido e preço fora da faixa P10-P90 do PDM. A categoria vem do PDM
(`CATEGORIA_POR_PDM`); PDM sem categoria é erro, não linha sem classificar. O arquivo não tem
número de série: o `numero_serie` técnico do arquivo de demonstração é um identificador sintético.
O fornecedor aparece só pelo CNPJ: a razão social foi omitida de propósito (minimização de dados),
porque a de empresário individual pode ser o nome do titular.

Registros coletados: **1705**. Federais: **702**. Descartes em sequência, sobre
os federais (o que se repete é medido sobre todos os coletados):

| Filtro | Descartados |
|---|---|
| identificador de fornecedor estrangeiro | 1 |
| razão social de pessoa física (microempreendedor) | 61 |
| CNPJ com mais de uma razão social | 15 |
| razão social com mais de um CNPJ | 26 |
| item com (idCompra, idCompraItem) repetido | 8 |
| preço fora da faixa P10-P90 do PDM | 124 |

| Registros de hardware normalizados | **467** |
|---|---|

| Categoria | Registros |
|---|---|
| Desktop | 102 |
| Impressora | 14 |
| Monitor | 57 |
| Notebook | 55 |
| Roteador | 41 |
| Servidor | 68 |
| Switch | 87 |
| Tablet | 43 |

## `software_ciclos_cves.csv` e `produtos_cruzamento.csv`: ciclo de vida e CVEs

Uma linha por ciclo (versão) de cada produto do endoflife: data de lançamento, data de fim de
suporte e situação **na data da coleta** do endoflife (2026-10-06): `EM_SUPORTE`,
`FORA_DE_SUPORTE` (a data de fim já chegou, inclusive o próprio dia, ou o endoflife marca `true`) ou
`SEM_DATA_DE_FIM` (o endoflife marca `false`). A situação não depende do dia em que o script roda.

As colunas de CVE (`cves_baixa`, `cves_media`, `cves_alta`, `cves_critica`, `cves_sem_cvss_v3`,
`cves_total`) vêm do NVD, só para os ciclos da tabela abaixo; `cves_total` conta todas as CVEs do
ciclo e `cves_sem_cvss_v3` é o total menos as quatro severidades (CVEs que a consulta por severidade CVSS v3 não alcança: sem análise do NVD ou sem métrica v3.x).

| Produto | Ciclo | CPE | Versão inicial (inclusive) | Versão final (exclusive) |
|---|---|---|---|---|
| `postgresql` | 16 | `cpe:2.3:a:postgresql:postgresql` | 16.0 | 17.0 |
| `postgresql` | 13 | `cpe:2.3:a:postgresql:postgresql` | 13.0 | 14.0 |
| `mysql` | 8.4 | `cpe:2.3:a:oracle:mysql` | 8.4.0 | 8.5.0 |
| `mysql` | 8.0 | `cpe:2.3:a:oracle:mysql` | 8.0.0 | 8.1.0 |
| `nginx` | 1.30 | `cpe:2.3:a:f5:nginx` | 1.30.0 | 1.31.0 |
| `nginx` | 1.28 | `cpe:2.3:a:f5:nginx` | 1.28.0 | 1.29.0 |
| `mongodb` | 8.0 | `cpe:2.3:a:mongodb:mongodb` | 8.0.0 | 8.1.0 |
| `mongodb` | 6.0 | `cpe:2.3:a:mongodb:mongodb` | 6.0.0 | 6.1.0 |
| `tomcat` | 10.1 | `cpe:2.3:a:apache:tomcat` | 10.1.0 | 10.2.0 |
| `tomcat` | 9.0 | `cpe:2.3:a:apache:tomcat` | 9.0.0 | 9.1.0 |
| `redis` | 7.2 | `cpe:2.3:a:redis:redis` | 7.2.0 | 7.3.0 |
| `redis` | 6.2 | `cpe:2.3:a:redis:redis` | 6.2.0 | 6.3.0 |
| `windows-server` | 2022 | `cpe:2.3:o:microsoft:windows_server_2022` | - | - |
| `windows-server` | 2019 | `cpe:2.3:o:microsoft:windows_server_2019` | - | - |

### Como ler as contagens do NVD

- O identificador de cada produto no NVD (o CPE) e a faixa de versão de cada ciclo foram **definidos manualmente** em `python/collectors/config.yaml`; nada foi encontrado nem deduzido por correspondência de nomes.
- Só os **14 ciclos** da tabela acima foram consultados no NVD. As demais versões ficaram fora **por decisão** de limitar o volume, não por falha de correspondência: o NVD não foi perguntado sobre elas, e o motivo de cada uma está em `motivo_nao_cruzado`.
- Contagem **zero** significa **nenhuma CVE encontrada por esta consulta**, não ausência de vulnerabilidades: depende do CPE e da faixa de versão escritos na configuração e do que o NVD tinha associado a eles na data da coleta. Na coleta de 2026-10-06, tiveram contagem zero: `nginx` 1.30 e `nginx` 1.28. Para o nginx, a conferência manual com o CPE antigo `cpe:2.3:a:nginx:nginx`, que também deu 0, está em `python/tests/fixtures/nvd/ORIGEM.md`.

| Contagem do D.6 | Produtos |
|---|---|
| Produtos analisados | **8** |
| Com correspondência no endoflife | **8** |
| Com correspondência no NVD | **7** |
| Com correspondência nas duas fontes | **7** |
| Não cruzados | **1** |

| Versões (ciclos) do endoflife | **152** |
|---|---|
| Versões cruzadas com o NVD | **14** |

Produtos não cruzados, com o motivo:

| Produto | Motivo |
|---|---|
| office | NVD: produto sem CPE configurado em collectors/config.yaml |

## Metodologia

- **Cruzamento conservador.** Produto e ciclo só se correspondem por igualdade exata de nome. O NVD só
  é consultado para o CPE e a faixa de versão que `python/collectors/config.yaml` escreve para cada
  ciclo; nada é deduzido por semelhança. Sem correspondência confiável o ciclo fica
  `NAO_CRUZADO`, com o motivo em `motivo_nao_cruzado`, e as colunas de CVE ficam **vazias, nunca zero**.
- **Um ciclo do NVD que não existe no endoflife é erro de configuração**, não linha ignorada.
- **Contagens por severidade** são `totalResults` de consultas de um registro por severidade CVSS v3
  (`cvssV3Severity`) e por ciclo, mais uma sem filtro (o total).
- **Determinismo.** Ordem fixa (produtos da configuração; ciclos pela data de lançamento, do mais
  novo ao mais antigo), sem data de execução, CSV com fim de linha `\n`.

## Reprodutibilidade: um retrato das coletas de referência

Estes arquivos correspondem às **coletas de referência** fixadas no bloco `referencia` de `python/collectors/config.yaml`: Compras.gov.br de 2026-10-05, endoflife de 2026-10-06 e NVD de 2026-10-06.

A fonte muda entre coletas: medido em 2026-10-06, entre as coletas do Compras.gov.br de 2026-10-05 e de 2026-10-06, **14 dos 1705 registros** mudaram (1691 ficaram iguais) e só 5 das 18 páginas ficaram idênticas byte a byte. Por isso uma coleta nova não reproduz estes arquivos.

O exportador de demonstração e o normalizador usam por padrão a coleta de referência, mesmo que `dataset/raw/` tenha uma mais recente. Usar outra coleta exige parâmetro explícito e `--saida` com um diretório que não seja o versionado.

Para atualizar a referência de propósito (nova coleta, sanitização, fixtures, regeneração e testes), siga a seção "Atualizando a referência" de `docs/guia/coleta-de-dados.md`.

## Limitações

- É uma referência de 8 produtos de software corporativo comuns, não um catálogo.
- As contagens do NVD são as da data da coleta (2026-10-06) e mudam todo dia na fonte; refazer a coleta
  gera valores diferentes. Contam CVEs que o NVD associa ao CPE e à faixa de versão escritos na
  configuração; não medem exposição de nenhum ativo.
- A severidade é a do CVSS v3.x; CVEs que não têm essa métrica (por exemplo, só CVSS v2 ou v4, ou ainda sem análise do NVD) aparecem apenas no total, e o arquivo não distingue o motivo.
- O endoflife publica `eol` por ciclo, não por versão de correção: o ciclo `16` do PostgreSQL cobre
  todas as `16.x`.
- Nenhum dado daqui é vinculado a ativo do ITAM, e não há alerta de ciclo de vida nem de CVE.

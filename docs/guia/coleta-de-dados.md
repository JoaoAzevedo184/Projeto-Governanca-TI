# Guia — Coletando Dados Reais

Parte do [Guia — ITAM](README.md). Ver também o [README da raiz](../../README.md).

## Coletando dados reais

O pipeline tem duas etapas independentes, **coleta** (APIs → `dataset/raw/`) e **normalização** (`dataset/raw/` → `dataset/processed/`). **Não há etapa de carga no banco:** D.5, D.7, D.8 e D.9 foram encerrados em 2026-10-06, substituídos pelo seed de demonstração (`python -m app.seed_demo`), e o único dado coletado que chega ao banco é o arquivo de demonstração do Compras.gov.br (`dataset/demo/`, seção abaixo).

```bash
# Coletores (a partir de python/, com o ambiente virtual ativo)
python -m collectors.compras_gov    # itens de TI do Compras.gov.br
python -m collectors.endoflife      # ciclos de vida (8 produtos)
python -m collectors.nvd            # CVEs por produto, ciclo e severidade (cerca de 70 consultas)

# Os três coletores e a normalização, de uma vez (exige o ambiente virtual ativo)
../scripts/collect.sh

# Normalizar as coletas de REFERÊNCIA (regenera dataset/processed/)
python -m etl.normalizar
```

O `scripts/collect.sh` usa `python`, que só existe com o ambiente virtual ativo (`source python/.venv/bin/activate`); sem ele, o script para com uma mensagem dizendo isso e não coleta nada. A coleta de hoje vai só para `dataset/raw/`: a etapa final do script normaliza as coletas de **referência** (seção abaixo), nunca a de hoje, e é pulada com um aviso se essas coletas não estão em `dataset/raw/`.

## Reprodutibilidade: os arquivos versionados são um retrato

`dataset/demo/` e `dataset/processed/` correspondem às **coletas de referência** fixadas no bloco `referencia` de `python/collectors/config.yaml`: Compras.gov.br de 2026-10-05, endoflife e NVD de 2026-10-06. **A fonte muda entre coletas.** Medido em 2026-10-06, entre as coletas do Compras.gov.br de 2026-10-05 e de 2026-10-06, **14 dos 1705 registros** mudaram (1691 ficaram iguais), só 5 das 18 páginas ficaram idênticas byte a byte, e o hardware normalizado foi de 467 para 466 registros. Uma coleta nova, portanto, não reproduz os arquivos versionados.

Por isso o exportador de demonstração e o normalizador usam **por padrão a coleta de referência**, mesmo que `dataset/raw/` tenha uma mais recente. Usar outra coleta exige parâmetro explícito (`--raw` no exportador; `--compras`, `--endoflife` e `--nvd` no normalizador) e `--saida` com um diretório que **não** seja o versionado; o comando recusa o contrário, sem gravar nada. Exemplo, para experimentar uma coleta nova sem tocar nos arquivos versionados:

```bash
cd python
python -m etl.normalizar --compras ../dataset/raw/compras_gov/AAAA-MM-DD --saida /tmp/processed-novo
python -m etl.exportar_inventario_demo --raw ../dataset/raw/compras_gov/AAAA-MM-DD --saida /tmp/demo-novo
```

### Atualizando a referência de propósito

Só quando a equipe decidir trocar o retrato (muda `dataset/demo/`, o arquivo que prova o Gate 1, e `dataset/processed/`). Passo a passo:

1. **Coletar.** `scripts/collect.sh` (ou cada `python -m collectors.<fonte>`). A coleta vai para `dataset/raw/<fonte>/<data>/`; o NVD sem chave leva cerca de 10 minutos.
2. **Sanitizar e copiar para as fixtures.** Compras.gov.br: `python -m etl.sanitizar_coleta dataset/raw/compras_gov/AAAA-MM-DD tests/fixtures/compras_gov/coleta_AAAA-MM-DD` (troca o CPF que segue o nome do microempreendedor por zeros; nunca `cp`). endoflife e NVD: copiar byte a byte para `tests/fixtures/endoflife/coleta_AAAA-MM-DD/` e `tests/fixtures/nvd/coleta_AAAA-MM-DD/`, depois de conferir dado pessoal e segredo (`pytest tests/unit/test_fixtures_sem_cpf.py tests/unit/test_fixtures_sem_segredos.py`; o teste para se aparecer e-mail fora da lista institucional, que exige revisão humana). Atualize os `ORIGEM.md`.
3. **Fixar a nova referência** no bloco `referencia` de `python/collectors/config.yaml`.
4. **Regenerar.** `python -m etl.exportar_inventario_demo` e `python -m etl.normalizar` (usam a nova referência por padrão). Sem `dataset/raw/` à mão, passe as pastas das fixtures (`--raw`, `--compras`, `--endoflife`, `--nvd`) com `--saida` apontando para o diretório versionado: é permitido porque a data da pasta é a da referência.
5. **Testes.** `pytest tests/unit/test_exportar_inventario_demo.py tests/unit/test_normalizar.py tests/unit/test_referencia.py`, depois a suíte inteira. Vão falhar, de propósito, os testes com número fixo da coleta antiga (por exemplo 467 registros, 14 ciclos, `nginx` com zero CVE, as 8 linhas inválidas do Gate 1 e as datas `2026-10-05` e `2026-10-06`): confira cada diferença no `git diff`, ajuste o esperado **depois** de entender a mudança e refaça `tests/integration/test_gate1_inventario_demo.py` (100 processadas, 92 aceitas, 8 rejeitadas).
6. **Documentar.** Atualize as datas citadas nos guias e no `docs/ROADMAP.md`, e registre a troca no `docs/REGISTRO_USO_DE_IA.md`.

| Coletor | Entrada | Saída bruta |
|---|---|---|
| `compras_gov` | PDMs do CATMAT de TI configurados em `python/collectors/config.yaml` | `dataset/raw/compras_gov/<data>/<tipo>_<codigo>_pNNN.json`, uma página por arquivo, como a API devolveu |
| `endoflife` | 8 produtos de software em `python/collectors/config.yaml` (bloco `endoflife`) | `dataset/raw/endoflife/<data>/<produto>.json` |
| `nvd` | Produtos, ciclos, CPE e faixa de versão em `python/collectors/config.yaml` (bloco `nvd`) | `dataset/raw/nvd/<data>/<produto>_<ciclo>_<severidade>.json` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL` ou `total`) |

Todos os coletores gravam a resposta sem transformação, com timeout, novas tentativas com espera crescente, intervalo entre requisições e gravação atômica (sem arquivo pela metade), e podem ser executados de novo no mesmo dia sem duplicar nem repetir o que já está completo.

**endoflife e NVD são só referência.** Os dois são coletados e processados em `dataset/processed/`, mas **não são carregados no banco, não aparecem nas telas do ITAM e não geram alertas na versão atual.** Compras.gov.br é a fonte do dataset de demonstração e dos dados de hardware do projeto.

### Coletor `endoflife` (D.3)

`GET https://endoflife.date/api/<produto>.json`, sem chave. Um arquivo por produto. O coletor não segue redirecionamento: o produto precisa existir na fonte com aquele nome (o `apache`, que redireciona, foi trocado pelo Tomcat). Para trocar um produto, edite a lista do bloco `endoflife` e confira com `curl -s -o /dev/null -w "%{http_code}" https://endoflife.date/api/<produto>.json` (tem de dar `200`).

### Coletor `nvd` (D.4)

`GET https://services.nvd.nist.gov/rest/json/cves/2.0`. Para cada ciclo listado no `config.yaml`, cinco consultas de **um registro** (`resultsPerPage=1`): uma por severidade CVSS v3 e o total. Só o `totalResults` é usado, então o volume é pequeno (cerca de 1 MB na coleta inteira) e não há consulta genérica.

- **Limites da API:** 5 consultas por 30 s sem chave e 50 com chave. O coletor espera 6,5 s entre consultas sem chave e 0,7 s com chave; a coleta inteira (70 consultas) levou cerca de 10 minutos sem chave em 2026-10-06. Um `403` (limite excedido) não é repetido: o ciclo falha, nada é gravado dele e a próxima execução o refaz.
- **`NVD_API_KEY` (opcional):** o coletor lê a variável **do ambiente** (o `scripts/collect.sh` não carrega o `.env`; exporte antes, `export NVD_API_KEY=...`). A chave vai no cabeçalho `apiKey` e nunca é gravada em arquivo, log nem mensagem de erro. Não a coloque em fixture, relatório nem comando de exemplo.
- **Cruzamento conservador:** o CPE e a faixa de versão de cada ciclo estão escritos no `config.yaml`; produto sem entrada lá (o Office) fica "não cruzado" na normalização.

### Normalização (D.6)

`python -m etl.normalizar` lê as coletas de **referência** de cada fonte (ou as pastas dadas em `--compras`, `--endoflife` e `--nvd`, com `--saida`; ver a seção de reprodutibilidade) e gera em `dataset/processed/`, de forma determinística e sem rede. Com `--se-houver-referencia`, sem as coletas de referência em `dataset/raw/` ele avisa e sai com 0 sem gravar nada (é o que o `collect.sh` usa):

| Arquivo | Conteúdo |
|---|---|
| `hardware_compras_gov.csv` | Hardware do Compras.gov.br normalizado e classificado por PDM e categoria, pelos filtros e regras do exportador de demonstração (sem pessoa física) |
| `software_ciclos_cves.csv` | Uma linha por ciclo do endoflife: data de fim de suporte, situação **na data da coleta** e, quando o cruzamento é determinístico, CVEs por severidade |
| `produtos_cruzamento.csv` | Por produto: correspondência no endoflife, no NVD e nas duas, e o motivo de cada não cruzado |
| `LEIAME.md` | Fontes, datas, filtros, metodologia, limitações e a contagem do D.6 |

Os arquivos de `dataset/processed/` são versionados (`dataset/raw/` não é). O teste `tests/unit/test_normalizar.py` regenera tudo das fixtures em `python/tests/fixtures/` e confere que o versionado é exatamente o que elas geram.

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

O exportador é determinístico: com a mesma coleta, gera arquivos idênticos, e usa por padrão a coleta de referência do `config.yaml` (ver a seção de reprodutibilidade; outra coleta exige `--raw` e `--saida`). A metodologia (filtros,
faixas de preço, as 8 linhas inválidas de propósito) está em `dataset/demo/inventario_demo.LEIAME.md`.
O `numero_serie` desses ativos, `CG-{idItemCompra}-001`, é um identificador técnico sintético: a
fonte pública não traz número de série.

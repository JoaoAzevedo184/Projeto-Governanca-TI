# Fontes de Dados — ITAM

Detalha, fonte a fonte, o que o `README.md` resume na seção "Origem dos dados". A decisão de combinar dados reais e sintéticos, e as alternativas rejeitadas, estão em [`docs/adr/0011-estrategia-dados-reais-demonstracao.md`](adr/0011-estrategia-dados-reais-demonstracao.md). O mapeamento completo para colunas de tabela está em [`docs/modelo-de-dados/`](modelo-de-dados/README.md); este documento mapeia até o nível de tabela, não de coluna, para não duplicar o dicionário de dados.

---

## Papel de cada fonte (estado em 2026-10-06)

| Fonte | Papel | Onde chega |
|---|---|---|
| Compras.gov.br | Fonte do dataset de demonstração e dos dados de hardware do projeto | `dataset/demo/` (carregado no banco pelo seed e pela importação) e `dataset/processed/hardware_compras_gov.csv` (referência) |
| endoflife.date | Coletada e processada como referência de ciclo de vida | `dataset/processed/software_ciclos_cves.csv` (referência) |
| NVD | Coletado e processado como referência de vulnerabilidades (contagem de CVEs por ciclo e severidade) | `dataset/processed/software_ciclos_cves.csv` (referência) |

**endoflife e NVD não são carregados no banco, não aparecem nas telas do ITAM e não geram alertas na versão atual.** Só o dataset do Compras.gov.br usado na demonstração é carregado no banco. O que cada seção abaixo diz de tabelas `produto_software` e `vulnerabilidade`, de `data_source = endoflife` ou `nvd` e de alertas de ciclo de vida ou de CVE descreve o que a ADR-011 previu, **não** o que existe: a decisão de 2026-10-06 foi manter as duas fontes só como arquivos de referência. A normalização está em `python/etl/normalizar.py`, e a metodologia e as contagens em `dataset/processed/LEIAME.md`.

---

## 1. Compras.gov.br — Dados Abertos

| Campo | Valor |
|---|---|
| **O que fornece** | Itens de TI efetivamente adquiridos por órgãos públicos federais: descrição, fabricante/marca, modelo, quantidade, valor unitário, data da compra, órgão comprador, classificado por código CATMAT |
| **URL base** | `https://dadosabertos.compras.gov.br` |
| **Documentação** | `https://dadosabertos.compras.gov.br/swagger-ui/index.html` |
| **Autenticação** | Nenhuma: os endpoints de consulta usados (`modulo-pesquisa-preco` e `modulo-material`) respondem sem chave nem cabeçalho de autorização (verificado em 2026-10-05). Os de `/usuarios` e `/autenticacao` da mesma API não são usados |
| **Endpoints usados** | `GET /modulo-pesquisa-preco/1_consultarMaterial` com `tipo=codigoPdm` e `codigo=<PDM>` (preço unitário, data da compra, CNPJ e razão social do fornecedor, marca, `idCompra`, `idCompraItem`, `idItemCompra`), configurado em `python/collectors/config.yaml`. Também usados na exploração: `modulo-material/3_consultarPdmMaterial` e `4_consultarItemMaterial` (catálogo CATMAT). O `modulo-legado/2_consultarItemLicitacao`, previsto na ADR-011, não traz preço pago nem data da compra e quase não traz CNPJ (ver ADR-011, atualização de 2026-10-05) |
| **Campos aproveitados** | descrição do item, código CATMAT, fabricante, modelo, quantidade, valor unitário, data de homologação/compra, órgão |
| **Mapeamento** | `ativo.nome` (`nomePdm` + `marca`), `ativo.valor_compra` (`precoUnitario`), `ativo.data_aquisicao` (`dataCompra`), `ativo.fornecedor_id` (razão social do fornecedor vencedor, `nomeFornecedor`, resolvida contra `fornecedor`), `ativo.numero_serie` (`CG-{idItemCompra}-001`, **identificador técnico sintético**: a fonte não traz número de série), `categoria_id` (PDM -> categoria, ver `dataset/demo/inventario_demo.LEIAME.md`) |
| **Requisitos atendidos** | FR-001, FR-003, FR-004 (fornecedor), FR-010, FR-011 |
| **Limites de uso** | A API não publica limite de requisições. `tamanhoPagina` aceita de 10 a 500 (fora disso, HTTP 400). O coletor espera 1 s entre requisições e repete 429 e 5xx com espera crescente; na coleta de 2026-10-05 (18 requisições) não houve 429 |
| **Licença** | Dados abertos do Governo Federal brasileiro |

**Classificação CATMAT.** A normalização usa o código CATMAT para decidir a `categoria` do ativo (Notebook, Desktop, Servidor, Monitor, Impressora, Switch, Roteador etc.), conforme a tabela de vida útil do FR-003. Os códigos monitorados ficam em `python/collectors/config.yaml`: 9 PDMs do grupo 70 (informática) do CATMAT, escolhidos pela equipe. Nobreak, Smartphone e Software perpétuo não têm PDM nesse grupo e ficam sem dado real.

---

## 2. endoflife.date

| Campo | Valor |
|---|---|
| **O que fornece** | Ciclo de vida e fim de suporte de sistemas operacionais e produtos de software (datas de lançamento, fim de suporte ativo, fim de suporte estendido, última versão) |
| **URL base** | `https://endoflife.date/api/` |
| **Documentação** | `https://endoflife.date/docs/api` |
| **Autenticação** | Nenhuma — API pública, sem chave |
| **Endpoints usados** | `GET /api/<produto>.json` (lista de ciclos do produto) para os 8 produtos configurados em `python/collectors/config.yaml` (`postgresql`, `mysql`, `nginx`, `mongodb`, `tomcat`, `redis`, `windows-server`, `office`; todos conferidos na API em 2026-10-06, e o slug `apache`, que redireciona com HTTP 301, foi trocado pelo Tomcat). Coletor: `python/collectors/endoflife.py` (D.3), que grava a resposta sem transformação em `dataset/raw/endoflife/<data>/<produto>.json` |
| **Campos aproveitados** | `cycle` (versão), `releaseDate`, `eol` (data de fim de suporte ou `false`), `latest` |
| **Mapeamento** | **Referência, sem tabela no banco:** `dataset/processed/software_ciclos_cves.csv` (uma linha por ciclo, com data de fim de suporte e situação na data da coleta) e `produtos_cruzamento.csv`, gerados por `python -m etl.normalizar`. A tabela `produto_software` e o `data_source = endoflife`, previstos na ADR-011, **não existem** (decisão de 2026-10-06) |
| **Requisitos atendidos** | Nenhum requisito funcional depende deste dado na versão atual: é referência. Os alertas de ciclo de vida (CP-05 e correlatos, ver FR-007) seguem fora do MVP |
| **Limites de uso** | <!-- TODO: confirmar --> política de rate limit publicada pelo projeto. O coletor espera 1 s entre requisições (8 requisições por coleta) e repete 429 e 5xx com espera crescente |
| **Licença** | MIT |

**Uso.** O seed de demonstração não usa esta fonte: não há ETL que sorteie software instalado (D.7 encerrado em 2026-10-06). A tabela de ciclos é só consulta de referência para quem quiser cruzar versões por conta própria.

---

## 3. NVD — National Vulnerability Database (NIST)

| Campo | Valor |
|---|---|
| **O que fornece** | Vulnerabilidades (CVE) e severidade (CVSS) associadas a um produto e versão |
| **URL base** | `https://services.nvd.nist.gov/rest/json/cves/2.0` |
| **Documentação** | `https://nvd.nist.gov/developers/vulnerabilities` |
| **Autenticação** | Opcional via `NVD_API_KEY` (cabeçalho `apiKey`), solicitada em `https://nvd.nist.gov/developers/request-an-api-key`; sem a chave, o limite de requisições é mais restrito (ver `README.md`, seção "Pré-requisitos") |
| **Endpoints usados** | `GET /rest/json/cves/2.0` com `virtualMatchString` (CPE do produto), `versionStart` e `versionEnd` (faixa do ciclo, escrita em `python/collectors/config.yaml`), `cvssV3Severity` e `resultsPerPage=1`. Por ciclo, cinco consultas: uma por severidade (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) e o total sem filtro; só o `totalResults` interessa, então cada resposta traz um registro e o volume é de poucos KB por arquivo. Não há consulta genérica por palavra-chave. Coletor: `python/collectors/nvd.py` (D.4), em `dataset/raw/nvd/<data>/<produto>_<ciclo>_<severidade ou total>.json` |
| **Campos aproveitados** | `totalResults` (contagem de CVEs por produto, ciclo e severidade CVSS v3). O restante do registro devolvido fica no arquivo bruto e não é usado |
| **Mapeamento** | **Referência, sem tabela no banco:** colunas `cves_*` de `dataset/processed/software_ciclos_cves.csv`, só para os ciclos que o `config.yaml` lista (cruzamento conservador, sem aproximação de nomes). A tabela `vulnerabilidade` e o `data_source = nvd`, previstos na ADR-011, **não existem** (decisão de 2026-10-06) |
| **Requisitos atendidos** | Nenhum requisito funcional depende deste dado na versão atual: é referência. Não há alerta de CVE nem insumo automático para o registro de riscos (FR-012) |
| **Limites de uso** | O NVD publica 5 requisições por janela de 30 s sem chave e 50 com chave (<!-- TODO: confirmar valores vigentes -->). O coletor espera 6,5 s entre consultas sem chave e 0,7 s com chave, e não repete 403 (o que o NVD devolve ao passar do limite) |
| **Segredo** | `NVD_API_KEY` é lida só do ambiente (o `scripts/collect.sh` não carrega o `.env`: exporte a variável), vai no cabeçalho `apiKey` e nunca é gravada em arquivo, log, mensagem de erro, fixture nem arquivo gerado (`tests/unit/test_nvd.py` e `tests/unit/test_fixtures_sem_segredos.py` conferem) |
| **Licença** | Domínio público (obra do governo dos EUA) |

---

## 4. IN RFB nº 1.700/2017 — Anexo III

| Campo | Valor |
|---|---|
| **O que fornece** | Vida útil e taxa de depreciação anual por categoria de bem, para fins de apuração de lucro real |
| **Uso no ITAM** | Base da vida útil padrão de cada `categoria` (computadores e periféricos: 5 anos, 20% a.a. — ver [`docs/modelo-de-dados/dados-semente.md`](modelo-de-dados/dados-semente.md)) |
| **Como é usada** | **Não é coletada por API.** É uma norma; seus valores são digitados uma vez no seed (`categoria.vida_util_meses`) e a fórmula de depreciação vive em `app/utils/depreciacao.py` (ADR-002) |
| **`data_source`** | Não aplicável a registros individuais — a regra em si não tem um `data_source`, mas nenhum valor de depreciação é armazenado (ver seção 5) |
| **Requisitos atendidos** | FR-003 |

---

## 5. A depreciação não é uma fonte de dados

Vale repetir aqui porque é a regra que mais gera confusão: o banco **não guarda** valor depreciado, depreciação acumulada nem valor residual. Guarda apenas `valor_compra`, `data_aquisicao`, `vida_util_meses` e a categoria (da qual deriva-se a taxa). Tudo o mais é calculado sob demanda por `app/utils/depreciacao.py`, com a IN RFB 1.700/2017 como referência normativa da vida útil padrão. Exceção: `baixa_ativo.valor_residual_baixa`, congelado na data da baixa (BR-015).

---

## 6. Mockaroo — entidades sintéticas

| Campo | Valor |
|---|---|
| **O que fornece** | Apenas entidades: colaboradores (nome, matrícula, e-mail, setor, cargo, localização) |
| **Autenticação** | N/A — ferramenta usada offline na geração; não é chamada em runtime |
| **Esquemas** | `dataset/synthetic/schemas/` |
| **CSVs gerados** | **Não gerados nem versionados** (D.5 encerrado em 2026-10-06: substituído pelo seed de demonstração, que cria os responsáveis `DEMO-`). Só os esquemas estão em `dataset/synthetic/schemas/` |
| **Gerador** | `python/etl/gerar_sinteticos.py` |
| **Mapeamento** | Tabela `responsavel` (ver [`docs/modelo-de-dados/dicionario-de-dados.md`](modelo-de-dados/dicionario-de-dados.md#33-setor-e-responsavel)), `data_source = sintetico` |
| **Requisitos atendidos** | FR-002 |
| **Limites de uso** | Plano gratuito do Mockaroo limita linhas por exportação — <!-- TODO: confirmar --> volume exato usado |
| **Licença** | Dados gerados não representam pessoas reais (ver `README.md`, seção "Licença") |

**Importante:** Mockaroo gera exclusivamente entidades — colaboradores. Não gera eventos. Setores usados pelo Mockaroo são referenciados por nome, mas o cadastro de `setor` em si é dado de configuração da organização fictícia, carregado pelo seed.

---

## 7. ETL — eventos sintéticos

**Encerrado em 2026-10-06 (D.7): substituído pelo seed de demonstração.** Não existe ETL de eventos sintéticos com `SYNTHETIC_SEED`. Os eventos que o projeto previa (transferências, baixas e instalações) são criados pelo seed de demonstração (`python -m app.seed_demo`, `python/app/seed_demo.py`), que chama os services (regras de negócio, trigger e auditoria valem), grava só `sintetico` e é idempotente. A associação ativo × software instalado não existe: o seed cria um software com licença e vínculos de licença, não "software sorteado por ciclo de vida".

Requisitos atendidos pelo seed: FR-002, FR-004, FR-005 (nos Gates 2 e 3) e FR-009 a FR-013 (no Gate 4).

---

## 8. Importação do usuário

Registrada aqui apenas por completude de `data_source`: planilhas CSV/XLSX enviadas via `POST /api/v1/importacoes` (FR-008) recebem `data_source = importacao`, salvo quando o arquivo traz a coluna opcional `data_source` com `compras_gov` (itens coletados do Compras.gov.br e exportados para planilha); `manual` não é aceito em arquivo, porque é a origem do cadastro pela API (AC-071). Não é uma fonte externa coletada — é dado informado pelo operador da API. Contrato completo do arquivo em [`docs/spec/pipeline-importacao.md`](spec/pipeline-importacao.md). Da mesma forma, registros criados direto pela API (`POST /ativos` e o vínculo de `POST /ativos/{id}/responsavel`) recebem `data_source = manual`.

---

## 9. Fronteira real × sintético

| Real (coletado de fonte pública, verificável) | Sintético (gerado, não representa fato real) |
|---|---|
| Item de TI, fabricante, modelo, preço, data de aquisição (Compras.gov.br) | Identidade do colaborador responsável (Mockaroo) |
| Ciclo de vida e fim de suporte de software (endoflife.date, só em `dataset/processed/`) | Data exata de uma transferência ou baixa específica (seed de demonstração) |
| Existência e severidade de uma CVE (NVD, só em `dataset/processed/`) | Qual ativo específico está vinculado a qual colaborador em um dado momento (seed de demonstração) |
| Vida útil e taxa de depreciação por categoria (IN RFB 1.700/2017 — norma, não coleta) | — |

A ADR-011 previu combinar as duas coisas num alerta de ciclo de vida ou de CVE. **Isso não existe na versão atual:** endoflife e NVD são só referência em `dataset/processed/`, não se ligam a nenhum ativo e não geram alerta. Os alertas de compliance do sistema (CP-01 a CP-04) usam licenças e responsáveis, não ciclo de vida nem CVE.

Consulta de verificação (já citada no `README.md`):

```sql
SELECT data_source, COUNT(*) FROM ativos GROUP BY data_source;
```

---

## 10. Conformidade com a LGPD

Nenhum dado de pessoa física neste projeto é real. A tabela `responsavel` — nome, matrícula, e-mail, cargo — é inteiramente gerada pelo Mockaroo (seção 6). Essa escolha não é uma limitação técnica, é a decisão correta em qualquer cenário: o ITAM não tem base legal, consentimento nem finalidade legítima para tratar dados de colaboradores reais de terceiros apenas para compor uma demonstração acadêmica. As únicas entidades com dado real neste projeto são objetos (ativos, softwares, vulnerabilidades) e valores públicos (preços de compras governamentais, normas), que não são dados pessoais sob a LGPD (Lei nº 13.709/2018, art. 5º, I).

Consequência prática: qualquer extensão futura que substitua o Mockaroo por uma fonte real de colaboradores (ex.: integração com AD/LDAP, fora do escopo do MVP — OUT-01 do PRD) exigiria, antes de qualquer coleta, base legal definida e DPO consultado. Isso está fora do escopo deste documento porque está fora do escopo do MVP.

---

## 11. Estado do pipeline (2026-10-06)

| Etapa | Estado |
|---|---|
| D.1 `compras_gov` | Coletor implementado (`python/collectors/compras_gov.py`) |
| D.2 arquivo do Gate 1 | `python/etl/exportar_inventario_demo.py` e `dataset/demo/` |
| D.3 `endoflife` | Coletor implementado (`python/collectors/endoflife.py`), fixtures reais, testes sem rede |
| D.4 `nvd` | Coletor implementado (`python/collectors/nvd.py`), fixtures reais, testes sem rede |
| D.5, D.7, D.8, D.9 | Encerrados: substituídos pelo seed de demonstração (decisão de 2026-10-06). Não há carga do pipeline no banco |
| D.6 normalização | `python/etl/normalizar.py` gera `dataset/processed/` (hardware, software × ciclo de vida × CVEs, cruzamento e `LEIAME.md`), sem rede e sem banco |

---

## 11. Origens oficiais de `data_source`

| Origem | Definição |
|---|---|
| `compras_gov` | Dado de coleta pública (Compras.gov.br), ou planilha gerada dela. |
| `importacao` | Registro vindo de arquivo enviado por um operador (`POST /importacoes`). |
| `manual` | Registro cadastrado pela API (`POST` das rotas de cadastro). É o padrão dos services. |
| `sintetico` | Registro criado só para demonstração, teste ou simulação. |

Dado público alimenta o inventário sempre que existe. O sintético representa apenas pessoas, vínculos e eventos internos que nenhuma fonte pública tem, e é sempre marcado `sintetico`: o ETL e o seed de demonstração (`python -m app.seed_demo`, ver [`docs/guia/demonstracao.md`](guia/demonstracao.md)) criam só `sintetico`. `setor`, `categoria` e `usuario` não têm a coluna; os setores `DEMO-` são sintéticos. `endoflife` e `nvd` (seções 2 e 3) **não são origens de registro do banco**: os coletores existem (D.3 e D.4), mas os dados ficam só em `dataset/raw/` e `dataset/processed/` como referência, e nenhuma tabela os recebe.

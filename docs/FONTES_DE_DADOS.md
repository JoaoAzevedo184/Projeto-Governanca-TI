# Fontes de Dados — ITAM

Detalha, fonte a fonte, o que o `README.md` resume na seção "Origem dos dados". A decisão de combinar dados reais e sintéticos, e as alternativas rejeitadas, estão em [`docs/adr/0011-estrategia-dados-reais-demonstracao.md`](adr/0011-estrategia-dados-reais-demonstracao.md). O mapeamento completo para colunas de tabela está em [`docs/modelo-de-dados/`](modelo-de-dados/README.md); este documento mapeia até o nível de tabela, não de coluna, para não duplicar o dicionário de dados.

---

## 1. Compras.gov.br — Dados Abertos

| Campo | Valor |
|---|---|
| **O que fornece** | Itens de TI efetivamente adquiridos por órgãos públicos federais: descrição, fabricante/marca, modelo, quantidade, valor unitário, data da compra, órgão comprador, classificado por código CATMAT |
| **URL base** | `https://dadosabertos.compras.gov.br` |
| **Documentação** | `https://dadosabertos.compras.gov.br/swagger-ui/index.html` |
| **Autenticação** | <!-- TODO: confirmar --> API de dados abertos; confirmar se algum endpoint usado exige chave ou se todos são de acesso público irrestrito |
| **Endpoints usados** | <!-- TODO: confirmar --> endpoint(s) de consulta de itens de compra/material por código CATMAT, a definir em `collectors/config.yaml` |
| **Campos aproveitados** | descrição do item, código CATMAT, fabricante, modelo, quantidade, valor unitário, data de homologação/compra, órgão |
| **Mapeamento** | `ativo.nome`, `ativo.valor_compra`, `ativo.data_aquisicao`, `ativo.fornecedor_id` (via razão social do fabricante, resolvida contra `fornecedor`), `categoria_id` (via classificação do CATMAT — ver seção 6) |
| **Requisitos atendidos** | FR-001, FR-003, FR-004 (fornecedor), FR-010, FR-011 |
| **Limites de uso** | <!-- TODO: confirmar --> limite de requisições por período da API de dados abertos |
| **Licença** | Dados abertos do Governo Federal brasileiro |

**Classificação CATMAT.** A normalização usa o código CATMAT para decidir a `categoria` do ativo (Notebook, Desktop, Servidor, Monitor, Impressora, Switch, Roteador etc.), conforme a tabela de vida útil do FR-003. Os códigos CATMAT específicos monitorados ficam em `collectors/config.yaml` — <!-- TODO: confirmar --> lista definitiva de códigos.

---

## 2. endoflife.date

| Campo | Valor |
|---|---|
| **O que fornece** | Ciclo de vida e fim de suporte de sistemas operacionais e produtos de software (datas de lançamento, fim de suporte ativo, fim de suporte estendido, última versão) |
| **URL base** | `https://endoflife.date/api/` |
| **Documentação** | `https://endoflife.date/docs/api` |
| **Autenticação** | Nenhuma — API pública, sem chave |
| **Endpoints usados** | `GET /api/<produto>.json` (lista de ciclos do produto) e/ou `GET /api/<produto>/<versao>.json` (ciclo específico) para os produtos configurados em `collectors/config.yaml` |
| **Campos aproveitados** | `cycle` (versão), `releaseDate`, `eol` (data de fim de suporte ou `false`), `latest` |
| **Mapeamento** | Tabela de ciclo de vida de software (ver [`docs/modelo-de-dados/dicionario-de-dados.md`](modelo-de-dados/dicionario-de-dados.md#produto_software) — nova, `data_source = endoflife`); referenciada pela associação ativo × software instalado |
| **Requisitos atendidos** | FR-004, FR-007 (CP-03 e correlatos de ciclo de vida) |
| **Limites de uso** | <!-- TODO: confirmar --> política de rate limit publicada pelo projeto |
| **Licença** | MIT |

**Uso pelo ETL sintético.** O ETL sorteia qual software está instalado em cada ativo, mas somente entre produtos e versões que existem nesta tabela — nunca inventa um produto ou uma versão de software.

---

## 3. NVD — National Vulnerability Database (NIST)

| Campo | Valor |
|---|---|
| **O que fornece** | Vulnerabilidades (CVE) e severidade (CVSS) associadas a um produto e versão |
| **URL base** | `https://services.nvd.nist.gov/rest/json/cves/2.0` |
| **Documentação** | `https://nvd.nist.gov/developers/vulnerabilities` |
| **Autenticação** | Opcional via `NVD_API_KEY` (cabeçalho `apiKey`), solicitada em `https://nvd.nist.gov/developers/request-an-api-key`; sem a chave, o limite de requisições é mais restrito (ver `README.md`, seção "Pré-requisitos") |
| **Endpoints usados** | `GET /rest/json/cves/2.0?keywordSearch=<produto>` ou parâmetro equivalente por CPE <!-- TODO: confirmar --> parâmetro exato de busca por produto/versão usado pelo coletor |
| **Campos aproveitados** | `id` (CVE), `descriptions`, `metrics` (score CVSS), `published`, `cpeMatch`/CPE do produto afetado |
| **Mapeamento** | Tabela de vulnerabilidades (ver [`docs/modelo-de-dados/dicionario-de-dados.md`](modelo-de-dados/dicionario-de-dados.md#vulnerabilidade) — nova, `data_source = nvd`), vinculada ao mesmo produto/versão de software da tabela de ciclo de vida |
| **Requisitos atendidos** | FR-007 (compliance de segurança), FR-012 (insumo para registro de riscos) |
| **Limites de uso** | <!-- TODO: confirmar valores vigentes --> historicamente 5 requisições por janela de 30s sem chave e 50 por janela de 30s com chave |
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
| **Esquemas** | `data/synthetic/schemas/` |
| **CSVs gerados** | `data/synthetic/`, versionados no repositório para reprodutibilidade |
| **Gerador** | `scripts/gerar_sinteticos.py` |
| **Mapeamento** | Tabela `responsavel` (ver [`docs/modelo-de-dados/dicionario-de-dados.md`](modelo-de-dados/dicionario-de-dados.md#33-setor-e-responsavel)), `data_source = sintetico` |
| **Requisitos atendidos** | FR-002 |
| **Limites de uso** | Plano gratuito do Mockaroo limita linhas por exportação — <!-- TODO: confirmar --> volume exato usado |
| **Licença** | Dados gerados não representam pessoas reais (ver `README.md`, seção "Licença") |

**Importante:** Mockaroo gera exclusivamente entidades — colaboradores. Não gera eventos. Setores usados pelo Mockaroo são referenciados por nome, mas o cadastro de `setor` em si é dado de configuração da organização fictícia, carregado pelo seed.

---

## 7. ETL — eventos sintéticos

| Campo | Valor |
|---|---|
| **O que fornece** | Eventos: transferências (`historico_transferencia`), baixas/descartes (`baixa_ativo`) e a associação ativo × software instalado (`licenca_vinculo` ou tabela equivalente de software instalado) |
| **Semente** | Fixa, via variável de ambiente `SYNTHETIC_SEED` — reprodutível entre execuções |
| **Regras de negócio respeitadas** | Nenhum evento anterior à `data_aquisicao` do ativo (BR-010); nenhuma transferência após a baixa (BR-009); baixa preferencialmente atribuída a ativos com vida útil encerrada; software sorteado apenas entre produtos/versões presentes na tabela de ciclo de vida do endoflife.date (seção 2) |
| **`data_source`** | `sintetico` |
| **Requisitos atendidos** | FR-002, FR-004, FR-005, FR-007 |
| **Onde vive** | `etl/`, fora de `app/` — a API nunca invoca o ETL durante uma requisição |

---

## 8. Importação do usuário

Registrada aqui apenas por completude de `data_source`: planilhas CSV/XLSX enviadas via `POST /api/v1/importacoes` (FR-008) recebem `data_source = importacao`. Não é uma fonte externa coletada — é dado informado pelo operador da API. Contrato completo do arquivo em [`docs/spec/pipeline-importacao.md`](spec/pipeline-importacao.md).

---

## 9. Fronteira real × sintético

| Real (coletado de fonte pública, verificável) | Sintético (gerado, não representa fato real) |
|---|---|
| Item de TI, fabricante, modelo, preço, data de aquisição (Compras.gov.br) | Identidade do colaborador responsável (Mockaroo) |
| Ciclo de vida e fim de suporte de software (endoflife.date) | Data exata de uma transferência ou baixa específica (ETL) |
| Existência e severidade de uma CVE (NVD) | Qual ativo específico está vinculado a qual colaborador em um dado momento (ETL) |
| Vida útil e taxa de depreciação por categoria (IN RFB 1.700/2017 — norma, não coleta) | — |

A combinação é o que sustenta o alerta: **o fato de que o produto está fora de suporte, ou que a CVE existe, é real — apenas a atribuição de "este ativo específico tem esta versão instalada" é sintética.** Isso é intencional (ver ADR-011): o alerta de compliance gerado a partir dela continua sendo uma demonstração verdadeira da regra de negócio, não uma simulação vazia.

Consulta de verificação (já citada no `README.md`):

```sql
SELECT data_source, COUNT(*) FROM ativos GROUP BY data_source;
```

---

## 10. Conformidade com a LGPD

Nenhum dado de pessoa física neste projeto é real. A tabela `responsavel` — nome, matrícula, e-mail, cargo — é inteiramente gerada pelo Mockaroo (seção 6). Essa escolha não é uma limitação técnica, é a decisão correta em qualquer cenário: o ITAM não tem base legal, consentimento nem finalidade legítima para tratar dados de colaboradores reais de terceiros apenas para compor uma demonstração acadêmica. As únicas entidades com dado real neste projeto são objetos (ativos, softwares, vulnerabilidades) e valores públicos (preços de compras governamentais, normas), que não são dados pessoais sob a LGPD (Lei nº 13.709/2018, art. 5º, I).

Consequência prática: qualquer extensão futura que substitua o Mockaroo por uma fonte real de colaboradores (ex.: integração com AD/LDAP, fora do escopo do MVP — OUT-01 do PRD) exigiria, antes de qualquer coleta, base legal definida e DPO consultado. Isso está fora do escopo deste documento porque está fora do escopo do MVP.

---

## 11. O que ainda não existe no código

Os componentes citados neste documento e no `README.md` — `collectors/`, `etl/`, `collectors/config.yaml`, `scripts/gerar_sinteticos.py`, `scripts/collect.sh`, `data/raw/`, `data/processed/`, `data/synthetic/`, `tests/fixtures/` — descrevem a arquitetura de dados **decidida**, não o estado atual do repositório. Ver a lista completa de pendências no resumo desta atualização de documentação.

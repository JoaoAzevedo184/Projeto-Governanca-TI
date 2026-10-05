# ADR-011 — Estratégia de dados reais para a base de demonstração

| Campo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-09-27 |
| **Relacionado a** | FR-001, FR-003, FR-004, FR-007, [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md) |

> A partir desta ADR, `docs/adr/` passa a ser o local dos registros de decisão arquitetural completos. As ADR-001 a ADR-010, resumidas em [`docs/spec/adrs-e-rastreabilidade.md`](../spec/adrs-e-rastreabilidade.md), continuam válidas nesse formato tabular; apenas decisões novas ganham arquivo próprio aqui.

## Contexto

A base de demonstração do ITAM precisa sustentar indicadores de depreciação, conformidade de licenciamento e exposição a vulnerabilidades que sejam **defensáveis na apresentação**: um valor residual calculado sobre um preço inventado, ou um alerta de fim de suporte sobre uma versão de software que nunca existiu, não comprova que a regra de negócio funciona — comprova apenas que o dataset foi bem desenhado. Ao mesmo tempo, o projeto não pode depender de descoberta automática de inventário (fora de escopo, OUT-02 do PRD) nem armazenar dados pessoais reais de colaboradores, o que violaria a LGPD sem necessidade, já que a demonstração não exige que as pessoas sejam reais — exige que os ativos, preços e datas sejam.

A equipe avaliou quatro fontes candidatas para ancorar o inventário em dado público verificável antes de decidir pela combinação registrada abaixo.

## Decisão

Adotar dados reais onde eles existem publicamente e são verificáveis, e dados sintéticos apenas onde o dado real não deveria existir (pessoas) ou não é publicamente auditável (eventos internos da organização fictícia):

1. **Itens de TI e preços** — API de Dados Abertos do Compras.gov.br, filtrados por código CATMAT de TI. Preço e data de aquisição são os valores reais da compra pública.
2. **Ciclo de vida de software** — endoflife.date.
3. **Vulnerabilidades** — API do NVD (NIST).
4. **Depreciação** — calculada, não coletada: Anexo III da IN RFB nº 1.700/2017.
5. **Pessoas (colaboradores) e eventos internos (transferências, baixas, associação ativo × software)** — sintéticos, gerados por Mockaroo (entidades) e por um ETL com semente fixa (eventos), respeitando as regras de negócio do PRD e sorteando software apenas entre produtos/versões reais do endoflife.date.

Toda tabela principal carrega `data_source` (`compras_gov`, `endoflife`, `nvd`, `sintetico`, `importacao`), tornando a fronteira real × sintético consultável em runtime, não apenas documentada. Detalhamento de endpoints, autenticação e mapeamento de campos em [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md).

## Alternativas consideradas e rejeitadas

| Alternativa | Por que foi rejeitada |
|---|---|
| **GLPI Agent para inventário automático** | Descartada pela equipe por baixa utilidade para o escopo: exige agente instalável nas máquinas monitoradas, o que está fora do escopo do MVP (OUT-02) e não se aplica a uma base de *demonstração* — não há parque físico real para inventariar. |
| **Scraping de lojas de hardware** | Fragilidade estrutural (o HTML de e-commerce muda sem aviso e quebra o coletor silenciosamente), risco de violar termos de uso dos sites-alvo, e preço volátil — o mesmo item custa valores diferentes em datas próximas, o que introduziria ruído na depreciação sem ganho correspondente de credibilidade. |
| **Datasets do Kaggle** | Avaliados dois candidatos: o dataset de ativos de TI ao estilo SAP é ele próprio sintético (não resolve o problema, só o terceiriza), e o S&P 500 é irrelevante para o domínio de ITAM. Nenhum dataset do Kaggle encontrado combina itens de TI reais com preço e data de aquisição verificáveis. |
| **Dados 100% sintéticos** | Enfraquece a credibilidade dos indicadores: um valor residual calculado sobre um preço inventado não é evidência de nada, e a disciplina exige que "nenhuma recomendação [seja feita] sem evidência" (princípio estruturante do `README.md`). |

## Decisão — identificador do ativo e fornecedor em compras públicas

`ck_ativo_identificador` exige `numero_serie` (HARDWARE) ou `chave_licenca` (SOFTWARE), mas o Compras.gov.br não expõe número de série por unidade — o item de compra é uma linha com quantidade, não uma lista de números de série.

**Fornecedor vencedor por item — resolvido.** O endpoint `/modulo-legado/2_consultarItemLicitacao` da [API Compras.gov.br](https://dadosabertos.compras.gov.br/swagger-ui/index.html) (schema `TbVwItemLicitacaoDTO`) retorna `nome_fornecedor` e `cnpj_fornecedor` por item, junto com `quantidade`, `id_compra` e `id_compra_item`. Não é preciso fornecedor genérico nem item pendente — o fornecedor é resolvido/criado por CNPJ na tabela `fornecedor` como qualquer outro cadastro.

**Identificador — combinação das alternativas 1 e 2.** Como `quantidade` é numérica por item (não uma lista de seriais) e pode ser grande demais pra virar 1:1 em ativos, o coletor expande cada item até um teto configurável (evita gerar milhares de ativos de uma única linha de compra) e deriva `numero_serie` determinístico e rastreável à compra de origem:

```
numero_serie = f"CG-{id_compra}-{id_compra_item}-{sequencial}"
```

Sinalizado como gerado (não é número de série de fábrica) — mesmo padrão de `data_source = "importacao"` já usado pra distinguir origem sem exigir campo novo. Fica para a implementação de D.1 decidir o teto de expansão por item (parâmetro de configuração, não hardcoded).

## Consequências

**Positivas**

- Depreciação, cobertura de inventário e valor patrimonial tornam-se auditáveis contra uma fonte pública externa ao projeto.
- Alertas de compliance de ciclo de vida e vulnerabilidade (CP-03, CP-05 e correlatos) refletem produtos e CVEs reais, não combinações artificiais.
- A coluna `data_source` torna a fronteira real × sintético uma consulta SQL, não uma afirmação no README.

**Negativas / custo aceito**

- O projeto passa a depender da disponibilidade e da estabilidade de três APIs externas (Compras.gov.br, endoflife.date, NVD) no momento da coleta. Mitigado por `dataset/raw/` imutável: a coleta não precisa ser refeita a cada carga, e a API do ITAM nunca depende dessas fontes em tempo de requisição.
- O catálogo de itens de TI disponíveis no Compras.gov.br é o que existe nos pregões públicos coletados — a diversidade de categorias no inventário fica limitada ao que órgãos públicos efetivamente compraram, e não a um catálogo desenhado sob medida para cobrir todos os cenários de compliance do dataset.
- Coordenar três coletores com regras de negócio do ETL (nenhum evento antes da aquisição, baixa preferencialmente em ativos com vida útil encerrada etc.) é mais complexo do que um gerador sintético único — custo aceito porque é o único caminho que preserva preço e data reais.

## Atualização de 2026-10-05 (D.1 e D.2)

A implementação do coletor (D.1) e do arquivo do Gate 1 (D.2) corrigiu dois pontos da decisão
sobre identificador e fornecedor acima. O restante da ADR segue valendo.

- **Endpoint.** O `/modulo-legado/2_consultarItemLicitacao` não serve: não traz preço pago nem data
  da compra (só `valor_estimado` e `dt_alteracao`), e numa amostra de 188 registros só 27 vinham
  com CNPJ do fornecedor e 29 com `valor_estimado` maior que zero. O coletor usa
  `/modulo-pesquisa-preco/1_consultarMaterial` (`tipo=codigoPdm`), que traz `precoUnitario`,
  `dataCompra`, `niFornecedor` (CNPJ), `nomeFornecedor`, `marca`, `idCompra`, `idCompraItem` e
  `idItemCompra`. Detalhes em `docs/FONTES_DE_DADOS.md`.
- **Identificador.** A fórmula `CG-{id_compra}-{id_compra_item}-{sequencial}` colide: em 13 itens
  da coleta o mesmo `idCompraItem` aparece com fornecedores e preços diferentes. O identificador
  passa a ser `numero_serie = CG-{idItemCompra}-001`, e `idItemCompra` é único nos 1705 registros
  coletados. A expansão por quantidade e o teto ficam para a carga do pipeline (D.8); o arquivo do
  Gate 1 usa uma linha por item de compra.
- **É sintético.** Esse número **não é número de série de fábrica**: a fonte pública não traz
  número de série. É um identificador técnico, derivado do item de compra, que só existe para
  satisfazer `ck_ativo_identificador` e a unicidade (BR-001). Deve ser tratado e documentado assim
  onde aparecer (`dataset/demo/inventario_demo.LEIAME.md`).
- **Fornecedor.** Vem de `nomeFornecedor` (razão social do vencedor) e `niFornecedor` (CNPJ), com
  `data_source = compras_gov`; o importador o resolve por razão social exata, então os fornecedores
  são carregados antes (`python -m etl.carregar_fornecedores`).

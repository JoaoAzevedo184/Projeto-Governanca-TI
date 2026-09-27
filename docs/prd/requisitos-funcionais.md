# PRD — Requisitos Funcionais (FR-)

Parte de [PRD — ITAM](README.md).

## 10. Requisitos Funcionais

### 10.1 Visão consolidada

| ID | Requisito | Prioridade | Épico | Depende de |
|---|---|---|---|---|
| FR-001 | Cadastro de Ativos | Must | E1 | — |
| FR-002 | Vinculação de Responsável | Must | E2 | FR-001 |
| FR-003 | Cálculo de Depreciação | Must | E3 | FR-001 |
| FR-004 | Controle de Licenças de Software | Must | E4 | FR-001 |
| FR-005 | Baixa/Descarte de Ativo | Must | E5 | FR-001, FR-002 |
| FR-006 | Relatório de Inventário | Must | E6 | FR-001, FR-003 |
| FR-007 | Alerta de Compliance | Must | E6 | FR-002, FR-004, FR-005 |
| FR-008 | Importação de Inventário | Must | E7 | FR-001 |
| FR-009 | Indicadores de ITAM | Must | E7 | FR-001 a FR-005 |
| FR-010 | Comparação de Cenários e TCO | Should | E7 | FR-003, FR-009 |
| FR-011 | Scorecard de Fornecedores | Should | E7 | FR-001 |
| FR-012 | Registro de Riscos | Should | E7 | — |
| FR-013 | Recomendação Rastreável | Must | E7 | FR-009, FR-012 |
| FR-014 | Dashboard e Observabilidade | Must | E7 | FR-009 |
| FR-015 | Autenticação e Controle de Acesso | Must | E8 | — |

> **Nota de escopo.** Os requisitos **FR-001 a FR-007** constituem o núcleo funcional definido originalmente. Os requisitos **FR-008 a FR-015** são a extensão exigida pela baseline da disciplina (ingestão de dataset, indicadores, decisão rastreável, observabilidade e segurança) e cobrem as dimensões da rubrica de avaliação que o núcleo sozinho não alcança.

> **Nota de origem dos dados.** Onde um requisito ou critério de aceite depende de um dado concreto para ser demonstrado, a origem desse dado (real, coletado, ou sintético) está indicada junto ao requisito. Detalhamento fonte a fonte em [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md); a decisão de combinar dado real e sintético está registrada em [ADR-011](../adr/0011-estrategia-dados-reais-demonstracao.md).

---

### FR-001 — Cadastro de Ativos

**Descrição.** O sistema deve permitir registrar, consultar, editar e listar ativos de TI.

**Origem dos dados.** Na base de demonstração, o ativo é criado a partir de um item de TI realmente adquirido por um órgão público (`data_source = compras_gov`) ou a partir de uma planilha enviada pelo usuário via FR-008 (`data_source = importacao`) — nunca digitado manualmente com valores inventados. Nome, valor de compra e data de aquisição são, portanto, reais quando `data_source = compras_gov`.

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `nome` | Texto (3–120) | Sim | — |
| `tipo` | Enum | Sim | `HARDWARE` \| `SOFTWARE` |
| `categoria` | Referência | Sim | Deve existir em Categoria |
| `numero_serie` | Texto (até 80) | Condicional | Obrigatório e único quando `tipo = HARDWARE` |
| `chave_licenca` | Texto (até 200) | Condicional | Obrigatório quando `tipo = SOFTWARE` |
| `data_aquisicao` | Data | Sim | Não pode ser futura |
| `valor_compra` | Decimal(12,2) | Sim | > 0 |
| `fornecedor` | Referência | Sim | Deve existir em Fornecedor |
| `status` | Enum | Sim | `ATIVO` \| `EM_MANUTENCAO` \| `BAIXADO`; padrão `ATIVO` |
| `vida_util_meses` | Inteiro | Não | Herdada da categoria se omitida; sobrescrevível |
| `localizacao` | Texto (até 120) | Não | — |
| `observacoes` | Texto (até 500) | Não | — |

**Comportamentos:**
- Na criação, o status assume `ATIVO` e a vida útil é herdada da categoria.
- O número de série é único em todo o sistema, incluindo ativos baixados.
- A transição para `BAIXADO` ocorre exclusivamente via FR-005, nunca por edição direta do campo.
- Listagem paginada, ordenável e filtrável por todos os campos indexados.

---

### FR-002 — Vinculação de Responsável

**Descrição.** O sistema deve associar cada ativo a um responsável (usuário e/ou setor) e manter o histórico completo de transferências.

**Origem dos dados.** O colaborador responsável é sempre sintético (`data_source = sintetico`, gerado por Mockaroo) — dado de pessoa real não é usado, por exigência da LGPD (ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md), seção 10). O evento de vínculo/transferência em si também é sintético, gerado pelo ETL com semente fixa, respeitando BR-009 e BR-010.

**Campos do vínculo:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `ativo` | Referência | Sim | Status ≠ `BAIXADO` |
| `responsavel` | Referência | Sim | Usuário ativo |
| `setor` | Referência | Sim | Setor ativo |
| `data_inicio` | Data | Sim | Não futura; ≥ `data_aquisicao` do ativo |
| `data_fim` | Data | Não | Preenchida automaticamente na transferência |
| `motivo` | Texto (até 200) | Não | — |
| `registrado_por` | Referência | Sim | Preenchido pelo sistema |

**Comportamentos:**
- Um ativo possui no máximo um vínculo aberto (`data_fim` nula) por vez.
- A transferência encerra o vínculo aberto com `data_fim = data_inicio` do novo vínculo e cria o novo em uma única transação.
- Vínculos encerrados são imutáveis: não admitem edição nem exclusão.
- A consulta de histórico retorna todos os vínculos em ordem cronológica decrescente.
- Ativos sem vínculo aberto são sinalizados pelo FR-007.

---

### FR-003 — Cálculo de Depreciação

**Descrição.** O sistema deve calcular a depreciação pelo método linear, com vida útil configurável por categoria.

**Origem dos dados.** A depreciação em si não é coletada nem armazenada — é calculada sob demanda a partir de `valor_compra` e `data_aquisicao` (reais, quando o ativo tem `data_source = compras_gov`) e da vida útil padrão por categoria, referenciada na IN RFB nº 1.700/2017 (norma, não API — ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md), seção 4). Como o preço e a data de aquisição são reais na maior parte da base, o valor residual exibido também é.

**Fórmulas:**

```
meses_decorridos      = meses_entre(data_aquisicao, data_referencia)
meses_efetivos        = min(meses_decorridos, vida_util_meses)
depreciacao_mensal    = valor_compra / vida_util_meses
depreciacao_acumulada = depreciacao_mensal × meses_efetivos
valor_residual        = max(valor_compra − depreciacao_acumulada, 0)
percentual_depreciado = (depreciacao_acumulada / valor_compra) × 100
```

**Regras:**
- `data_referencia` é a data corrente para ativos em operação e a `data_baixa` para ativos baixados.
- Vida útil padrão por categoria (referência: IN RFB nº 1.700/2017, anexo III):

| Categoria | Vida útil (meses) | Taxa anual |
|---|---|---|
| Notebook / Desktop | 60 | 20% |
| Servidor | 60 | 20% |
| Monitor | 60 | 20% |
| Switch / Roteador | 60 | 20% |
| Impressora | 48 | 25% |
| Smartphone / Tablet | 36 | 33,3% |
| Nobreak | 60 | 20% |
| Software (licença perpétua) | 60 | 20% |

- O valor residual nunca é negativo; ao atingir a vida útil, estabiliza em zero.
- O cálculo é determinístico e recalculado sob demanda, não persistido como valor congelado — exceto na baixa.
- Arredondamento em duas casas decimais, modo *half-up*.

---

### FR-004 — Controle de Licenças de Software

**Descrição.** O sistema deve registrar licenças de software e monitorar sua conformidade quantitativa e temporal.

**Origem dos dados.** O contrato de licença (`licenca`) é sintético (`data_source = sintetico`): não existe fonte pública de contratos comerciais de licenciamento. Já o **produto e a versão** eventualmente instalados em cada ativo são sorteados apenas entre software real cadastrado a partir do endoflife.date (`data_source = endoflife`) — a associação é sintética, o produto não é (ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md), seção 9).

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `software` | Texto (3–120) | Sim | — |
| `fornecedor` | Referência | Sim | — |
| `chave_licenca` | Texto (até 200) | Sim | — |
| `quantidade_contratada` | Inteiro | Sim | ≥ 1 |
| `quantidade_em_uso` | Inteiro | Sim | ≥ 0; derivado dos vínculos |
| `data_aquisicao` | Data | Sim | Não futura |
| `data_expiracao` | Data | Sim | > `data_aquisicao` |
| `valor_total` | Decimal(12,2) | Sim | > 0 |
| `tipo_licenciamento` | Enum | Sim | `PERPETUA` \| `SUBSCRICAO` \| `OEM` |

**Alertas gerados:**

| Condição | Severidade | Mensagem |
|---|---|---|
| `quantidade_em_uso > quantidade_contratada` | **Crítico** | Uso acima do contratado — risco de autuação |
| `data_expiracao < hoje` | **Crítico** | Licença vencida |
| `data_expiracao − hoje ≤ 30 dias` | **Alto** | Licença próxima do vencimento |
| `quantidade_em_uso = quantidade_contratada` | **Médio** | Licença saturada — sem saldo disponível |
| `quantidade_em_uso ≤ 50% do contratado` após 6 meses | **Baixo** | Subutilização — oportunidade de redução |

**Comportamentos:**
- A vinculação que faria `quantidade_em_uso` exceder o contratado é **bloqueada** e registrada na auditoria.
- A janela de alerta antecipado (30 dias) é parâmetro configurável.
- Licenças vencidas permanecem no sistema, sinalizadas, até renovação ou baixa.

---

### FR-005 — Baixa/Descarte de Ativo

**Descrição.** O sistema deve registrar a baixa de um ativo, retirando-o do inventário operacional e preservando o histórico permanentemente.

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `ativo` | Referência | Sim | Status ≠ `BAIXADO` |
| `motivo` | Enum | Sim | `OBSOLESCENCIA` \| `DEFEITO` \| `FURTO_ROUBO` \| `FIM_VIDA_UTIL` \| `OUTRO` |
| `justificativa` | Texto (10–500) | Sim quando `motivo = OUTRO` | — |
| `data_baixa` | Data | Sim | Não futura; ≥ `data_aquisicao` |
| `destinacao` | Enum | Sim | `RECICLAGEM_CERTIFICADA` \| `DOACAO` \| `DEVOLUCAO_FORNECEDOR` \| `VENDA` \| `DESCARTE` |
| `valor_residual_baixa` | Decimal(12,2) | Sim | Calculado pelo sistema na data da baixa |
| `registrado_por` | Referência | Sim | Preenchido pelo sistema |

**Comportamentos:**
- Ao registrar a baixa: status → `BAIXADO`, vínculo de responsável aberto é encerrado, depreciação é congelada e persistida.
- O ativo desaparece do inventário ativo, mas permanece acessível por filtro explícito e pelo histórico.
- A baixa é irreversível no MVP; estorno exige nova versão do produto.
- O campo `destinacao` sustenta a evidência de TI Verde e o relatório de descarte.

---

### FR-006 — Relatório de Inventário

**Descrição.** O sistema deve gerar relatórios do inventário com filtros combináveis e exportação.

**Filtros disponíveis:**

| Filtro | Tipo | Observação |
|---|---|---|
| Status | Múltipla escolha | Ativo, Em manutenção, Baixado |
| Tipo | Múltipla escolha | Hardware, Software |
| Categoria | Múltipla escolha | — |
| Responsável | Busca | Usuário ou setor |
| Fornecedor | Múltipla escolha | — |
| Faixa de valor depreciado | Intervalo numérico | Valor mínimo e máximo |
| Percentual depreciado | Intervalo | 0–100% |
| Período de aquisição | Intervalo de datas | — |
| Próximos do fim da vida útil | Booleano | ≥ 80% da vida útil consumida |

**Saída do relatório:** identificador, nome, tipo, categoria, número de série ou chave, responsável atual, setor, status, data de aquisição, valor de compra, depreciação acumulada, percentual depreciado, valor residual, fornecedor.

**Comportamentos:**
- Filtros combináveis por conjunção (AND).
- Exportação em CSV e XLSX, com cabeçalho contendo data/hora de geração e usuário solicitante.
- Totalizadores no rodapé: contagem de ativos, soma de valor de compra, soma de valor residual.
- Paginação obrigatória na visualização; exportação sem limite de linhas.

---

### FR-007 — Alerta de Compliance

**Descrição.** O sistema deve manter um painel consolidado de não conformidades, avaliadas em tempo de consulta.

**Origem dos dados.** CP-01 a CP-03 (licenciamento) e CP-04 a CP-09 (ativo) usam apenas dados já presentes em `ativo`, `licenca` e `historico_transferencia`. Os alertas de ciclo de vida e vulnerabilidade de software instalado (extensão de FR-007 sobre a tabela `ativo_software`, ver [`docs/modelo-de-dados/dicionario-de-dados.md`](../modelo-de-dados/dicionario-de-dados.md#311-ciclo-de-vida-de-software-e-vulnerabilidades)) dependem de `produto_software.data_fim_suporte` (`data_source = endoflife`) e de `vulnerabilidade` (`data_source = nvd`) — a data de fim de suporte e a existência da CVE são reais, ainda que a atribuição a um ativo específico seja sintética.

**Regras de sinalização:**

| ID | Condição | Severidade | Origem |
|---|---|---|---|
| CP-01 | Licença com `data_expiracao < hoje` | Crítico | FR-004 |
| CP-02 | Licença com `quantidade_em_uso > quantidade_contratada` | Crítico | FR-004 |
| CP-03 | Licença expirando em ≤ 30 dias | Alto | FR-004 |
| CP-04 | Ativo `ATIVO` sem vínculo de responsável aberto | Alto | FR-002 |
| CP-05 | Ativo totalmente depreciado ainda em operação | Médio | FR-003 |
| CP-06 | Ativo `EM_MANUTENCAO` há mais de 90 dias | Médio | FR-001 |
| CP-07 | Ativo baixado sem destinação registrada | Médio | FR-005 |
| CP-08 | Ativo sem movimentação registrada há mais de 12 meses | Baixo | FR-002 |
| CP-09 | Ativo com valor de compra ausente ou zerado | Baixo | FR-001 |

**Comportamentos:**
- O painel agrupa por severidade e permite navegar do alerta para o registro de origem.
- Cada alerta exibe a regra aplicada, tornando a sinalização explicável.
- O conjunto de alertas é exportável como relatório de conformidade datado.
- Alertas não são persistidos como registros próprios: são derivados do estado atual, o que garante que nunca fiquem obsoletos.

---

### FR-008 — Importação de Inventário *(extensão)*

**Descrição.** O sistema deve importar ativos em lote a partir de arquivos CSV ou XLSX.

**Comportamentos:**
- Validação dos cabeçalhos esperados antes de processar as linhas.
- Conversão e validação de datas, valores decimais e enumerados.
- Detecção de duplicidade por número de série, dentro do arquivo e contra a base.
- Separação entre registros válidos (importados) e inválidos (rejeitados).
- Criação de um **lote de importação** com identificador, data, usuário, total processado, total aceito e total rejeitado.
- Relatório de erros por linha, com número da linha, campo e motivo da rejeição, exportável.
- A importação é atômica por registro: um registro inválido não impede os demais.

---

### FR-009 — Indicadores de ITAM *(extensão)*

**Descrição.** O sistema deve calcular e expor indicadores agregados do parque.

| Indicador | Fórmula |
|---|---|
| Total de ativos por status | contagem agrupada |
| Distribuição hardware x software | contagem por tipo |
| Valor patrimonial bruto | soma de `valor_compra` dos ativos não baixados |
| Valor residual total | soma de `valor_residual` dos ativos não baixados |
| Percentual depreciado do parque | (1 − valor residual / valor bruto) × 100 |
| Cobertura de responsáveis | ativos com vínculo aberto / ativos ativos |
| Conformidade de licenças | licenças conformes / total de licenças |
| Idade média do parque | média de (hoje − `data_aquisicao`) em meses |
| Custo médio por ativo | valor patrimonial bruto / total de ativos |
| Ativos ociosos | ativos sem movimentação em 12 meses / total |
| Taxa de baixas no período | baixas no período / total de ativos no início do período |

**Comportamentos:**
- Todos os indicadores são filtráveis por categoria, setor, fornecedor e período.
- A resposta expõe a fórmula aplicada e o tamanho da amostra, permitindo verificação.

---

### FR-010 — Comparação de Cenários e TCO *(extensão)*

**Descrição.** O sistema deve comparar alternativas de tratamento do parque com horizonte de cinco anos.

**Cenários:** `MANTER` (prorrogar o uso), `RENOVAR` (substituir por equipamento equivalente), `MIGRAR_ASSINATURA` (substituir aquisição por serviço recorrente).

**Para cada cenário o sistema calcula:** CAPEX inicial, OPEX anual, TCO de 5 anos, custo por ativo/ano, economia relativa ao cenário baseline e score de risco agregado.

**Comportamento crítico:** o sistema **ordena** os cenários por custo e risco, mas **não seleciona** automaticamente a alternativa. A decisão permanece humana e deve ser registrada via FR-013.

---

### FR-011 — Scorecard de Fornecedores *(extensão)*

**Descrição.** O sistema deve avaliar fornecedores por critérios ponderados.

**Comportamentos:**
- Critérios configuráveis com pesos que devem totalizar exatamente 100%.
- Notas por critério no intervalo de 0 a 10; nota obrigatória para todos os critérios.
- Pontuação ponderada calculada e ranking produzido.
- Critérios sugeridos: preço, prazo de entrega, qualidade do suporte, taxa de defeitos no período, aderência contratual.
- Rejeição explícita de submissões com soma de pesos diferente de 100% ou com critérios sem nota.

---

### FR-012 — Registro de Riscos *(extensão)*

**Descrição.** O sistema deve manter um registro formal de riscos do parque de TI.

**Campos:** título, descrição, categoria (operacional, financeiro, legal, segurança, continuidade), probabilidade (1–5), impacto (1–5), `score = probabilidade × impacto`, resposta (aceitar, mitigar, transferir, evitar), responsável, status, gatilho, data de revisão.

**Classificação:** score 1–4 baixo, 5–9 médio, 10–14 alto, 15–25 crítico.

---

### FR-013 — Recomendação Rastreável *(extensão)*

**Descrição.** O sistema deve registrar recomendações de decisão, obrigatoriamente vinculadas a evidências.

**Regra estruturante:** uma recomendação **só pode ser gravada** se possuir ao menos uma evidência associada. Evidências admitidas: indicador calculado (FR-009), risco registrado (FR-012), ativo ou licença específicos, resultado de scorecard (FR-011), cenário comparado (FR-010) ou premissa financeira declarada.

**Campos:** título, contexto, recomendação, alternativas consideradas, evidências vinculadas (≥ 1), responsável pela decisão, data, status (proposta, aprovada, rejeitada, implementada).

Tentativas de gravar recomendação sem evidência retornam erro de validação com mensagem explícita.

---

### FR-014 — Dashboard e Observabilidade *(extensão)*

**Descrição.** O sistema deve expor painel gerencial e instrumentação técnica.

**Painel gerencial:** indicadores do FR-009 com visualização gráfica, painel de alertas do FR-007 e atalhos para os relatórios do FR-006.

**Instrumentação técnica:**
- `GET /health` — estado da aplicação e da conexão com o banco;
- `GET /metrics` — métricas no formato de exposição Prometheus;
- contador de requisições por endpoint e por código de retorno;
- histograma de duração das requisições;
- identificação do ambiente em execução na resposta do health check.

---

### FR-015 — Autenticação e Controle de Acesso *(extensão)*

**Descrição.** O sistema deve autenticar usuários e restringir operações por perfil.

| Perfil | Ativos | Responsáveis | Licenças | Baixas | Relatórios | Configuração |
|---|---|---|---|---|---|---|
| `ADMIN` | CRUD | CRUD | CRUD | Criar | Ler | CRUD |
| `OPERADOR` | Criar, Ler, Editar | Criar, Ler | Ler, Editar | Criar | Ler | — |
| `GESTOR` | Ler | Ler | Ler | Ler | Ler | — |
| `AUDITOR` | Ler | Ler | Ler | Ler | Ler | — |

Autenticação por JWT com expiração configurável. Toda operação de escrita registra autor e carimbo de tempo.


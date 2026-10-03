# SPEC — Contrato da API

Parte de [SPEC — ITAM](README.md).

## 6. Contrato da API

**Prefixo:** `/api/v1` · **Formato:** JSON · **Autenticação:** `Authorization: Bearer <jwt>` em todos os endpoints exceto `/auth/login`, `/health` e `/metrics`.

### 6.1 Autenticação

| Método | Rota | Perfis | Descrição |
|---|---|---|---|
| POST | `/auth/login` | público | Emite JWT a partir de login e senha |
| GET | `/auth/me` | todos | Retorna o usuário autenticado e seu perfil |

### 6.2 Cadastros de apoio

| Método | Rota | Perfis | FR |
|---|---|---|---|
| GET/POST | `/categorias` | GET: todos · POST: ADMIN | FR-001 |
| GET/PATCH | `/categorias/{id}` | ADMIN | FR-001 |
| GET/POST | `/fornecedores` | GET: todos · POST: ADMIN | FR-001 |
| GET/POST | `/setores` | GET: todos · POST: ADMIN | FR-002 |
| GET/POST | `/responsaveis` | GET: todos · POST: ADMIN, OPERADOR | FR-002 |

### 6.3 Ativos

| Método | Rota | Perfis | FR |
|---|---|---|---|
| POST | `/ativos` | ADMIN, OPERADOR | FR-001 |
| GET | `/ativos` | todos | FR-001, FR-006 |
| GET | `/ativos/{id}` | todos | FR-001 |
| PATCH | `/ativos/{id}` | ADMIN, OPERADOR | FR-001 |
| GET | `/ativos/{id}/depreciacao` | todos | FR-003 |
| GET | `/ativos/{id}/historico` | todos | FR-002 |
| POST | `/ativos/{id}/responsavel` | ADMIN, OPERADOR | FR-002 |
| POST | `/ativos/{id}/baixa` | ADMIN, OPERADOR | FR-005 |

**Parâmetros de `GET /ativos`:** `status`, `tipo`, `categoria_id`, `fornecedor_id`, `responsavel_id`, `busca` (nome ou número de série), `valor_depreciado_min`, `valor_depreciado_max`, `percentual_depreciado_min`, `percentual_depreciado_max`, `aquisicao_de`, `aquisicao_ate`, `fim_vida_util` (bool), `pagina` (padrão 1), `tamanho` (padrão 20, máx. 100), `ordenar_por`, `direcao`.

**Envelope de listagem (padrão em toda a API):**

```json
{
  "itens": [],
  "pagina": 1,
  "tamanho": 20,
  "total": 437,
  "total_paginas": 22
}
```

**`POST /ativos` — requisição:**

```json
{
  "nome": "Notebook Dell Latitude 5440",
  "tipo": "HARDWARE",
  "categoria_id": 1,
  "fornecedor_id": 3,
  "numero_serie": "BR9K2LM7",
  "data_aquisicao": "2025-03-14",
  "valor_compra": "6000.00",
  "localizacao": "Bloco A - Sala 204"
}
```

**Resposta `201`:** o recurso criado, já com `status: "ATIVO"`, `vida_util_meses` herdada e bloco `depreciacao` calculado.

**`GET /ativos/{id}/depreciacao` — resposta:**

```json
{
  "ativo_id": 12,
  "data_referencia": "2026-03-14",
  "metodo": "LINEAR",
  "valor_compra": "6000.00",
  "vida_util_meses": 60,
  "meses_decorridos": 12,
  "meses_efetivos": 12,
  "depreciacao_mensal": "100.00",
  "depreciacao_acumulada": "1200.00",
  "valor_residual": "4800.00",
  "percentual_depreciado": "20.00"
}
```

Expor `meses_efetivos` e `depreciacao_mensal` é deliberado: torna o cálculo auditável sem acesso ao código, atendendo ao princípio de rastreabilidade (AC-015).

**`depreciacao_mensal` é informativa e arredondada.** A acumulada é `valor_compra × meses_efetivos ÷ vida_util_meses`, arredondada só no fim ([regras de cálculo §7.1](regras-de-calculo.md#71-depreciação-linear-fr-003)); `mensal × meses` pode diferir dela em centavos.

**Valores monetários são strings decimais** em toda resposta (`"6000.00"`, não `6000.00`). Número em JSON costuma ser lido como ponto flutuante, que perde precisão; a string preserva o valor exato. Na requisição, `valor_compra` aceita string ou número, e a string é a forma recomendada.

**`POST /ativos/{id}/responsavel`** — serve tanto para a primeira atribuição quanto para a transferência; o serviço decide se há vínculo a encerrar.

```json
{ "responsavel_id": 45, "setor_id": 7, "data_inicio": "2026-03-20", "motivo": "Mudança de setor" }
```

**`POST /ativos/{id}/baixa`:**

```json
{
  "motivo": "DEFEITO",
  "justificativa": "Placa-mãe queimada, orçamento de reparo acima de 70% do valor residual",
  "data_baixa": "2026-03-18",
  "destinacao": "RECICLAGEM_CERTIFICADA"
}
```

Resposta `201`: o registro de baixa, com `valor_residual_baixa` (string decimal) congelado na `data_baixa` (BR-015), e `data_source = "manual"`. Na mesma transação o ativo passa a `BAIXADO`, o vínculo de responsável aberto é encerrado com `data_fim = data_baixa` (BR-012) e todos os vínculos de licença ativos da máquina são encerrados por desvínculo lógico (BR-031, AC-058). Se o ativo baixado é o `SOFTWARE` de uma licença perpétua, os vínculos ativos dessa licença, em qualquer máquina, também são encerrados (BR-036, AC-063); a licença não é apagada nem alterada. Cada encerramento gera uma linha `EXCLUIR` na auditoria (`entidade = licenca_vinculo`, `detalhe.origem = "baixa"`) e a `quantidade_em_uso` e o `saldo` das licenças afetadas passam a refletir a liberação. Depois disso `GET /ativos/{id}/depreciacao` usa a `data_baixa` como referência e o valor congelado (AC-019).

Recusas, sempre `409` com `regra` e linha `RECUSADO` na auditoria: `BR-024` (ativo já baixado), `BR-023` (motivo `OUTRO` sem justificativa de 10 caracteres), `BR-022` (data futura ou anterior à aquisição), `BR-026` (sem `destinacao`) e `BR-012` (data anterior ao início do vínculo aberto). Motivo ou destinação fora do enum, e data malformada, retornam `422`.

> **Permissões (ADR-013).** Esta tabela dizia só `ADMIN` para a baixa. A matriz do FR-015 permite a `OPERADOR` criar baixa; o PRD prevalece em regra de negócio, e o contrato foi corrigido (registrado no [`ROADMAP.md`](../ROADMAP.md)).

### 6.4 Licenças

| Método | Rota | Perfis | FR |
|---|---|---|---|
| GET/POST | `/licencas` | GET: todos · POST: ADMIN | FR-004 |
| GET | `/licencas/{id}` | todos | FR-004 |
| PATCH | `/licencas/{id}` | ADMIN, OPERADOR | FR-004 |
| GET | `/licencas/{id}/vinculos` | todos | FR-004 |
| POST | `/licencas/{id}/vinculos` | ADMIN, OPERADOR | FR-004 |
| DELETE | `/licencas/{id}/vinculos/{ativo_id}` | ADMIN, OPERADOR | FR-004 |

A resposta de licença sempre inclui o bloco derivado:

```json
{
  "quantidade_contratada": 50,
  "quantidade_em_uso": 47,
  "saldo": 3,
  "dias_para_expiracao": 22
}
```

`quantidade_em_uso` é o `COUNT` dos vínculos ativos (BR-021, ADR-008), nunca informada. `dias_para_expiracao` é negativo quando a licença já venceu. O bloco ganha `status_conformidade` e `alertas`, derivados na hora (nada é armazenado): `alertas` lista os códigos CP-01 a CP-03 disparados hoje (por exemplo `["CP-03"]`) e `status_conformidade` é `NAO_CONFORME` quando há CP-01 ou CP-02 (críticos), `ALERTA` quando só há CP-03, e `CONFORME` sem alertas. A janela do CP-03 vem de `JANELA_ALERTA_LICENCA_DIAS` (padrão 30).

**`POST /licencas`** — o corpo segue `ck_licenca_tipo`: `PERPETUA` aponta para um ativo `SOFTWARE` (`ativo_id`), sem `software` nem `valor_total`; `SUBSCRICAO` leva `software` e `valor_total`; `OEM` leva `software`, sem valor. `PERPETUA` que aponta para ativo que não é `SOFTWARE` é recusada com `409`, `regra = BR-035` (AC-062) e auditoria `RECUSADO`. Valores monetários são strings decimais.

**Chave de licença (RI-08).** `chave_licenca` sai mascarada (`****-****-A3F9`) em toda listagem e para quem não é `ADMIN`; completa só no detalhe e só para `ADMIN`. A mesma regra vale para a chave do ativo `SOFTWARE`. Chave com menos de 8 caracteres sai toda mascarada.

**`POST /licencas/{id}/vinculos`** — corpo `{ "ativo_id": 12, "data_vinculo": "2026-03-20" }`; `ativo_id` é a máquina hospedeira (`HARDWARE`) e `data_vinculo` é opcional (padrão hoje). Recusas `409` com `regra` e auditoria `RECUSADO`: `BR-018` (excederia o contratado, AC-021), `BR-020` (licença vencida, AC-025), `BR-032` (máquina `BAIXADO`, AC-059), `BR-037` (o ativo `SOFTWARE` da licença está `BAIXADO`, AC-064), `BR-033` (máquina que não é `HARDWARE`, AC-060) e `BR-034` (máquina já vinculada a esta licença, AC-061). Se a máquina falha em mais de uma regra, vale a primeira nesta ordem de verificação: `BR-032`, `BR-037`, `BR-020`, `BR-033`, `BR-034`, `BR-018`. `BR-037` é derivado do status do ativo, sem coluna própria, e só se aplica a licença `PERPETUA`. `DELETE /licencas/{id}/vinculos/{ativo_id}` é desvínculo **lógico** (`ativo_vinculo = false`, `204`): a quantidade em uso cai sozinha (AC-026) e nenhum registro é apagado. `GET .../vinculos` lista ativos e desvinculados.

**`PATCH /licencas/{id}`** — edita `fornecedor_id`, `chave_licenca`, `quantidade_contratada`, `data_inicio_vigencia` e `data_expiracao`. Recusas: `BR-019` (expiração não posterior ao início, AC-024) e `BR-018` (contratada abaixo do uso). `POST /licencas` também recusa `BR-019` com `409`.

> **Permissões (ADR-013).** Esta tabela dizia `ADMIN` para `GET` e `PATCH /licencas/{id}`. A matriz do FR-015 dá `Ler` a todos e `Ler, Editar` ao `OPERADOR`; o contrato foi corrigido.

### 6.5 Relatórios, compliance e indicadores

| Método | Rota | Perfis | FR |
|---|---|---|---|
| GET | `/relatorios/inventario` | todos | FR-006 |
| GET | `/relatorios/depreciacao` | todos | FR-003, FR-006 |
| GET | `/relatorios/conformidade` | todos | FR-007 |
| GET | `/relatorios/baixas` | todos | FR-005 |
| GET | `/relatorios/historico-responsaveis` | todos | FR-002 |
| GET | `/compliance/alertas` | todos | FR-007 |
| GET | `/indicadores` | todos | FR-009 |

**Implementados na Sprint 4:** `/relatorios/inventario`, `/relatorios/conformidade`, `/compliance/alertas` e `/indicadores`. `/relatorios/depreciacao`, `/relatorios/baixas` e `/relatorios/historico-responsaveis` seguem previstos, sem AC próprio, e não foram implementados.

**`GET /relatorios/inventario`** — filtros `status` (repetível), `tipo` (repetível), `categoria_id` (repetível), `fornecedor_id` (repetível), `responsavel_id`, `valor_depreciado_min|max`, `percentual_depreciado_min|max`, `aquisicao_de|ate` e `fim_vida_util` (≥ 80% da vida útil, `LIMIAR_FIM_VIDA_UTIL_PERCENTUAL`), todos em conjunção. **Sem `status`, o ativo `BAIXADO` não aparece** (inventário ativo, AC-031); `status=BAIXADO` o traz de volta. A resposta é o envelope de listagem mais `totais` (`quantidade`, `valor_compra`, `valor_residual`) sobre todo o resultado filtrado, não só a página. A chave de licença do ativo `SOFTWARE` sai sempre mascarada (RI-08). O baixado usa a data da baixa e o residual congelado (AC-019).

**`GET /compliance/alertas`** — alertas CP-01 a CP-04 derivados na hora, agrupados por severidade da mais crítica para a menos (AC-040). Cada alerta traz `codigo`, `severidade`, `regra` (a regra aplicada, legível, AC-042), `mensagem`, `entidade`, `entidade_id`, `recurso` e `link` para o registro de origem (AC-041). Resposta: `{ "data_referencia", "total", "por_severidade", "grupos": [{ "severidade", "total", "alertas": [] }] }`. Só entram grupos com alerta. `/relatorios/conformidade` devolve o mesmo conteúdo e, em `csv`/`xlsx`, como relatório datado.

Todo relatório aceita `formato=json|csv|xlsx`. Em `csv` e `xlsx`, o cabeçalho traz data, hora e login do solicitante (AC-036) e a paginação é ignorada (AC-037).

**`GET /indicadores` — resposta:** cada indicador acompanha a fórmula e a amostra (AC-047).

```json
{
  "data_referencia": "2026-03-20T14:31:07Z",
  "filtros_aplicados": { "categoria_id": null, "setor_id": null },
  "indicadores": [
    {
      "codigo": "KPI-02",
      "nome": "Cobertura de responsáveis",
      "valor": 96.8,
      "unidade": "%",
      "formula": "ativos com vínculo aberto / ativos com status ATIVO * 100",
      "amostra": 437,
      "meta": 98.0,
      "atende_meta": false
    }
  ]
}
```

Códigos: `KPI-02` (cobertura de responsáveis), `KPI-03` (conformidade de licenças), `KPI-06` (ativos sem movimentação), `KPI-07` (idade média), `KPI-08` (baixas com destinação) e, para os indicadores do FR-009 sem código KPI no PRD, `IND-01` (total por status), `IND-02` (hardware × software), `IND-03` (valor bruto), `IND-04` (valor residual), `IND-05` (percentual depreciado), `IND-06` (custo médio) e `IND-07` (taxa de baixas no período). `valor` é string decimal para dinheiro e número para percentual e contagem; fica nulo quando a amostra é vazia. `sentido_meta` (`>=` ou `<=`) acompanha `meta`. Os de distribuição trazem `detalhe`. Filtros: `categoria_id`, `setor_id` (setor do vínculo de responsável aberto), `fornecedor_id`, `data_inicio` e `data_fim` (esta janela só afeta `IND-07`; padrão: os 365 dias até hoje).

### 6.6 Importação

| Método | Rota | Perfis | FR |
|---|---|---|---|
| POST | `/importacoes` | ADMIN | FR-008 |
| GET | `/importacoes` | todos | FR-008 |
| GET | `/importacoes/{id}` | todos | FR-008 |
| GET | `/importacoes/{id}/erros` | todos | FR-008 |

`POST` recebe `multipart/form-data` com o campo `arquivo`. Resposta `202`:

```json
{
  "lote_id": 8,
  "nome_arquivo": "inventario_2026.xlsx",
  "total_processado": 100,
  "total_aceito": 92,
  "total_rejeitado": 8,
  "erros_url": "/api/v1/importacoes/8/erros"
}
```

### 6.7 Governança e decisão

| Método | Rota | Perfis | FR |
|---|---|---|---|
| POST | `/cenarios/comparar` | ADMIN, GESTOR | FR-010 |
| POST | `/fornecedores/scorecard` | ADMIN, GESTOR | FR-011 |
| GET/POST | `/riscos` | GET: todos · POST: ADMIN, GESTOR | FR-012 |
| GET/PATCH | `/riscos/{id}` | ADMIN, GESTOR | FR-012 |
| GET/POST | `/recomendacoes` | GET: todos · POST: ADMIN, GESTOR | FR-013 |
| GET | `/recomendacoes/{id}` | todos | FR-013 |

**`POST /recomendacoes`** — a lista `evidencias` deve conter pelo menos um item; lista vazia retorna `422` citando `BR-027` (AC-051).

**`POST /cenarios/comparar`** — a resposta ordena por custo e risco e **não** marca nenhum cenário como escolhido (BR-028, AC-052):

```json
{
  "horizonte_anos": 5,
  "cenarios": [
    { "nome": "MANTER", "capex": 0, "opex_anual": 84000, "tco_5_anos": 420000,
      "custo_por_ativo_ano": 210.0, "economia_vs_baseline": 0, "score_risco": 16 }
  ],
  "ordenado_por": ["tco_5_anos", "score_risco"],
  "observacao": "A seleção da alternativa é decisão humana e deve ser registrada em /recomendacoes."
}
```

### 6.8 Endpoints técnicos

| Método | Rota | Autenticação | NFR |
|---|---|---|---|
| GET | `/health` | público | NFR-DIS-03 |
| GET | `/metrics` | público (rede interna) | NFR-OBS-01 |
| GET | `/docs`, `/redoc`, `/openapi.json` | público | NFR-MAN-02 |

```json
{ "status": "UP", "environment": "docker", "database": { "status": "UP", "dialect": "postgresql" }, "version": "1.0.0" }
```

Com o banco fora do ar, `/health` responde `503` com `status` e `database.status` `DOWN`. `/metrics` responde sempre `200` no formato de exposição Prometheus (`text/plain; version=0.0.4`), com `itam_database_up` indicando o estado do banco (ver [`observabilidade.md`](observabilidade.md)). Toda resposta traz `X-Request-ID`.


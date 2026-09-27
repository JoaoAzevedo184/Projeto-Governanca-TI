# Modelo de Dados — Dicionário de Dados

Parte de [Modelo de Dados — ITAM](README.md).

## 3. Dicionário de dados

### 3.1 `categoria`

| Coluna | Tipo | Nulo | Padrão | Descrição |
|---|---|---|---|---|
| `id` | BIGINT | não | identity | Chave primária |
| `nome` | VARCHAR(80) | não | — | Único. Ex.: "Notebook", "Servidor" |
| `descricao` | VARCHAR(255) | sim | — | Texto livre |
| `vida_util_meses` | INTEGER | não | — | `CHECK > 0`. Base da depreciação |
| `tipo_aplicavel` | VARCHAR(10) | não | — | `HARDWARE` ou `SOFTWARE` |
| `ativa` | BOOLEAN | não | `true` | Desativação lógica |

### 3.2 `fornecedor`

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `razao_social` | VARCHAR(160) | não | — |
| `cnpj` | VARCHAR(18) | sim | Único quando presente |
| `contato`, `telefone`, `email` | VARCHAR | sim | Dados de contato |
| `ativo` | BOOLEAN | não | Padrão `true` |
| `data_source` | VARCHAR(20) | não | `compras_gov` quando resolvido a partir do fabricante informado na compra; `sintetico` nos demais |

### 3.3 `setor` e `responsavel`

| `setor` | Tipo | Descrição |
|---|---|---|
| `id` | BIGINT | PK |
| `nome` | VARCHAR(120) | Único |
| `sigla` | VARCHAR(12) | — |
| `ativo` | BOOLEAN | Padrão `true` |

| `responsavel` | Tipo | Descrição |
|---|---|---|
| `id` | BIGINT | PK |
| `nome` | VARCHAR(160) | — |
| `matricula` | VARCHAR(30) | Único quando presente |
| `email`, `cargo` | VARCHAR | — |
| `localizacao` | VARCHAR(120) | Campo do esquema Mockaroo (`data/synthetic/schemas/`); texto livre, ex.: "Bloco A - 2º andar" |
| `setor_id` | BIGINT | FK → `setor`. Lotação atual, independente do setor do vínculo |
| `ativo` | BOOLEAN | Desligamento é desativação, nunca exclusão |
| `data_source` | VARCHAR(20) | Sempre `sintetico` — colaborador não é pessoa real (ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md#10-conformidade-com-a-lgpd)) |

> `responsavel.setor_id` é a lotação da pessoa; `historico_transferencia.setor_id` é o setor que respondeu pelo ativo naquele período. São campos distintos de propósito: uma pessoa muda de setor sem que o histórico do ativo seja reescrito.

### 3.4 `ativo`

| Coluna | Tipo | Nulo | Regra | Descrição |
|---|---|---|---|---|
| `id` | BIGINT | não | — | PK |
| `nome` | VARCHAR(120) | não | `CHECK length ≥ 3` | Identificação humana |
| `tipo` | VARCHAR(10) | não | enum | `HARDWARE` ou `SOFTWARE` |
| `categoria_id` | BIGINT | não | BR-005 | FK |
| `fornecedor_id` | BIGINT | não | BR-005 | FK |
| `numero_serie` | VARCHAR(80) | sim | BR-001, BR-002 | **Único**, inclusive entre baixados |
| `chave_licenca` | VARCHAR(200) | sim | BR-002 | Mascarada fora do perfil ADMIN |
| `data_aquisicao` | DATE | não | BR-003 | Não futura |
| `valor_compra` | NUMERIC(12,2) | não | BR-004 | `CHECK > 0` |
| `vida_util_meses` | INTEGER | não | BR-006 | Herdada da categoria, sobrescrevível |
| `status` | VARCHAR(20) | não | — | Padrão `ATIVO` |
| `localizacao` | VARCHAR(120) | sim | — | Texto livre |
| `observacoes` | VARCHAR(500) | sim | — | — |
| `lote_importacao_id` | BIGINT | sim | — | Procedência; nulo em cadastro manual |
| `data_source` | VARCHAR(20) | não | — | `compras_gov` para itens coletados, `importacao` para itens vindos de planilha do usuário |
| `criado_em`, `atualizado_em` | TIMESTAMPTZ | não | — | UTC |

```sql
CONSTRAINT ck_ativo_identificador CHECK (
  (tipo = 'HARDWARE' AND numero_serie IS NOT NULL) OR
  (tipo = 'SOFTWARE' AND chave_licenca  IS NOT NULL)
)
```

**Não existe coluna `responsavel_id`** (ADR-003) nem colunas de depreciação (ADR-002). Ambos são derivados — ver seção 6.

### 3.5 `historico_transferencia` — *append-only*

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `ativo_id` | BIGINT | não | FK |
| `responsavel_id` | BIGINT | não | FK |
| `setor_id` | BIGINT | não | FK. Setor no momento do vínculo |
| `data_inicio` | DATE | não | ≥ `ativo.data_aquisicao` (BR-010) |
| `data_fim` | DATE | **sim** | **Nulo = vínculo vigente** |
| `motivo` | VARCHAR(200) | sim | Texto livre |
| `registrado_por_id` | BIGINT | não | FK → `usuario` |
| `data_source` | VARCHAR(20) | não | Sempre `sintetico` — evento gerado pelo ETL (`SYNTHETIC_SEED`) |
| `criado_em` | TIMESTAMPTZ | não | — |

```sql
CONSTRAINT ck_periodo CHECK (data_fim IS NULL OR data_fim >= data_inicio)
```

### 3.6 `baixa_ativo` — *append-only*

| Coluna | Tipo | Nulo | Regra |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `ativo_id` | BIGINT | não | FK, **UNIQUE** (BR-024) |
| `motivo` | VARCHAR(20) | não | enum |
| `justificativa` | VARCHAR(500) | sim | Obrigatória se `motivo = OUTRO` (BR-023) |
| `data_baixa` | DATE | não | Não futura, ≥ aquisição (BR-022) |
| `destinacao` | VARCHAR(30) | não | BR-026 — evidência de TI Verde |
| `valor_residual_baixa` | NUMERIC(12,2) | não | `CHECK ≥ 0`. Congelado (BR-015) |
| `registrado_por_id` | BIGINT | não | FK |
| `data_source` | VARCHAR(20) | não | Sempre `sintetico` — evento gerado pelo ETL, preferencialmente em ativos com vida útil encerrada |
| `criado_em` | TIMESTAMPTZ | não | — |

```sql
CONSTRAINT ck_baixa_justificativa CHECK (
  motivo <> 'OUTRO' OR (justificativa IS NOT NULL AND length(justificativa) >= 10)
)
```

O `UNIQUE` em `ativo_id` é o que torna BR-024 ("ativo já baixado não pode ser baixado de novo") uma garantia, e não uma verificação que pode falhar sob concorrência.

### 3.7 `licenca` e `licenca_vinculo`

| `licenca` | Tipo | Regra |
|---|---|---|
| `id` | BIGINT | PK |
| `software` | VARCHAR(120) | — |
| `fornecedor_id` | BIGINT | FK |
| `chave_licenca` | VARCHAR(200) | Mascarada fora do ADMIN |
| `quantidade_contratada` | INTEGER | `CHECK ≥ 1` |
| `data_aquisicao` | DATE | Não futura |
| `data_expiracao` | DATE | `CHECK > data_aquisicao` (BR-019) |
| `valor_total` | NUMERIC(12,2) | `CHECK > 0` |
| `tipo_licenciamento` | VARCHAR(20) | enum |
| `data_source` | VARCHAR(20) | Sempre `sintetico` — contrato de licença gerado pelo ETL |

| `licenca_vinculo` | Tipo | Regra |
|---|---|---|
| `id` | BIGINT | PK |
| `licenca_id` | BIGINT | FK |
| `ativo_id` | BIGINT | FK |
| `data_vinculo` | DATE | — |
| `ativo_vinculo` | BOOLEAN | Padrão `true`; desvínculo é lógico |
| `data_source` | VARCHAR(20) | Sempre `sintetico` |

```sql
CREATE UNIQUE INDEX ux_licenca_ativo
  ON licenca_vinculo (licenca_id, ativo_id)
  WHERE ativo_vinculo = true;
```

**`quantidade_em_uso` não é coluna** (BR-021, ADR-008). É `COUNT(*)` sobre `licenca_vinculo` com `ativo_vinculo = true`.

### 3.8 Importação

| `lote_importacao` | Tipo |
|---|---|
| `id`, `nome_arquivo`, `data_importacao`, `usuario_id`, `total_processado`, `total_aceito`, `total_rejeitado` | — |

| `erro_importacao` | Tipo | Descrição |
|---|---|---|
| `id` | BIGINT | PK |
| `lote_id` | BIGINT | FK, CASCADE |
| `numero_linha` | INTEGER | Linha do arquivo original |
| `campo` | VARCHAR(80) | Campo que falhou |
| `valor_recebido` | VARCHAR(255) | Valor bruto, para diagnóstico |
| `motivo` | VARCHAR(255) | Mensagem legível |

### 3.9 Governança

| `risco` | Tipo | Regra |
|---|---|---|
| `probabilidade`, `impacto` | INTEGER | `CHECK BETWEEN 1 AND 5` |
| `score` | INTEGER | `GENERATED ALWAYS AS (probabilidade * impacto) STORED` |
| `categoria`, `resposta`, `status` | VARCHAR | enums |
| `titulo`, `descricao`, `gatilho` | VARCHAR | — |
| `responsavel_id`, `data_revisao` | — | — |

| `recomendacao` | `titulo`, `contexto`, `recomendacao`, `alternativas`, `responsavel_id`, `data`, `status` |
|---|---|
| `evidencia` | `id`, `recomendacao_id` (FK CASCADE), `tipo`, `referencia_id`, `descricao` |

| `fornecedor_avaliacao` | Tipo |
|---|---|
| `fornecedor_id`, `criterio`, `peso` (NUMERIC(5,2)), `nota` (NUMERIC(4,2), `CHECK 0–10`), `periodo` | — |

### 3.10 `usuario` e `audit_log`

| `usuario` | Tipo |
|---|---|
| `id`, `login` (UNIQUE), `senha_hash`, `nome`, `perfil` (enum), `ativo`, `criado_em` | — |

| `audit_log` — *append-only* | Tipo | Descrição |
|---|---|---|
| `usuario_id` | BIGINT | Autor |
| `operacao` | VARCHAR(20) | `CRIAR`, `ATUALIZAR`, `EXCLUIR`, `BLOQUEAR`, `LOGIN` |
| `entidade`, `entidade_id` | VARCHAR/BIGINT | Alvo |
| `resultado` | VARCHAR(10) | `SUCESSO` ou `RECUSADO` |
| `regra_violada` | VARCHAR(10) | Ex.: `BR-018`. Nulo em sucesso |
| `detalhe` | JSONB | Payload relevante, sem dados sensíveis |
| `carimbo` | TIMESTAMPTZ | UTC |

### 3.11 Ciclo de vida de software e vulnerabilidades

Tabelas alimentadas pelos coletores `endoflife` e `nvd` (ver [`docs/FONTES_DE_DADOS.md`](../FONTES_DE_DADOS.md)). A associação com o ativo é sintética; o produto, a versão, a data de fim de suporte e a vulnerabilidade em si são reais.

#### `produto_software`

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `nome` | VARCHAR(120) | não | Nome do produto no endoflife.date (ex.: "ubuntu", "postgresql") |
| `versao` | VARCHAR(40) | não | Campo `cycle` da API |
| `data_lancamento` | DATE | sim | Campo `releaseDate` |
| `data_fim_suporte` | DATE | sim | Campo `eol`; nulo quando o produto não tem data de fim de suporte publicada |
| `data_source` | VARCHAR(20) | não | Sempre `endoflife` |

```sql
CONSTRAINT ux_produto_versao UNIQUE (nome, versao)
```

#### `vulnerabilidade`

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `cve_id` | VARCHAR(20) | não | Identificador CVE, único |
| `produto_software_id` | BIGINT | não | FK → `produto_software` |
| `descricao` | VARCHAR(1000) | sim | Descrição resumida da CVE |
| `severidade_cvss` | NUMERIC(3,1) | sim | Score CVSS, `CHECK BETWEEN 0 AND 10` |
| `data_publicacao` | DATE | sim | Campo `published` da API do NVD |
| `data_source` | VARCHAR(20) | não | Sempre `nvd` |

#### `ativo_software` — associação ativo × software instalado

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | BIGINT | não | PK |
| `ativo_id` | BIGINT | não | FK → `ativo` |
| `produto_software_id` | BIGINT | não | FK → `produto_software` |
| `data_instalacao` | DATE | não | ≥ `ativo.data_aquisicao`, gerada pelo ETL |
| `data_source` | VARCHAR(20) | não | Sempre `sintetico` — a combinação ativo × versão é sorteada; o produto e a versão em si são reais |

A associação alimenta o alerta de compliance de ciclo de vida (CP-03 e correlatos, FR-007): a query de conformidade cruza `ativo_software.produto_software_id` com `produto_software.data_fim_suporte` e com `vulnerabilidade.produto_software_id`.


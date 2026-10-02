# SPEC — Modelo Físico de Dados

Parte de [SPEC — ITAM](README.md).

## 5. Modelo Físico de Dados

### 5.1 Enumerações

| Enum | Valores |
|---|---|
| `tipo_ativo` | `HARDWARE`, `SOFTWARE` |
| `status_ativo` | `ATIVO`, `EM_MANUTENCAO`, `BAIXADO` |
| `motivo_baixa` | `OBSOLESCENCIA`, `DEFEITO`, `FURTO_ROUBO`, `FIM_VIDA_UTIL`, `OUTRO` |
| `destinacao_baixa` | `RECICLAGEM_CERTIFICADA`, `DOACAO`, `DEVOLUCAO_FORNECEDOR`, `VENDA`, `DESCARTE` |
| `tipo_licenciamento` | `PERPETUA`, `SUBSCRICAO`, `OEM` |
| `perfil_usuario` | `ADMIN`, `OPERADOR`, `GESTOR`, `AUDITOR` |
| `severidade_alerta` | `CRITICO`, `ALTO`, `MEDIO`, `BAIXO` |
| `categoria_risco` | `OPERACIONAL`, `FINANCEIRO`, `LEGAL`, `SEGURANCA`, `CONTINUIDADE` |
| `resposta_risco` | `ACEITAR`, `MITIGAR`, `TRANSFERIR`, `EVITAR` |
| `status_recomendacao` | `PROPOSTA`, `APROVADA`, `REJEITADA`, `IMPLEMENTADA` |
| `tipo_evidencia` | `INDICADOR`, `RISCO`, `ATIVO`, `LICENCA`, `SCORECARD`, `CENARIO`, `PREMISSA` |

> Implementar como `str, Enum` no Python e como tipo `VARCHAR` com `CHECK` no banco. Enums nativos do PostgreSQL dificultam a migração e não existem no SQLite.

### 5.2 Tabelas

#### `categoria`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK, identity |
| `nome` | VARCHAR(80) | NOT NULL, UNIQUE |
| `descricao` | VARCHAR(255) | |
| `vida_util_meses` | INTEGER | NOT NULL, CHECK > 0 |
| `tipo_aplicavel` | VARCHAR(10) | NOT NULL, CHECK IN tipo_ativo |
| `ativa` | BOOLEAN | NOT NULL, DEFAULT true |

#### `fornecedor`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `razao_social` | VARCHAR(160) | NOT NULL |
| `cnpj` | VARCHAR(18) | UNIQUE |
| `contato` | VARCHAR(120) | |
| `telefone` | VARCHAR(20) | |
| `email` | VARCHAR(160) | |
| `ativo` | BOOLEAN | NOT NULL, DEFAULT true |
| `data_source` | VARCHAR(20) | NOT NULL — `compras_gov` ou `sintetico` |

#### `setor`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `nome` | VARCHAR(120) | NOT NULL, UNIQUE |
| `sigla` | VARCHAR(12) | |
| `ativo` | BOOLEAN | NOT NULL, DEFAULT true |

#### `responsavel`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `nome` | VARCHAR(160) | NOT NULL |
| `matricula` | VARCHAR(30) | UNIQUE |
| `email` | VARCHAR(160) | |
| `cargo` | VARCHAR(120) | |
| `localizacao` | VARCHAR(120) | |
| `setor_id` | BIGINT | FK → setor |
| `ativo` | BOOLEAN | NOT NULL, DEFAULT true |
| `data_source` | VARCHAR(20) | NOT NULL, sempre `sintetico` |

#### `ativo`

| Coluna | Tipo | Restrições | Regra |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `nome` | VARCHAR(120) | NOT NULL, CHECK length ≥ 3 | |
| `tipo` | VARCHAR(10) | NOT NULL, CHECK IN tipo_ativo | |
| `categoria_id` | BIGINT | NOT NULL, FK | BR-005 |
| `fornecedor_id` | BIGINT | NOT NULL, FK | BR-005 |
| `numero_serie` | VARCHAR(80) | UNIQUE | BR-001, BR-002 |
| `chave_licenca` | VARCHAR(200) | | BR-002 |
| `data_aquisicao` | DATE | NOT NULL | BR-003 |
| `valor_compra` | NUMERIC(12,2) | NOT NULL, CHECK > 0 | BR-004 |
| `vida_util_meses` | INTEGER | NOT NULL, CHECK > 0 | BR-006 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `ATIVO` | |
| `localizacao` | VARCHAR(120) | | |
| `observacoes` | VARCHAR(500) | | |
| `lote_importacao_id` | BIGINT | FK, nullable | procedência |
| `produto_software_id` | BIGINT | FK → `produto_software`, nullable | catálogo (só `SOFTWARE`) |
| `data_source` | VARCHAR(20) | NOT NULL | `compras_gov`, `importacao` ou `manual` (cadastro direto pela API) |
| `criado_em` / `atualizado_em` | TIMESTAMPTZ | NOT NULL | |

**Constraint de tipo (BR-002):**

```sql
CONSTRAINT ck_ativo_identificador CHECK (
  (tipo = 'HARDWARE' AND numero_serie IS NOT NULL) OR
  (tipo = 'SOFTWARE' AND chave_licenca IS NOT NULL)
)
```

**Índices:** `numero_serie` (único), `status`, `categoria_id`, `fornecedor_id`, `data_aquisicao` (NFR-PER-05).

#### `historico_transferencia` *(append-only)*

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `ativo_id` | BIGINT | NOT NULL, FK |
| `responsavel_id` | BIGINT | NOT NULL, FK |
| `setor_id` | BIGINT | NOT NULL, FK |
| `data_inicio` | DATE | NOT NULL |
| `data_fim` | DATE | NULL = vínculo aberto |
| `motivo` | VARCHAR(200) | |
| `registrado_por_id` | BIGINT | NOT NULL, FK → usuario |
| `data_source` | VARCHAR(20) | NOT NULL, `manual` (API) ou `sintetico` (ETL) |
| `criado_em` | TIMESTAMPTZ | NOT NULL |

**Invariante crítica (BR-007) — um único vínculo aberto por ativo:**

```sql
CREATE UNIQUE INDEX ux_vinculo_aberto
  ON historico_transferencia (ativo_id)
  WHERE data_fim IS NULL;
```

Índice único parcial no PostgreSQL. No SQLite, `CREATE UNIQUE INDEX ... WHERE` também é suportado. A validação na aplicação é complementar, **não substituta**: sob concorrência, só o banco garante a invariante.

**Constraint de período:** `CHECK (data_fim IS NULL OR data_fim >= data_inicio)`.

#### `baixa_ativo` *(append-only)*

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `ativo_id` | BIGINT | NOT NULL, FK, **UNIQUE** (BR-024) |
| `motivo` | VARCHAR(20) | NOT NULL, CHECK IN motivo_baixa |
| `justificativa` | VARCHAR(500) | |
| `data_baixa` | DATE | NOT NULL |
| `destinacao` | VARCHAR(30) | NOT NULL (BR-026) |
| `valor_residual_baixa` | NUMERIC(12,2) | NOT NULL, CHECK ≥ 0 (BR-015) |
| `registrado_por_id` | BIGINT | NOT NULL, FK |
| `data_source` | VARCHAR(20) | NOT NULL, `manual` (API) ou `sintetico` (ETL); mesmo critério do item 8 da resolução do Sprint 2 |
| `criado_em` | TIMESTAMPTZ | NOT NULL |

```sql
CONSTRAINT ck_baixa_justificativa CHECK (
  motivo <> 'OUTRO' OR (justificativa IS NOT NULL AND length(justificativa) >= 10)
)
```

#### `licenca`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `ativo_id` | BIGINT | FK → `ativo` (`SOFTWARE`), nullable; obrigatório em `PERPETUA` |
| `software` | VARCHAR(120) | nullable; só sem `ativo_id` |
| `fornecedor_id` | BIGINT | NOT NULL, FK |
| `chave_licenca` | VARCHAR(200) | NOT NULL |
| `quantidade_contratada` | INTEGER | NOT NULL, CHECK ≥ 1 |
| `data_inicio_vigencia` | DATE | NOT NULL |
| `data_expiracao` | DATE | NOT NULL, CHECK > `data_inicio_vigencia` (BR-019) |
| `valor_total` | NUMERIC(12,2) | nullable, CHECK > 0; só em `SUBSCRICAO` |
| `tipo_licenciamento` | VARCHAR(20) | NOT NULL, CHECK IN `tipo_licenciamento` |
| `data_source` | VARCHAR(20) | NOT NULL, `manual` (API) ou `sintetico` (ETL) |

*Implementado na Sprint 3 (migração `f5f9acc0de7b`). Além do que está na tabela, o banco tem `ck_licenca_quantidade_minima`, `ck_licenca_vigencia` (BR-019) e `ck_licenca_valor_positivo`.*

A licença é **só o contrato de direito de uso** (ADR-012). `software`, `data_aquisicao` e `valor_total` deixaram de duplicar o ativo: o nome e o valor patrimonial da licença perpétua vêm do ativo `SOFTWARE`.

```sql
-- Um único dono para nome e valor (ADR-012, item 4 da resolução do Sprint 2):
-- perpétua aponta para o ativo; subscrição e OEM não são ativo e guardam o nome aqui.
CONSTRAINT ck_licenca_tipo CHECK (
  (tipo_licenciamento = 'PERPETUA'   AND ativo_id IS NOT NULL AND software IS NULL     AND valor_total IS NULL) OR
  (tipo_licenciamento = 'SUBSCRICAO' AND ativo_id IS NULL     AND software IS NOT NULL AND valor_total IS NOT NULL) OR
  (tipo_licenciamento = 'OEM'        AND ativo_id IS NULL     AND software IS NOT NULL AND valor_total IS NULL)
)
```

`licenca.ativo_id` deve apontar para ativo com `tipo = 'SOFTWARE'`. Como o CHECK não enxerga outra tabela, a regra é validada no serviço de licenças.

> `quantidade_em_uso` **não é coluna** — é derivada de `COUNT(*)` em `licenca_vinculo` (BR-021). Se a medição de desempenho exigir materialização, criar coluna sincronizada por trigger e cobrir com teste de consistência.

#### `licenca_vinculo`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `licenca_id` | BIGINT | NOT NULL, FK |
| `ativo_id` | BIGINT | NOT NULL, FK → máquina hospedeira (hardware onde o software está instalado) |
| `data_vinculo` | DATE | NOT NULL |
| `ativo_vinculo` | BOOLEAN | NOT NULL, DEFAULT true |
| `data_source` | VARCHAR(20) | NOT NULL, `manual` (API) ou `sintetico` (ETL) |
| UNIQUE | | (`licenca_id`, `ativo_id`) onde `ativo_vinculo = true` (`ux_licenca_ativo`) |

#### `produto_software`, `vulnerabilidade` e `ativo_software`

Alimentadas pelos coletores `endoflife` e `nvd`; a associação com o ativo é sintética. Dicionário completo em [`docs/modelo-de-dados/dicionario-de-dados.md`](../modelo-de-dados/dicionario-de-dados.md#311-ciclo-de-vida-de-software-e-vulnerabilidades).

| `produto_software` | `id`, `nome`, `versao`, `data_lancamento`, `data_fim_suporte`, `data_source` (`endoflife`) |
|---|---|
| `vulnerabilidade` | `id`, `cve_id` (UNIQUE), `produto_software_id` (FK), `descricao`, `severidade_cvss`, `data_publicacao`, `data_source` (`nvd`) |
| `ativo_software` | `id`, `ativo_id` (FK), `produto_software_id` (FK), `data_instalacao`, `data_source` (`sintetico`) |

`produto_software` é catálogo; `ativo_software` é instalação observada e **não** é unificada com `licenca_vinculo` (consumo de assento). Ver o dicionário §3.11.

#### `lote_importacao` e `erro_importacao`

| `lote_importacao` | Tipo |
|---|---|
| `id`, `nome_arquivo`, `data_importacao`, `usuario_id`, `total_processado`, `total_aceito`, `total_rejeitado` | — |

| `erro_importacao` | Tipo |
|---|---|
| `id`, `lote_id` (FK), `numero_linha` (INT), `campo` (VARCHAR), `valor_recebido` (VARCHAR), `motivo` (VARCHAR) | — |

#### `risco`

`id`, `titulo`, `descricao`, `categoria` (enum), `probabilidade` (INT 1–5), `impacto` (INT 1–5), `score` (INT, gerado), `resposta` (enum), `responsavel_id`, `status`, `gatilho`, `data_revisao`.

```sql
score INTEGER GENERATED ALWAYS AS (probabilidade * impacto) STORED
```

#### `recomendacao` e `evidencia`

| `recomendacao` | `titulo`, `contexto`, `recomendacao`, `alternativas`, `responsavel_id`, `data`, `status` |
|---|---|
| `evidencia` | `id`, `recomendacao_id` (FK, CASCADE), `tipo` (enum), `referencia_id`, `descricao` |

**BR-027 não pode ser garantida por constraint simples** (exigiria checar filhos no insert do pai). Implementar na camada de serviço, criando pai e evidências na mesma transação, e cobrir com teste de integração (AC-051).

#### `usuario`

`id`, `login` (UNIQUE), `senha_hash`, `nome`, `perfil` (enum), `ativo`, `criado_em`.

#### `audit_log` *(append-only)*

`id`, `usuario_id`, `operacao` (CRIAR/ATUALIZAR/EXCLUIR/BLOQUEAR/LOGIN), `entidade`, `entidade_id`, `resultado` (SUCESSO/RECUSADO), `regra_violada` (nullable, ex.: `BR-018`), `detalhe` (JSON), `carimbo` (TIMESTAMPTZ NOT NULL).

### 5.3 Garantia de imutabilidade (NFR-AUD-01)

Para `historico_transferencia`, `baixa_ativo` e `audit_log`, aplicar no PostgreSQL (aplicado nas três; ver [`migracoes.md`](../modelo-de-dados/migracoes.md)):

```sql
CREATE OR REPLACE FUNCTION bloquear_mutacao() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Registro histórico é imutável (NFR-AUD-01)';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_historico_imutavel
  BEFORE UPDATE OR DELETE ON historico_transferencia
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();
```

**Exceção necessária:** a transferência precisa preencher `data_fim` do vínculo anterior. Duas saídas possíveis — escolher uma e registrar em ADR:

- **(a)** O trigger permite UPDATE exclusivamente quando `OLD.data_fim IS NULL AND NEW.data_fim IS NOT NULL` e nenhuma outra coluna muda;
- **(b)** Não há `data_fim`: o vínculo vigente é o de maior `data_inicio`, e o encerramento é inferido. Insert-only puro, mas consultas mais caras.

Recomenda-se **(a)**: mantém as consultas simples e preserva a imutabilidade no que importa (autor, datas de início, responsável).


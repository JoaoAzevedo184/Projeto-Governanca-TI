# SPEC — ITAM: Especificação Técnica

| Campo | Valor |
|---|---|
| **Produto** | ITAM — Gestão de Ativos de TI |
| **Documento** | Especificação técnica de implementação |
| **Versão** | 1.0 |
| **Stack** | Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL |
| **Documento de origem** | `PRD-ITAM.md` |
| **Disciplina** | Governança de TI — UNINASSAU Olinda |

> Este documento define **como** construir. O **o quê** e o **por quê** estão no PRD. Todo identificador citado aqui (FR, BR, AC, NFR, US, KPI) refere-se ao PRD e é estável: implementações devem preservá-lo em comentários, nomes de teste e mensagens de erro.

---

## 1. Escopo Técnico

### 1.1 O que este documento cobre

Arquitetura, modelo físico de dados, contrato da API, regras de cálculo, padrão de erros, segurança, pipeline de importação, observabilidade, estratégia de testes e plano de sprints.

### 1.2 Premissas arquiteturais

| # | Premissa | Consequência |
|---|---|---|
| P1 | Monólito modular, não microsserviços | Um único processo; separação por pacote, não por rede |
| P2 | Contrato OpenAPI é a fonte de verdade da API | Qualquer implementação alternativa deve passar na mesma suíte de contrato (NFR-MAN-01) |
| P3 | Regra de negócio vive na camada de serviço, nunca no router nem no modelo | Routers só orquestram; testes de regra não precisam subir HTTP |
| P4 | Depreciação é função pura, não estado persistido | Recalculável a qualquer momento; exceção única no registro de baixa (BR-015) |
| P5 | Tabelas históricas são *append-only* garantidas no banco | Imutabilidade não depende de disciplina de código (NFR-AUD-01) |
| P6 | SQLite para execução local, PostgreSQL para o ambiente orquestrado | Seleção por variável de ambiente, mesma suíte de testes nos dois perfis |

---

## 2. Arquitetura

### 2.1 Camadas

```
┌──────────────────────────────────────────────────────────┐
│  API  —  app/api/v1/routers/                             │
│  Roteamento, validação de entrada/saída (Pydantic),      │
│  autenticação, autorização. Sem regra de negócio.        │
└────────────────────────┬─────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────┐
│  SERVIÇOS  —  app/services/                              │
│  Regras de negócio (BR-001 a BR-030), orquestração de    │
│  transações, cálculos, validações de invariante.         │
└────────────────────────┬─────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────┐
│  REPOSITÓRIOS  —  app/repositories/                      │
│  Acesso a dados. Consultas, filtros, paginação.          │
│  Nenhuma decisão de negócio.                             │
└────────────────────────┬─────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────┐
│  MODELOS  —  app/models/                                 │
│  Mapeamento SQLAlchemy, constraints, índices.            │
└────────────────────────┬─────────────────────────────────┘
                         ▼
              PostgreSQL 16  /  SQLite (local)
```

**Regras de dependência:** a seta aponta em um sentido só. Router importa serviço; serviço importa repositório; repositório importa modelo. Nunca o inverso. Um serviço nunca importa outro router; um repositório nunca importa um serviço.

### 2.2 Módulos transversais

| Módulo | Responsabilidade |
|---|---|
| `app/core/config.py` | Carregamento de configuração via Pydantic Settings |
| `app/core/database.py` | Engine, sessão, dependência `get_db` |
| `app/core/security.py` | Emissão e verificação de JWT, hash de senha, dependências de perfil |
| `app/core/exceptions.py` | Exceções de domínio e handlers globais |
| `app/core/metrics.py` | Instrumentação Prometheus |
| `app/core/audit.py` | Escrita na trilha de auditoria (NFR-AUD-02) |
| `app/utils/depreciacao.py` | Funções puras de cálculo (FR-003) |

---

## 3. Stack e Dependências

### 3.1 Runtime

| Componente | Versão de referência | Papel |
|---|---|---|
| Python | 3.12 | Runtime |
| FastAPI | 0.115.x | Framework web e geração de OpenAPI |
| Uvicorn | 0.32.x | Servidor ASGI |
| SQLAlchemy | 2.0.x | ORM (estilo declarativo 2.0, `Mapped[...]`) |
| Alembic | 1.13.x | Migrações versionadas |
| Pydantic | 2.9.x | Validação e serialização |
| pydantic-settings | 2.6.x | Configuração por ambiente |
| psycopg | 3.2.x | Driver PostgreSQL |
| PyJWT | 2.9.x | Emissão e verificação de token |
| passlib[bcrypt] | 1.7.x | Hash de senha (NFR-SEG-03) |
| pandas | 2.2.x | Leitura de CSV/XLSX na importação |
| openpyxl | 3.1.x | Suporte a XLSX |
| prometheus-client | 0.21.x | Exposição de métricas |
| python-multipart | 0.0.x | Upload de arquivo |

### 3.2 Desenvolvimento

| Componente | Papel |
|---|---|
| pytest, pytest-cov, pytest-asyncio | Testes e cobertura |
| httpx | Cliente de teste da API |
| factory-boy / Faker | Geração de massa de teste |
| ruff | Lint e formatação |
| mypy | Verificação de tipos |
| bandit | Análise estática de segurança |

> **Pinagem obrigatória.** `requirements.txt` fixa versões exatas (`==`). Nenhuma dependência sem versão definida, sob pena de o ambiente do professor divergir do da equipe.

---

## 4. Estrutura de Diretórios

```
itam-api/
├── app/
│   ├── main.py                      # criação do app, routers, handlers, métricas
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── metrics.py
│   │   ├── audit.py
│   │   └── logging.py
│   ├── models/
│   │   ├── base.py                  # DeclarativeBase, mixins de timestamp
│   │   ├── ativo.py
│   │   ├── categoria.py
│   │   ├── fornecedor.py
│   │   ├── responsavel.py
│   │   ├── setor.py
│   │   ├── licenca.py
│   │   ├── historico.py             # HistoricoTransferencia (append-only)
│   │   ├── baixa.py                 # BaixaAtivo (append-only)
│   │   ├── importacao.py            # LoteImportacao, ErroImportacao
│   │   ├── risco.py
│   │   ├── recomendacao.py          # Recomendacao, Evidencia
│   │   ├── usuario.py
│   │   └── auditoria.py             # AuditLog (append-only)
│   ├── schemas/                     # um módulo por agregado
│   ├── repositories/
│   ├── services/
│   │   ├── ativo_service.py
│   │   ├── responsavel_service.py
│   │   ├── depreciacao_service.py
│   │   ├── licenca_service.py
│   │   ├── baixa_service.py
│   │   ├── relatorio_service.py
│   │   ├── compliance_service.py
│   │   ├── indicador_service.py
│   │   ├── importacao_service.py
│   │   ├── cenario_service.py
│   │   ├── scorecard_service.py
│   │   ├── risco_service.py
│   │   └── recomendacao_service.py
│   ├── api/
│   │   ├── deps.py                  # get_db, get_current_user, require_perfil
│   │   └── v1/
│   │       ├── router.py            # agregador
│   │       └── routers/
│   └── utils/
│       ├── depreciacao.py
│       ├── datas.py
│       └── exportacao.py            # CSV/XLSX
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── unit/                        # funções puras e serviços
│   ├── integration/                 # API + banco
│   └── contract/                    # validação contra openapi.yaml
├── data/
│   ├── inventario_demo.csv
│   ├── licencas_demo.csv
│   └── seed.sql
├── scripts/
│   ├── start.sh
│   ├── stop.sh
│   ├── reset.sh
│   ├── seed.sh
│   └── smoke_test.sh
├── docker/
│   ├── prometheus/prometheus.yml
│   └── grafana/provisioning/
├── docs/
│   ├── PRD-ITAM.md
│   ├── ARQUITETURA.md
│   ├── MODELO_DE_DADOS.md
│   ├── CRITERIOS_DE_ACEITE.md
│   └── adr/
├── api/openapi.yaml                 # contrato congelado, usado nos testes
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── pytest.ini
├── ruff.toml
├── README.md
└── SPEC.md
```

---

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
| `setor_id` | BIGINT | FK → setor |
| `ativo` | BOOLEAN | NOT NULL, DEFAULT true |

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
| `software` | VARCHAR(120) | NOT NULL |
| `fornecedor_id` | BIGINT | NOT NULL, FK |
| `chave_licenca` | VARCHAR(200) | NOT NULL |
| `quantidade_contratada` | INTEGER | NOT NULL, CHECK ≥ 1 |
| `data_aquisicao` | DATE | NOT NULL |
| `data_expiracao` | DATE | NOT NULL, CHECK > `data_aquisicao` (BR-019) |
| `valor_total` | NUMERIC(12,2) | NOT NULL, CHECK > 0 |
| `tipo_licenciamento` | VARCHAR(20) | NOT NULL |

> `quantidade_em_uso` **não é coluna** — é derivada de `COUNT(*)` em `licenca_vinculo` (BR-021). Se a medição de desempenho exigir materialização, criar coluna sincronizada por trigger e cobrir com teste de consistência.

#### `licenca_vinculo`

| Coluna | Tipo | Restrições |
|---|---|---|
| `id` | BIGINT | PK |
| `licenca_id` | BIGINT | NOT NULL, FK |
| `ativo_id` | BIGINT | NOT NULL, FK |
| `data_vinculo` | DATE | NOT NULL |
| `ativo_vinculo` | BOOLEAN | NOT NULL, DEFAULT true |
| UNIQUE | | (`licenca_id`, `ativo_id`) onde `ativo_vinculo = true` |

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

Para `historico_transferencia`, `baixa_ativo` e `audit_log`, aplicar no PostgreSQL:

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

---

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
| POST | `/ativos/{id}/baixa` | ADMIN | FR-005 |

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
  "valor_compra": 6000.00,
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
  "valor_compra": 6000.00,
  "vida_util_meses": 60,
  "meses_decorridos": 12,
  "meses_efetivos": 12,
  "depreciacao_mensal": 100.00,
  "depreciacao_acumulada": 1200.00,
  "valor_residual": 4800.00,
  "percentual_depreciado": 20.00
}
```

Expor `meses_efetivos` e `depreciacao_mensal` é deliberado: torna o cálculo auditável sem acesso ao código, atendendo ao princípio de rastreabilidade (AC-015).

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

### 6.4 Licenças

| Método | Rota | Perfis | FR |
|---|---|---|---|
| GET/POST | `/licencas` | GET: todos · POST: ADMIN | FR-004 |
| GET/PATCH | `/licencas/{id}` | ADMIN | FR-004 |
| GET | `/licencas/{id}/vinculos` | todos | FR-004 |
| POST | `/licencas/{id}/vinculos` | ADMIN, OPERADOR | FR-004 |
| DELETE | `/licencas/{id}/vinculos/{ativo_id}` | ADMIN, OPERADOR | FR-004 |

A resposta de licença sempre inclui o bloco derivado:

```json
{
  "quantidade_contratada": 50,
  "quantidade_em_uso": 47,
  "saldo": 3,
  "dias_para_expiracao": 22,
  "status_conformidade": "ALERTA",
  "alertas": ["CP-03"]
}
```

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

### 6.6 Importação

| Método | Rota | Perfis | FR |
|---|---|---|---|
| POST | `/importacoes` | ADMIN | FR-008 |
| GET | `/importacoes` | ADMIN, AUDITOR | FR-008 |
| GET | `/importacoes/{id}` | ADMIN, AUDITOR | FR-008 |
| GET | `/importacoes/{id}/erros` | ADMIN, AUDITOR | FR-008 |

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

---

## 7. Regras de Cálculo

### 7.1 Depreciação linear (FR-003)

```python
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import date

CENTAVO = Decimal("0.01")

def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)   # BR-017

def meses_entre(inicio: date, fim: date) -> int:
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    if fim.day < inicio.day:
        meses -= 1
    return max(meses, 0)

@dataclass(frozen=True)
class Depreciacao:
    valor_compra: Decimal
    vida_util_meses: int
    meses_decorridos: int
    meses_efetivos: int
    depreciacao_mensal: Decimal
    depreciacao_acumulada: Decimal
    valor_residual: Decimal
    percentual_depreciado: Decimal

def calcular(valor_compra: Decimal, data_aquisicao: date,
             vida_util_meses: int, data_referencia: date) -> Depreciacao:
    decorridos = meses_entre(data_aquisicao, data_referencia)
    efetivos = min(decorridos, vida_util_meses)
    mensal = _arredondar(valor_compra / Decimal(vida_util_meses))
    acumulada = _arredondar(mensal * efetivos)
    if acumulada > valor_compra:
        acumulada = valor_compra                       # BR-014
    residual = _arredondar(valor_compra - acumulada)
    percentual = _arredondar(acumulada / valor_compra * Decimal(100))
    return Depreciacao(valor_compra, vida_util_meses, decorridos, efetivos,
                       mensal, acumulada, residual, percentual)
```

**Pontos obrigatórios:**

- `Decimal` em todo cálculo monetário. `float` introduz erro de representação e quebra a conciliação contábil (KPI-05). Colunas mapeadas como `Numeric(12, 2)`, nunca `Float`.
- Função pura, sem sessão de banco e sem acesso a `date.today()` internamente — a `data_referencia` é sempre injetada, o que torna os casos AC-015 a AC-020 testáveis sem manipular o relógio.
- `data_referencia` = `date.today()` para ativos em operação; `baixa.data_baixa` para ativos baixados (BR-015, AC-019).

### 7.2 Conformidade de licença (FR-004)

```
saldo             = quantidade_contratada − quantidade_em_uso
dias_expiracao    = (data_expiracao − hoje).days

CP-02 CRITICO  se  quantidade_em_uso > quantidade_contratada
CP-01 CRITICO  se  dias_expiracao < 0
CP-03 ALTO     se  0 <= dias_expiracao <= JANELA_ALERTA_DIAS
      MEDIO    se  saldo == 0
      BAIXO    se  quantidade_em_uso <= contratada * 0.5 e idade > 6 meses
```

`JANELA_ALERTA_DIAS` é configurável (padrão 30, QA-07 em aberto).

### 7.3 Score de risco (FR-012)

`score = probabilidade × impacto`, ambos de 1 a 5. Faixas: 1–4 baixo, 5–9 médio, 10–14 alto, 15–25 crítico (AC-050).

### 7.4 Scorecard de fornecedores (FR-011)

```
validar: soma(pesos) == 100          → senão 422 citando BR-029 (AC-048)
validar: 0 <= nota <= 10 para todos os critérios
pontuacao(f) = soma(nota[f][c] * peso[c] / 100)
ranking = ordenar por pontuacao desc
```

A comparação de soma de pesos usa `Decimal`, não `float` — `0.3 + 0.3 + 0.4 != 1.0` em ponto flutuante binário.

### 7.5 TCO de cenários (FR-010)

```
tco_5_anos           = capex + (opex_anual * 5)
custo_por_ativo_ano  = tco_5_anos / (quantidade_ativos * 5)
economia_vs_baseline = tco_baseline − tco_cenario
score_risco          = soma dos scores dos riscos vinculados ao cenário
```

---

## 8. Padrão de Erros

Formato único em toda a API, inspirado na RFC 7807, com o campo adicional `regra`:

```json
{
  "tipo": "/erros/regra-de-negocio",
  "titulo": "Operação recusada por regra de negócio",
  "status": 409,
  "detalhe": "A quantidade em uso não pode exceder a quantidade contratada.",
  "instancia": "/api/v1/licencas/12/vinculos",
  "regra": "BR-018",
  "erros": []
}
```

O campo `regra` cria rastreabilidade direta entre o comportamento em runtime e o documento de requisitos — útil na defesa e exigido pela matriz de rastreabilidade.

| Situação | HTTP | Exemplo de regra |
|---|---|---|
| Payload malformado ou validação Pydantic | 422 | — |
| Violação de regra de negócio | 409 | BR-009, BR-018, BR-024 |
| Violação de unicidade | 409 | BR-001 |
| Recurso inexistente | 404 | — |
| Sem token ou token inválido | 401 | — |
| Perfil sem permissão | 403 | FR-015 |
| Erro interno | 500 | — |

**Regra de ouro (NFR-SEG-06):** nenhuma resposta de erro expõe stack trace, nome de tabela ou versão de framework. O handler global captura `Exception`, registra o traceback no log estruturado e devolve payload genérico.

**Toda recusa por regra de negócio é registrada na auditoria** com `resultado = RECUSADO` e `regra_violada` preenchida (NFR-AUD-05, AC-021).

---

## 9. Segurança

### 9.1 Autenticação

- JWT HS256, `SECRET_KEY` obrigatoriamente via variável de ambiente (NFR-SEG-07);
- Claims: `sub` (id), `login`, `perfil`, `exp`, `iat`;
- Expiração padrão de 8 horas, configurável;
- Senha com BCrypt, custo ≥ 10 (NFR-SEG-03).

### 9.2 Autorização

```python
def require_perfil(*perfis: PerfilUsuario):
    def _verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfis:
            raise PermissaoNegadaError(perfil=usuario.perfil.value)
        return usuario
    return _verificar

@router.post("/ativos", dependencies=[Depends(require_perfil(ADMIN, OPERADOR))])
```

Nenhum perfil possui permissão de DELETE sobre registros de domínio (RI-06). A tabela completa está no FR-015 do PRD e deve ser coberta por teste parametrizado — um caso por célula da matriz (AC-055).

### 9.3 Outros controles

- Consultas exclusivamente via ORM ou `text()` com bind parameters (NFR-SEG-05);
- `chave_licenca` mascarada nas listagens (`****-****-A3F9`), completa apenas no detalhe e apenas para `ADMIN` (RI-08);
- CORS restrito por lista de origens configurável;
- `bandit` no pipeline, falhando o build em severidade alta.

---

## 10. Pipeline de Importação (FR-008)

### 10.1 Esquema do arquivo de ativos

| Coluna | Obrigatória | Formato |
|---|---|---|
| `nome` | Sim | texto, 3–120 |
| `tipo` | Sim | `HARDWARE` ou `SOFTWARE` |
| `categoria` | Sim | nome da categoria existente |
| `fornecedor` | Sim | razão social existente |
| `numero_serie` | Condicional | texto |
| `chave_licenca` | Condicional | texto |
| `data_aquisicao` | Sim | `AAAA-MM-DD` |
| `valor_compra` | Sim | decimal, ponto como separador |
| `localizacao` | Não | texto |

### 10.2 Etapas

```
1. Ler arquivo (pandas: read_csv | read_excel)
2. Validar cabeçalhos
   └── divergente → 422, arquivo inteiro recusado, nenhuma linha processada (AC-045)
3. Para cada linha:
   ├── normalizar (trim, upper em enums, parse de data e decimal)
   ├── validar campos obrigatórios e domínios
   ├── resolver categoria e fornecedor por nome
   ├── verificar duplicidade contra o arquivo já lido
   ├── verificar duplicidade contra a base (AC-046)
   ├── válida   → acumular em lote_aceitos
   └── inválida → registrar ErroImportacao (linha, campo, valor, motivo)
4. Persistir aceitos em transação única, com lote_importacao_id
5. Persistir LoteImportacao e ErroImportacao
6. Retornar resumo com URL dos erros
```

**Isolamento por registro (FR-008):** uma linha inválida não impede as demais. Erros de validação são acumulados, não lançados.

**Limite:** arquivos acima de 5 MB ou 5.000 linhas são recusados no MVP. Processamento assíncrono fica para a V2.

---

## 11. Observabilidade

### 11.1 Métricas expostas

| Métrica | Tipo | Labels |
|---|---|---|
| `itam_http_requests_total` | Counter | `method`, `endpoint`, `status` |
| `itam_http_request_duration_seconds` | Histogram | `method`, `endpoint` |
| `itam_ativos_total` | Gauge | `status` |
| `itam_licencas_nao_conformes` | Gauge | `motivo` |
| `itam_importacoes_total` | Counter | `resultado` |
| `itam_regras_violadas_total` | Counter | `regra` |

`itam_regras_violadas_total` é a métrica mais interessante do conjunto: permite demonstrar em Grafana, durante a defesa, quantas tentativas de operar em desconformidade o sistema bloqueou.

### 11.2 Log estruturado

JSON em uma linha por evento, com `timestamp`, `level`, `logger`, `mensagem`, `request_id`, `usuario_id` e `regra`. Nível configurável por `LOG_LEVEL`.

### 11.3 Grafana

Provisionamento automático: datasource Prometheus, pasta **Governança de TI**, dashboard com disponibilidade, requisições por minuto, distribuição de códigos de retorno, latência p50/p95/p99 e estado do banco.

---

## 12. Estratégia de Testes

| Camada | Alvo | Ferramenta | Meta |
|---|---|---|---|
| Unitário | Funções puras (`utils/depreciacao.py`) e serviços com repositório falso | pytest | 100% das regras de cálculo |
| Integração | Endpoints com banco real (SQLite em memória ou PostgreSQL efêmero) | pytest + httpx | Um teste por critério de aceite |
| Contrato | Validação das respostas contra `api/openapi.yaml` | schemathesis | Todos os endpoints |
| Fumaça | Ambiente orquestrado no ar | `scripts/smoke_test.sh` | health, metrics, KPIs |
| Segurança | Análise estática | bandit, ruff | Zero achados de severidade alta |

**Convenção de nomenclatura.** Cada teste carrega o identificador do critério que valida:

```python
def test_ac015_depreciacao_linear_12_meses_de_60(): ...
def test_ac021_bloqueia_vinculo_acima_do_contratado(): ...
def test_ac051_recusa_recomendacao_sem_evidencia(): ...
```

Isso torna a matriz de rastreabilidade verificável por comando, não por inspeção manual:

```bash
pytest --collect-only -q | grep -c "test_ac"
```

**Cobertura mínima:** 70% global (NFR-MAN-03), com exigência de 100% em `app/utils/` e `app/services/`.

**Casos de borda obrigatórios:** ativo adquirido hoje (zero meses); ativo com vida útil esgotada; ativo com vida útil de 1 mês; transferência no mesmo dia da aquisição; licença expirando exatamente hoje; importação com arquivo vazio; importação só com linhas inválidas.

---

## 13. Configuração

### 13.1 `.env.example`

```dotenv
# Aplicação
APP_NAME=ITAM
APP_VERSION=1.0.0
ENVIRONMENT=local              # local | docker | producao
LOG_LEVEL=INFO
API_PREFIX=/api/v1

# Banco
DATABASE_URL=sqlite:///./itam.db
# DATABASE_URL=postgresql+psycopg://itam:itam@db:5432/itam_db

# Segurança
SECRET_KEY=troque-esta-chave-em-qualquer-ambiente-real
JWT_ALGORITHM=HS256
JWT_EXPIRACAO_MINUTOS=480
CORS_ORIGINS=http://localhost:3000

# Regras de negócio configuráveis
JANELA_ALERTA_LICENCA_DIAS=30
LIMIAR_FIM_VIDA_UTIL_PERCENTUAL=80
DIAS_MANUTENCAO_ALERTA=90
MESES_SEM_MOVIMENTACAO_ALERTA=12

# Importação
IMPORTACAO_TAMANHO_MAX_MB=5
IMPORTACAO_LINHAS_MAX=5000
```

Nenhum valor padrão de `SECRET_KEY` é aceito quando `ENVIRONMENT != local`: a aplicação deve **recusar a inicialização**, não apenas emitir aviso.

### 13.2 Migrações e carga inicial

- Alembic com uma migração por alteração de esquema, nunca `create_all()` em ambiente não local;
- `scripts/seed.sh` popula categorias com a vida útil padrão da tabela do FR-003, os quatro perfis de usuário e os datasets de demonstração;
- `scripts/reset.sh` derruba volumes e recria do zero — **somente em laboratório**.

---

## 14. Plano de Sprints

| Sprint | Entregas técnicas | Critérios cobertos |
|---|---|---|
| **0** | Repositório, estrutura de pastas, Docker Compose, Alembic, CI, `openapi.yaml` inicial, ADRs 001–003 | — |
| **1** | Modelos e migrações de `categoria`, `fornecedor`, `setor`, `responsavel`, `ativo`, `usuario`; auth + RBAC; CRUD de ativos; importação CSV/XLSX | AC-001 a AC-008, AC-044 a AC-046, AC-055 a AC-057 |
| **2** | `historico_transferencia` com índice único parcial e triggers; endpoint de responsável; `utils/depreciacao.py`; endpoint de depreciação | AC-009 a AC-020 |
| **3** | `licenca`, `licenca_vinculo`, bloqueio de excedente; `baixa_ativo` com congelamento de valor residual | AC-021 a AC-033 |
| **4** | Relatórios com filtros e exportação; painel de compliance; indicadores; `/health`, `/metrics`, Grafana provisionado | AC-034 a AC-043, AC-047, AC-053, AC-054 |
| **5** | Cenários, scorecard, riscos, recomendação rastreável; testes de contrato; documentação final; smoke test; defesa | AC-048 a AC-052 |

**Definition of Done por sprint:** código na branch principal · migração aplicada e reversível · testes dos critérios da sprint passando · `openapi.yaml` regenerado e versionado · `docker compose up` sobe o ambiente sem intervenção manual · README atualizado se houve mudança de execução.

---

## 15. Decisões Arquiteturais (ADR resumidas)

| ID | Decisão | Alternativa descartada | Motivo |
|---|---|---|---|
| ADR-001 | Monólito modular em FastAPI | Microsserviços | Escopo de MVP; complexidade operacional sem benefício proporcional |
| ADR-002 | Depreciação calculada sob demanda | Persistir valor depreciado | Evita job de recálculo e divergência entre o valor armazenado e a data corrente |
| ADR-003 | Responsável atual derivado do histórico | Coluna `responsavel_id` no ativo | Elimina fonte de verdade concorrente (seção 14.3 do PRD) |
| ADR-004 | `Decimal` com `Numeric(12,2)` | `float` | Precisão contábil exigida pelo KPI-05 |
| ADR-005 | Imutabilidade por trigger no banco | Convenção de código | Garantia independente da disciplina da equipe (NFR-AUD-01) |
| ADR-006 | Índice único parcial para vínculo aberto | Validação só na aplicação | Só o banco garante a invariante sob concorrência (BR-007) |
| ADR-007 | Enums como VARCHAR + CHECK | Tipo ENUM do PostgreSQL | Portabilidade para SQLite e migrações mais simples |
| ADR-008 | `quantidade_em_uso` derivada por COUNT | Coluna materializada | Elimina risco de dessincronização (BR-021) |
| ADR-009 | Campo `regra` no payload de erro | Mensagem livre | Rastreabilidade runtime → requisito, verificável na defesa |
| ADR-010 | Testes nomeados pelo identificador do critério | Nomes livres | Matriz de rastreabilidade verificável por comando |

---

## Apêndice — Mapa Requisito → Módulo → Teste

| FR | Serviço | Módulo de teste |
|---|---|---|
| FR-001 | `ativo_service.py` | `tests/integration/test_ativos.py` |
| FR-002 | `responsavel_service.py` | `tests/integration/test_responsaveis.py` |
| FR-003 | `depreciacao_service.py`, `utils/depreciacao.py` | `tests/unit/test_depreciacao.py` |
| FR-004 | `licenca_service.py` | `tests/integration/test_licencas.py` |
| FR-005 | `baixa_service.py` | `tests/integration/test_baixas.py` |
| FR-006 | `relatorio_service.py` | `tests/integration/test_relatorios.py` |
| FR-007 | `compliance_service.py` | `tests/integration/test_compliance.py` |
| FR-008 | `importacao_service.py` | `tests/integration/test_importacao.py` |
| FR-009 | `indicador_service.py` | `tests/integration/test_indicadores.py` |
| FR-010 | `cenario_service.py` | `tests/unit/test_cenarios.py` |
| FR-011 | `scorecard_service.py` | `tests/unit/test_scorecard.py` |
| FR-012 | `risco_service.py` | `tests/unit/test_riscos.py` |
| FR-013 | `recomendacao_service.py` | `tests/integration/test_recomendacoes.py` |
| FR-014 | `core/metrics.py` | `tests/integration/test_observabilidade.py` |
| FR-015 | `core/security.py`, `api/deps.py` | `tests/integration/test_seguranca.py` |
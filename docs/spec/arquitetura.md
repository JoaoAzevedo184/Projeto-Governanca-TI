# SPEC — Arquitetura

Parte de [SPEC — ITAM](README.md).

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
│  MODELOS  —  app/models/                                 │
│  Mapeamento SQLAlchemy, constraints, índices.            │
└────────────────────────┬─────────────────────────────────┘
                         ▼
              PostgreSQL 16  /  SQLite (local)
```

*SQLite revisado (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)):* a aplicação continua rodando em SQLite para execução local sem Docker (`DATABASE_URL`), mas os testes rodam só em PostgreSQL 16. A migração `c8365ce7e5e4` só cria o trigger `permitir_apenas_encerramento` quando o dialeto é PostgreSQL (`_postgres()`); o índice único parcial `ux_vinculo_aberto` é criado nos dois bancos.

**Regras de dependência:** a seta aponta em um sentido só. Router importa serviço; serviço importa modelo e usa a `Session` do SQLAlchemy direto. Nunca o inverso: um serviço nunca importa router, um modelo nunca importa serviço.

**Não há camada de repositório.** `app/repositories/` existe só com `.gitkeep`; nenhum módulo a importa. O acesso a dados fica nos serviços, pela `Session`.

**Leituras diretas no router.** Consultas sem regra de negócio acessam o modelo direto pela `Session`, sem passar por serviço: listagens de `categorias`, `fornecedores`, `setores` e `responsaveis`; `POST /auth/login`; `GET /importacoes`, `GET /importacoes/{id}` e `GET /importacoes/{id}/erros`; e a dependência `get_current_user` em `app/api/deps.py`. Toda escrita passa por serviço. Os desvios condicionais nesses pontos são autenticação, autorização e 404, não regra de negócio (BR).

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


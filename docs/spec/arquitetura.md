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


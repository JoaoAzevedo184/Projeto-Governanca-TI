# SPEC — Stack e Dependências

Parte de [SPEC — ITAM](README.md).

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


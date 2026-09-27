# Modelo de Dados — Dados Semente

Parte de [Modelo de Dados — ITAM](README.md).

## 7. Dados semente

Carregados por `scripts/seed.sh`, obrigatórios para o sistema funcionar:

### Categorias (vida útil conforme IN RFB nº 1.700/2017)

| Nome | Tipo | Vida útil (meses) |
|---|---|---|
| Notebook | HARDWARE | 60 |
| Desktop | HARDWARE | 60 |
| Servidor | HARDWARE | 60 |
| Monitor | HARDWARE | 60 |
| Switch | HARDWARE | 60 |
| Roteador | HARDWARE | 60 |
| Impressora | HARDWARE | 48 |
| Smartphone | HARDWARE | 36 |
| Tablet | HARDWARE | 36 |
| Nobreak | HARDWARE | 60 |
| Software perpétuo | SOFTWARE | 60 |

### Usuários de demonstração

Um por perfil — `admin`, `operador`, `gestor`, `auditor` — com senhas definidas em `.env`, para uso exclusivo em laboratório.


# Modelo de Dados — ITAM

Modelo lógico e físico do MVP de Gestão de Ativos de TI. Referencia as regras `BR-` do [`docs/prd/regras-de-negocio.md`](../prd/regras-de-negocio.md) e detalha o que o [`docs/spec/modelo-fisico.md`](../spec/modelo-fisico.md) resume.

Dividido em arquivos menores por responsabilidade. Índice:

| Arquivo | Conteúdo |
|---|---|
| [`diagrama-er.md`](diagrama-er.md) | Diagrama de entidade-relacionamento (Mermaid) |
| [`enumeracoes.md`](enumeracoes.md) | Enumerações usadas nas tabelas |
| [`dicionario-de-dados.md`](dicionario-de-dados.md) | Dicionário de dados completo — todas as tabelas, colunas, tipos e regras |
| [`invariantes.md`](invariantes.md) | Invariantes e como são garantidas (constraint, trigger, serviço) |
| [`indices.md`](indices.md) | Índices |
| [`consultas-de-referencia.md`](consultas-de-referencia.md) | Consultas SQL derivadas de referência |
| [`dados-semente.md`](dados-semente.md) | Dados semente obrigatórios (categorias, usuários) |
| [`datasets-de-demonstracao.md`](datasets-de-demonstracao.md) | Mapeamento dos datasets de demonstração e desvios plantados |
| [`migracoes.md`](migracoes.md) | Migrações e compatibilidade com SQLite |

# PRD — Requisitos Não Funcionais (NFR-)

Parte de [PRD — ITAM](README.md).

## 13. Requisitos Não Funcionais

### 13.1 Segurança

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-SEG-01 | Autenticação via JWT com expiração configurável (padrão: 8 horas) | Requisição sem token válido retorna HTTP 401 |
| NFR-SEG-02 | Controle de acesso baseado em papéis (RBAC) com os perfis `ADMIN`, `OPERADOR`, `GESTOR` e `AUDITOR` | Matriz de permissões do FR-015 validada por teste automatizado |
| NFR-SEG-03 | Senhas armazenadas com hash e salt (BCrypt, custo ≥ 10) | Inspeção da base não revela senha em texto claro |
| NFR-SEG-04 | Validação de entrada em todos os endpoints, com rejeição de payload malformado | Teste de injeção não altera estado do sistema |
| NFR-SEG-05 | Uso obrigatório de consultas parametrizadas ou ORM; nenhuma concatenação de SQL | Análise estática sem ocorrências |
| NFR-SEG-06 | Mensagens de erro não expõem stack trace, versão de framework ou estrutura interna | Resposta de erro padronizada verificada em teste |
| NFR-SEG-07 | Segredos (credenciais de banco, chave JWT) fora do código-fonte, via variáveis de ambiente | Repositório sem segredos versionados |

### 13.2 Performance

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-PER-01 | Consultas comuns (busca de ativo, detalhe, listagem paginada) respondem em menos de 2 segundos | Percentil 95 medido com base de 1.000 ativos |
| NFR-PER-02 | Geração de relatório de inventário completo em menos de 5 segundos | Medido com 1.000 ativos |
| NFR-PER-03 | Importação de arquivo com 1.000 linhas concluída em menos de 30 segundos | Medido em ambiente de referência |
| NFR-PER-04 | Listagens sempre paginadas, com tamanho de página padrão de 20 e máximo de 100 | Requisição acima do máximo é limitada, não recusada |
| NFR-PER-05 | Índices em `numero_serie`, `status`, `categoria_id`, `fornecedor_id` e nas chaves de vínculo | Verificado nas migrações de banco |

### 13.3 Auditoria

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-AUD-01 | Histórico de alterações imutável: registros de vínculo, baixa e auditoria não admitem UPDATE nem DELETE | Tentativa de exclusão retorna erro; teste automatizado. *Estado atual:* verificado para vínculo (AC-013), auditoria e baixa, com teste direto no PostgreSQL |
| NFR-AUD-02 | Toda operação de escrita grava usuário autor, operação, entidade, identificador e carimbo de tempo | Trilha consultável por entidade e por período |
| NFR-AUD-03 | Carimbos de tempo em UTC, com fuso apresentado na interface | Verificado na resposta da API |
| NFR-AUD-04 | Relatórios exportados identificam data, hora e usuário gerador | Cabeçalho do arquivo exportado |
| NFR-AUD-05 | Operações bloqueadas por regra de negócio (ex.: excedente de licença) também são registradas | Trilha contém tentativas recusadas |

### 13.4 Usabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-USA-01 | Interface responsiva, utilizável em telas a partir de 360 px de largura | Testado em resolução móvel |
| NFR-USA-02 | Formulário de transferência de responsável com no máximo 4 campos | Inspeção da tela |
| NFR-USA-03 | Mensagens de erro em português, indicando o campo e a correção esperada | Inspeção das respostas de validação |
| NFR-USA-04 | Busca global de ativos acessível de qualquer tela | Inspeção da navegação |
| NFR-USA-05 | Ações destrutivas ou irreversíveis (baixa) exigem confirmação explícita | Inspeção da interface |

### 13.5 Disponibilidade e Confiabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-DIS-01 | Sistema suporta ao menos 20 usuários simultâneos sem degradação perceptível | Teste de carga |
| NFR-DIS-02 | Transações que envolvem múltiplas entidades (transferência, baixa) são atômicas | Teste de falha simulada não deixa estado parcial |
| NFR-DIS-03 | Health check disponível para verificação externa | `GET /health` retorna 200 |
| NFR-DIS-04 | Aplicação reinicia sem perda de dados persistidos | Reinício de contêiner preserva o volume |

### 13.6 Manutenibilidade e Portabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-MAN-01 | Implementações Python e Java obedecem ao **mesmo contrato de API** | Testes de contrato passam contra as duas implementações |
| NFR-MAN-02 | Documentação OpenAPI gerada automaticamente e acessível | `/docs` e `/swagger-ui` disponíveis |
| NFR-MAN-03 | Cobertura de testes automatizados ≥ 70% nas regras de negócio | Relatório de cobertura |
| NFR-MAN-04 | Execução via Docker Compose com um único comando | `docker compose up` sobe o ambiente completo |
| NFR-MAN-05 | Banco de dados local simplificado (SQLite/H2) e definitivo (PostgreSQL) selecionáveis por variável de ambiente | Ambos os perfis executam os mesmos testes. *Revisado (item 13 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)):* a aplicação continua rodando em SQLite para execução local sem Docker (`DATABASE_URL`), mas os testes rodam só em PostgreSQL 16, local e no CI |
| NFR-MAN-06 | Migrações de banco versionadas | Base criada do zero por script |

### 13.7 Observabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-OBS-01 | Endpoint `/metrics` no padrão de exposição Prometheus | Scrape do Prometheus bem-sucedido |
| NFR-OBS-02 | Contador de requisições por endpoint e código de retorno, e histograma de duração | Métricas visíveis no Grafana |
| NFR-OBS-03 | Log estruturado com nível configurável | Inspeção da saída |
| NFR-OBS-04 | Identificação do ambiente em execução exposta no health check | Campo `environment` na resposta |


# PRD — Critérios de Aceitação (AC-)

Parte de [PRD — ITAM](README.md).

## 12. Critérios de Aceitação

### FR-001 — Cadastro de Ativos

- [ ] **AC-001** — Dado um administrador autenticado, quando cadastra um notebook com todos os campos obrigatórios, então o ativo é criado com status `ATIVO` e recebe identificador único.
- [ ] **AC-002** — Dado um número de série já existente na base, quando o administrador tenta cadastrar outro ativo com o mesmo número, então o sistema recusa a operação e informa o ativo conflitante.
- [ ] **AC-003** — Dado um ativo do tipo `HARDWARE` sem número de série, quando se tenta salvar, então o sistema retorna erro de validação no campo `numero_serie`.
- [ ] **AC-004** — Dado um ativo do tipo `SOFTWARE` sem chave de licença, quando se tenta salvar, então o sistema retorna erro de validação no campo `chave_licenca`.
- [ ] **AC-005** — Dada uma data de aquisição futura, quando se tenta salvar, então o sistema recusa com mensagem específica.
- [ ] **AC-006** — Dado um valor de compra igual a zero ou negativo, quando se tenta salvar, então o sistema recusa.
- [ ] **AC-007** — Dado um ativo cadastrado sem vida útil informada, quando ele é criado, então a vida útil é herdada da categoria selecionada.
- [ ] **AC-008** — Dada uma busca por número de série parcial, quando executada, então o sistema retorna os ativos correspondentes em menos de 2 segundos.

### FR-002 — Vinculação de Responsável

- [ ] **AC-009** — Dado um ativo sem responsável, quando o operador atribui um responsável com data, então um vínculo aberto é criado.
- [ ] **AC-010** — Dado um ativo com vínculo aberto, quando o operador registra uma transferência, então o vínculo anterior é encerrado com `data_fim` igual à `data_inicio` do novo e o novo vínculo é criado na mesma transação.
- [ ] **AC-011** — Dado um ativo com status `BAIXADO`, quando se tenta atribuir responsável, então o sistema recusa a operação.
- [ ] **AC-012** — Dado um ativo com três transferências, quando se consulta o histórico, então os quatro vínculos são retornados em ordem cronológica, sem sobreposição de períodos.
- [ ] **AC-013** — Dado um vínculo encerrado, quando qualquer perfil tenta editá-lo ou excluí-lo, então a operação é negada.
- [ ] **AC-014** — Dada uma data de início anterior à data de aquisição do ativo, quando se tenta salvar, então o sistema recusa.

### FR-003 — Cálculo de Depreciação

- [ ] **AC-015** — Dado um ativo de R$ 6.000,00 com vida útil de 60 meses adquirido há 12 meses, quando se consulta sua depreciação, então o sistema retorna depreciação acumulada de R$ 1.200,00, valor residual de R$ 4.800,00 e 20% depreciado.
- [ ] **AC-016** — Dado um ativo com 72 meses de uso e vida útil de 60 meses, quando se consulta, então o valor residual é R$ 0,00 e o percentual depreciado é 100%.
- [ ] **AC-017** — Dado qualquer ativo, quando se consulta o valor residual, então o resultado nunca é negativo.
- [ ] **AC-018** — Dado um ativo recém-cadastrado, quando a tela de detalhe é aberta, então a depreciação já aparece calculada, sem ação adicional do usuário.
- [ ] **AC-019** — Dado um ativo baixado, quando se consulta a depreciação, então o cálculo utiliza a data da baixa como referência e não a data corrente.
- [ ] **AC-020** — Dadas duas categorias com vidas úteis distintas, quando ativos de mesmo valor são consultados, então as depreciações acumuladas diferem proporcionalmente.

### FR-004 — Controle de Licenças

- [ ] **AC-021** — Dada uma licença com 50 unidades contratadas e 50 em uso, quando se tenta vincular a 51ª instalação, então o sistema bloqueia e registra o evento na auditoria.
- [ ] **AC-022** — Dada uma licença com expiração em 25 dias, quando o painel de compliance é consultado, então ela aparece com severidade **Alto**.
- [ ] **AC-023** — Dada uma licença vencida, quando o painel é consultado, então ela aparece com severidade **Crítico**.
- [ ] **AC-024** — Dada uma data de expiração anterior à data de aquisição, quando se tenta salvar a licença, então o sistema recusa.
- [ ] **AC-025** — Dada uma licença vencida, quando se tenta vincular nova instalação, então a operação é recusada.
- [ ] **AC-026** — Dada uma licença com vínculos, quando um vínculo é removido, então a quantidade em uso é decrementada automaticamente.

### FR-005 — Baixa/Descarte

- [ ] **AC-027** — Dado um ativo ativo com responsável, quando a baixa é registrada, então o status passa a `BAIXADO` e o vínculo de responsável é encerrado.
- [ ] **AC-028** — Dada uma baixa com motivo `OUTRO` e justificativa vazia, quando se tenta salvar, então o sistema recusa.
- [ ] **AC-029** — Dada uma data de baixa futura, quando se tenta salvar, então o sistema recusa.
- [ ] **AC-030** — Dado um ativo já baixado, quando se tenta registrar nova baixa, então o sistema recusa.
- [ ] **AC-031** — Dado um ativo baixado, quando o relatório de inventário ativo é gerado, então o ativo não aparece; quando o filtro `Baixado` é aplicado, então ele aparece.
- [ ] **AC-032** — Dada uma baixa registrada, quando o histórico do ativo é consultado, então todos os vínculos anteriores permanecem visíveis e íntegros.
- [ ] **AC-033** — Dada uma baixa sem destinação informada, quando se tenta salvar, então o sistema recusa.

### FR-006 — Relatório de Inventário

- [ ] **AC-034** — Dado o relatório de inventário, quando se aplicam simultaneamente os filtros de status, categoria e responsável, então o resultado respeita todos os critérios em conjunção.
- [ ] **AC-035** — Dado o filtro de faixa de valor depreciado entre R$ 1.000,00 e R$ 3.000,00, quando aplicado, então apenas ativos nessa faixa são retornados.
- [ ] **AC-036** — Dado um relatório gerado, quando exportado em CSV, então o arquivo contém cabeçalho com data, hora e usuário solicitante.
- [ ] **AC-037** — Dado um relatório com 500 ativos, quando a exportação é solicitada, então todos os 500 registros constam no arquivo, sem truncamento por paginação.
- [ ] **AC-038** — Dado o filtro "próximos do fim da vida útil", quando aplicado, então retorna apenas ativos com 80% ou mais da vida útil consumida.

### FR-007 — Alerta de Compliance

- [ ] **AC-039** — Dado um ativo ativo sem responsável, quando o painel de compliance é consultado, então o alerta CP-04 é exibido com severidade **Alto**.
- [ ] **AC-040** — Dado o painel de compliance, quando exibido, então os alertas são agrupados por severidade em ordem decrescente de criticidade.
- [ ] **AC-041** — Dado um alerta exibido, quando o usuário clica sobre ele, então é redirecionado ao registro de origem.
- [ ] **AC-042** — Dado um alerta, quando exibido, então a regra que o originou é apresentada de forma legível.
- [ ] **AC-043** — Dado que a não conformidade foi corrigida, quando o painel é recarregado, então o alerta correspondente desaparece sem ação manual.

### FR-008 a FR-015 — Extensão

- [ ] **AC-044** — Dado um CSV com 100 linhas, das quais 8 inválidas, quando importado, então 92 ativos são criados e o relatório de erros lista as 8 linhas com número, campo e motivo.
- [ ] **AC-045** — Dado um CSV com cabeçalhos divergentes do esperado, quando importado, então o sistema recusa o arquivo inteiro antes de processar qualquer linha.
- [ ] **AC-046** — Dado um CSV com dois registros de mesmo número de série, quando importado, então o segundo é rejeitado por duplicidade.
- [ ] **AC-047** — Dado um conjunto de ativos, quando os indicadores são consultados, então cada indicador retorna acompanhado da fórmula aplicada e do tamanho da amostra.
- [ ] **AC-048** — Dado um scorecard com pesos somando 95%, quando submetido, então o sistema recusa com mensagem explícita.
- [ ] **AC-049** — Dado um scorecard válido, quando submetido, então o sistema retorna a pontuação ponderada e o ranking dos fornecedores.
- [ ] **AC-050** — Dado um risco com probabilidade 4 e impacto 5, quando registrado, então o score é 20 e a classificação é **Crítico**.
- [ ] **AC-051** — Dada uma recomendação sem evidência vinculada, quando se tenta gravá-la, então o sistema recusa com erro de validação explícito.
- [ ] **AC-052** — Dada uma comparação de cenários, quando executada, então o sistema retorna os cenários ordenados por custo e risco, sem marcar nenhum como escolhido.
- [ ] **AC-053** — Dado o endpoint `/health`, quando requisitado, então retorna HTTP 200 com o estado da aplicação e da conexão com o banco.
- [ ] **AC-054** — Dado o endpoint `/metrics`, quando requisitado, então retorna métricas no formato de exposição Prometheus.
- [ ] **AC-055** — Dado um usuário com perfil `AUDITOR`, quando tenta criar ou editar qualquer registro, então recebe HTTP 403.
- [ ] **AC-056** — Dada uma requisição sem token JWT válido a endpoint protegido, quando executada, então recebe HTTP 401.
- [ ] **AC-057** — Dada qualquer operação de escrita, quando concluída, então a trilha de auditoria registra usuário, operação, entidade afetada e carimbo de tempo.

### FR-004 e FR-005 — Vínculo de licença e baixa (BR-031 a BR-038)

- [ ] **AC-058** — Dada uma máquina com vínculos ativos de duas licenças, quando a baixa é registrada, então os dois vínculos são encerrados na mesma transação, cada encerramento é registrado na auditoria, e a quantidade em uso e o saldo de cada licença refletem a liberação dos assentos.
- [ ] **AC-059** — Dada uma máquina com status `BAIXADO`, quando se tenta vincular uma licença a ela, então o sistema recusa a operação com `regra = BR-032` e registra a recusa na auditoria.
- [ ] **AC-060** — Dado um ativo que não é `HARDWARE`, quando se tenta vinculá-lo a uma licença como máquina hospedeira, então o sistema recusa a operação com `regra = BR-033` e registra a recusa na auditoria.
- [ ] **AC-061** — Dada uma máquina que já tem vínculo ativo de uma licença, quando se tenta vinculá-la de novo à mesma licença, então o sistema recusa a operação com `regra = BR-034` e registra a recusa na auditoria.
- [ ] **AC-062** — Dada uma licença `PERPETUA` que aponta para um ativo que não é `SOFTWARE`, quando se tenta criá-la, então o sistema recusa a operação com `regra = BR-035` e registra a recusa na auditoria.
- [ ] **AC-063** — Dado o ativo `SOFTWARE` de uma licença perpétua com vínculos ativos em duas máquinas, quando a baixa do software é registrada, então os dois vínculos são encerrados na mesma transação, cada encerramento é registrado na auditoria, a quantidade em uso e o saldo da licença refletem a liberação dos assentos e a licença permanece inalterada.
- [ ] **AC-064** — Dada uma licença cujo ativo `SOFTWARE` está `BAIXADO`, quando se tenta vincular uma máquina a ela, então o sistema recusa a operação com `regra = BR-037` e registra a recusa na auditoria.
- [ ] **AC-065** — Dado um responsável ou um setor inativo, quando se tenta atribuí-lo a um ativo, então o sistema recusa a operação com `regra = BR-038` e registra a recusa na auditoria.
- [ ] **AC-066** — Dado um ativo `SOFTWARE` com status `BAIXADO`, quando se tenta criar uma licença `PERPETUA` apontando para ele, então o sistema recusa a operação com `regra = BR-037` e registra a recusa na auditoria.

# PRD — Jornadas e Histórias de Usuário

Parte de [PRD — ITAM](README.md).

## 8. Jornada do Usuário

### 8.1 Cadastro de Hardware

**Ator:** Marcos (Administrador de TI) · **Gatilho:** chegada de um lote de notebooks

1. Marcos autentica-se e acessa **Ativos → Novo Ativo**.
2. Seleciona o tipo **Hardware**. O formulário exibe o campo *Número de Série* e oculta *Chave de Licença*.
3. Preenche nome, categoria (*Notebook*), número de série, data de aquisição, valor de compra e fornecedor.
4. O sistema valida a unicidade do número de série. Se já existir, exibe o ativo conflitante e bloqueia o salvamento.
5. Ao salvar, o status é definido automaticamente como **Ativo** e a vida útil é herdada da categoria (60 meses).
6. O sistema calcula imediatamente a depreciação acumulada e o valor residual para a data corrente.
7. A tela de detalhe é exibida, com aviso de que o ativo ainda não possui responsável (pendência de compliance).
8. Marcos clica em **Atribuir Responsável** e segue para a jornada 8.3.

**Resultado:** ativo inventariado, depreciando, e sinalizado como pendente até a atribuição de responsável.

---

### 8.2 Cadastro de Software

**Ator:** Marcos · **Gatilho:** renovação anual de um pacote de licenças

1. Marcos acessa **Licenças → Nova Licença**.
2. Informa o software, o fornecedor, a quantidade contratada (50), a data de aquisição, a data de expiração e o valor total.
3. O sistema valida que a data de expiração é posterior à data de aquisição.
4. Ao salvar, a quantidade em uso inicia em zero e o status de conformidade é **Conforme**.
5. Marcos vincula as instalações existentes, incrementando a quantidade em uso.
6. Ao atingir 50 de 50, o sistema exibe aviso de saturação. Na tentativa de vincular a 51ª, o sistema bloqueia e registra um alerta de excedente.
7. A licença passa a ser monitorada: quando faltarem 30 dias para a expiração, entra no painel de alertas.

**Resultado:** licença sob controle quantitativo e temporal, com bloqueio preventivo de uso irregular.

---

### 8.3 Transferência de Responsável

**Ator:** Juliana (Analista de Infraestrutura) · **Gatilho:** colaborador muda de setor

1. Juliana busca o ativo pelo número de série ou pelo nome do responsável atual.
2. Na tela de detalhe, aciona **Transferir**.
3. Informa o novo responsável, o setor de destino, a data da transferência e, opcionalmente, uma observação.
4. O sistema valida que o ativo não está **Baixado** — se estiver, a operação é recusada.
5. Ao confirmar, o sistema encerra o vínculo anterior gravando a data de término e cria um novo vínculo com data de início.
6. O registro anterior permanece no histórico, sem possibilidade de edição ou exclusão.
7. A linha do tempo do ativo é atualizada e exibida em ordem cronológica.

**Resultado:** posse transferida com trilha de auditoria completa e sem sobreposição de vínculos.

---

### 8.4 Registro de Baixa

**Ator:** Marcos · **Gatilho:** notebook com placa-mãe queimada, sem viabilidade de reparo

1. Marcos localiza o ativo e aciona **Registrar Baixa**.
2. Informa o motivo (**Defeito**), a data da baixa, a destinação (**Reciclagem certificada**) e uma justificativa textual.
3. O sistema valida que a data da baixa não é futura e que o ativo não está já baixado.
4. Ao confirmar, o status passa a **Baixado**, o vínculo de responsável ativo é encerrado e o cálculo de depreciação é congelado na data da baixa.
5. O ativo deixa de aparecer nos relatórios de inventário ativo, mas continua acessível pelo filtro **Baixados** e pelo histórico.
6. O evento é gravado na trilha de auditoria com autor e carimbo de tempo.

**Resultado:** ativo removido da operação, com histórico preservado e destinação ambiental documentada.

---

### 8.5 Gestão de Licenças

**Ator:** Diego (Auditor) · **Gatilho:** preparação para auditoria de licenciamento

1. Diego autentica-se com perfil **AUDITOR** (somente leitura).
2. Acessa **Compliance → Conformidade de Licenças**.
3. O painel apresenta, por licença: contratado, em uso, saldo, data de expiração e status de conformidade.
4. Diego filtra por **Não conforme** e obtém duas licenças: uma vencida há 12 dias e uma com uso de 52 sobre 50 contratados.
5. Abre o detalhe da licença excedente e visualiza os ativos vinculados, com data de vinculação.
6. Exporta o relatório em CSV. O arquivo carrega data e hora de geração e o identificador do usuário que o gerou.
7. Diego tenta editar um registro histórico e recebe negativa de permissão — comportamento esperado e registrado.

**Resultado:** evidência de conformidade gerada sem intervenção da área auditada.

---

## 9. User Stories

### Épico E1 — Inventário de Ativos

| ID | História | Prioridade |
|---|---|---|
| US-001 | Como **Administrador de TI**, quero cadastrar um ativo informando nome, tipo, categoria, identificador, data de aquisição, valor e fornecedor, para que o item passe a constar no inventário oficial. | Must |
| US-002 | Como **Administrador de TI**, quero que o sistema recuse números de série duplicados, para que eu não crie registros redundantes do mesmo equipamento. | Must |
| US-003 | Como **Analista de Infraestrutura**, quero buscar um ativo por nome, número de série ou responsável, para que eu o localize em segundos durante o atendimento. | Must |
| US-004 | Como **Administrador de TI**, quero alterar o status de um ativo para *Em manutenção*, para que o relatório de inventário reflita a indisponibilidade temporária. | Must |
| US-005 | Como **Administrador de TI**, quero cadastrar categorias com vida útil própria, para que a depreciação respeite a natureza de cada tipo de equipamento. | Must |
| US-006 | Como **Administrador de TI**, quero cadastrar fornecedores, para que eu possa consolidar o parque por origem de aquisição. | Should |

### Épico E2 — Responsabilidade e Histórico

| ID | História | Prioridade |
|---|---|---|
| US-007 | Como **Analista de Infraestrutura**, quero atribuir um responsável a um ativo informando a data, para que a posse fique formalmente registrada. | Must |
| US-008 | Como **Analista de Infraestrutura**, quero transferir um ativo para outro responsável, para que a mudança de posse seja registrada sem apagar o histórico. | Must |
| US-009 | Como **Auditor**, quero visualizar a linha do tempo completa de responsáveis de um ativo, para que eu identifique quem o detinha em qualquer data passada. | Must |
| US-010 | Como **Administrador de TI**, quero associar um ativo a um setor além de a uma pessoa, para que ativos compartilhados tenham responsabilidade definida. | Should |
| US-011 | Como **Auditor**, quero que registros históricos não possam ser editados nem excluídos, para que o histórico sirva como evidência de auditoria. | Must |

### Épico E3 — Depreciação e Valor Patrimonial

| ID | História | Prioridade |
|---|---|---|
| US-012 | Como **Gestora de Patrimônio**, quero que o sistema calcule a depreciação linear automaticamente, para que eu não precise recalcular em planilha. | Must |
| US-013 | Como **Gestora de Patrimônio**, quero consultar valor de compra, depreciação acumulada, percentual depreciado e valor residual de cada ativo, para que eu concilie com o registro contábil. | Must |
| US-014 | Como **Gestora de Patrimônio**, quero que o valor residual nunca seja negativo, para que o relatório não apresente inconsistência contábil. | Must |
| US-015 | Como **Gestora de Patrimônio**, quero exportar o relatório de depreciação em CSV, para que eu o anexe ao fechamento mensal. | Should |
| US-016 | Como **Administrador de TI**, quero visualizar os ativos totalmente depreciados, para que eu planeje a substituição do parque. | Should |

### Épico E4 — Licenças de Software

| ID | História | Prioridade |
|---|---|---|
| US-017 | Como **Administrador de TI**, quero registrar uma licença com quantidade contratada e data de expiração, para que o uso passe a ser controlado. | Must |
| US-018 | Como **Administrador de TI**, quero vincular instalações a uma licença, para que a quantidade em uso reflita a realidade. | Must |
| US-019 | Como **Administrador de TI**, quero que o sistema bloqueie a vinculação que excederia o contratado, para que a organização não opere em desconformidade. | Must |
| US-020 | Como **Administrador de TI**, quero ser alertado com 30 dias de antecedência sobre licenças a vencer, para que a renovação seja negociada com tempo. | Must |
| US-021 | Como **Auditor**, quero um relatório de conformidade de licenças com data de geração, para que eu o apresente em auditoria. | Must |

### Épico E5 — Baixa e Descarte

| ID | História | Prioridade |
|---|---|---|
| US-022 | Como **Administrador de TI**, quero registrar a baixa de um ativo informando motivo e data, para que ele saia do inventário ativo. | Must |
| US-023 | Como **Administrador de TI**, quero registrar a destinação do ativo baixado, para que a política de TI Verde tenha evidência documental. | Should |
| US-024 | Como **Auditor**, quero consultar ativos baixados com motivo e justificativa, para que eu valide a regularidade das baixas. | Must |
| US-025 | Como **Gestora de Patrimônio**, quero que a depreciação seja congelada na data da baixa, para que o valor residual do fechamento esteja correto. | Must |

### Épico E6 — Relatórios e Compliance

| ID | História | Prioridade |
|---|---|---|
| US-026 | Como **Gestora de Patrimônio**, quero filtrar o inventário por status, categoria, responsável, fornecedor e faixa de valor depreciado, para que eu extraia o recorte necessário a cada análise. | Must |
| US-027 | Como **Administrador de TI**, quero listar ativos próximos do fim da vida útil, para que eu antecipe o orçamento de reposição. | Should |
| US-028 | Como **Auditor**, quero um painel único com todas as não conformidades, para que eu priorize a investigação. | Must |
| US-029 | Como **Administrador de TI**, quero ser alertado sobre ativos sem responsável definido, para que nenhum equipamento fique órfão. | Must |
| US-030 | Como **Direção**, quero um painel com total de ativos, valor patrimonial e valor depreciado, para que eu acompanhe o investimento em TI. | Should |

### Épico E7 — Governança, Dados e Decisão *(extensão da baseline)*

| ID | História | Prioridade |
|---|---|---|
| US-031 | Como **Administrador de TI**, quero importar o inventário existente em CSV ou XLSX, para que eu não redigite centenas de registros. | Must |
| US-032 | Como **Administrador de TI**, quero receber um relatório de erros da importação separando registros válidos e inválidos, para que eu corrija apenas o que falhou. | Must |
| US-033 | Como **Direção**, quero comparar cenários de renovar, substituir ou migrar para assinatura com TCO de cinco anos, para que a decisão de investimento seja fundamentada. | Should |
| US-034 | Como **Gestora de Patrimônio**, quero avaliar fornecedores por scorecard ponderado, para que a recontratação considere desempenho e não apenas preço. | Should |
| US-035 | Como **Auditor**, quero registrar riscos com probabilidade e impacto, para que a exposição do parque seja tratada formalmente. | Should |
| US-036 | Como **Direção**, quero que toda recomendação registrada esteja vinculada a pelo menos uma evidência, para que nenhuma decisão se apoie em opinião. | Must |
| US-037 | Como **Administrador de TI**, quero endpoints de health check e métricas, para que a operação do sistema seja monitorável. | Must |

### Épico E8 — Segurança e Acesso

| ID | História | Prioridade |
|---|---|---|
| US-038 | Como **usuário**, quero autenticar-me com credenciais e receber um token, para que meu acesso seja controlado. | Must |
| US-039 | Como **Administrador de TI**, quero que cada perfil tenha permissões distintas, para que auditores não alterem dados. | Must |
| US-040 | Como **Auditor**, quero que toda alteração registre autor e carimbo de tempo, para que a responsabilidade seja rastreável. | Must |


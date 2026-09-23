# PRD — ITAM: Gestão de Ativos de TI

| Campo | Valor |
|---|---|
| **Produto** | ITAM — Gestão de Ativos de TI |
| **Versão do documento** | 1.0 |
| **Tipo** | Product Requirements Document (PRD) |
| **Disciplina** | Governança de TI — Sistemas de Informação — UNINASSAU Olinda |
| **Baseline técnica** | Guia de Orquestração para 3 Projetos de MVPs (dual Python + Java) |
| **Status** | Aprovado para especificação técnica (SDD) |
| **Idioma** | Português (Brasil) |

---

## 1. Executive Summary

### Visão do produto

O **ITAM** é um sistema web de apoio à governança do parque tecnológico de uma organização. Ele centraliza o registro de ativos de hardware e software, mantém a cadeia de responsabilidade sobre cada item, calcula a depreciação patrimonial e sinaliza desvios de conformidade antes que virem prejuízo financeiro ou risco legal.

O produto **não** é um sistema de descoberta automática de inventário nem um ERP patrimonial. É uma **camada de orquestração, análise e apoio à decisão** sobre os dados de ativos que a organização já possui, alinhada ao escopo definido na baseline da disciplina.

### Problema que resolve

Organizações de médio porte administram centenas de ativos de TI em planilhas desconexas. O resultado recorrente: equipamentos sem responsável identificado, licenças de software renovadas por inércia ou usadas acima do contratado, valor patrimonial desatualizado no balanço e ausência de histórico auditável de quem usou o quê e quando.

### Objetivo do MVP

Entregar um sistema funcional capaz de:

1. Registrar e consultar o inventário completo de ativos de TI;
2. Manter o histórico imutável de responsáveis por ativo;
3. Calcular automaticamente a depreciação linear e o valor residual;
4. Controlar licenças de software contra o quantitativo contratado e a data de expiração;
5. Registrar baixas com motivo, data e destinação;
6. Produzir relatórios de inventário filtráveis;
7. Sinalizar ativos e licenças em desconformidade.

### Benefícios

| Área | Benefício esperado |
|---|---|
| Equipe de TI | Localiza o responsável por qualquer ativo em segundos, sem consultar planilhas paralelas |
| Patrimônio / Contabilidade | Valor residual do parque calculado automaticamente, pronto para conciliação contábil |
| Compliance / Auditoria | Trilha de auditoria imutável de transferências e baixas, com evidência para auditorias de licenciamento |
| Direção | Visão consolidada do valor investido, do valor depreciado e da exposição a riscos de licenciamento |
| Sustentabilidade | Registro da destinação dos equipamentos baixados, sustentando a política de TI Verde |

---

## 2. Product Vision

### Visão de longo prazo

> Ser a fonte única de verdade sobre o parque de TI da organização — do momento da aquisição ao descarte certificado — de modo que nenhuma decisão de compra, renovação ou substituição seja tomada sem dado verificável.

### Como o produto melhora a governança de ativos

A gestão de ativos é um processo formalmente descrito nos principais frameworks de governança, e o ITAM materializa esses processos em software:

- **ISO/IEC 19770-1** define o sistema de gestão de ativos de TI. O ITAM implementa o núcleo desse sistema: identificação, propriedade, ciclo de vida e conformidade.
- **COBIT 2019 — BAI09 (Gerenciar Ativos)** exige que ativos sejam contabilizados, otimizados e protegidos ao longo do ciclo de vida. O FR-001, o FR-003 e o FR-005 endereçam diretamente esse objetivo.
- **ITIL 4 — prática de Gestão de Ativos de TI** exige rastreabilidade de propriedade e de valor. O FR-002 e o FR-006 sustentam essa prática.
- **ISO/IEC 38500** estabelece os princípios de Responsabilidade, Aquisição e Conformidade. O modelo de responsáveis, o registro de fornecedor e os alertas de compliance operacionalizam os três.

### Impacto esperado em compliance e gestão financeira

| Dimensão | Situação atual típica | Situação com o ITAM |
|---|---|---|
| Auditoria de licenciamento | Levantamento manual, dias de trabalho, risco de multa | Relatório de conformidade gerado sob demanda |
| Fechamento contábil | Depreciação recalculada em planilha, sujeita a erro | Valor residual calculado por regra configurável |
| Renovação de contratos | Renovação automática sem análise de uso real | Alerta antecipado com quantidade contratada x em uso |
| Responsabilidade patrimonial | "Quem está com o notebook?" sem resposta | Responsável atual e histórico completo por ativo |

---

## 3. Problem Statement

### P1 — Ativos sem controle

O inventário vive em planilhas mantidas por pessoas diferentes, com colunas divergentes e versões conflitantes. Não existe um número total confiável de ativos, nem certeza de que um equipamento listado ainda existe fisicamente.

### P2 — Licenças vencidas ou em excesso

Licenças de software são contratadas em lote e renovadas sem verificação do uso real. A organização paga por licenças ociosas ou, pior, opera acima do quantitativo contratado — expondo-se a autuação em auditoria do fabricante.

### P3 — Dificuldade para localizar responsáveis

Quando um equipamento precisa ser recolhido, atualizado ou investigado, não há registro confiável de quem o recebeu. Em desligamentos de colaboradores, ativos simplesmente desaparecem do controle.

### P4 — Falta de histórico

Transferências entre setores acontecem por e-mail ou verbalmente. Não existe trilha de auditoria: não se sabe quem teve a posse de um ativo em determinada data, o que inviabiliza apuração de responsabilidade por danos ou extravios.

### P5 — Ausência de cálculo de depreciação

O valor patrimonial registrado é o valor de compra, congelado no tempo. A contabilidade recalcula manualmente em planilha, sem vínculo com o inventário operacional, gerando divergência entre o controle físico e o contábil.

### P6 — Descarte sem rastreabilidade

Equipamentos baixados saem do controle sem registro de destinação. Não há evidência para a política de TI Verde nem para exigências de descarte de resíduos eletroeletrônicos.

---

## 4. Objetivos do Produto

### 4.1 Objetivos Principais

| ID | Objetivo |
|---|---|
| OBJ-01 | Centralizar o cadastro de 100% dos ativos de TI em uma base única e consultável |
| OBJ-02 | Garantir que todo ativo em operação tenha um responsável identificado e um histórico completo de posse |
| OBJ-03 | Calcular automaticamente a depreciação e o valor residual de cada ativo sem intervenção manual |
| OBJ-04 | Impedir que a organização opere acima do quantitativo de licenças contratado |
| OBJ-05 | Preservar histórico permanente e imutável de transferências e baixas |
| OBJ-06 | Disponibilizar relatórios de inventário filtráveis para uso em auditoria e planejamento orçamentário |

### 4.2 Objetivos Secundários

| ID | Objetivo |
|---|---|
| OBJ-07 | Antecipar decisões de renovação e substituição por meio de alertas configuráveis |
| OBJ-08 | Registrar a destinação ambiental dos ativos descartados (TI Verde) |
| OBJ-09 | Fornecer indicadores consolidados em painel para apoio à decisão executiva |
| OBJ-10 | Oferecer trilha de evidências que sustente recomendações de investimento |

### 4.3 Métricas de Sucesso

| ID | Métrica | Fórmula | Meta do MVP |
|---|---|---|---|
| KPI-01 | Cobertura de inventário | ativos cadastrados / ativos estimados no parque | ≥ 95% |
| KPI-02 | Ativos com responsável definido | ativos ativos com responsável / total de ativos ativos | ≥ 98% |
| KPI-03 | Conformidade de licenças | licenças com uso ≤ contratado e não vencidas / total de licenças | 100% |
| KPI-04 | Tempo médio para localizar um ativo | tempo entre a consulta e a identificação do responsável | ≤ 30 segundos |
| KPI-05 | Acurácia da depreciação | divergência entre valor residual do sistema e o contábil | ≤ 1% |
| KPI-06 | Ativos sem movimentação registrada | ativos sem evento nos últimos 12 meses / total | ≤ 10% |
| KPI-07 | Idade média do parque | média da diferença entre hoje e a data de aquisição | monitorada, sem meta no MVP |
| KPI-08 | Taxa de baixas com destinação registrada | baixas com destinação / total de baixas | 100% |

---

## 5. Stakeholders

| Stakeholder | Papel no sistema | Responsabilidades | Interesses |
|---|---|---|---|
| **Administrador de TI** | Usuário-chave, perfil `ADMIN` | Cadastrar ativos, configurar categorias e vida útil, gerenciar usuários e parâmetros do sistema | Controle total do parque; reduzir tempo gasto em levantamentos manuais |
| **Analista de Infraestrutura** | Operador, perfil `OPERADOR` | Registrar transferências, atualizar status, lançar manutenções e baixas | Registro rápido e sem burocracia; evitar retrabalho |
| **Gestor de Patrimônio** | Consulta e conciliação, perfil `GESTOR` | Conciliar o inventário de TI com o registro patrimonial; validar valores depreciados | Valor residual correto e conciliável com a contabilidade |
| **Colaborador responsável** | Sujeito do registro, sem acesso direto no MVP | Receber e devolver ativos mediante registro formal | Clareza sobre o que está sob sua responsabilidade |
| **Auditor / Compliance** | Leitura e evidência, perfil `AUDITOR` | Verificar conformidade de licenças e integridade do histórico | Trilha de auditoria íntegra e relatórios exportáveis |
| **Direção / Patrocinador** | Consumidor de indicadores | Aprovar orçamento de renovação do parque | Visão de valor investido, depreciado e exposição a risco |
| **Fornecedor** | Entidade referenciada, sem acesso | — | — |

---

## 6. Personas

### Persona 1 — Marcos Tavares

| Atributo | Descrição |
|---|---|
| **Cargo** | Administrador de TI, 38 anos, 9 anos na organização |
| **Contexto** | Responde sozinho por cerca de 400 ativos distribuídos em três andares e dois anexos |
| **Objetivos** | Ter um número confiável de ativos; saber onde está cada equipamento; parar de responder "deixa eu verificar" |
| **Dores** | Mantém quatro planilhas que nunca batem; perde meio dia por mês consolidando dados para o patrimônio; descobre licenças vencidas só quando o software para de funcionar |
| **Necessidades** | Cadastro rápido com poucos campos obrigatórios; busca por número de série; alerta automático de vencimento |
| **Citação** | "Eu não preciso de um sistema bonito. Preciso de um lugar onde o dado esteja certo." |

### Persona 2 — Juliana Rego

| Atributo | Descrição |
|---|---|
| **Cargo** | Analista de Infraestrutura, 27 anos, 2 anos na organização |
| **Contexto** | Executa o atendimento de campo: entrega equipamentos, recolhe em desligamentos, leva itens para manutenção |
| **Objetivos** | Registrar uma transferência em menos de um minuto, direto do celular, no momento da entrega |
| **Dores** | Anota no papel e depois esquece de lançar; quando lança, já não lembra a data exata; formulários longos a desestimulam |
| **Necessidades** | Interface responsiva; formulário de transferência com no máximo quatro campos; busca por nome do colaborador |
| **Citação** | "Se eu não registrar na hora, não registro mais." |

### Persona 3 — Rosângela Lima

| Atributo | Descrição |
|---|---|
| **Cargo** | Gestora de Patrimônio, 45 anos, ligada à área financeira |
| **Contexto** | Responde pelo registro patrimonial de toda a organização, não só de TI |
| **Objetivos** | Fechar o mês com o valor residual de TI conciliado; justificar baixas para a auditoria externa |
| **Dores** | Recebe planilhas de TI em formatos diferentes a cada mês; recalcula depreciação manualmente; não tem documento que comprove o motivo de uma baixa |
| **Necessidades** | Relatório exportável com valor de compra, depreciação acumulada e valor residual por ativo; motivo e data da baixa registrados |
| **Citação** | "O que eu preciso não é o inventário de vocês. É o inventário de vocês fechando com o meu." |

### Persona 4 — Diego Amaral

| Atributo | Descrição |
|---|---|
| **Cargo** | Auditor Interno / Compliance, 34 anos |
| **Contexto** | Conduz auditorias internas semestrais e prepara a organização para auditorias de licenciamento de fabricantes |
| **Objetivos** | Comprovar que o uso de software está dentro do contratado; verificar que nenhum registro histórico foi alterado |
| **Dores** | Depende de levantamentos ad hoc feitos pela própria área auditada; não tem como saber se uma planilha foi editada |
| **Necessidades** | Acesso somente leitura; relatório de conformidade com data de geração; histórico imutável |
| **Citação** | "Se o dado pode ser apagado, ele não é evidência." |

### Persona 5 — Carlos Menezes

| Atributo | Descrição |
|---|---|
| **Cargo** | Analista Comercial, 31 anos — colaborador responsável por ativos |
| **Contexto** | Usa notebook, monitor, headset e celular corporativo; já trocou de setor duas vezes |
| **Objetivos** | Saber exatamente o que está sob sua responsabilidade; não ser cobrado por um equipamento que devolveu |
| **Dores** | Assinou um termo de responsabilidade há três anos e não sabe se ainda vale; devolveu um monitor sem comprovante |
| **Necessidades** | Que a devolução gere registro com data; que o termo reflita a posse atual |
| **Citação** | "Eu devolvi. Só não tenho como provar." |

---

## 7. Escopo do MVP

### 7.1 Incluído no MVP

| ID | Item | Requisito relacionado |
|---|---|---|
| IN-01 | Cadastro, edição e consulta de ativos de hardware e software | FR-001 |
| IN-02 | Cadastro de categorias com vida útil configurável | FR-001, FR-003 |
| IN-03 | Cadastro de fornecedores | FR-001 |
| IN-04 | Cadastro de responsáveis (usuários e setores) | FR-002 |
| IN-05 | Atribuição e transferência de responsável com histórico | FR-002 |
| IN-06 | Cálculo automático de depreciação linear e valor residual | FR-003 |
| IN-07 | Cadastro de licenças com quantitativo contratado e em uso | FR-004 |
| IN-08 | Alertas de excedente e de expiração de licença | FR-004, FR-007 |
| IN-09 | Registro de baixa com motivo, data e destinação | FR-005 |
| IN-10 | Relatório de inventário com filtros combináveis | FR-006 |
| IN-11 | Painel de alertas de compliance | FR-007 |
| IN-12 | Importação de inventário via CSV/XLSX | FR-008 |
| IN-13 | Indicadores de ITAM e dashboard | FR-009, FR-014 |
| IN-14 | Autenticação JWT e perfis de acesso (RBAC) | NFR-SEG-01, NFR-SEG-02 |
| IN-15 | Trilha de auditoria imutável | NFR-AUD-01 |
| IN-16 | API REST documentada via OpenAPI | NFR-MAN-02 |
| IN-17 | Health check e métricas no padrão Prometheus | NFR-OBS-01, NFR-OBS-02 |

### 7.2 Fora do Escopo do MVP

| ID | Item excluído | Justificativa |
|---|---|---|
| OUT-01 | Integração com Active Directory / LDAP | Dependência de infraestrutura externa; usuários são cadastrados localmente no MVP |
| OUT-02 | Descoberta automática de inventário via agente | Exige desenvolvimento de cliente instalável, fora do escopo de um MVP de governança |
| OUT-03 | Integração com Microsoft SCCM / Intune | Dependência de licenciamento e ambiente corporativo indisponível |
| OUT-04 | Gestão financeira completa (contas a pagar, centro de custo, rateio) | Domínio de ERP; o MVP entrega apenas depreciação e valor residual |
| OUT-05 | Módulo de compras, cotações e contratos | Processo upstream; o MVP parte do ativo já adquirido |
| OUT-06 | Service Desk / abertura de chamados | Coberto pelo Projeto 1 da baseline da disciplina |
| OUT-07 | Leitura de QR Code / código de barras | Previsto para a V2 |
| OUT-08 | Upload de nota fiscal e anexos | Previsto para a V2 |
| OUT-09 | Gestão de garantia e contratos de manutenção | Previsto para a V2 |
| OUT-10 | Múltiplas moedas e múltiplas filiais | Assume-se moeda única (BRL) e organização única |
| OUT-11 | Métodos de depreciação além do linear | O linear atende à IN RFB 1.700; demais métodos na V2 |
| OUT-12 | Aplicativo móvel nativo | A interface web responsiva atende à Persona 2 |
| OUT-13 | Assinatura digital de termo de responsabilidade | Previsto para a V2 |

---

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

---

## 10. Requisitos Funcionais

### 10.1 Visão consolidada

| ID | Requisito | Prioridade | Épico | Depende de |
|---|---|---|---|---|
| FR-001 | Cadastro de Ativos | Must | E1 | — |
| FR-002 | Vinculação de Responsável | Must | E2 | FR-001 |
| FR-003 | Cálculo de Depreciação | Must | E3 | FR-001 |
| FR-004 | Controle de Licenças de Software | Must | E4 | FR-001 |
| FR-005 | Baixa/Descarte de Ativo | Must | E5 | FR-001, FR-002 |
| FR-006 | Relatório de Inventário | Must | E6 | FR-001, FR-003 |
| FR-007 | Alerta de Compliance | Must | E6 | FR-002, FR-004, FR-005 |
| FR-008 | Importação de Inventário | Must | E7 | FR-001 |
| FR-009 | Indicadores de ITAM | Must | E7 | FR-001 a FR-005 |
| FR-010 | Comparação de Cenários e TCO | Should | E7 | FR-003, FR-009 |
| FR-011 | Scorecard de Fornecedores | Should | E7 | FR-001 |
| FR-012 | Registro de Riscos | Should | E7 | — |
| FR-013 | Recomendação Rastreável | Must | E7 | FR-009, FR-012 |
| FR-014 | Dashboard e Observabilidade | Must | E7 | FR-009 |
| FR-015 | Autenticação e Controle de Acesso | Must | E8 | — |

> **Nota de escopo.** Os requisitos **FR-001 a FR-007** constituem o núcleo funcional definido originalmente. Os requisitos **FR-008 a FR-015** são a extensão exigida pela baseline da disciplina (ingestão de dataset, indicadores, decisão rastreável, observabilidade e segurança) e cobrem as dimensões da rubrica de avaliação que o núcleo sozinho não alcança.

---

### FR-001 — Cadastro de Ativos

**Descrição.** O sistema deve permitir registrar, consultar, editar e listar ativos de TI.

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `nome` | Texto (3–120) | Sim | — |
| `tipo` | Enum | Sim | `HARDWARE` \| `SOFTWARE` |
| `categoria` | Referência | Sim | Deve existir em Categoria |
| `numero_serie` | Texto (até 80) | Condicional | Obrigatório e único quando `tipo = HARDWARE` |
| `chave_licenca` | Texto (até 200) | Condicional | Obrigatório quando `tipo = SOFTWARE` |
| `data_aquisicao` | Data | Sim | Não pode ser futura |
| `valor_compra` | Decimal(12,2) | Sim | > 0 |
| `fornecedor` | Referência | Sim | Deve existir em Fornecedor |
| `status` | Enum | Sim | `ATIVO` \| `EM_MANUTENCAO` \| `BAIXADO`; padrão `ATIVO` |
| `vida_util_meses` | Inteiro | Não | Herdada da categoria se omitida; sobrescrevível |
| `localizacao` | Texto (até 120) | Não | — |
| `observacoes` | Texto (até 500) | Não | — |

**Comportamentos:**
- Na criação, o status assume `ATIVO` e a vida útil é herdada da categoria.
- O número de série é único em todo o sistema, incluindo ativos baixados.
- A transição para `BAIXADO` ocorre exclusivamente via FR-005, nunca por edição direta do campo.
- Listagem paginada, ordenável e filtrável por todos os campos indexados.

---

### FR-002 — Vinculação de Responsável

**Descrição.** O sistema deve associar cada ativo a um responsável (usuário e/ou setor) e manter o histórico completo de transferências.

**Campos do vínculo:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `ativo` | Referência | Sim | Status ≠ `BAIXADO` |
| `responsavel` | Referência | Sim | Usuário ativo |
| `setor` | Referência | Sim | Setor ativo |
| `data_inicio` | Data | Sim | Não futura; ≥ `data_aquisicao` do ativo |
| `data_fim` | Data | Não | Preenchida automaticamente na transferência |
| `motivo` | Texto (até 200) | Não | — |
| `registrado_por` | Referência | Sim | Preenchido pelo sistema |

**Comportamentos:**
- Um ativo possui no máximo um vínculo aberto (`data_fim` nula) por vez.
- A transferência encerra o vínculo aberto com `data_fim = data_inicio` do novo vínculo e cria o novo em uma única transação.
- Vínculos encerrados são imutáveis: não admitem edição nem exclusão.
- A consulta de histórico retorna todos os vínculos em ordem cronológica decrescente.
- Ativos sem vínculo aberto são sinalizados pelo FR-007.

---

### FR-003 — Cálculo de Depreciação

**Descrição.** O sistema deve calcular a depreciação pelo método linear, com vida útil configurável por categoria.

**Fórmulas:**

```
meses_decorridos      = meses_entre(data_aquisicao, data_referencia)
meses_efetivos        = min(meses_decorridos, vida_util_meses)
depreciacao_mensal    = valor_compra / vida_util_meses
depreciacao_acumulada = depreciacao_mensal × meses_efetivos
valor_residual        = max(valor_compra − depreciacao_acumulada, 0)
percentual_depreciado = (depreciacao_acumulada / valor_compra) × 100
```

**Regras:**
- `data_referencia` é a data corrente para ativos em operação e a `data_baixa` para ativos baixados.
- Vida útil padrão por categoria (referência: IN RFB nº 1.700/2017, anexo III):

| Categoria | Vida útil (meses) | Taxa anual |
|---|---|---|
| Notebook / Desktop | 60 | 20% |
| Servidor | 60 | 20% |
| Monitor | 60 | 20% |
| Switch / Roteador | 60 | 20% |
| Impressora | 48 | 25% |
| Smartphone / Tablet | 36 | 33,3% |
| Nobreak | 60 | 20% |
| Software (licença perpétua) | 60 | 20% |

- O valor residual nunca é negativo; ao atingir a vida útil, estabiliza em zero.
- O cálculo é determinístico e recalculado sob demanda, não persistido como valor congelado — exceto na baixa.
- Arredondamento em duas casas decimais, modo *half-up*.

---

### FR-004 — Controle de Licenças de Software

**Descrição.** O sistema deve registrar licenças de software e monitorar sua conformidade quantitativa e temporal.

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `software` | Texto (3–120) | Sim | — |
| `fornecedor` | Referência | Sim | — |
| `chave_licenca` | Texto (até 200) | Sim | — |
| `quantidade_contratada` | Inteiro | Sim | ≥ 1 |
| `quantidade_em_uso` | Inteiro | Sim | ≥ 0; derivado dos vínculos |
| `data_aquisicao` | Data | Sim | Não futura |
| `data_expiracao` | Data | Sim | > `data_aquisicao` |
| `valor_total` | Decimal(12,2) | Sim | > 0 |
| `tipo_licenciamento` | Enum | Sim | `PERPETUA` \| `SUBSCRICAO` \| `OEM` |

**Alertas gerados:**

| Condição | Severidade | Mensagem |
|---|---|---|
| `quantidade_em_uso > quantidade_contratada` | **Crítico** | Uso acima do contratado — risco de autuação |
| `data_expiracao < hoje` | **Crítico** | Licença vencida |
| `data_expiracao − hoje ≤ 30 dias` | **Alto** | Licença próxima do vencimento |
| `quantidade_em_uso = quantidade_contratada` | **Médio** | Licença saturada — sem saldo disponível |
| `quantidade_em_uso ≤ 50% do contratado` após 6 meses | **Baixo** | Subutilização — oportunidade de redução |

**Comportamentos:**
- A vinculação que faria `quantidade_em_uso` exceder o contratado é **bloqueada** e registrada na auditoria.
- A janela de alerta antecipado (30 dias) é parâmetro configurável.
- Licenças vencidas permanecem no sistema, sinalizadas, até renovação ou baixa.

---

### FR-005 — Baixa/Descarte de Ativo

**Descrição.** O sistema deve registrar a baixa de um ativo, retirando-o do inventário operacional e preservando o histórico permanentemente.

**Campos:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `ativo` | Referência | Sim | Status ≠ `BAIXADO` |
| `motivo` | Enum | Sim | `OBSOLESCENCIA` \| `DEFEITO` \| `FURTO_ROUBO` \| `FIM_VIDA_UTIL` \| `OUTRO` |
| `justificativa` | Texto (10–500) | Sim quando `motivo = OUTRO` | — |
| `data_baixa` | Data | Sim | Não futura; ≥ `data_aquisicao` |
| `destinacao` | Enum | Sim | `RECICLAGEM_CERTIFICADA` \| `DOACAO` \| `DEVOLUCAO_FORNECEDOR` \| `VENDA` \| `DESCARTE` |
| `valor_residual_baixa` | Decimal(12,2) | Sim | Calculado pelo sistema na data da baixa |
| `registrado_por` | Referência | Sim | Preenchido pelo sistema |

**Comportamentos:**
- Ao registrar a baixa: status → `BAIXADO`, vínculo de responsável aberto é encerrado, depreciação é congelada e persistida.
- O ativo desaparece do inventário ativo, mas permanece acessível por filtro explícito e pelo histórico.
- A baixa é irreversível no MVP; estorno exige nova versão do produto.
- O campo `destinacao` sustenta a evidência de TI Verde e o relatório de descarte.

---

### FR-006 — Relatório de Inventário

**Descrição.** O sistema deve gerar relatórios do inventário com filtros combináveis e exportação.

**Filtros disponíveis:**

| Filtro | Tipo | Observação |
|---|---|---|
| Status | Múltipla escolha | Ativo, Em manutenção, Baixado |
| Tipo | Múltipla escolha | Hardware, Software |
| Categoria | Múltipla escolha | — |
| Responsável | Busca | Usuário ou setor |
| Fornecedor | Múltipla escolha | — |
| Faixa de valor depreciado | Intervalo numérico | Valor mínimo e máximo |
| Percentual depreciado | Intervalo | 0–100% |
| Período de aquisição | Intervalo de datas | — |
| Próximos do fim da vida útil | Booleano | ≥ 80% da vida útil consumida |

**Saída do relatório:** identificador, nome, tipo, categoria, número de série ou chave, responsável atual, setor, status, data de aquisição, valor de compra, depreciação acumulada, percentual depreciado, valor residual, fornecedor.

**Comportamentos:**
- Filtros combináveis por conjunção (AND).
- Exportação em CSV e XLSX, com cabeçalho contendo data/hora de geração e usuário solicitante.
- Totalizadores no rodapé: contagem de ativos, soma de valor de compra, soma de valor residual.
- Paginação obrigatória na visualização; exportação sem limite de linhas.

---

### FR-007 — Alerta de Compliance

**Descrição.** O sistema deve manter um painel consolidado de não conformidades, avaliadas em tempo de consulta.

**Regras de sinalização:**

| ID | Condição | Severidade | Origem |
|---|---|---|---|
| CP-01 | Licença com `data_expiracao < hoje` | Crítico | FR-004 |
| CP-02 | Licença com `quantidade_em_uso > quantidade_contratada` | Crítico | FR-004 |
| CP-03 | Licença expirando em ≤ 30 dias | Alto | FR-004 |
| CP-04 | Ativo `ATIVO` sem vínculo de responsável aberto | Alto | FR-002 |
| CP-05 | Ativo totalmente depreciado ainda em operação | Médio | FR-003 |
| CP-06 | Ativo `EM_MANUTENCAO` há mais de 90 dias | Médio | FR-001 |
| CP-07 | Ativo baixado sem destinação registrada | Médio | FR-005 |
| CP-08 | Ativo sem movimentação registrada há mais de 12 meses | Baixo | FR-002 |
| CP-09 | Ativo com valor de compra ausente ou zerado | Baixo | FR-001 |

**Comportamentos:**
- O painel agrupa por severidade e permite navegar do alerta para o registro de origem.
- Cada alerta exibe a regra aplicada, tornando a sinalização explicável.
- O conjunto de alertas é exportável como relatório de conformidade datado.
- Alertas não são persistidos como registros próprios: são derivados do estado atual, o que garante que nunca fiquem obsoletos.

---

### FR-008 — Importação de Inventário *(extensão)*

**Descrição.** O sistema deve importar ativos em lote a partir de arquivos CSV ou XLSX.

**Comportamentos:**
- Validação dos cabeçalhos esperados antes de processar as linhas.
- Conversão e validação de datas, valores decimais e enumerados.
- Detecção de duplicidade por número de série, dentro do arquivo e contra a base.
- Separação entre registros válidos (importados) e inválidos (rejeitados).
- Criação de um **lote de importação** com identificador, data, usuário, total processado, total aceito e total rejeitado.
- Relatório de erros por linha, com número da linha, campo e motivo da rejeição, exportável.
- A importação é atômica por registro: um registro inválido não impede os demais.

---

### FR-009 — Indicadores de ITAM *(extensão)*

**Descrição.** O sistema deve calcular e expor indicadores agregados do parque.

| Indicador | Fórmula |
|---|---|
| Total de ativos por status | contagem agrupada |
| Distribuição hardware x software | contagem por tipo |
| Valor patrimonial bruto | soma de `valor_compra` dos ativos não baixados |
| Valor residual total | soma de `valor_residual` dos ativos não baixados |
| Percentual depreciado do parque | (1 − valor residual / valor bruto) × 100 |
| Cobertura de responsáveis | ativos com vínculo aberto / ativos ativos |
| Conformidade de licenças | licenças conformes / total de licenças |
| Idade média do parque | média de (hoje − `data_aquisicao`) em meses |
| Custo médio por ativo | valor patrimonial bruto / total de ativos |
| Ativos ociosos | ativos sem movimentação em 12 meses / total |
| Taxa de baixas no período | baixas no período / total de ativos no início do período |

**Comportamentos:**
- Todos os indicadores são filtráveis por categoria, setor, fornecedor e período.
- A resposta expõe a fórmula aplicada e o tamanho da amostra, permitindo verificação.

---

### FR-010 — Comparação de Cenários e TCO *(extensão)*

**Descrição.** O sistema deve comparar alternativas de tratamento do parque com horizonte de cinco anos.

**Cenários:** `MANTER` (prorrogar o uso), `RENOVAR` (substituir por equipamento equivalente), `MIGRAR_ASSINATURA` (substituir aquisição por serviço recorrente).

**Para cada cenário o sistema calcula:** CAPEX inicial, OPEX anual, TCO de 5 anos, custo por ativo/ano, economia relativa ao cenário baseline e score de risco agregado.

**Comportamento crítico:** o sistema **ordena** os cenários por custo e risco, mas **não seleciona** automaticamente a alternativa. A decisão permanece humana e deve ser registrada via FR-013.

---

### FR-011 — Scorecard de Fornecedores *(extensão)*

**Descrição.** O sistema deve avaliar fornecedores por critérios ponderados.

**Comportamentos:**
- Critérios configuráveis com pesos que devem totalizar exatamente 100%.
- Notas por critério no intervalo de 0 a 10; nota obrigatória para todos os critérios.
- Pontuação ponderada calculada e ranking produzido.
- Critérios sugeridos: preço, prazo de entrega, qualidade do suporte, taxa de defeitos no período, aderência contratual.
- Rejeição explícita de submissões com soma de pesos diferente de 100% ou com critérios sem nota.

---

### FR-012 — Registro de Riscos *(extensão)*

**Descrição.** O sistema deve manter um registro formal de riscos do parque de TI.

**Campos:** título, descrição, categoria (operacional, financeiro, legal, segurança, continuidade), probabilidade (1–5), impacto (1–5), `score = probabilidade × impacto`, resposta (aceitar, mitigar, transferir, evitar), responsável, status, gatilho, data de revisão.

**Classificação:** score 1–4 baixo, 5–9 médio, 10–14 alto, 15–25 crítico.

---

### FR-013 — Recomendação Rastreável *(extensão)*

**Descrição.** O sistema deve registrar recomendações de decisão, obrigatoriamente vinculadas a evidências.

**Regra estruturante:** uma recomendação **só pode ser gravada** se possuir ao menos uma evidência associada. Evidências admitidas: indicador calculado (FR-009), risco registrado (FR-012), ativo ou licença específicos, resultado de scorecard (FR-011), cenário comparado (FR-010) ou premissa financeira declarada.

**Campos:** título, contexto, recomendação, alternativas consideradas, evidências vinculadas (≥ 1), responsável pela decisão, data, status (proposta, aprovada, rejeitada, implementada).

Tentativas de gravar recomendação sem evidência retornam erro de validação com mensagem explícita.

---

### FR-014 — Dashboard e Observabilidade *(extensão)*

**Descrição.** O sistema deve expor painel gerencial e instrumentação técnica.

**Painel gerencial:** indicadores do FR-009 com visualização gráfica, painel de alertas do FR-007 e atalhos para os relatórios do FR-006.

**Instrumentação técnica:**
- `GET /health` — estado da aplicação e da conexão com o banco;
- `GET /metrics` — métricas no formato de exposição Prometheus;
- contador de requisições por endpoint e por código de retorno;
- histograma de duração das requisições;
- identificação do ambiente em execução na resposta do health check.

---

### FR-015 — Autenticação e Controle de Acesso *(extensão)*

**Descrição.** O sistema deve autenticar usuários e restringir operações por perfil.

| Perfil | Ativos | Responsáveis | Licenças | Baixas | Relatórios | Configuração |
|---|---|---|---|---|---|---|
| `ADMIN` | CRUD | CRUD | CRUD | Criar | Ler | CRUD |
| `OPERADOR` | Criar, Ler, Editar | Criar, Ler | Ler, Editar | Criar | Ler | — |
| `GESTOR` | Ler | Ler | Ler | Ler | Ler | — |
| `AUDITOR` | Ler | Ler | Ler | Ler | Ler | — |

Autenticação por JWT com expiração configurável. Toda operação de escrita registra autor e carimbo de tempo.

---

## 11. Regras de Negócio

### Cadastro e identificação

| ID | Regra |
|---|---|
| BR-001 | O número de série é único em todo o sistema, incluindo ativos baixados. |
| BR-002 | Ativo do tipo `HARDWARE` exige número de série; ativo do tipo `SOFTWARE` exige chave de licença. |
| BR-003 | A data de aquisição não pode ser posterior à data corrente. |
| BR-004 | O valor de compra deve ser estritamente maior que zero. |
| BR-005 | Todo ativo deve pertencer a exatamente uma categoria e a exatamente um fornecedor. |
| BR-006 | A vida útil do ativo é herdada da categoria no momento do cadastro e pode ser sobrescrita individualmente; alterações posteriores na categoria não afetam ativos já cadastrados. |

### Responsabilidade

| ID | Regra |
|---|---|
| BR-007 | Um ativo pode ter no máximo um vínculo de responsável aberto por vez. |
| BR-008 | A transferência encerra automaticamente o vínculo anterior, sem sobreposição de períodos. |
| BR-009 | Ativo com status `BAIXADO` não pode receber novo responsável. |
| BR-010 | A data de início de um vínculo não pode ser anterior à data de aquisição do ativo. |
| BR-011 | Vínculos encerrados são imutáveis: não admitem edição nem exclusão por nenhum perfil. |
| BR-012 | O registro de baixa encerra automaticamente o vínculo de responsável aberto. |

### Depreciação

| ID | Regra |
|---|---|
| BR-013 | A depreciação utiliza exclusivamente o método linear no MVP. |
| BR-014 | O valor residual nunca é negativo; ao esgotar a vida útil, estabiliza em zero. |
| BR-015 | A depreciação é congelada na data da baixa e persistida no registro de baixa. |
| BR-016 | Ativos com status `EM_MANUTENCAO` continuam depreciando normalmente. |
| BR-017 | Valores monetários são arredondados em duas casas decimais, modo *half-up*. |

### Licenças

| ID | Regra |
|---|---|
| BR-018 | A quantidade em uso não pode exceder a quantidade contratada; a operação que violaria a regra é bloqueada. |
| BR-019 | A data de expiração deve ser posterior à data de aquisição. |
| BR-020 | Licença vencida não pode receber novas vinculações de uso. |
| BR-021 | A quantidade em uso é derivada da contagem de vínculos ativos, nunca informada manualmente. |

### Baixa e histórico

| ID | Regra |
|---|---|
| BR-022 | A data da baixa não pode ser futura nem anterior à data de aquisição. |
| BR-023 | O motivo `OUTRO` exige justificativa textual de no mínimo 10 caracteres. |
| BR-024 | Um ativo já baixado não pode ser baixado novamente. |
| BR-025 | O histórico nunca pode ser apagado: exclusão física de registros históricos é vedada em qualquer circunstância. |
| BR-026 | Toda baixa exige destinação registrada. |

### Governança e decisão

| ID | Regra |
|---|---|
| BR-027 | Nenhuma recomendação pode ser registrada sem ao menos uma evidência vinculada. |
| BR-028 | O sistema não seleciona automaticamente a alternativa de investimento; apenas ordena por custo e risco. |
| BR-029 | Os pesos do scorecard de fornecedores devem totalizar exatamente 100%. |
| BR-030 | Toda operação de escrita registra o usuário autor e o carimbo de tempo na trilha de auditoria. |

---

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

---

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
| NFR-AUD-01 | Histórico de alterações imutável: registros de vínculo, baixa e auditoria não admitem UPDATE nem DELETE | Tentativa de exclusão retorna erro; teste automatizado |
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
| NFR-MAN-05 | Banco de dados local simplificado (SQLite/H2) e definitivo (PostgreSQL) selecionáveis por variável de ambiente | Ambos os perfis executam os mesmos testes |
| NFR-MAN-06 | Migrações de banco versionadas | Base criada do zero por script |

### 13.7 Observabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| NFR-OBS-01 | Endpoint `/metrics` no padrão de exposição Prometheus | Scrape do Prometheus bem-sucedido |
| NFR-OBS-02 | Contador de requisições por endpoint e código de retorno, e histograma de duração | Métricas visíveis no Grafana |
| NFR-OBS-03 | Log estruturado com nível configurável | Inspeção da saída |
| NFR-OBS-04 | Identificação do ambiente em execução exposta no health check | Campo `environment` na resposta |

---

## 14. Modelo Conceitual de Dados

### 14.1 Entidades

| Entidade | Descrição | Atributos principais |
|---|---|---|
| **Ativo** | Item de hardware ou software sob gestão | nome, tipo, número de série, chave de licença, data de aquisição, valor de compra, status, vida útil, localização |
| **Categoria** | Classificação do ativo, portadora da vida útil padrão | nome, descrição, vida útil em meses, tipo aplicável |
| **Fornecedor** | Origem da aquisição | razão social, CNPJ, contato, telefone, e-mail |
| **Responsavel** | Pessoa a quem um ativo pode ser atribuído | nome, matrícula, e-mail, cargo, situação |
| **Setor** | Unidade organizacional | nome, sigla, responsável pelo setor |
| **Licenca** | Direito de uso de software, com quantitativo e vigência | software, chave, quantidade contratada, quantidade em uso, data de aquisição, data de expiração, valor, tipo |
| **HistoricoTransferencia** | Vínculo temporal entre ativo e responsável | ativo, responsável, setor, data de início, data de fim, motivo, registrado por |
| **BaixaAtivo** | Evento terminal do ciclo de vida do ativo | ativo, motivo, justificativa, data da baixa, destinação, valor residual congelado, registrado por |
| **Usuario** | Operador do sistema | login, senha (hash), perfil, situação |
| **LoteImportacao** | Registro de uma execução de importação | arquivo, data, usuário, total processado, aceitos, rejeitados |
| **ErroImportacao** | Falha em uma linha específica | lote, número da linha, campo, motivo |
| **Risco** | Exposição registrada formalmente | título, categoria, probabilidade, impacto, score, resposta, responsável, status, gatilho |
| **Fornecedor_Avaliacao** | Nota de um fornecedor em um critério | fornecedor, critério, peso, nota, período |
| **Recomendacao** | Decisão proposta, sustentada por evidências | título, contexto, recomendação, responsável, data, status |
| **Evidencia** | Elo entre recomendação e o dado que a sustenta | recomendação, tipo de origem, identificador da origem, descrição |
| **AuditLog** | Trilha imutável de operações | usuário, operação, entidade, identificador, carimbo de tempo, resultado |

### 14.2 Relacionamentos

```
Categoria      1 ──── N  Ativo
Fornecedor     1 ──── N  Ativo
Fornecedor     1 ──── N  Licenca
Fornecedor     1 ──── N  Fornecedor_Avaliacao

Ativo          1 ──── N  HistoricoTransferencia
Responsavel    1 ──── N  HistoricoTransferencia
Setor          1 ──── N  HistoricoTransferencia
Setor          1 ──── N  Responsavel

Ativo          1 ──── 0..1  BaixaAtivo
Licenca        N ──── N  Ativo            (via vínculo de instalação)

LoteImportacao 1 ──── N  ErroImportacao
LoteImportacao 1 ──── N  Ativo            (procedência do registro)

Recomendacao   1 ──── N  Evidencia
Usuario        1 ──── N  AuditLog
Usuario        1 ──── N  HistoricoTransferencia   (como registrador)
Usuario        1 ──── N  BaixaAtivo               (como registrador)
```

### 14.3 Notas de modelagem

- **Responsável atual não é atributo do Ativo.** É derivado do `HistoricoTransferencia` com `data_fim` nula. Guardar o responsável diretamente no ativo criaria uma fonte de verdade concorrente com o histórico e permitiria divergência entre os dois.
- **Depreciação não é persistida.** É calculada sob demanda a partir de `valor_compra`, `data_aquisicao` e `vida_util_meses`. A única exceção é o `valor_residual_baixa`, congelado no momento da baixa por ser um fato contábil datado.
- **`quantidade_em_uso` da licença é derivada** da contagem de vínculos de instalação. O campo pode ser materializado por desempenho, mas nunca editado diretamente.
- **`HistoricoTransferencia`, `BaixaAtivo` e `AuditLog` são append-only.** A camada de persistência deve impedir UPDATE e DELETE nessas tabelas, preferencialmente por restrição no próprio banco, não apenas por convenção de código.
- **Períodos de vínculo não se sobrepõem.** A invariante "no máximo um vínculo aberto por ativo" deve ser garantida por índice único parcial, não apenas por validação na aplicação.

---

## 15. Fluxos de Negócio

### 15.1 Cadastro de Ativo

```
[Início]
   │
   ▼
Usuário informa dados do ativo
   │
   ▼
Tipo = HARDWARE? ──Sim──► Número de série informado? ──Não──► [Erro: campo obrigatório]
   │                                  │
   Não                               Sim
   │                                  ▼
   ▼                        Número de série já existe? ──Sim──► [Erro: duplicidade]
Chave de licença informada?                │
   │                                      Não
   ├──Não──► [Erro: campo obrigatório]     │
   │                                       │
  Sim ◄────────────────────────────────────┘
   │
   ▼
Data de aquisição válida e valor > 0? ──Não──► [Erro: validação]
   │
  Sim
   │
   ▼
Herdar vida útil da categoria
   │
   ▼
Persistir ativo com status = ATIVO
   │
   ▼
Registrar na trilha de auditoria
   │
   ▼
Calcular depreciação para a data corrente
   │
   ▼
Ativo possui responsável? ──Não──► Sinalizar alerta CP-04
   │
  Sim
   │
   ▼
[Fim: exibir detalhe do ativo]
```

### 15.2 Transferência de Responsável

```
[Início]
   │
   ▼
Localizar ativo
   │
   ▼
Status = BAIXADO? ──Sim──► [Erro: BR-009 — ativo baixado não recebe responsável]
   │
  Não
   │
   ▼
Informar novo responsável, setor e data
   │
   ▼
Data ≥ data de aquisição? ──Não──► [Erro: BR-010]
   │
  Sim
   │
   ▼
┌─── INÍCIO DA TRANSAÇÃO ───┐
│  Existe vínculo aberto?   │
│      │            │        │
│     Sim          Não       │
│      │            │        │
│      ▼            │        │
│  Encerrar vínculo │        │
│  (data_fim = data)│        │
│      │            │        │
│      └─────┬──────┘        │
│            ▼               │
│  Criar novo vínculo aberto │
│            ▼               │
│  Registrar auditoria       │
└─── FIM DA TRANSAÇÃO ──────┘
   │
   ▼
[Fim: linha do tempo atualizada]
```

### 15.3 Baixa de Ativo

```
[Início]
   │
   ▼
Localizar ativo
   │
   ▼
Status = BAIXADO? ──Sim──► [Erro: BR-024 — baixa já registrada]
   │
  Não
   │
   ▼
Informar motivo, data, destinação e justificativa
   │
   ▼
Motivo = OUTRO e justificativa vazia? ──Sim──► [Erro: BR-023]
   │
  Não
   │
   ▼
Data válida (não futura, ≥ aquisição)? ──Não──► [Erro: BR-022]
   │
  Sim
   │
   ▼
┌─── INÍCIO DA TRANSAÇÃO ─────────────┐
│  Calcular valor residual na data    │
│  Persistir BaixaAtivo               │
│  Encerrar vínculo de responsável    │
│  Alterar status para BAIXADO        │
│  Registrar auditoria                │
└─── FIM DA TRANSAÇÃO ────────────────┘
   │
   ▼
Ativo sai do inventário ativo, histórico preservado
   │
   ▼
[Fim]
```

### 15.4 Renovação de Licença

```
[Início: alerta CP-03 — licença expira em ≤ 30 dias]
   │
   ▼
Administrador consulta detalhe da licença
   │
   ▼
Verificar quantidade em uso vs. contratada
   │
   ├──► Uso < 50% do contratado ──► Sinalizar subutilização
   │                                (oportunidade de redução)
   │
   ├──► Uso entre 50% e 100% ────► Renovar quantitativo atual
   │
   └──► Uso = contratado ────────► Avaliar ampliação
   │
   ▼
Comparar cenários de renovação (FR-010)
   │
   ▼
Registrar recomendação com evidências (FR-013)
   │
   ▼
Evidência vinculada? ──Não──► [Erro: BR-027]
   │
  Sim
   │
   ▼
Decisão registrada → nova licença cadastrada ou licença atual atualizada
   │
   ▼
[Fim: alerta cessa automaticamente]
```

### 15.5 Avaliação de Compliance

```
[Gatilho: acesso ao painel ou geração de relatório]
   │
   ▼
Para cada licença:
   ├── expirada?                 ──► CP-01 Crítico
   ├── uso > contratado?         ──► CP-02 Crítico
   └── expira em ≤ 30 dias?      ──► CP-03 Alto
   │
   ▼
Para cada ativo com status ATIVO:
   ├── sem vínculo aberto?       ──► CP-04 Alto
   ├── 100% depreciado?          ──► CP-05 Médio
   ├── EM_MANUTENCAO > 90 dias?  ──► CP-06 Médio
   ├── sem movimentação 12 meses?──► CP-08 Baixo
   └── valor de compra ausente?  ──► CP-09 Baixo
   │
   ▼
Para cada ativo baixado:
   └── sem destinação?           ──► CP-07 Médio
   │
   ▼
Agrupar por severidade (Crítico → Alto → Médio → Baixo)
   │
   ▼
Exibir painel com link para o registro de origem
   │
   ▼
[Fim: exportação opcional como relatório datado]
```

---

## 16. Dashboard e Relatórios

### 16.1 Painel inicial — cartões de indicadores

| Cartão | Conteúdo | Origem |
|---|---|---|
| Total de ativos | Contagem geral, com desdobramento por status | FR-009 |
| Hardware x Software | Proporção por tipo | FR-009 |
| Valor patrimonial bruto | Soma dos valores de compra dos ativos não baixados | FR-009 |
| Valor depreciado | Depreciação acumulada do parque, em valor e percentual | FR-003, FR-009 |
| Valor residual | Soma dos valores residuais | FR-003, FR-009 |
| Licenças vencendo | Contagem de licenças com expiração em ≤ 30 dias | FR-004 |
| Ativos sem responsável | Contagem de ativos ativos sem vínculo aberto | FR-002 |
| Ativos em manutenção | Contagem com status `EM_MANUTENCAO` | FR-001 |
| Não conformidades | Total de alertas abertos, por severidade | FR-007 |
| Idade média do parque | Em meses | FR-009 |

### 16.2 Gráficos

| Gráfico | Tipo | Eixos |
|---|---|---|
| Distribuição por categoria | Barras horizontais | Categoria × contagem |
| Evolução do valor residual | Linha | Mês × valor residual total |
| Ativos por status | Rosca | Proporção entre ativo, manutenção e baixado |
| Conformidade de licenças | Barras empilhadas | Licença × contratado e em uso |
| Baixas por motivo | Barras | Motivo × contagem no período |
| Ativos por faixa de idade | Histograma | Faixa etária × contagem |

### 16.3 Relatórios disponíveis

| Relatório | Público-alvo | Formatos |
|---|---|---|
| Inventário completo com filtros | Administrador, Patrimônio | Tela, CSV, XLSX |
| Depreciação e valor residual por ativo | Patrimônio, Contabilidade | CSV, XLSX |
| Conformidade de licenças | Auditoria, Compliance | Tela, CSV |
| Histórico de responsáveis por ativo | Auditoria | Tela, CSV |
| Termo de responsabilidade por colaborador | Administrador, RH | Tela, CSV |
| Baixas por período e destinação | Patrimônio, Sustentabilidade | CSV |
| Não conformidades abertas | Auditoria | Tela, CSV |
| Ativos próximos do fim da vida útil | Administrador, Direção | Tela, CSV |
| Erros de importação por lote | Administrador | CSV |

### 16.4 Dashboard técnico (Grafana)

Provisionado automaticamente na pasta **Governança de TI**, com fonte de dados Prometheus:

- disponibilidade das APIs Python e Java;
- volume de requisições por minuto;
- distribuição de códigos de retorno;
- latência (percentis 50, 95 e 99);
- estado da conexão com o banco de dados.

---

## 17. Riscos e Restrições

### 17.1 Riscos do produto

| ID | Risco | Prob. | Impacto | Score | Mitigação |
|---|---|---|---|---|---|
| RI-01 | Dados iniciais de inventário incompletos ou inconsistentes, comprometendo a confiança no sistema | 4 | 4 | 16 | Importação com validação e relatório de erros (FR-008); indicador de cobertura como métrica de adoção |
| RI-02 | Usuários deixarem de registrar transferências, tornando o histórico irreal | 4 | 4 | 16 | Formulário de transferência com no máximo 4 campos (NFR-USA-02); interface responsiva para registro em campo |
| RI-03 | Divergência entre o valor residual do sistema e o registro contábil | 3 | 4 | 12 | Método linear explícito e parametrizado; relatório conciliável; vida útil alinhada à IN RFB 1.700 |
| RI-04 | Bloqueio de excedente de licença sendo contornado por cadastro paralelo | 3 | 4 | 12 | Registro da tentativa bloqueada na auditoria (NFR-AUD-05); relatório de conformidade periódico |
| RI-05 | Divergência funcional entre as implementações Python e Java | 3 | 3 | 9 | Contrato OpenAPI único; suíte de testes de contrato executada contra ambas |
| RI-06 | Perda de histórico por exclusão indevida | 2 | 5 | 10 | Tabelas append-only com restrição no banco; RBAC sem permissão de exclusão para nenhum perfil |
| RI-07 | Escopo expandindo para funcionalidades de ERP durante o desenvolvimento | 3 | 3 | 9 | Seção 7.2 como referência contratual; mudança de escopo exige registro formal |
| RI-08 | Vazamento de chaves de licença armazenadas em texto claro | 2 | 4 | 8 | Acesso à chave restrito ao perfil `ADMIN`; mascaramento na listagem |
| RI-09 | Degradação de desempenho com crescimento da base | 2 | 3 | 6 | Paginação obrigatória; índices definidos nas migrações (NFR-PER-05) |
| RI-10 | Indisponibilidade do ambiente durante a demonstração | 2 | 4 | 8 | Perfil de execução local com SQLite/H2, independente de infraestrutura externa; smoke test antes da apresentação |

### 17.2 Restrições

| ID | Restrição | Natureza |
|---|---|---|
| RE-01 | As implementações Python e Java devem obedecer ao mesmo contrato de API | Técnica — definida pela baseline da disciplina |
| RE-02 | Moeda única (BRL) e organização única no MVP | Escopo |
| RE-03 | Método de depreciação restrito ao linear | Escopo |
| RE-04 | Nenhuma integração com sistemas externos (AD, ERP, SCCM) | Escopo |
| RE-05 | Execução obrigatória via Docker Compose com um comando | Técnica |
| RE-06 | A decisão de investimento permanece humana; o sistema não escolhe automaticamente | Governança — princípio da baseline |
| RE-07 | Toda recomendação exige evidência vinculada | Governança — princípio da baseline |
| RE-08 | O sistema é uma camada de apoio à governança, não um simulador de infraestrutura real | Posicionamento — definido pelo guia de orquestração |

---

## 18. Roadmap

### 18.1 MVP — versão 1.0

**Objetivo:** inventário confiável, responsabilidade rastreável e conformidade visível.

| Sprint | Entrega |
|---|---|
| Sprint 0 | Discovery, modelo de dados, contrato OpenAPI, ambiente Docker Compose |
| Sprint 1 | FR-001, FR-008, FR-015 — cadastro, importação, autenticação e RBAC |
| Sprint 2 | FR-002, FR-003 — responsáveis, histórico e depreciação |
| Sprint 3 | FR-004, FR-005 — licenças, alertas e baixas |
| Sprint 4 | FR-006, FR-007, FR-009, FR-014 — relatórios, compliance, indicadores e dashboard |
| Sprint 5 | FR-010 a FR-013 — cenários, scorecard, riscos e recomendação rastreável; testes, documentação e defesa |

### 18.2 V2 — consolidação operacional

- Geração e leitura de **QR Code** por ativo, para inventário físico assistido por celular;
- **Upload de nota fiscal**, manuais e fotos, com armazenamento de anexos;
- **Termo de responsabilidade** gerado em PDF, com assinatura digital;
- **Renovação assistida de licenças**, com fluxo de aprovação;
- **Gestão de garantia e contratos de manutenção**, com alertas próprios;
- Métodos adicionais de depreciação (soma dos dígitos, unidades produzidas);
- Suporte a **múltiplas filiais** e centros de custo;
- Notificações por e-mail para alertas críticos.

### 18.3 V3 — automação e inteligência

- **Inventário automático via agente** instalado nas estações;
- **Integração com Microsoft Intune** para sincronização de dispositivos gerenciados;
- **Integração com Active Directory / LDAP** para autenticação e base de responsáveis;
- **Integração com ERP** para conciliação patrimonial automática;
- **Modelo preditivo de substituição de ativos**, estimando o momento ótimo de troca a partir de idade, histórico de manutenção e custo acumulado;
- Detecção de anomalias de uso de licenças;
- API pública para consumo por sistemas de terceiros.

---

## 19. Perguntas em Aberto

| ID | Pergunta | Impacto se não respondida | Responsável por responder |
|---|---|---|---|
| QA-01 | Haverá múltiplas filiais ou unidades com inventários segregados? | Afeta o modelo de dados (entidade Unidade) e o escopo dos relatórios | Patrocinador |
| QA-02 | Haverá necessidade de múltiplas moedas para ativos importados? | Afeta os campos monetários e o cálculo de depreciação | Patrimônio |
| QA-03 | Haverá integração com ERP para conciliação patrimonial, ainda que por exportação? | Define o formato de exportação exigido | Patrimônio / TI |
| QA-04 | Qual o formato do inventário legado a ser importado? | Define o parser e o mapeamento de colunas do FR-008 | Administrador de TI |
| QA-05 | A vida útil deve seguir a tabela fiscal ou uma política interna própria? | Afeta a parametrização padrão das categorias | Contabilidade |
| QA-06 | Software adquirido deve ser modelado como Ativo, como Licença ou como ambos? | Afeta o modelo de dados e a interpretação dos indicadores | Arquitetura / Patrimônio |
| QA-07 | A janela de alerta de vencimento de licença é fixa em 30 dias ou varia por fornecedor? | Define se o parâmetro é global ou por licença | Administrador de TI |
| QA-08 | Ativos compartilhados (impressoras, projetores) devem ter pessoa responsável ou apenas setor? | Afeta a obrigatoriedade do campo responsável no FR-002 | Administrador de TI |
| QA-09 | Deve existir estorno de baixa, ou a operação é definitiva? | Afeta a imutabilidade assumida no BR-024 | Patrimônio / Auditoria |
| QA-10 | Colaboradores terão acesso de consulta aos próprios ativos? | Cria um quinto perfil de acesso, hoje fora do escopo | Patrocinador |
| QA-11 | Qual a política de retenção do histórico e da trilha de auditoria? | Afeta o volume da base e eventual expurgo | Compliance |
| QA-12 | Qual o destinatário formal dos relatórios de conformidade e com que periodicidade? | Define automação de geração e envio | Compliance |

---

## Anexo A — Matriz de Aderência a Frameworks de Governança

| Framework | Referência específica | Requisitos que a implementam |
|---|---|---|
| **ISO/IEC 19770-1** | Sistema de gestão de ativos de TI: identificação, propriedade, ciclo de vida | FR-001, FR-002, FR-005, FR-006 |
| **ISO/IEC 19770-3** | Direitos de uso de software e entitlement | FR-004, FR-007 |
| **COBIT 2019 — BAI09** | Gerenciar Ativos: contabilizar, otimizar e proteger ao longo do ciclo de vida | FR-001, FR-003, FR-005, FR-009 |
| **COBIT 2019 — BAI10** | Gerenciar Configuração: registro confiável dos itens e seus atributos | FR-001, FR-008 |
| **COBIT 2019 — APO10** | Gerenciar Fornecedores: avaliação e monitoramento de desempenho | FR-011 |
| **COBIT 2019 — APO12** | Gerenciar Riscos: identificação, avaliação e resposta | FR-012, FR-007 |
| **COBIT 2019 — APO06** | Gerenciar Orçamento e Custos | FR-003, FR-010 |
| **ITIL 4** | Prática de Gestão de Ativos de TI | FR-001, FR-002, FR-005 |
| **ITIL 4** | Prática de Gestão de Configuração de Serviço | FR-001, FR-006 |
| **ISO/IEC 38500** | Princípio da Responsabilidade | FR-002, FR-015 |
| **ISO/IEC 38500** | Princípio da Aquisição | FR-010, FR-011 |
| **ISO/IEC 38500** | Princípio da Conformidade | FR-004, FR-007 |
| **Val IT** | Gestão do valor do investimento em TI | FR-003, FR-009, FR-010 |
| **Risk IT** | Risco de negócio associado ao uso de TI | FR-004, FR-007, FR-012 |
| **BSC — perspectiva financeira** | Indicadores de valor patrimonial e custo | KPI-05, FR-009, FR-010 |
| **BSC — perspectiva de processos** | Indicadores de cobertura e conformidade | KPI-01, KPI-02, KPI-03 |
| **TI Verde** | Descarte responsável de resíduos eletroeletrônicos | FR-005 (campo `destinacao`), relatório de baixas por destinação |
| **CMMI / MPS.BR** | Rastreabilidade de requisitos e gestão de configuração | Anexo B, NFR-MAN-01, NFR-MAN-06 |
| **IN RFB nº 1.700/2017** | Taxas de depreciação de bens do ativo imobilizado | FR-003, tabela de vida útil por categoria |

---

## Anexo B — Matriz de Rastreabilidade

| Requisito | Histórias | Regras de negócio | Critérios de aceite | Indicador associado |
|---|---|---|---|---|
| FR-001 | US-001 a US-006 | BR-001 a BR-006 | AC-001 a AC-008 | KPI-01 |
| FR-002 | US-007 a US-011 | BR-007 a BR-012 | AC-009 a AC-014 | KPI-02 |
| FR-003 | US-012 a US-016 | BR-013 a BR-017 | AC-015 a AC-020 | KPI-05 |
| FR-004 | US-017 a US-021 | BR-018 a BR-021 | AC-021 a AC-026 | KPI-03 |
| FR-005 | US-022 a US-025 | BR-022 a BR-026 | AC-027 a AC-033 | KPI-08 |
| FR-006 | US-026, US-027 | BR-014 | AC-034 a AC-038 | — |
| FR-007 | US-028 a US-030 | BR-007, BR-018, BR-026 | AC-039 a AC-043 | KPI-02, KPI-03 |
| FR-008 | US-031, US-032 | BR-001, BR-002, BR-003 | AC-044 a AC-046 | KPI-01 |
| FR-009 | US-030 | — | AC-047 | KPI-01 a KPI-08 |
| FR-010 | US-033 | BR-028 | AC-052 | — |
| FR-011 | US-034 | BR-029 | AC-048, AC-049 | — |
| FR-012 | US-035 | — | AC-050 | — |
| FR-013 | US-036 | BR-027 | AC-051 | — |
| FR-014 | US-037 | — | AC-053, AC-054 | KPI-04 |
| FR-015 | US-038 a US-040 | BR-030 | AC-055 a AC-057 | — |

---

## Anexo C — Glossário

| Termo | Definição |
|---|---|
| **Ativo de TI** | Qualquer item de hardware ou software de valor econômico sob gestão da área de tecnologia |
| **Baixa** | Evento terminal que retira o ativo do inventário operacional, preservando seu histórico |
| **CAPEX** | Despesa de capital: investimento em aquisição de bens |
| **Depreciação linear** | Método que distribui uniformemente o valor do bem ao longo de sua vida útil |
| **Entitlement** | Direito de uso de software concedido por uma licença |
| **ITAM** | *IT Asset Management* — gestão de ativos de tecnologia da informação |
| **OPEX** | Despesa operacional: custo recorrente de manutenção e operação |
| **RBAC** | *Role-Based Access Control* — controle de acesso por perfil |
| **TCO** | *Total Cost of Ownership* — custo total de propriedade ao longo do ciclo de vida |
| **Valor residual** | Valor contábil remanescente após a depreciação acumulada |
| **Vida útil** | Período estimado de uso econômico do bem, em meses |

---

*Documento preparado como insumo para a especificação técnica (SDD) e para a implementação assistida por IA. Todo requisito possui identificador estável; toda alteração posterior deve preservar os identificadores existentes e adicionar novos ao final da sequência.*
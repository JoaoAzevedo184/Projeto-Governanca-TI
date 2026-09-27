# PRD — Stakeholders e Personas

Parte de [PRD — ITAM](README.md).

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


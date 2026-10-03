# PRD — Visão Geral

Parte de [PRD — ITAM](README.md).

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

| ID | Métrica | Fórmula | Meta do MVP | Situação no MVP |
|---|---|---|---|---|
| KPI-01 | Cobertura de inventário | ativos cadastrados / ativos estimados no parque | ≥ 95% | **Fora do MVP:** o denominador (ativos estimados no parque) é um dado externo que o sistema não cadastra |
| KPI-02 | Ativos com responsável definido | ativos ativos com responsável / total de ativos ativos | ≥ 98% | Calculado em `GET /indicadores` |
| KPI-03 | Conformidade de licenças | licenças com uso ≤ contratado e não vencidas / total de licenças | 100% | Calculado em `GET /indicadores` |
| KPI-04 | Tempo médio para localizar um ativo | tempo entre a consulta e a identificação do responsável | ≤ 30 segundos | **Fora do MVP:** mede o tempo de uso por uma pessoa, e o sistema não instrumenta nem armazena essa medição |
| KPI-05 | Acurácia da depreciação | divergência entre valor residual do sistema e o contábil | ≤ 1% | **Fora do MVP:** exige o valor residual contábil, que vem de fonte externa e não existe no sistema |
| KPI-06 | Ativos sem movimentação registrada | ativos sem evento nos últimos 12 meses / total | ≤ 10% | Calculado em `GET /indicadores` |
| KPI-07 | Idade média do parque | média da diferença entre hoje e a data de aquisição | monitorada, sem meta no MVP | Calculado em `GET /indicadores` |
| KPI-08 | Taxa de baixas com destinação registrada | baixas com destinação / total de baixas | 100% | Calculado em `GET /indicadores` |

> **KPI-01, KPI-04 e KPI-05 estão fora do MVP**: continuam definidos aqui como métricas de sucesso do projeto, mas não são calculados pelo sistema, pelos motivos da última coluna. `GET /indicadores` não os devolve. Os identificadores permanecem.


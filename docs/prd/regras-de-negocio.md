# PRD — Regras de Negócio (BR-)

Parte de [PRD — ITAM](README.md).

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
| BR-019 | A data de expiração deve ser posterior à data de início da vigência. |
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


# ADR-012 — Software adquirido é modelado como Ativo

| Campo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-09-29 |
| **Resolve** | QA-06 ([`docs/prd/planejamento.md`](../prd/planejamento.md)) |
| **Relacionado a** | FR-001, FR-003, FR-004, BR-002, BR-006, BR-013, BR-014, ADR-011 |

## Contexto

A pergunta em aberto QA-06 do PRD — *"Software adquirido deve ser modelado como Ativo, como Licença ou como ambos?"* — afeta o modelo de dados e a interpretação dos indicadores. O esquema físico já admitia as duas leituras ao mesmo tempo:

- `ativo.tipo` aceita `SOFTWARE`, com `chave_licenca` obrigatória (BR-002, `ck_ativo_identificador`), e a categoria semente "Software perpétuo" define 60 meses de vida útil (FR-003, [`dados-semente.md`](../modelo-de-dados/dados-semente.md));
- `licenca` também carrega `software`, `chave_licenca`, `data_aquisicao` e `valor_total` (FR-004, [`modelo-fisico.md`](../spec/modelo-fisico.md)).

Sem decisão, o mesmo software comprado poderia entrar no patrimônio duas vezes, e o Sprint 2 (depreciação) precisava saber se software deprecia pela regra do ativo.

## Decisão

**Software adquirido é um Ativo.** É registrado na tabela `ativo` com `tipo = 'SOFTWARE'`, distinguido do hardware apenas pelo tipo. Não existe entidade patrimonial separada para software.

Consequências diretas, sem regra nova:

1. **Identificação** — `chave_licenca` obrigatória para `SOFTWARE`, como já exige BR-002.
2. **Valor e depreciação** — o valor patrimonial do software é `ativo.valor_compra`, depreciado pelo mesmo método linear do hardware (BR-013), com vida útil herdada da categoria (BR-006) e residual zero ao fim da vida útil (BR-014). `app/utils/depreciacao.py` não tem nenhum ramo por tipo de ativo.
3. **Responsabilidade, baixa e auditoria** — software participa de `historico_transferencia`, `baixa_ativo` e `audit_log` exatamente como o hardware.

## Alternativas consideradas e rejeitadas

| Alternativa | Por que foi rejeitada |
|---|---|
| **Só Licença** — software existe apenas em `licenca`, fora de `ativo` | Tira o software do inventário patrimonial: ele deixaria de ter responsável (FR-002), depreciação (FR-003) e baixa (FR-005), e a distribuição hardware × software do painel (FR-009) ficaria sem base. Também contradiz BR-002 e `ck_ativo_identificador`, que já preveem ativos `SOFTWARE`. |
| **Ambos** — o mesmo software com valor patrimonial registrado em `ativo` **e** em `licenca` | Duas fontes de verdade para o mesmo bem: `ativo.valor_compra` e `licenca.valor_total` somariam a mesma compra duas vezes no valor do parque e nos indicadores, sem regra que diga qual prevalece. É o mesmo problema que a ADR-003 evitou para o responsável atual. |

## Consequências

**Positivas**

- Um único lugar para valor, depreciação, responsável e baixa de qualquer ativo de TI; indicadores de inventário e de valor patrimonial não dependem do tipo.
- Nenhuma mudança de schema nem de regra: BR-002 e a categoria "Software perpétuo" já sustentavam essa leitura.

**Negativas / pendentes**

- **Papel de `licenca` (Sprint 3) — resolvido em 2026-09-30.** Esta ADR decide onde o software *patrimonial* vive, não remove `licenca` nem o FR-004. O papel da licença foi decidido no item 4 da resolução (ver abaixo).
- **Software não perpétuo — resolvido em 2026-09-30** (item 2 de [`RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md)). Só a licença perpétua é ativo. Subscrição é despesa, registrada só como licença com vigência. OEM não é ativo separado: o valor está no hardware.
- **Amortização × depreciação** (item 3 da resolução). Software é bem intangível, e o termo contábil correto é amortização (CPC 04). O sistema mantém um único cálculo linear e o termo "depreciação" na API e no código, porque o cálculo é idêntico (linear, sem residual). O glossário do PRD registra que, para `tipo = SOFTWARE`, o valor representa a amortização.
- **Papel de `licenca` — resolvido em 2026-09-30** (item 4 da resolução). A licença passa a ser só o contrato de direito de uso, com FK para o ativo `SOFTWARE` nas licenças perpétuas. Ver [`dicionario-de-dados.md`](../modelo-de-dados/dicionario-de-dados.md#37-licenca-e-licenca_vinculo) §3.7.
- Documentos do PRD e do modelo de dados que ainda tratam software como licença estão listados no resumo de entrega do Sprint 2 e no `ROADMAP`, para a equipe decidir a redação. Nenhuma regra de negócio foi alterada por esta ADR.

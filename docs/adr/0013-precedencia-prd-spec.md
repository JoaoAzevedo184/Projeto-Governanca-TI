# ADR-013 — Precedência entre PRD e SPEC

| Campo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-09-30 |
| **Origem** | Item 0 de [`docs/RESOLUCAO_PENDENCIAS_SPRINT2.md`](../RESOLUCAO_PENDENCIAS_SPRINT2.md) |
| **Relacionado a** | FR-003, BR-014, BR-017, [`docs/prd/`](../prd/README.md), [`docs/spec/`](../spec/README.md) |

## Contexto

O PRD e o SPEC são escritos separadamente. No Sprint 2 os dois divergiram no cálculo da depreciação: o PRD (FR-003) define a regra de negócio, e o código de referência do SPEC (§7.1 de [`regras-de-calculo.md`](../spec/regras-de-calculo.md)) arredonda a depreciação mensal antes de multiplicar pelos meses. Os dois caminhos dão resultados diferentes (R$ 2.000,04 contra R$ 2.000,00 no exemplo de R$ 6.000,00 em 36 meses, após 12 meses). Não havia regra para decidir qual documento vale quando os dois discordam, e cada divergência virava uma discussão caso a caso.

## Decisão

- **O PRD prevalece em regra de negócio**: o que o sistema faz e quais resultados produz (FR, BR, AC, fórmulas e valores esperados).
- **O SPEC prevalece em implementação**: como o sistema faz (estrutura, tecnologia, padrões, contrato técnico, modelo físico).
- Havendo conflito sobre regra de negócio, **corrige-se o SPEC** para seguir o PRD, e a correção é registrada no ROADMAP.
- Se o PRD for omisso ou ambíguo sobre uma regra de negócio, a equipe decide e registra a decisão no PRD (ou numa ADR, se afetar a arquitetura) antes de alterar o código.

## Alternativas consideradas e rejeitadas

| Alternativa | Por que foi rejeitada |
|---|---|
| **SPEC sempre prevalece** | O SPEC é derivado do PRD. Deixá-lo decidir regra de negócio permitiria que um detalhe de implementação mudasse o resultado entregue ao usuário sem passar pela equipe de produto. |
| **Decidir caso a caso** | É a situação que gerou esta ADR: cada divergência vira discussão, e a decisão não fica rastreável. |

## Consequências

**Positivas**

- Divergências futuras têm resolução automática e rastreável.
- O primeiro caso já aplicado: a depreciação passa a seguir a fórmula do PRD, arredondando só no resultado final (item 1 da resolução).

**Negativas / custo aceito**

- Quando o PRD muda, o SPEC precisa ser revisado. A regra não impede a divergência; só define quem cede.

# Modelo de dados

- Event: origem, serviço, severidade, tipo, acionável, duplicado, MTTD, MTTR, owner, runbook e incidente.
- ServiceSlo: serviço, SLI, meta, janela, medição e error budget.
- TelemetryCost: fonte, volume, retenção, preço unitário e centro de custo.
- Risk: probabilidade, impacto, resposta, owner e trigger.
- Recommendation/Evidence: ação de tuning e justificativas.

Restrições: severidade válida; MTTD/MTTR não negativos; metas de SLO entre 0 e 1; custos não negativos; recomendação com evidências.

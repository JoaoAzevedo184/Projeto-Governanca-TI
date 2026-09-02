# SPEC — MVP de Observabilidade Híbrida

## Contexto
A Logística Nordeste S.A. opera datacenter, 14 filiais e workloads em cloud. Possui monitoramento fragmentado, cerca de 1.800 alertas/dia, 92% não acionáveis, MTTD de 38 minutos, MTTR de 200 minutos, cobertura de 63% e runbooks em apenas 25% dos alarmes.

## Objetivo
Criar uma camada executável de análise e governança de observabilidade. O MVP não substitui Zabbix, Prometheus, Grafana ou uma plataforma SaaS. Ele organiza sinais, custos, owners, SLOs e decisões de melhoria.

## Funções obrigatórias
1. Importar eventos e alertas em CSV/XLSX.
2. Calcular total, MTTD, MTTR, acionabilidade, duplicidade e incident conversion.
3. Segmentar por serviço, origem, severidade, owner e tipo.
4. Cadastrar SLI, SLO e janela de medição.
5. Calcular error budget e burn rate simplificado.
6. Verificar cobertura de ativos e serviços.
7. Associar owner e runbook aos alertas críticos.
8. Simular retenção, volume e custo de telemetria.
9. Comparar self-managed, SaaS e modelo híbrido.
10. Registrar riscos e controles.
11. Gerar recomendações de tuning com evidências.
12. Expor health checks, métricas e documentação OpenAPI.

## Regras
- MTTD e MTTR são médias dos eventos válidos, com unidade explícita.
- Alerta acionável possui owner e ação ou runbook compatível.
- Duplicidades devem ser medidas antes de removidas.
- SLO deve possuir serviço, SLI, meta e janela.
- Error budget = 1 - meta do SLO, aplicado à janela.
- Telemetria deve ser justificada por valor, risco e custo.
- Recomendação publicada exige evidência operacional, financeira e de risco.

## Metas
- cobertura >= 95%;
- MTTD <= 10 min;
- MTTR <= 90 min;
- alertas acionáveis >= 40%;
- runbooks em alertas críticos >= 90%;
- SLO dos serviços críticos conforme tier;
- custo equivalente por host <= R$ 300/mês.

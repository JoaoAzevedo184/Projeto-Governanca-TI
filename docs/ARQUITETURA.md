# Arquitetura

Cliente -> API REST -> serviços de ingestão, indicadores, SLO, custos, riscos e tuning -> persistência -> Prometheus/Grafana.

O domínio contém Event, Service, Slo, Runbook, TelemetryCost, Risk, Recommendation e Evidence. Python e Java usam o mesmo contrato comportamental e as mesmas fixtures.

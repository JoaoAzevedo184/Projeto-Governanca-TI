# Arquitetura

Cliente -> API REST -> serviços de ingestão, indicadores, SLO, custos, riscos e tuning -> persistência -> Prometheus/Grafana.

O domínio contém Event, Service, Slo, Runbook, TelemetryCost, Risk, Recommendation e Evidence. A implementação de referência é a API Python, que consome as fixtures em `datasets/`.

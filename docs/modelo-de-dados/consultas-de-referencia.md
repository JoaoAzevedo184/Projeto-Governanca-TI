# Modelo de Dados — Consultas Derivadas de Referência

Parte de [Modelo de Dados — ITAM](README.md).

## 6. Consultas derivadas de referência

### Responsável atual de um ativo

```sql
SELECT r.id, r.nome, s.nome AS setor, h.data_inicio
FROM historico_transferencia h
JOIN responsavel r ON r.id = h.responsavel_id
JOIN setor s       ON s.id = h.setor_id
WHERE h.ativo_id = :ativo_id
  AND h.data_fim IS NULL;
```

### Quantidade em uso de uma licença

```sql
SELECT COUNT(*) AS quantidade_em_uso
FROM licenca_vinculo
WHERE licenca_id = :licenca_id
  AND ativo_vinculo = true;
```

### Ativos sem responsável (alerta CP-04)

```sql
SELECT a.id, a.nome, a.numero_serie
FROM ativo a
LEFT JOIN historico_transferencia h
       ON h.ativo_id = a.id AND h.data_fim IS NULL
WHERE a.status = 'ATIVO'
  AND h.id IS NULL;
```

### Depreciação em SQL (para conferência do cálculo da aplicação)

```sql
SELECT
  a.id,
  a.valor_compra,
  LEAST(
    EXTRACT(YEAR  FROM age(CURRENT_DATE, a.data_aquisicao)) * 12
  + EXTRACT(MONTH FROM age(CURRENT_DATE, a.data_aquisicao)),
    a.vida_util_meses
  )::int AS meses_efetivos,
  ROUND(a.valor_compra / a.vida_util_meses, 2) AS depreciacao_mensal
FROM ativo a
WHERE a.status <> 'BAIXADO';
```

Esta consulta existe para **conferir** o resultado da aplicação, não para substituí-lo. A fonte de verdade do cálculo é `app/utils/depreciacao.py` (ADR-002); divergência entre os dois indica bug e deve virar teste.

### Licenças não conformes (CP-01 e CP-02)

```sql
SELECT l.id, l.software, l.quantidade_contratada,
       COUNT(v.id) FILTER (WHERE v.ativo_vinculo) AS em_uso,
       l.data_expiracao,
       CASE
         WHEN l.data_expiracao < CURRENT_DATE THEN 'CP-01'
         WHEN COUNT(v.id) FILTER (WHERE v.ativo_vinculo) > l.quantidade_contratada THEN 'CP-02'
       END AS alerta
FROM licenca l
LEFT JOIN licenca_vinculo v ON v.licenca_id = l.id
GROUP BY l.id
HAVING l.data_expiracao < CURRENT_DATE
    OR COUNT(v.id) FILTER (WHERE v.ativo_vinculo) > l.quantidade_contratada;
```


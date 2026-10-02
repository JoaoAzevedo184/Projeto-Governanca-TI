# Modelo de Dados — Invariantes e Como São Garantidas

Parte de [Modelo de Dados — ITAM](README.md).

## 4. Invariantes e como são garantidas

| Invariante | Regra | Garantia | Camada |
|---|---|---|---|
| Número de série único no sistema | BR-001 | `UNIQUE` | Banco |
| Hardware tem série; software tem chave | BR-002 | `CHECK` composto | Banco |
| Um único vínculo aberto por ativo | BR-007 | Índice único parcial | **Banco** |
| Períodos de vínculo não se sobrepõem | BR-008 | Transação única + `SELECT FOR UPDATE` | Serviço + banco |
| Ativo baixado não recebe responsável | BR-009 | Verificação com lock | Serviço |
| Histórico não pode ser alterado | BR-011, BR-025 | Trigger `BEFORE UPDATE OR DELETE` | **Banco** |
| Um ativo tem no máximo uma baixa | BR-024 | `UNIQUE (ativo_id)` | Banco |
| Uso de licença ≤ contratado | BR-018 | Verificação com lock na licença | Serviço |
| Valor residual nunca negativo | BR-014 | `max(..., 0)` + `CHECK ≥ 0` na baixa | Cálculo + banco |
| Recomendação exige evidência | BR-027 | Criação na mesma transação | **Serviço** (ver abaixo) |
| Pesos do scorecard somam 100% | BR-029 | Validação com `Decimal` | Serviço |

### O caso do BR-027

É a única invariante estrutural que **não** pode ser expressa como constraint simples: exigiria verificar a existência de filhos no momento do INSERT do pai. As saídas seriam uma `CONSTRAINT TRIGGER DEFERRABLE` ou uma verificação no commit — complexidade que não se paga num MVP.

A decisão: criar `recomendacao` e suas `evidencia` na mesma transação, no serviço, e cobrir com teste de integração (AC-051). O custo aceito é que uma escrita direta no banco, contornando a API, poderia violar a regra. Aceitável porque nenhum perfil tem acesso direto ao banco.

### Imutabilidade e a exceção necessária

```sql
CREATE OR REPLACE FUNCTION bloquear_mutacao() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Registro histórico é imutável (NFR-AUD-01)';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_baixa_imutavel
  BEFORE UPDATE OR DELETE ON baixa_ativo
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();

CREATE TRIGGER tg_audit_imutavel
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();
```

`historico_transferencia` precisa de tratamento próprio, porque a transferência escreve `data_fim` no vínculo anterior:

```sql
CREATE OR REPLACE FUNCTION permitir_apenas_encerramento() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Vínculo histórico não pode ser excluído (BR-025)';
  END IF;
  IF OLD.data_fim IS NOT NULL THEN
    RAISE EXCEPTION 'Vínculo já encerrado é imutável (BR-011)';
  END IF;
  IF NEW.id                IS DISTINCT FROM OLD.id
  OR NEW.ativo_id          IS DISTINCT FROM OLD.ativo_id
  OR NEW.responsavel_id    IS DISTINCT FROM OLD.responsavel_id
  OR NEW.setor_id          IS DISTINCT FROM OLD.setor_id
  OR NEW.data_inicio       IS DISTINCT FROM OLD.data_inicio
  OR NEW.motivo            IS DISTINCT FROM OLD.motivo
  OR NEW.registrado_por_id IS DISTINCT FROM OLD.registrado_por_id
  OR NEW.data_source       IS DISTINCT FROM OLD.data_source
  OR NEW.criado_em         IS DISTINCT FROM OLD.criado_em THEN
    RAISE EXCEPTION 'Somente data_fim pode ser preenchida (BR-011)';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

O trigger permite exatamente uma transição — nulo para não-nulo em `data_fim` — e nada mais. É a materialização da ADR-005. Todas as colunas além de `data_fim` são protegidas, inclusive `motivo`, `data_source` e `criado_em`: deixá-las editáveis permitiria reescrever o passado (BR-011, BR-025). Esta é a DDL aplicada pela migração `c8365ce7e5e4` e por `app/models/historico.py` (item 10 da resolução do Sprint 2).


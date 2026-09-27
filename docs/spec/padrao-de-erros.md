# SPEC — Padrão de Erros

Parte de [SPEC — ITAM](README.md).

## 8. Padrão de Erros

Formato único em toda a API, inspirado na RFC 7807, com o campo adicional `regra`:

```json
{
  "tipo": "/erros/regra-de-negocio",
  "titulo": "Operação recusada por regra de negócio",
  "status": 409,
  "detalhe": "A quantidade em uso não pode exceder a quantidade contratada.",
  "instancia": "/api/v1/licencas/12/vinculos",
  "regra": "BR-018",
  "erros": []
}
```

O campo `regra` cria rastreabilidade direta entre o comportamento em runtime e o documento de requisitos — útil na defesa e exigido pela matriz de rastreabilidade.

| Situação | HTTP | Exemplo de regra |
|---|---|---|
| Payload malformado ou validação Pydantic | 422 | — |
| Violação de regra de negócio | 409 | BR-009, BR-018, BR-024 |
| Violação de unicidade | 409 | BR-001 |
| Recurso inexistente | 404 | — |
| Sem token ou token inválido | 401 | — |
| Perfil sem permissão | 403 | FR-015 |
| Erro interno | 500 | — |

**Regra de ouro (NFR-SEG-06):** nenhuma resposta de erro expõe stack trace, nome de tabela ou versão de framework. O handler global captura `Exception`, registra o traceback no log estruturado e devolve payload genérico.

**Toda recusa por regra de negócio é registrada na auditoria** com `resultado = RECUSADO` e `regra_violada` preenchida (NFR-AUD-05, AC-021).


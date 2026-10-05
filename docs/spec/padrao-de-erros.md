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
| Violação de unicidade | 409 | BR-001, BR-039 |
| Recurso inexistente | 404 | — |
| Sem token ou token inválido | 401 | — |
| Perfil sem permissão | 403 | FR-015 |
| Corpo da requisição ilegível (JSON ou multipart inválido) | 400 | — |
| Rota inexistente | 404 | — |
| Método não permitido | 405 | — |
| Valor numérico fora do intervalo aceito pelo banco (id além de 32 bits) | 422 | — |
| Erro interno | 500 | — |

Os erros do próprio framework (token ausente, corpo ilegível, rota inexistente, método não permitido) saem no mesmo formato, com `tipo = /erros/http-<status>` e `regra = null`. O `www-authenticate` do `401` é preservado. Um id maior que o inteiro do banco é entrada inválida, nunca `500`: o handler devolve `422` sem a mensagem do driver (NFR-SEG-06). O `openapi.yaml` documenta `400`, `401`, `403`, `404`, `409` e `422` em toda rota com o schema `ErroResponse`, e os testes de contrato conferem as respostas contra ele.

**Regra de ouro (NFR-SEG-06):** nenhuma resposta de erro expõe stack trace, nome de tabela ou versão de framework. O handler global captura `Exception`, registra o traceback no log estruturado e devolve payload genérico.

**Toda recusa por regra de negócio é registrada na auditoria** com `resultado = RECUSADO` e `regra_violada` preenchida (NFR-AUD-05, AC-021).


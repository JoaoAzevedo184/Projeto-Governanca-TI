# SPEC — Segurança

Parte de [SPEC — ITAM](README.md).

## 9. Segurança

### 9.1 Autenticação

- JWT HS256, `SECRET_KEY` obrigatoriamente via variável de ambiente (NFR-SEG-07);
- Claims: `sub` (id), `login`, `perfil`, `exp`, `iat`;
- Expiração padrão de 8 horas, configurável;
- Senha com BCrypt, custo ≥ 10 (NFR-SEG-03).

### 9.2 Autorização

```python
def require_perfil(*perfis: PerfilUsuario):
    def _verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfis:
            raise PermissaoNegadaError(perfil=usuario.perfil.value)
        return usuario
    return _verificar

@router.post("/ativos", dependencies=[Depends(require_perfil(ADMIN, OPERADOR))])
```

Nenhum perfil possui permissão de DELETE sobre registros de domínio (RI-06). A tabela completa está no FR-015 do PRD e deve ser coberta por teste parametrizado — um caso por célula da matriz (AC-055).

### 9.3 Outros controles

- Consultas exclusivamente via ORM ou `text()` com bind parameters (NFR-SEG-05);
- `chave_licenca` mascarada nas listagens (`****-****-A3F9`), completa apenas no detalhe e apenas para `ADMIN` (RI-08);
- CORS restrito por lista de origens configurável;
- `bandit` no pipeline, falhando o build em severidade alta.


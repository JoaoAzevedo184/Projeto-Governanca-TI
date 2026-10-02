"""Mascaramento da chave de licença (RI-08, docs/spec/seguranca.md §9.3).

Função pura. A chave completa só sai no detalhe e só para ADMIN; em listagens, e para os demais
perfis, sai mascarada (`****-****-A3F9`).
"""

from app.models.enums import PerfilUsuario


def mascarar_chave(chave: str) -> str:
    # O sufixo de 4 caracteres de uma chave curta revelaria quase tudo: abaixo de 8, mascara tudo.
    return f"****-****-{chave[-4:]}" if len(chave) >= 8 else "****-****-****"


def chave_para_perfil(chave: str | None, perfil: PerfilUsuario, *, detalhe: bool) -> str | None:
    if chave is None:
        return None
    if detalhe and perfil == PerfilUsuario.ADMIN:
        return chave
    return mascarar_chave(chave)

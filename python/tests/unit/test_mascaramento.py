"""Mascaramento da chave de licença (RI-08)."""

import pytest

from app.models.enums import PerfilUsuario
from app.utils.mascaramento import chave_para_perfil, mascarar_chave


def test_mascara_mostra_so_os_quatro_ultimos_caracteres():
    assert mascarar_chave("ABCD-1234-EFGH-A3F9") == "****-****-A3F9"


@pytest.mark.parametrize("chave", ["", "K", "ABCD", "K-SW1", "1234567"])
def test_chave_curta_demais_e_mascarada_por_inteiro(chave):
    assert mascarar_chave(chave) == "****-****-****"


def test_oito_caracteres_ja_mostram_so_o_sufixo():
    assert mascarar_chave("12345678") == "****-****-5678"


@pytest.mark.parametrize("perfil", list(PerfilUsuario))
@pytest.mark.parametrize("detalhe", [True, False])
def test_so_o_admin_no_detalhe_ve_a_chave_completa(perfil, detalhe):
    chave = chave_para_perfil("ABCD-1234-A3F9", perfil, detalhe=detalhe)

    esperado_completa = perfil == PerfilUsuario.ADMIN and detalhe
    assert chave == ("ABCD-1234-A3F9" if esperado_completa else "****-****-A3F9")


def test_chave_ausente_continua_ausente():
    assert chave_para_perfil(None, PerfilUsuario.ADMIN, detalhe=True) is None

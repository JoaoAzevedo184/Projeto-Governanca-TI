import io
import zipfile
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.importacao import ErroImportacao, LoteImportacao
from app.models.usuario import Usuario


def _total(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


def _csv(linhas: list[str]) -> bytes:
    return ("\n".join(linhas) + "\n").encode("utf-8")


def _importar(client, token, conteudo: bytes, nome_arquivo: str = "inventario.csv"):
    return client.post(
        "/api/v1/importacoes",
        headers={"Authorization": f"Bearer {token}"},
        files={"arquivo": (nome_arquivo, io.BytesIO(conteudo), "text/csv")},
    )


def test_ac044_importa_csv_com_linhas_invalidas(client, db, token_admin, categoria, fornecedor):
    cat, forn = categoria.nome, fornecedor.razao_social
    linhas = ["nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra"]
    for i in range(92):
        linhas.append(f"Notebook {i},HARDWARE,{cat},{forn},SN-{i:03d},2025-01-10,1000.00")
    for i in range(8):
        linhas.append(f"Sem serie {i},HARDWARE,{cat},{forn},,2025-01-10,1000.00")

    resposta = _importar(client, token_admin, _csv(linhas))
    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["total_processado"] == 100
    assert corpo["total_aceito"] == 92
    assert corpo["total_rejeitado"] == 8

    headers = {"Authorization": f"Bearer {token_admin}"}
    erros = client.get(f"/api/v1/importacoes/{corpo['lote_id']}/erros", headers=headers)
    assert erros.status_code == 200
    assert len(erros.json()) == 8
    assert _total(db, Ativo) == 92


def test_ac045_recusa_cabecalho_divergente_sem_processar_linhas(client, db, token_admin):
    resposta = _importar(client, token_admin, _csv(["coluna_errada,outra", "x,y"]))
    assert resposta.status_code == 422

    lotes = client.get("/api/v1/importacoes", headers={"Authorization": f"Bearer {token_admin}"})
    assert lotes.json() == []
    assert _total(db, LoteImportacao) == 0
    assert _total(db, Ativo) == 0


def test_ac046_rejeita_numero_serie_duplicado_dentro_do_arquivo(
    client, db, token_admin, categoria, fornecedor
):
    cat, forn = categoria.nome, fornecedor.razao_social
    linhas = [
        "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra",
        f"Notebook A,HARDWARE,{cat},{forn},SN-DUP,2025-01-10,1000.00",
        f"Notebook B,HARDWARE,{cat},{forn},SN-DUP,2025-01-10,1000.00",
    ]
    resposta = _importar(client, token_admin, _csv(linhas))
    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["total_aceito"] == 1
    assert corpo["total_rejeitado"] == 1
    assert db.execute(
        select(Ativo.nome, Ativo.data_source).where(Ativo.numero_serie == "SN-DUP")
    ).all() == [("Notebook A", "importacao")]


CABECALHO = "nome,tipo,categoria,fornecedor,numero_serie,chave_licenca,data_aquisicao,valor_compra"


def _linha(cat, forn, **campos):
    valores = {
        "nome": "Notebook Valido",
        "tipo": "HARDWARE",
        "categoria": cat.nome,
        "fornecedor": forn.razao_social,
        "numero_serie": "SN-LINHA",
        "chave_licenca": "",
        "data_aquisicao": "2025-01-10",
        "valor_compra": "1000.00",
        **campos,
    }
    return ",".join(valores[c] for c in CABECALHO.split(","))


@pytest.mark.parametrize(
    ("campos", "campo_erro", "motivo"),
    [
        ({"nome": "AB"}, "nome", "ao menos 3 caracteres"),
        ({"tipo": "IMPRESSORA"}, "tipo", "HARDWARE ou SOFTWARE"),
        ({"categoria": "Inexistente"}, "categoria", "Categoria não encontrada"),
        ({"fornecedor": "Inexistente"}, "fornecedor", "Fornecedor não encontrado"),
        ({"tipo": "SOFTWARE", "numero_serie": ""}, "chave_licenca", "BR-002"),
        ({"data_aquisicao": "2099-01-01"}, "data_aquisicao", "BR-003"),
        ({"data_aquisicao": "10/01/2025"}, "data_aquisicao", "AAAA-MM-DD"),
        ({"valor_compra": "0"}, "valor_compra", "BR-004"),
        ({"valor_compra": "mil reais"}, "valor_compra", "decimal inválido"),
    ],
)
def test_linha_invalida_e_rejeitada_com_campo_e_motivo(
    client, db, token_admin, categoria, fornecedor, campos, campo_erro, motivo
):
    conteudo = _csv([CABECALHO, _linha(categoria, fornecedor, **campos)])

    resposta = _importar(client, token_admin, conteudo)

    assert resposta.status_code == 202
    assert resposta.json()["total_aceito"] == 0
    erros = db.scalars(select(ErroImportacao)).all()
    assert [(e.numero_linha, e.campo) for e in erros] == [(2, campo_erro)]
    assert motivo in erros[0].motivo
    assert _total(db, Ativo) == 0


def test_rejeita_numero_serie_ja_cadastrado_na_base(client, db, token_admin, categoria, fornecedor):
    linha = _linha(categoria, fornecedor, numero_serie="SN-BASE")
    assert _importar(client, token_admin, _csv([CABECALHO, linha])).json()["total_aceito"] == 1

    segunda = _importar(client, token_admin, _csv([CABECALHO, linha])).json()

    assert (segunda["total_aceito"], segunda["total_rejeitado"]) == (0, 1)
    erro = db.scalars(select(ErroImportacao).where(ErroImportacao.lote_id == segunda["lote_id"]))
    assert "BR-001" in erro.one().motivo
    assert _total(db, Ativo) == 1


def test_importa_planilha_xlsx(client, db, token_admin, categoria, fornecedor):
    buffer = io.BytesIO()
    pd.DataFrame(
        [
            [
                "Notebook Xlsx",
                "HARDWARE",
                categoria.nome,
                fornecedor.razao_social,
                "SN-XLSX",
                "2025-01-10",
                "1500.00",
            ]
        ],
        columns=[
            "nome",
            "tipo",
            "categoria",
            "fornecedor",
            "numero_serie",
            "data_aquisicao",
            "valor_compra",
        ],
    ).to_excel(buffer, index=False)

    resposta = _importar(client, token_admin, buffer.getvalue(), "inventario.xlsx")

    assert resposta.status_code == 202
    ativo = db.scalars(select(Ativo)).one()
    assert (ativo.numero_serie, ativo.valor_compra) == ("SN-XLSX", Decimal("1500.00"))


def test_recusa_arquivo_acima_de_5_mb_sem_criar_lote(client, db, token_admin):
    conteudo = _csv([CABECALHO]) + b"x" * (5 * 1024 * 1024)

    resposta = _importar(client, token_admin, conteudo)

    assert resposta.status_code == 422
    assert "5 MB" in resposta.json()["detalhe"]
    assert _total(db, LoteImportacao) == 0


def test_recusa_arquivo_acima_de_5000_linhas_sem_criar_lote(
    client, db, token_admin, categoria, fornecedor
):
    linhas = [_linha(categoria, fornecedor, numero_serie=f"SN-{i}") for i in range(5001)]

    resposta = _importar(client, token_admin, _csv([CABECALHO, *linhas]))

    assert resposta.status_code == 422
    assert "5.000 linhas" in resposta.json()["detalhe"]
    assert _total(db, LoteImportacao) == 0
    assert _total(db, Ativo) == 0


_CSV_VALIDO = (CABECALHO + "\nNotebook,HARDWARE,Notebook,Dell,SN-1,2025-01-10,1000.00\n").encode()
_ZIP_SEM_PLANILHA = io.BytesIO()
with zipfile.ZipFile(_ZIP_SEM_PLANILHA, "w") as _zip:
    _zip.writestr("lixo.txt", "x")
_XLSX_VALIDO = io.BytesIO()
pd.DataFrame({"nome": ["a"]}).to_excel(_XLSX_VALIDO, index=False)

ARQUIVOS_RECUSADOS = [
    pytest.param("inventario.csv", b"", "vazio", id="csv-vazio"),
    pytest.param("inventario.csv", b"  \n\n", "vazio", id="csv-so-espacos"),
    pytest.param("inventario.xlsx", b"", "vazio", id="xlsx-vazio"),
    pytest.param("inventario.csv", bytes(range(128, 256)) * 4, "ilegível", id="csv-binario"),
    pytest.param("inventario.csv", "nome;ação\n".encode("latin-1"), "ilegível", id="csv-nao-utf8"),
    pytest.param("inventario.xlsx", _CSV_VALIDO, "ilegível", id="csv-com-extensao-xlsx"),
    pytest.param("inventario.xlsx", _XLSX_VALIDO.getvalue()[:100], "ilegível", id="xlsx-truncado"),
    pytest.param(
        "inventario.xlsx", _ZIP_SEM_PLANILHA.getvalue(), "ilegível", id="zip-sem-planilha"
    ),
    pytest.param("inventario.txt", _CSV_VALIDO, "Extensão", id="extensao-txt"),
    pytest.param("inventario.xls", _CSV_VALIDO, "Extensão", id="extensao-xls"),
    pytest.param("inventario", _CSV_VALIDO, "Extensão", id="sem-extensao"),
]


@pytest.mark.parametrize(("nome_arquivo", "conteudo", "trecho"), ARQUIVOS_RECUSADOS)
def test_recusa_arquivo_vazio_ou_ilegivel_sem_criar_lote(
    client, db, token_admin, nome_arquivo, conteudo, trecho
):
    resposta = _importar(client, token_admin, conteudo, nome_arquivo)

    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["tipo"] == "/erros/arquivo-invalido"
    assert trecho in corpo["detalhe"]
    assert _total(db, LoteImportacao) == 0
    assert _total(db, Ativo) == 0


def _auditoria(db, entidade: str) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).where(AuditLog.entidade == entidade)))


def test_ac057_importacao_audita_cada_ativo_criado_com_o_lote_de_origem(
    client, db, token_admin, categoria, fornecedor
):
    linhas = [
        _linha(categoria, fornecedor, nome="Notebook A", numero_serie="SN-A"),
        _linha(categoria, fornecedor, nome="Notebook B", numero_serie="SN-B"),
        _linha(categoria, fornecedor, nome="Notebook C", numero_serie="SN-C"),
        _linha(categoria, fornecedor, nome="Sem serie", numero_serie=""),
        _linha(categoria, fornecedor, nome="Valor zero", numero_serie="SN-Z", valor_compra="0"),
    ]

    resposta = _importar(client, token_admin, _csv([CABECALHO, *linhas]))

    assert resposta.status_code == 202
    lote_id = resposta.json()["lote_id"]
    autor = db.scalar(select(Usuario.id).where(Usuario.login == "admin_teste"))
    ativos = {a.numero_serie: a.id for a in db.scalars(select(Ativo))}
    assert set(ativos) == {"SN-A", "SN-B", "SN-C"}

    registros = _auditoria(db, "ativo")
    # Uma linha por ativo criado e nenhuma para as 2 linhas rejeitadas (3 e não 5).
    assert len(registros) == 3
    assert {r.entidade_id for r in registros} == set(ativos.values())
    for registro in registros:
        assert (registro.operacao, registro.resultado) == ("CRIAR", "SUCESSO")
        assert registro.regra_violada is None
        assert registro.usuario_id == autor
        assert registro.carimbo is not None
        assert registro.detalhe == {"lote_importacao_id": lote_id, "data_source": "importacao"}
    # Da auditoria chega-se ao lote e ao arquivo de origem.
    lote = db.get(LoteImportacao, registros[0].detalhe["lote_importacao_id"])
    assert (lote.nome_arquivo, lote.usuario_id) == ("inventario.csv", autor)


def test_ac057_importacao_audita_a_criacao_do_lote_com_os_totais(
    client, db, token_admin, categoria, fornecedor
):
    linhas = [
        _linha(categoria, fornecedor, numero_serie="SN-OK"),
        _linha(categoria, fornecedor, numero_serie="", nome="Sem serie"),
    ]

    lote_id = _importar(client, token_admin, _csv([CABECALHO, *linhas])).json()["lote_id"]

    autor = db.scalar(select(Usuario.id).where(Usuario.login == "admin_teste"))
    registro = _auditoria(db, "lote_importacao")
    assert len(registro) == 1
    assert (registro[0].operacao, registro[0].resultado) == ("CRIAR", "SUCESSO")
    assert (registro[0].entidade_id, registro[0].usuario_id) == (lote_id, autor)
    assert registro[0].detalhe == {
        "nome_arquivo": "inventario.csv",
        "total_processado": 2,
        "total_aceito": 1,
        "total_rejeitado": 1,
    }


def test_ac057_importacao_so_com_rejeicoes_audita_o_lote_e_nenhum_ativo(
    client, db, token_admin, categoria, fornecedor
):
    linhas = [
        _linha(categoria, fornecedor, numero_serie="", nome=f"Sem serie {i}") for i in range(2)
    ]

    resposta = _importar(client, token_admin, _csv([CABECALHO, *linhas]))

    assert resposta.status_code == 202
    assert resposta.json()["total_aceito"] == 0
    assert _total(db, Ativo) == 0
    assert _auditoria(db, "ativo") == []
    assert len(_auditoria(db, "lote_importacao")) == 1


def test_importacao_recusada_antes_de_processar_nao_grava_auditoria(client, db, token_admin):
    resposta = _importar(client, token_admin, _csv(["coluna_errada,outra", "x,y"]))

    assert resposta.status_code == 422
    assert _total(db, AuditLog) == 0


def test_ac067_importacao_rejeita_so_a_linha_com_chave_repetida_no_arquivo_ou_na_base(
    client, db, token_admin, categoria, fornecedor
):
    base = {
        "nome": "Suite Base",
        "tipo": "SOFTWARE",
        "categoria_id": categoria.id,
        "fornecedor_id": fornecedor.id,
        "chave_licenca": "BASE-1111-2222-ZZ99",
        "data_aquisicao": "2025-01-10",
        "valor_compra": "100.00",
    }
    headers = {"Authorization": f"Bearer {token_admin}"}
    assert client.post("/api/v1/ativos", headers=headers, json=base).status_code == 201

    def software(nome, chave):
        return _linha(
            categoria, fornecedor, nome=nome, tipo="SOFTWARE", numero_serie="", chave_licenca=chave
        )

    linhas = [
        software("Soft A", "NOVA-1111-2222-AA11"),
        software("Soft B", "NOVA-1111-2222-AA11"),  # repetida dentro do arquivo
        software("Soft C", "BASE-1111-2222-ZZ99"),  # já existe na base
        software("Soft D", "NOVA-3333-4444-DD44"),
    ]
    resposta = _importar(client, token_admin, _csv([CABECALHO, *linhas]))

    assert resposta.status_code == 202
    corpo = resposta.json()
    assert (corpo["total_processado"], corpo["total_aceito"], corpo["total_rejeitado"]) == (4, 2, 2)
    assert sorted(db.scalars(select(Ativo.nome))) == ["Soft A", "Soft D", "Suite Base"]
    erros = db.scalars(select(ErroImportacao).order_by(ErroImportacao.numero_linha)).all()
    assert [(e.numero_linha, e.campo) for e in erros] == [
        (3, "chave_licenca"),
        (4, "chave_licenca"),
    ]
    assert "dentro do próprio arquivo" in erros[0].motivo and "BR-039" in erros[0].motivo
    assert "cadastrada na base" in erros[1].motivo and "BR-039" in erros[1].motivo
    # RI-08: o relatório de erros guarda a chave mascarada, nunca a completa.
    assert [e.valor_recebido for e in erros] == ["****-****-AA11", "****-****-ZZ99"]
    relatorio = client.get(f"/api/v1/importacoes/{corpo['lote_id']}/erros", headers=headers)
    assert "NOVA-1111-2222-AA11" not in relatorio.text
    assert "BASE-1111-2222-ZZ99" not in relatorio.text


def test_ac067_importacao_aceita_varias_linhas_sem_chave(
    client, db, token_admin, categoria, fornecedor
):
    linhas = [_linha(categoria, fornecedor, numero_serie=f"SN-{i}") for i in range(3)]

    resposta = _importar(client, token_admin, _csv([CABECALHO, *linhas]))

    assert resposta.json()["total_aceito"] == 3
    assert db.scalar(select(func.count()).where(Ativo.chave_licenca.is_(None))) == 3


COLUNAS = [*CABECALHO.split(","), "localizacao"]
LIMITE_NOME = Ativo.__table__.c.nome.type.length
LIMITE_SERIE = Ativo.__table__.c.numero_serie.type.length
LIMITE_CHAVE = Ativo.__table__.c.chave_licenca.type.length
LIMITE_LOCALIZACAO = Ativo.__table__.c.localizacao.type.length
LIMITE_VALOR_RECEBIDO = ErroImportacao.__table__.c.valor_recebido.type.length
FORMATOS = pytest.mark.parametrize("formato", ["csv", "xlsx"])


def _arquivo(formato: str, linhas: list[dict], colunas=COLUNAS) -> tuple[bytes, str]:
    """CSV e XLSX com as mesmas linhas, tudo como texto (o importador lê tudo como texto)."""
    tabela = pd.DataFrame(linhas, columns=colunas, dtype=str).fillna("")
    if formato == "csv":
        return tabela.to_csv(index=False).encode("utf-8"), "inventario.csv"
    buffer = io.BytesIO()
    tabela.to_excel(buffer, index=False)
    return buffer.getvalue(), "inventario.xlsx"


def _linha_valida(cat, forn, serie, **campos):
    return {
        "nome": f"Notebook {serie}",
        "tipo": "HARDWARE",
        "categoria": cat.nome,
        "fornecedor": forn.razao_social,
        "numero_serie": serie,
        "chave_licenca": "",
        "data_aquisicao": "2025-01-10",
        "valor_compra": "1000.00",
        "localizacao": "",
        **campos,
    }


def _importar_formato(client, token, formato, linhas, colunas=COLUNAS):
    conteudo, nome = _arquivo(formato, linhas, colunas)
    return _importar(client, token, conteudo, nome)


def _erros(db, lote_id):
    consulta = select(ErroImportacao).where(ErroImportacao.lote_id == lote_id)
    return db.scalars(consulta.order_by(ErroImportacao.numero_linha, ErroImportacao.campo)).all()


@FORMATOS
def test_ac068_texto_maior_que_a_coluna_vira_erro_de_linha_e_o_lote_segue(
    client, db, token_admin, categoria, fornecedor, formato
):
    chave_longa = "K" * (LIMITE_CHAVE + 1)
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-OK-1"),
        _linha_valida(categoria, fornecedor, "SN-NOME", nome="N" * (LIMITE_NOME + 1)),
        _linha_valida(categoria, fornecedor, "S" * (LIMITE_SERIE + 1)),
        _linha_valida(
            categoria,
            fornecedor,
            "",
            nome="Licenca longa",
            tipo="SOFTWARE",
            chave_licenca=chave_longa,
        ),
        _linha_valida(
            categoria, fornecedor, "SN-LOCAL", localizacao="L" * (LIMITE_LOCALIZACAO + 1)
        ),
        _linha_valida(categoria, fornecedor, "SN-OK-2"),
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas)

    assert resposta.status_code == 202  # nem 422 do arquivo inteiro, nem 500
    corpo = resposta.json()
    assert (corpo["total_processado"], corpo["total_aceito"], corpo["total_rejeitado"]) == (6, 2, 4)
    assert sorted(db.scalars(select(Ativo.numero_serie))) == ["SN-OK-1", "SN-OK-2"]
    erros = _erros(db, corpo["lote_id"])
    assert [(e.numero_linha, e.campo) for e in erros] == [
        (3, "nome"),
        (4, "numero_serie"),
        (5, "chave_licenca"),
        (6, "localizacao"),
    ]
    limites = {
        "nome": LIMITE_NOME,
        "numero_serie": LIMITE_SERIE,
        "chave_licenca": LIMITE_CHAVE,
        "localizacao": LIMITE_LOCALIZACAO,
    }
    for erro in erros:
        assert str(limites[erro.campo]) in erro.motivo  # o limite vem da coluna do modelo
        assert len(erro.valor_recebido) <= LIMITE_VALOR_RECEBIDO
    # RI-08: a chave, mesmo recusada, não sai inteira no relatório.
    relatorio = client.get(
        f"/api/v1/importacoes/{corpo['lote_id']}/erros",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert chave_longa not in relatorio.text and chave_longa[:60] not in relatorio.text
    assert erros[2].valor_recebido == "****-****-" + chave_longa[-4:]


@FORMATOS
def test_ac068_texto_exatamente_no_limite_da_coluna_e_aceito(
    client, db, token_admin, categoria, fornecedor, formato
):
    linha = _linha_valida(
        categoria,
        fornecedor,
        "S" * LIMITE_SERIE,
        nome="N" * LIMITE_NOME,
        localizacao="L" * LIMITE_LOCALIZACAO,
    )
    software = _linha_valida(
        categoria, fornecedor, "", tipo="SOFTWARE", chave_licenca="K" * LIMITE_CHAVE
    )

    resposta = _importar_formato(client, token_admin, formato, [linha, software])

    assert (resposta.status_code, resposta.json()["total_aceito"]) == (202, 2)
    gravado = db.scalar(select(Ativo).where(Ativo.numero_serie == "S" * LIMITE_SERIE))
    assert len(gravado.nome) == LIMITE_NOME and len(gravado.localizacao) == LIMITE_LOCALIZACAO


@FORMATOS
def test_ac068_valor_do_relatorio_de_erros_e_cortado_no_tamanho_da_coluna(
    client, db, token_admin, categoria, fornecedor, formato
):
    """O valor recebido de qualquer campo inválido cabe no relatório: antes, um `tipo` ou uma
    categoria de 400 caracteres estourava `erro_importacao.valor_recebido` e derrubava o lote."""
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-OK"),
        _linha_valida(categoria, fornecedor, "SN-TIPO", tipo="T" * 400),
        _linha_valida(categoria, fornecedor, "SN-CAT", categoria="C" * 400),
        _linha_valida(categoria, fornecedor, "SN-FORN", fornecedor="F" * 400),
        _linha_valida(categoria, fornecedor, "SN-DATA", data_aquisicao="9" * 400),
        _linha_valida(categoria, fornecedor, "SN-VALOR", valor_compra="9" * 400),
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas)

    assert (resposta.status_code, resposta.json()["total_aceito"]) == (202, 1)
    erros = _erros(db, resposta.json()["lote_id"])
    assert [(e.numero_linha, e.campo) for e in erros] == [
        (3, "tipo"),
        (4, "categoria"),
        (5, "fornecedor"),
        (6, "data_aquisicao"),
        (7, "valor_compra"),
    ]
    assert {len(e.valor_recebido) for e in erros} == {LIMITE_VALOR_RECEBIDO}


@FORMATOS
def test_ac069_valor_fora_do_que_a_coluna_comporta_vira_erro_de_linha_e_o_lote_segue(
    client, db, token_admin, categoria, fornecedor, formato
):
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-OK"),
        _linha_valida(categoria, fornecedor, "SN-11", valor_compra="99999999999.99"),
        _linha_valida(categoria, fornecedor, "SN-EXP", valor_compra="1E+30"),
        _linha_valida(categoria, fornecedor, "SN-INF", valor_compra="Infinity"),
        _linha_valida(categoria, fornecedor, "SN-3CASAS", valor_compra="442.584"),
        _linha_valida(categoria, fornecedor, "SN-MICRO", valor_compra="0.001"),
        _linha_valida(categoria, fornecedor, "SN-LIMITE", valor_compra="9999999999.99"),
        _linha_valida(categoria, fornecedor, "SN-ZERO-FINAL", valor_compra="442.580"),
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas)

    assert resposta.status_code == 202  # nem 422 do arquivo inteiro, nem 500
    corpo = resposta.json()
    assert (corpo["total_processado"], corpo["total_aceito"], corpo["total_rejeitado"]) == (8, 3, 5)
    valores = dict(db.execute(select(Ativo.numero_serie, Ativo.valor_compra)).all())
    # escrito à mão: 442.580 vale 442.58 sem perder nada, então não é arredondamento
    assert valores == {
        "SN-OK": Decimal("1000.00"),
        "SN-LIMITE": Decimal("9999999999.99"),
        "SN-ZERO-FINAL": Decimal("442.58"),
    }
    erros = _erros(db, corpo["lote_id"])
    assert [(e.numero_linha, e.campo) for e in erros] == [(3, "valor_compra")] + [
        (n, "valor_compra") for n in (4, 5, 6, 7)
    ]
    motivos = {e.numero_linha: e.motivo for e in erros}
    assert "10 dígitos inteiros" in motivos[3] and "10 dígitos inteiros" in motivos[4]
    assert "inválido" in motivos[5]
    assert "2 casas decimais" in motivos[6] and "2 casas decimais" in motivos[7]
    assert [e.valor_recebido for e in erros if e.numero_linha == 6] == ["442.584"]


@FORMATOS
def test_ac068_ac069_uma_linha_invalida_de_cada_tipo_importa_as_validas_e_relata_cada_erro(
    client, db, token_admin, categoria, fornecedor, formato
):
    """Critério do bloco: 1 linha de cada tipo + N válidas: N importadas, cada erro com linha e
    campo, e nenhuma resposta 422/500 para o arquivo."""
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-A"),
        _linha_valida(categoria, fornecedor, "SN-NOME", nome="N" * (LIMITE_NOME + 1)),
        _linha_valida(categoria, fornecedor, "SN-B"),
        _linha_valida(categoria, fornecedor, "S" * (LIMITE_SERIE + 1)),
        _linha_valida(categoria, fornecedor, "SN-C"),
        _linha_valida(
            categoria, fornecedor, "", tipo="SOFTWARE", chave_licenca="K" * (LIMITE_CHAVE + 1)
        ),
        _linha_valida(categoria, fornecedor, "SN-D", localizacao="L" * (LIMITE_LOCALIZACAO + 1)),
        _linha_valida(categoria, fornecedor, "SN-INT", valor_compra="12345678901.00"),
        _linha_valida(categoria, fornecedor, "SN-DEC", valor_compra="1.001"),
        _linha_valida(categoria, fornecedor, "SN-E"),
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas)

    assert resposta.status_code == 202
    corpo = resposta.json()
    assert (corpo["total_aceito"], corpo["total_rejeitado"]) == (4, 6)
    erros = _erros(db, corpo["lote_id"])
    assert [(e.numero_linha, e.campo) for e in erros] == [
        (3, "nome"),
        (5, "numero_serie"),
        (7, "chave_licenca"),
        (8, "localizacao"),
        (9, "valor_compra"),
        (10, "valor_compra"),
    ]
    assert sorted(db.scalars(select(Ativo.numero_serie))) == ["SN-A", "SN-B", "SN-C", "SN-E"]


COLUNAS_COM_ORIGEM = [*COLUNAS, "data_source"]


def _origens(db):
    return dict(db.execute(select(Ativo.numero_serie, Ativo.data_source)).all())


@FORMATOS
def test_ac071_arquivo_sem_a_coluna_data_source_grava_importacao(
    client, db, token_admin, categoria, fornecedor, formato
):
    linhas = [_linha_valida(categoria, fornecedor, f"SN-{i}") for i in range(3)]

    resposta = _importar_formato(client, token_admin, formato, linhas)

    assert resposta.json()["total_aceito"] == 3
    assert set(_origens(db).values()) == {"importacao"}


@FORMATOS
def test_ac071_data_source_da_linha_vale_e_a_vazia_cai_em_importacao(
    client, db, token_admin, categoria, fornecedor, formato
):
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-CG", data_source="compras_gov"),
        _linha_valida(categoria, fornecedor, "SN-VAZIO", data_source=""),
        _linha_valida(categoria, fornecedor, "SN-IMP", data_source="importacao"),
        _linha_valida(categoria, fornecedor, "SN-NORM", data_source="  Compras_GOV "),
        _linha_valida(categoria, fornecedor, "SN-AUSENTE"),  # sem o campo na linha
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas, COLUNAS_COM_ORIGEM)

    assert (resposta.status_code, resposta.json()["total_aceito"]) == (202, 5)
    assert _origens(db) == {
        "SN-CG": "compras_gov",
        "SN-VAZIO": "importacao",
        "SN-IMP": "importacao",
        "SN-NORM": "compras_gov",  # mesma normalização do `tipo`: espaços e maiúsculas
        "SN-AUSENTE": "importacao",
    }
    # A auditoria de cada ativo diz a origem gravada, a mesma que está no ativo.
    auditoria = {
        a.entidade_id: a.detalhe["data_source"]
        for a in db.scalars(select(AuditLog).where(AuditLog.entidade == "ativo"))
    }
    ids = dict(db.execute(select(Ativo.id, Ativo.data_source)).all())
    assert auditoria == ids and set(ids.values()) == {"compras_gov", "importacao"}


@FORMATOS
def test_ac071_data_source_fora_da_lista_e_erro_de_linha_e_o_lote_segue(
    client, db, token_admin, categoria, fornecedor, formato
):
    linhas = [
        _linha_valida(categoria, fornecedor, "SN-OK", data_source="compras_gov"),
        _linha_valida(categoria, fornecedor, "SN-MANUAL", data_source="manual"),
        _linha_valida(categoria, fornecedor, "SN-NVD", data_source="nvd"),
        _linha_valida(categoria, fornecedor, "SN-LONGO", data_source="x" * 400),
        _linha_valida(categoria, fornecedor, "SN-OK-2"),
    ]

    resposta = _importar_formato(client, token_admin, formato, linhas, COLUNAS_COM_ORIGEM)

    assert resposta.status_code == 202  # nem 422 do arquivo inteiro, nem 500
    corpo = resposta.json()
    assert (corpo["total_aceito"], corpo["total_rejeitado"]) == (2, 3)
    assert sorted(_origens(db)) == ["SN-OK", "SN-OK-2"]
    erros = _erros(db, corpo["lote_id"])
    assert [(e.numero_linha, e.campo) for e in erros] == [
        (3, "data_source"),
        (4, "data_source"),
        (5, "data_source"),
    ]
    assert [e.valor_recebido for e in erros][:2] == ["manual", "nvd"]
    assert len(erros[2].valor_recebido) == LIMITE_VALOR_RECEBIDO
    assert "compras_gov" in erros[0].motivo and "importacao" in erros[0].motivo

import io
import zipfile
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.models.ativo import Ativo
from app.models.importacao import ErroImportacao, LoteImportacao


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

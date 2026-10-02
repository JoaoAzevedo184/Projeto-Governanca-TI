from sqlalchemy import func, select

from app.models.auditoria import AuditLog
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.responsavel import Responsavel
from app.models.setor import Setor


def _cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def _total(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


# ---------------------------------------------------------------- categoria


def test_cria_e_lista_categoria(client, token_admin):
    payload = {"nome": "Servidor", "vida_util_meses": 60, "tipo_aplicavel": "HARDWARE"}
    criada = client.post("/api/v1/categorias", headers=_cabecalho(token_admin), json=payload)
    assert criada.status_code == 201
    assert criada.json()["nome"] == "Servidor"

    listadas = client.get("/api/v1/categorias", headers=_cabecalho(token_admin))
    assert any(c["nome"] == "Servidor" for c in listadas.json())


def test_recusa_categoria_com_nome_duplicado(client, db, token_admin, categoria):
    payload = {"nome": categoria.nome, "vida_util_meses": 60, "tipo_aplicavel": "HARDWARE"}
    resposta = client.post("/api/v1/categorias", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 409
    assert _total(db, Categoria) == 1


def test_recusa_categoria_com_vida_util_zero(client, db, token_admin):
    payload = {"nome": "Categoria Invalida", "vida_util_meses": 0, "tipo_aplicavel": "HARDWARE"}
    resposta = client.post("/api/v1/categorias", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 422
    assert _total(db, Categoria) == 0


def test_obtem_categoria_inexistente_retorna_404(client, token_admin):
    resposta = client.get("/api/v1/categorias/9999", headers=_cabecalho(token_admin))
    assert resposta.status_code == 404


def test_atualiza_categoria_existente(client, db, token_admin, categoria):
    resposta = client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=_cabecalho(token_admin),
        json={"descricao": "Atualizada"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Atualizada"
    db.refresh(categoria)
    assert categoria.descricao == "Atualizada"


def test_atualiza_categoria_inexistente_retorna_404(client, token_admin):
    resposta = client.patch(
        "/api/v1/categorias/9999", headers=_cabecalho(token_admin), json={"descricao": "x"}
    )
    assert resposta.status_code == 404


def test_ac057_registra_auditoria_ao_criar_categoria(client, db, token_admin):
    payload = {"nome": "Impressora", "vida_util_meses": 48, "tipo_aplicavel": "HARDWARE"}
    resposta = client.post("/api/v1/categorias", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "categoria").first()
    assert registro is not None
    assert registro.operacao == "CRIAR"


def test_ac057_registra_auditoria_ao_atualizar_categoria(client, db, token_admin, categoria):
    resposta = client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=_cabecalho(token_admin),
        json={"descricao": "Atualizada"},
    )
    assert resposta.status_code == 200

    registro = (
        db.query(AuditLog)
        .filter(AuditLog.entidade == "categoria", AuditLog.operacao == "ATUALIZAR")
        .first()
    )
    assert registro is not None


# --------------------------------------------------------------- fornecedor


def test_cria_e_lista_fornecedor(client, token_admin):
    payload = {"razao_social": "Fornecedor Novo LTDA"}
    criado = client.post("/api/v1/fornecedores", headers=_cabecalho(token_admin), json=payload)
    assert criado.status_code == 201

    listados = client.get("/api/v1/fornecedores", headers=_cabecalho(token_admin))
    assert any(f["razao_social"] == "Fornecedor Novo LTDA" for f in listados.json())


def test_recusa_fornecedor_com_cnpj_duplicado(client, db, token_admin):
    headers = _cabecalho(token_admin)
    payload = {"razao_social": "Fornecedor A", "cnpj": "00.000.000/0001-00"}
    assert client.post("/api/v1/fornecedores", headers=headers, json=payload).status_code == 201

    payload_duplicado = {"razao_social": "Fornecedor B", "cnpj": "00.000.000/0001-00"}
    resposta = client.post("/api/v1/fornecedores", headers=headers, json=payload_duplicado)
    assert resposta.status_code == 409
    assert _total(db, Fornecedor) == 1


def test_ac057_registra_auditoria_ao_criar_fornecedor(client, db, token_admin):
    payload = {"razao_social": "Fornecedor Auditado"}
    resposta = client.post("/api/v1/fornecedores", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "fornecedor").first()
    assert registro is not None
    assert registro.operacao == "CRIAR"


# -------------------------------------------------------------------- setor


def test_cria_e_lista_setor(client, token_admin):
    payload = {"nome": "TI"}
    criado = client.post("/api/v1/setores", headers=_cabecalho(token_admin), json=payload)
    assert criado.status_code == 201

    listados = client.get("/api/v1/setores", headers=_cabecalho(token_admin))
    assert any(s["nome"] == "TI" for s in listados.json())


def test_recusa_setor_com_nome_duplicado(client, db, token_admin):
    headers = _cabecalho(token_admin)
    payload = {"nome": "Financeiro"}
    assert client.post("/api/v1/setores", headers=headers, json=payload).status_code == 201

    resposta = client.post("/api/v1/setores", headers=headers, json=payload)
    assert resposta.status_code == 409
    assert _total(db, Setor) == 1


def test_ac057_registra_auditoria_ao_criar_setor(client, db, token_admin):
    payload = {"nome": "Compras"}
    resposta = client.post("/api/v1/setores", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "setor").first()
    assert registro is not None
    assert registro.operacao == "CRIAR"


# -------------------------------------------------------------- responsavel


def test_cria_e_lista_responsavel(client, token_admin):
    payload = {"nome": "Maria Souza"}
    criado = client.post("/api/v1/responsaveis", headers=_cabecalho(token_admin), json=payload)
    assert criado.status_code == 201
    assert criado.json()["data_source"] == "sintetico"

    listados = client.get("/api/v1/responsaveis", headers=_cabecalho(token_admin))
    assert any(r["nome"] == "Maria Souza" for r in listados.json())


def test_recusa_responsavel_com_matricula_duplicada(client, db, token_admin):
    headers = _cabecalho(token_admin)
    payload = {"nome": "Joao Silva", "matricula": "MAT-001"}
    assert client.post("/api/v1/responsaveis", headers=headers, json=payload).status_code == 201

    payload_duplicado = {"nome": "Outro Nome", "matricula": "MAT-001"}
    resposta = client.post("/api/v1/responsaveis", headers=headers, json=payload_duplicado)
    assert resposta.status_code == 409
    assert _total(db, Responsavel) == 1


def test_ac057_registra_auditoria_ao_criar_responsavel(client, db, token_admin):
    payload = {"nome": "Ana Costa"}
    resposta = client.post("/api/v1/responsaveis", headers=_cabecalho(token_admin), json=payload)
    assert resposta.status_code == 201

    registro = db.query(AuditLog).filter(AuditLog.entidade == "responsavel").first()
    assert registro is not None
    assert registro.operacao == "CRIAR"

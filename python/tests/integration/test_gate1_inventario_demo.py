"""Gate 1 (D.2): o arquivo `dataset/demo/inventario_demo.csv` importa com 100 linhas processadas,
92 aceitas e 8 rejeitadas, de verdade, pelo fluxo da demonstração: seed, fornecedores, importação.

Sem mock de banco, de API ou do importador. O arquivo e os fornecedores são os versionados em
`dataset/demo/`.
"""

import io
from pathlib import Path

from sqlalchemy import func, select

from app import seed
from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.fornecedor import Fornecedor
from app.models.importacao import ErroImportacao
from etl import carregar_fornecedores

ARQUIVO = Path(__file__).resolve().parents[3] / "dataset" / "demo" / "inventario_demo.csv"
SENHAS = {"admin": "s-admin", "operador": "s-oper", "gestor": "s-gest", "auditor": "s-audit"}

# (numero_linha, campo, trecho do motivo): a tabela das 8 inválidas do LEIAME, escrita à mão.
RELATORIO_ESPERADO = [
    (7, "nome", "ao menos 3 caracteres"),
    (18, "tipo", "HARDWARE ou SOFTWARE"),
    (31, "categoria", "Categoria não encontrada"),
    (46, "fornecedor", "Fornecedor não encontrado"),
    (58, "numero_serie", "Obrigatório para ativos do tipo HARDWARE (BR-002)"),
    (71, "numero_serie", "Duplicado dentro do próprio arquivo (AC-046)"),
    (84, "data_aquisicao", "Não pode ser futura (BR-003)"),
    (97, "valor_compra", "Deve ser maior que zero (BR-004)"),
]


def _importar_arquivo_do_gate(client, db):
    seed.semear(db, SENHAS)
    carga = carregar_fornecedores.carregar(
        client, "admin", SENHAS["admin"], carregar_fornecedores.ler_fornecedores()
    )
    token = client.post(
        "/api/v1/auth/login", json={"login": "admin", "senha": SENHAS["admin"]}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resposta = client.post(
        "/api/v1/importacoes",
        headers=headers,
        files={"arquivo": ("inventario_demo.csv", io.BytesIO(ARQUIVO.read_bytes()), "text/csv")},
    )
    return carga, resposta, headers


def test_gate1_importa_100_linhas_92_aceitas_e_8_rejeitadas(client, db):
    carga, resposta, headers = _importar_arquivo_do_gate(client, db)

    assert len(carga.criados) == 17 and carga.existentes == []
    assert resposta.status_code == 202
    corpo = resposta.json()
    assert (corpo["total_processado"], corpo["total_aceito"], corpo["total_rejeitado"]) == (
        100,
        92,
        8,
    )
    # relatório de erros linha a linha: linha e campo exatos, um erro por linha rejeitada
    erros = db.scalars(
        select(ErroImportacao)
        .where(ErroImportacao.lote_id == corpo["lote_id"])
        .order_by(ErroImportacao.numero_linha)
    ).all()
    assert [(e.numero_linha, e.campo) for e in erros] == [(n, c) for n, c, _ in RELATORIO_ESPERADO]
    for erro, (_, _, trecho) in zip(erros, RELATORIO_ESPERADO, strict=True):
        assert trecho in erro.motivo
    assert erros[-2].valor_recebido == "2099-12-31" and erros[-1].valor_recebido == "0"
    relatorio = client.get(f"/api/v1/importacoes/{corpo['lote_id']}/erros", headers=headers)
    assert [(e["numero_linha"], e["campo"]) for e in relatorio.json()] == [
        (n, c) for n, c, _ in RELATORIO_ESPERADO
    ]


def test_gate1_92_ativos_compras_gov_e_93_linhas_de_auditoria(client, db):
    _, resposta, _ = _importar_arquivo_do_gate(client, db)
    lote_id = resposta.json()["lote_id"]

    origens = db.execute(select(Ativo.data_source, func.count()).group_by(Ativo.data_source)).all()
    assert origens == [("compras_gov", 92)]
    assert db.scalar(select(func.count()).where(Ativo.lote_importacao_id == lote_id)) == 92
    # 92 ativos + 1 lote (o seed e os fornecedores têm as suas próprias linhas)
    por_entidade = dict(
        db.execute(
            select(AuditLog.entidade, func.count())
            .where(AuditLog.entidade.in_(["ativo", "lote_importacao"]))
            .group_by(AuditLog.entidade)
        ).all()
    )
    assert por_entidade == {"ativo": 92, "lote_importacao": 1}
    assert sum(por_entidade.values()) == 93
    detalhes = db.scalars(select(AuditLog.detalhe).where(AuditLog.entidade == "ativo")).all()
    assert {d["data_source"] for d in detalhes} == {"compras_gov"}
    assert {d["lote_importacao_id"] for d in detalhes} == {lote_id}


def test_gate1_os_fornecedores_e_as_linhas_validas_sao_do_compras_gov(client, db):
    _importar_arquivo_do_gate(client, db)

    assert db.execute(
        select(Fornecedor.data_source, func.count()).group_by(Fornecedor.data_source)
    ).all() == [("compras_gov", 17)]
    ativos = db.scalars(select(Ativo)).all()
    assert len({a.numero_serie for a in ativos}) == 92
    assert all(a.numero_serie.startswith("CG-") and a.numero_serie.endswith("-001") for a in ativos)
    assert {a.tipo for a in ativos} == {"HARDWARE"}
    assert len({a.categoria.nome for a in ativos}) == 8  # os 9 PDMs caem em 8 categorias do seed


def test_gate1_rodar_o_fluxo_de_novo_rejeita_as_92_por_serie_ja_cadastrada(client, db):
    _, primeira, headers = _importar_arquivo_do_gate(client, db)

    segunda = client.post(
        "/api/v1/importacoes",
        headers=headers,
        files={"arquivo": ("inventario_demo.csv", io.BytesIO(ARQUIVO.read_bytes()), "text/csv")},
    )

    assert primeira.json()["total_aceito"] == 92
    corpo = segunda.json()
    assert (corpo["total_aceito"], corpo["total_rejeitado"]) == (0, 100)
    assert db.scalar(select(func.count()).select_from(Ativo)) == 92  # nada duplicado

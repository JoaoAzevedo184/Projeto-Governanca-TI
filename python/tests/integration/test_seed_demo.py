"""Seed de demonstração dos Gates 2 e 3 (`app/seed_demo.py`).

Parte de um banco com o seed básico, os fornecedores e os 92 ativos de
`dataset/demo/inventario_demo.csv` importados pelo fluxo real da demonstração, e confere o que o
seed cria: contagens, origem `sintetico`, auditoria, histórico de transferências, o AC-015, a
licença em 50 de 50 com o 51º vínculo recusado, os alertas e a idempotência.
"""

import io
import os
import subprocess
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select, text

from app import seed, seed_demo
from app.core.exceptions import RegraNegocioError
from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.baixa import BaixaAtivo
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.historico import HistoricoTransferencia
from app.models.licenca import Licenca, LicencaVinculo
from app.models.responsavel import Responsavel
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.licenca import VinculoLicencaCreate
from app.services import compliance_service, licenca_service
from app.services.depreciacao_service import calcular_para_ativo
from app.utils.datas import hoje
from app.utils.depreciacao import meses_entre
from etl import carregar_fornecedores

ARQUIVO = Path(__file__).resolve().parents[3] / "dataset" / "demo" / "inventario_demo.csv"
SENHAS = {"admin": "s-admin", "operador": "s-oper", "gestor": "s-gest", "auditor": "s-audit"}
ESPERADO = {
    "setores": 3,
    "responsaveis": 6,
    "fornecedores": 1,
    "ativos_demo": 4,
    "vinculos_responsavel": 95,  # 89 reais + 4 do ativo das transferências + AC-015 + software
    "licencas": 3,
    "vinculos_licenca": 50,
    "baixas": 1,
}


def _importar_demonstracao(client, db):
    """O fluxo real da demonstração: seed básico, fornecedores e importação do arquivo do Gate 1."""
    seed.semear(db, SENHAS)
    carregar_fornecedores.carregar(
        client, "admin", SENHAS["admin"], carregar_fornecedores.ler_fornecedores()
    )
    token = client.post(
        "/api/v1/auth/login", json={"login": "admin", "senha": SENHAS["admin"]}
    ).json()["access_token"]
    resposta = client.post(
        "/api/v1/importacoes",
        headers={"Authorization": f"Bearer {token}"},
        files={"arquivo": ("inventario_demo.csv", io.BytesIO(ARQUIVO.read_bytes()), "text/csv")},
    )
    assert resposta.json()["total_aceito"] == 92
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def importado(client, db):
    """Seed básico, fornecedores e os 92 ativos importados; o `seed_demo` ainda não rodou."""
    return _importar_demonstracao(client, db)


@pytest.fixture
def cenario(importado, db):
    reais = [
        (a.numero_serie, a.nome, a.valor_compra, a.status, a.data_source)
        for a in db.scalars(select(Ativo).order_by(Ativo.id))
    ]
    criados = seed_demo.semear_demo(db)
    return {"headers": importado, "criados": criados, "reais_antes": reais}


def _contar(db, modelo, *condicoes) -> int:
    return db.scalar(select(func.count()).select_from(modelo).where(*condicoes))


def _ativo(db, serie=None, chave=None) -> Ativo:
    condicao = Ativo.numero_serie == serie if serie else Ativo.chave_licenca == chave
    return db.scalars(select(Ativo).where(condicao)).one()


def _reais_por_serie(db) -> list[Ativo]:
    consulta = select(Ativo).where(Ativo.data_source == "compras_gov").order_by(Ativo.numero_serie)
    return list(db.scalars(consulta))


def test_cria_a_quantidade_certa_de_cada_tipo_e_tudo_como_sintetico(cenario, db):
    assert cenario["criados"] == ESPERADO

    assert _contar(db, Setor, Setor.nome.like("DEMO-%")) == 3 and _contar(db, Setor) == 3
    responsaveis = db.scalars(select(Responsavel)).all()
    assert len(responsaveis) == 6
    assert {r.data_source for r in responsaveis} == {"sintetico"}
    assert all(r.matricula.startswith("DEMO-") for r in responsaveis)
    assert all(r.email.endswith("@demo.invalid") for r in responsaveis)
    demo = db.scalars(select(Ativo).where(Ativo.data_source == "sintetico")).all()
    assert len(demo) == 4 and all(a.nome.startswith("DEMO-") for a in demo)
    assert _contar(db, Fornecedor, Fornecedor.data_source == "sintetico") == 1
    licencas = db.scalars(select(Licenca)).all()
    assert len(licencas) == 3 and {lic.data_source for lic in licencas} == {"sintetico"}
    assert all(lic.chave_licenca.startswith("DEMO-") for lic in licencas)
    assert _contar(db, LicencaVinculo) == 50
    assert _contar(db, LicencaVinculo, LicencaVinculo.data_source == "sintetico") == 50
    assert _contar(db, BaixaAtivo, BaixaAtivo.data_source == "sintetico") == 1
    assert _contar(db, HistoricoTransferencia) == 95
    assert (
        _contar(db, HistoricoTransferencia, HistoricoTransferencia.data_source == "sintetico") == 95
    )


def test_os_92_ativos_reais_seguem_compras_gov_e_nada_neles_mudou(cenario, db):
    assert _contar(db, Ativo, Ativo.data_source == "compras_gov") == 92
    depois = [
        (a.numero_serie, a.nome, a.valor_compra, a.status, a.data_source)
        for a in db.scalars(select(Ativo).where(Ativo.id <= 92).order_by(Ativo.id))
    ]
    assert depois == cenario["reais_antes"]
    # 89 dos 92 receberam responsável; os outros 3 ficam sem, de propósito
    reais = _reais_por_serie(db)
    com_vinculo = [
        _contar(db, HistoricoTransferencia, HistoricoTransferencia.ativo_id == a.id) for a in reais
    ]
    assert [i for i, n in enumerate(com_vinculo) if n == 0] == [7, 41, 77]
    assert all(n == 1 for n in com_vinculo if n)


def test_cada_escrita_do_seed_tem_linha_na_auditoria(cenario, db):
    tabelas = {
        "setor": Setor,
        "responsavel": Responsavel,
        "fornecedor": Fornecedor,
        "ativo": Ativo,
        "licenca": Licenca,
        "licenca_vinculo": LicencaVinculo,
        "historico_transferencia": HistoricoTransferencia,
        "baixa_ativo": BaixaAtivo,
    }
    for entidade, modelo in tabelas.items():
        auditados = set(
            db.scalars(
                select(AuditLog.entidade_id).where(
                    AuditLog.entidade == entidade,
                    AuditLog.operacao == "CRIAR",
                    AuditLog.resultado == "SUCESSO",
                )
            )
        )
        ids = set(db.scalars(select(modelo.id)))
        assert ids <= auditados, f"{entidade}: registros sem auditoria {sorted(ids - auditados)}"
    sem_autor = db.scalars(select(AuditLog.id).where(AuditLog.usuario_id.is_(None))).all()
    # as linhas sem autor são só as do seed básico (usuários e categorias), nunca as do seed demo
    assert len(sem_autor) == 4 + 11


def test_gate2_historico_com_atribuicao_inicial_e_tres_transferencias(cenario, db, client):
    ativo = _ativo(db, serie=seed_demo.SERIE_TRANSFERENCIAS)

    vinculos = db.scalars(
        select(HistoricoTransferencia)
        .where(HistoricoTransferencia.ativo_id == ativo.id)
        .order_by(HistoricoTransferencia.data_inicio)
    ).all()

    assert len(vinculos) == 4
    inicios = [v.data_inicio for v in vinculos]
    assert inicios == sorted(set(inicios)) and inicios[0] > ativo.data_aquisicao
    for anterior, seguinte in zip(vinculos, vinculos[1:], strict=False):
        assert anterior.data_fim == seguinte.data_inicio  # encerrado na transferência, sem sobrepor
    assert [v.data_fim for v in vinculos[:-1]] == inicios[1:]
    assert vinculos[-1].data_fim is None  # só o último está aberto
    assert len({v.responsavel_id for v in vinculos}) == 4
    assert inicios[-1] <= hoje()
    historico = client.get(f"/api/v1/ativos/{ativo.id}/historico", headers=cenario["headers"])
    # a rota devolve do mais recente ao mais antigo (AC-012)
    assert [h["data_inicio"] for h in historico.json()] == [
        i.isoformat() for i in reversed(inicios)
    ]


def test_gate2_depreciacao_do_ac015_residual_de_4800(cenario, db, client):
    ativo = _ativo(db, serie=seed_demo.SERIE_AC015)

    resultado = calcular_para_ativo(ativo, hoje())

    # R$ 6.000,00 x 12 / 60 = R$ 1.200,00 depreciados; 6.000,00 - 1.200,00 = R$ 4.800,00
    assert (ativo.valor_compra, ativo.vida_util_meses) == (Decimal("6000.00"), 60)
    assert resultado.meses_decorridos == 12
    assert resultado.depreciacao_acumulada == Decimal("1200.00")
    assert resultado.valor_residual == Decimal("4800.00")
    resposta = client.get(f"/api/v1/ativos/{ativo.id}/depreciacao", headers=cenario["headers"])
    assert resposta.json()["valor_residual"] == "4800.00"


def test_gate3_licenca_em_50_de_50_e_o_51o_vinculo_e_recusado_com_br018(cenario, db):
    licenca = db.scalars(
        select(Licenca).where(Licenca.chave_licenca == seed_demo.CHAVE_LICENCA_50)
    ).one()
    assert licenca.quantidade_contratada == 50
    assert licenca_service.contar_em_uso(db, [licenca.id])[licenca.id] == 50
    maquinas = [a for a in _reais_por_serie(db) if a.tipo == "HARDWARE"]
    vinculadas = set(db.scalars(select(LicencaVinculo.ativo_id)))
    assert vinculadas == {m.id for m in maquinas[:50]}
    admin = db.scalar(select(Usuario).where(Usuario.login == "admin"))
    cinquenta_e_um = maquinas[50]  # a máquina do guia de demonstração

    with pytest.raises(RegraNegocioError) as erro:
        licenca_service.vincular(
            db, licenca.id, VinculoLicencaCreate(ativo_id=cinquenta_e_um.id), admin
        )

    assert erro.value.regra == "BR-018"
    recusa = db.scalars(
        select(AuditLog).where(
            AuditLog.resultado == "RECUSADO", AuditLog.entidade == "licenca_vinculo"
        )
    ).one()
    assert (recusa.operacao, recusa.regra_violada) == ("CRIAR", "BR-018")
    assert _contar(db, LicencaVinculo) == 50  # nada foi criado


def test_gate3_alertas_licenca_vencida_licenca_a_vencer_e_exatamente_3_ativos_sem_responsavel(
    cenario, db
):
    alertas = compliance_service.apurar_alertas(db, hoje())

    por_codigo = {}
    for alerta in alertas:
        por_codigo.setdefault(alerta.codigo, []).append(alerta)
    assert set(por_codigo) == {"CP-01", "CP-03", "CP-04"}  # a de 50 de 50 não dispara nada
    (vencida,) = por_codigo["CP-01"]
    assert (vencida.severidade, vencida.recurso) == ("CRITICO", "DEMO-Antivírus corporativo")
    (a_vencer,) = por_codigo["CP-03"]
    assert (a_vencer.severidade, a_vencer.recurso) == ("ALTO", "DEMO-Backup em nuvem")
    sem_responsavel = por_codigo["CP-04"]
    assert len(sem_responsavel) == 3
    esperados = [_reais_por_serie(db)[i].id for i in (7, 41, 77)]
    assert sorted(a.entidade_id for a in sem_responsavel) == sorted(esperados)
    # datas pelas regras do cenário, não pelo que o seed escolheu
    vencida_licenca = db.scalars(
        select(Licenca).where(Licenca.chave_licenca == seed_demo.CHAVE_VENCIDA)
    ).one()
    assert hoje() - vencida_licenca.data_expiracao == timedelta(days=40)
    a_vencer_licenca = db.scalars(
        select(Licenca).where(Licenca.chave_licenca == seed_demo.CHAVE_A_VENCER)
    ).one()
    assert 0 <= (a_vencer_licenca.data_expiracao - hoje()).days <= 30


def test_gate3_ativo_baixado_com_motivo_data_e_destinacao(cenario, db):
    ativo = _ativo(db, serie=seed_demo.SERIE_BAIXADO)
    baixa = db.scalars(select(BaixaAtivo).where(BaixaAtivo.ativo_id == ativo.id)).one()

    assert ativo.status == "BAIXADO"
    assert (baixa.motivo, baixa.destinacao) == ("FIM_VIDA_UTIL", "RECICLAGEM_CERTIFICADA")
    assert hoje() - baixa.data_baixa == timedelta(days=30)
    # R$ 2.500,00 em 48 meses, baixado entre 28 e 30 meses de uso: residual entre
    # 2.500 x (48 - 30) / 48 = 937,50 e 2.500 x (48 - 28) / 48 = 1.041,67 (congelado na baixa)
    assert Decimal("937.50") <= baixa.valor_residual_baixa <= Decimal("1041.67")
    assert baixa.data_source == "sintetico"


def test_segunda_execucao_nao_cria_nem_altera_nada(cenario, db):
    tabelas = (
        Setor,
        Responsavel,
        Fornecedor,
        Ativo,
        Licenca,
        LicencaVinculo,
        HistoricoTransferencia,
        BaixaAtivo,
        AuditLog,
    )

    def foto():
        return {
            t.__tablename__: (
                db.scalar(select(func.count()).select_from(t)),
                db.scalar(select(func.max(t.id))),
            )
            for t in tabelas
        }

    antes = foto()
    conteudo = db.execute(
        select(Ativo.id, Ativo.status, Ativo.data_source, Ativo.atualizado_em).order_by(Ativo.id)
    ).all()

    segunda = seed_demo.semear_demo(db)

    assert segunda == dict.fromkeys(ESPERADO, 0)
    assert foto() == antes
    assert (
        db.execute(
            select(Ativo.id, Ativo.status, Ativo.data_source, Ativo.atualizado_em).order_by(
                Ativo.id
            )
        ).all()
        == conteudo
    )


def test_retoma_o_que_faltou_quando_uma_execucao_foi_interrompida(cenario, db):
    """Idempotência passo a passo: apagar vínculos de licença e recriar só repõe o que sumiu."""
    db.execute(
        text(
            "DELETE FROM licenca_vinculo WHERE id IN "
            "(SELECT id FROM licenca_vinculo ORDER BY id DESC LIMIT 5)"
        )
    )
    db.commit()

    reposto = seed_demo.semear_demo(db)

    assert reposto == {**dict.fromkeys(ESPERADO, 0), "vinculos_licenca": 5}
    assert _contar(db, LicencaVinculo) == 50


def test_sem_o_seed_basico_recusa_e_nao_cria_nada(db):
    with pytest.raises(seed_demo.ErroSeedDemo, match="seed básico"):
        seed_demo.semear_demo(db)

    assert _contar(db, Setor) == 0 and _contar(db, Responsavel) == 0 and _contar(db, AuditLog) == 0


def test_sem_a_importacao_recusa_dizendo_quantos_ativos_faltam(db):
    seed.semear(db, SENHAS)
    auditoria_antes = _contar(db, AuditLog)

    with pytest.raises(seed_demo.ErroSeedDemo, match="esperados 92 ativos compras_gov, há 0"):
        seed_demo.semear_demo(db)

    assert _contar(db, Setor) == 0 and _contar(db, Fornecedor) == 0
    assert _contar(db, AuditLog) == auditoria_antes


def test_importacao_incompleta_tambem_recusa(client, db):
    _importar_demonstracao(client, db)
    db.execute(Ativo.__table__.update().where(Ativo.id == 1).values(data_source="importacao"))
    db.commit()

    with pytest.raises(seed_demo.ErroSeedDemo, match="há 91"):
        seed_demo.semear_demo(db)

    assert _contar(db, Setor) == 0


def test_main_recusa_producao(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "producao")

    with pytest.raises(SystemExit, match="producao"):
        seed_demo.main()


def test_main_sai_com_a_mensagem_do_pre_requisito(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    with pytest.raises(SystemExit, match="Seed de demonstração recusado"):
        seed_demo.main()


def test_main_cria_o_cenario_e_resume(cenario, db, monkeypatch, capsys):
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    seed_demo.main()

    assert "0 setores" in capsys.readouterr().out  # o cenário já existia: nada novo


def test_menos_meses_conta_pela_regra_do_projeto():
    for dia in (date(2026, 10, 5), date(2026, 3, 31), date(2026, 5, 31), date(2024, 2, 29)):
        for meses in (1, 12, 15, 50):
            assert meses_entre(seed_demo.menos_meses(dia, meses), dia) == meses
    assert seed_demo.menos_meses(date(2026, 3, 31), 1) == date(2026, 2, 28)


def test_as_rotas_seguem_com_a_origem_padrao_a_origem_nao_vira_campo_da_api(client, db):
    """A origem é parâmetro interno dos services: pela API tudo continua `manual`, exceto o
    responsável, que já era (e segue) `sintetico`."""
    seed.semear(db, SENHAS)
    token = client.post(
        "/api/v1/auth/login", json={"login": "admin", "senha": SENHAS["admin"]}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    setor = client.post("/api/v1/setores", headers=headers, json={"nome": "Setor API"}).json()
    responsavel = client.post(
        "/api/v1/responsaveis",
        headers=headers,
        json={"nome": "Pessoa API", "setor_id": setor["id"]},
    ).json()
    forn = client.post(
        "/api/v1/fornecedores", headers=headers, json={"razao_social": "Forn API"}
    ).json()
    cat = db.scalars(select(Categoria).where(Categoria.nome == "Notebook")).one()
    ativo = client.post(
        "/api/v1/ativos",
        headers=headers,
        json={
            "nome": "Notebook API",
            "tipo": "HARDWARE",
            "categoria_id": cat.id,
            "fornecedor_id": forn["id"],
            "numero_serie": "API-1",
            "data_aquisicao": "2025-01-10",
            "valor_compra": "1000.00",
            "data_source": "compras_gov",
        },
    ).json()
    vinculo = client.post(
        f"/api/v1/ativos/{ativo['id']}/responsavel",
        headers=headers,
        json={
            "responsavel_id": responsavel["id"],
            "setor_id": setor["id"],
            "data_inicio": "2025-02-01",
        },
    ).json()
    licenca = client.post(
        "/api/v1/licencas",
        headers=headers,
        json={
            "tipo_licenciamento": "SUBSCRICAO",
            "software": "Software API",
            "fornecedor_id": forn["id"],
            "chave_licenca": "API-KEY-0001",
            "quantidade_contratada": 1,
            "valor_total": "10.00",
            "data_inicio_vigencia": "2025-01-01",
            "data_expiracao": "2099-01-01",
            "data_source": "sintetico",
        },
    ).json()
    vinc_lic = client.post(
        f"/api/v1/licencas/{licenca['id']}/vinculos",
        headers=headers,
        json={"ativo_id": ativo["id"]},
    ).json()
    baixa = client.post(
        f"/api/v1/ativos/{ativo['id']}/baixa",
        headers=headers,
        json={"motivo": "DEFEITO", "data_baixa": "2025-06-01", "destinacao": "DESCARTE"},
    ).json()

    assert responsavel["data_source"] == "sintetico"
    assert ativo["data_source"] == "manual"  # o `data_source` enviado no corpo é ignorado
    assert vinculo["data_source"] == "manual"
    assert licenca["data_source"] == "manual"
    assert vinc_lic["data_source"] == "manual"
    assert baixa["data_source"] == "manual"


def test_roda_sozinho_como_modulo_e_cria_o_cenario(importado, db):
    """`python -m app.seed_demo` num processo novo, na primeira execução: só vale o que o próprio
    seed importa (o mapeamento dos modelos precisa estar completo, o que o `conftest.py`
    mascara, e só aparece quando o seed cria um ativo)."""
    ambiente = {k: v for k, v in os.environ.items() if k != "ENVIRONMENT"}
    ambiente["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

    saida = subprocess.run(
        [sys.executable, "-m", "app.seed_demo"],
        cwd=Path(__file__).resolve().parents[2],
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert saida.returncode == 0, saida.stderr[-600:]
    assert saida.stdout.strip() == (
        "Seed de demonstração: 3 setores, 6 responsaveis, 1 fornecedores, 4 ativos_demo, "
        "95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas"
    )
    db.expire_all()
    assert _contar(db, Ativo, Ativo.data_source == "sintetico") == 4

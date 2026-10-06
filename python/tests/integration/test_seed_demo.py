"""Seed de demonstração dos Gates 2, 3 e 4 (`app/seed_demo.py`).

Parte de um banco com o seed básico, os fornecedores e os 92 ativos de
`dataset/demo/inventario_demo.csv` importados pelo fluxo real da demonstração, e confere o que o
seed cria: contagens, origem `sintetico`, auditoria, histórico de transferências, o AC-015, a
licença em 50 de 50 com o 51º vínculo recusado, os alertas e a idempotência. O cenário de decisão
do Gate 4 (riscos, scorecard, recomendação e o corpo de exemplo dos cenários) está no fim.
"""

import io
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select, text

from app import seed, seed_demo
from app.core.config import get_settings
from app.core.exceptions import RegraNegocioError
from app.models.ativo import Ativo
from app.models.auditoria import AuditLog
from app.models.baixa import BaixaAtivo
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor, FornecedorAvaliacao
from app.models.historico import HistoricoTransferencia
from app.models.licenca import Licenca, LicencaVinculo
from app.models.recomendacao import Evidencia, Recomendacao
from app.models.responsavel import Responsavel
from app.models.risco import Risco
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
    "fornecedores": 3,  # o de demonstração e os 2 de software do scorecard
    "ativos_demo": 4,
    "vinculos_responsavel": 95,  # 89 reais + 4 do ativo das transferências + AC-015 + software
    "licencas": 3,
    "vinculos_licenca": 50,
    "baixas": 1,
    "riscos": 2,
    "avaliacoes": 3,  # um scorecard, 3 fornecedores avaliados
    "recomendacoes": 1,
}
GATE4 = ("fornecedores", "riscos", "avaliacoes", "recomendacoes")
EXEMPLO_CENARIOS = (
    Path(__file__).resolve().parents[3] / "docs" / "guia" / "exemplos" / "cenarios_gate4.json"
)


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
    assert _contar(db, Fornecedor, Fornecedor.data_source == "sintetico") == 3
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
        "risco": Risco,
        "recomendacao": Recomendacao,
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
        Risco,
        FornecedorAvaliacao,
        Recomendacao,
        Evidencia,
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
    ambiente["DATABASE_URL"] = get_settings().database_url

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
        "Seed de demonstração: 3 setores, 6 responsaveis, 3 fornecedores, 4 ativos_demo, "
        "95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas, 2 riscos, "
        "3 avaliacoes, 1 recomendacoes"
    )
    db.expire_all()
    assert _contar(db, Ativo, Ativo.data_source == "sintetico") == 4


# ---- Gate 4: regularização do licenciamento (riscos, scorecard, recomendação, cenários) ----

TITULO_CRITICO = "uso de software sem licença válida"
TITULO_MEDIO = "saturação da licença de escritório"
TITULO_RECOMENDACAO = "Regularizar o licenciamento de software"
PERIODO = "DEMO-LICENCIAMENTO"
# Pesos (somam 100) e notas do scorecard; a pontuação esperada é conta à mão, em 2 casas:
# Alfa  = 8x.30 + 9x.15 + 9x.25 + 8x.15 + 9x.15 = 2,40 + 1,35 + 2,25 + 1,20 + 1,35 = 8,55
# Demo  = 7x.30 + 6x.15 + 7x.25 + 7x.15 + 8x.15 = 2,10 + 0,90 + 1,75 + 1,05 + 1,20 = 7,00
# Beta  = 6x.30 + 7x.15 + 5x.25 + 6x.15 + 6x.15 = 1,80 + 1,05 + 1,25 + 0,90 + 0,90 = 5,90
PESOS = {
    "Preço": Decimal("30"),
    "Prazo de entrega": Decimal("15"),
    "Qualidade do suporte": Decimal("25"),
    "Taxa de defeitos": Decimal("15"),
    "Aderência contratual": Decimal("15"),
}
PONTUACAO = {
    "DEMO-Software Alfa LTDA": Decimal("8.55"),
    "DEMO-Fornecedor de Demonstração LTDA": Decimal("7.00"),
    "DEMO-Software Beta LTDA": Decimal("5.90"),
}


def _tabelas_gate4():
    return (Risco, FornecedorAvaliacao, Recomendacao, Evidencia)


def _recomendacao(db) -> Recomendacao:
    return db.scalars(select(Recomendacao).where(Recomendacao.titulo == TITULO_RECOMENDACAO)).one()


def test_gate4_ac050_risco_4_por_5_sai_critico_e_o_de_saturacao_sai_medio(cenario, db, client):
    critico = db.scalars(select(Risco).where(Risco.titulo == TITULO_CRITICO)).one()
    medio = db.scalars(select(Risco).where(Risco.titulo == TITULO_MEDIO)).one()

    assert (critico.probabilidade, critico.impacto, critico.score) == (4, 5, 20)  # 4 x 5
    assert medio.score == medio.probabilidade * medio.impacto and 5 <= medio.score <= 9
    pelo_sistema = {
        r["titulo"]: r["classificacao"]
        for r in client.get("/api/v1/riscos", headers=cenario["headers"]).json()["itens"]
    }
    assert pelo_sistema == {TITULO_CRITICO: "CRITICO", TITULO_MEDIO: "MEDIO"}
    assert critico.id < medio.id  # ids 1 e 2 num banco novo: o exemplo dos cenários depende disso


def test_gate4_scorecard_dos_tres_fornecedores_demo_ordenado_com_vencedor_claro(cenario, db):
    linhas = db.scalars(select(FornecedorAvaliacao)).all()
    nomes = {f.id: f.razao_social for f in db.scalars(select(Fornecedor))}

    assert {linha.periodo for linha in linhas} == {PERIODO}  # mesmo período para os três
    assert {linha.data_source for linha in linhas} == {"sintetico"}
    assert len(linhas) == 3 * len(PESOS)
    assert {nomes[linha.fornecedor_id] for linha in linhas} == set(PONTUACAO)
    por_fornecedor: dict[str, list[FornecedorAvaliacao]] = {}
    for linha in linhas:
        por_fornecedor.setdefault(nomes[linha.fornecedor_id], []).append(linha)
    for razao, grupo in por_fornecedor.items():
        assert {g.criterio: g.peso for g in grupo} == PESOS
        assert sum(g.peso for g in grupo) == Decimal("100")  # BR-029
        assert sum(g.nota * g.peso / 100 for g in grupo) == PONTUACAO[razao]
    ordem = sorted(PONTUACAO, key=PONTUACAO.get, reverse=True)
    assert ordem == [
        "DEMO-Software Alfa LTDA",
        "DEMO-Fornecedor de Demonstração LTDA",
        "DEMO-Software Beta LTDA",
    ]
    assert len(set(PONTUACAO.values())) == 3  # nenhum empate


def test_nenhum_fornecedor_demo_tem_cnpj_e_o_seed_nao_usa_o_cnpj_de_empresa_real(cenario, db):
    demo = db.scalars(select(Fornecedor).where(Fornecedor.razao_social.like("DEMO-%"))).all()

    assert len(demo) == 3
    assert {f.cnpj for f in demo} == {None}
    assert "FORNECEDOR_DEMO" in vars(seed_demo)  # identificado pelo nome DEMO-
    assert "00.000.000/0001-91" not in Path(seed_demo.__file__).read_text(encoding="utf-8")


def test_fornecedor_demo_e_identificado_pelo_nome_mesmo_com_cnpj_de_um_banco_antigo(importado, db):
    """Um banco semeado antes desta mudança tem o fornecedor com CNPJ: o seed o reconhece pelo
    nome `DEMO-`, não cria outro e não mexe no que já está gravado."""
    db.add(
        Fornecedor(
            razao_social=seed_demo.FORNECEDOR_DEMO,
            cnpj="00.000.000/0001-91",
            data_source="sintetico",
        )
    )
    db.commit()

    criados = seed_demo.semear_demo(db)

    assert criados["fornecedores"] == 2  # só os dois de software do Gate 4
    demo = db.scalars(
        select(Fornecedor).where(Fornecedor.razao_social == seed_demo.FORNECEDOR_DEMO)
    )
    (antigo,) = demo.all()
    assert antigo.cnpj == "00.000.000/0001-91"
    assert _contar(db, Fornecedor, Fornecedor.razao_social.like("DEMO-%")) == 3
    assert seed_demo.semear_demo(db) == dict.fromkeys(ESPERADO, 0)


def test_gate4_os_dois_fornecedores_novos_sao_de_software_e_demo(cenario, db):
    novos = db.scalars(
        select(Fornecedor).where(Fornecedor.razao_social.like("DEMO-Software%"))
    ).all()

    assert sorted(f.razao_social for f in novos) == [
        "DEMO-Software Alfa LTDA",
        "DEMO-Software Beta LTDA",
    ]
    assert {f.data_source for f in novos} == {"sintetico"}
    assert _contar(db, Fornecedor, Fornecedor.razao_social.like("DEMO-%")) == 3


def test_gate4_recomendacao_com_quatro_evidencias_cada_uma_com_o_que_a_sustenta(cenario, db):
    recomendacao = _recomendacao(db)
    por_tipo = {e.tipo: e for e in recomendacao.evidencias}

    assert recomendacao.data_source == "sintetico" and recomendacao.status == "PROPOSTA"
    assert len(recomendacao.evidencias) == 4
    assert set(por_tipo) == {"RISCO", "SCORECARD", "INDICADOR", "CENARIO"}
    # as duas que apontam para registro: o risco crítico e o fornecedor mais bem avaliado
    risco = db.get(Risco, por_tipo["RISCO"].referencia_id)
    assert risco is not None and risco.titulo == TITULO_CRITICO and risco.score == 20
    vencedor = db.get(Fornecedor, por_tipo["SCORECARD"].referencia_id)
    assert vencedor is not None and vencedor.razao_social == "DEMO-Software Alfa LTDA"
    assert db.scalars(
        select(FornecedorAvaliacao).where(FornecedorAvaliacao.fornecedor_id == vencedor.id)
    ).all()  # o scorecard do vencedor existe
    # indicador e cenário não têm registro (FR-013): levam o valor no momento do registro
    for tipo in ("INDICADOR", "CENARIO"):
        assert por_tipo[tipo].referencia_id is None and por_tipo[tipo].descricao


def test_gate4_evidencia_de_indicador_traz_o_valor_do_kpi_03_do_sistema(cenario, db, client):
    """KPI-03 com o seed: a de 50 de 50 e a a vencer estão conformes, a vencida não: 2 de 3."""
    indicador = next(
        i
        for i in client.get("/api/v1/indicadores", headers=cenario["headers"]).json()["indicadores"]
        if i["codigo"] == "KPI-03"
    )
    descricao = {e.tipo: e.descricao for e in _recomendacao(db).evidencias}["INDICADOR"]

    assert indicador["amostra"] == 3
    assert "KPI-03" in descricao and "Conformidade de licenças" in descricao
    assert f"{indicador['valor']:.2f}".replace(".", ",") + "%" in descricao
    assert "3 licenças" in descricao


def test_gate4_evidencia_de_cenario_traz_os_tco_do_exemplo(cenario, db):
    descricao = {e.tipo: e.descricao for e in _recomendacao(db).evidencias}["CENARIO"]

    # TCO de 5 anos: MANTER 0 + 4.000 x 5; RENOVAR 12.000 + 6.000 x 5; MIGRAR 3.000 + 9.600 x 5
    # score de risco: MANTER 20 + 9, RENOVAR 9 (só a saturação), MIGRAR nenhum
    for esperado in (
        "MANTER R$ 20.000,00 (risco 29)",
        "RENOVAR R$ 42.000,00 (risco 9)",
        "MIGRAR_ASSINATURA R$ 51.000,00 (risco 0)",
    ):
        assert esperado in descricao
    assert "nenhuma" in descricao.lower()  # a escolha segue humana (BR-028)


def test_gate4_corpo_de_exemplo_dos_cenarios_e_aceito_ordenado_por_tco_e_sem_escolha(
    cenario, client
):
    corpo = json.loads(EXEMPLO_CENARIOS.read_text(encoding="utf-8"))

    resposta = client.post("/api/v1/cenarios/comparar", headers=cenario["headers"], json=corpo)

    assert resposta.status_code == 200, resposta.text
    resultado = resposta.json()
    assert [c["nome"] for c in corpo["cenarios"]] == ["MANTER", "RENOVAR", "MIGRAR_ASSINATURA"]
    # TCO de 5 anos à mão: capex + opex x 5
    assert [(c["nome"], c["tco_5_anos"]) for c in resultado["cenarios"]] == [
        ("MANTER", "20000.00"),  # 0 + 4.000 x 5
        ("RENOVAR", "42000.00"),  # 12.000 + 6.000 x 5
        ("MIGRAR_ASSINATURA", "51000.00"),  # 3.000 + 9.600 x 5
    ]
    # score de risco = soma dos scores dos riscos do seed: 20 + 9, 9 e nenhum
    assert [c["score_risco"] for c in resultado["cenarios"]] == [29, 9, 0]
    assert resultado["ordenado_por"] == ["tco_5_anos", "score_risco"]
    assert resultado["baseline"] == "MANTER"
    texto = json.dumps(resultado).lower()
    assert "escolhid" not in texto and "selecionad" not in texto  # BR-028
    assert all(set(c) == set(resultado["cenarios"][0]) for c in resultado["cenarios"])


def test_gate4_o_exemplo_dos_cenarios_tem_os_mesmos_valores_do_seed(cenario, db):
    corpo = json.loads(EXEMPLO_CENARIOS.read_text(encoding="utf-8"))
    ids = {r.titulo: r.id for r in db.scalars(select(Risco))}

    do_seed = [
        {
            "nome": nome.value,
            "capex": str(capex),
            "opex_anual": str(opex),
            "riscos_ids": [ids[t] for t in titulos],
        }
        for nome, capex, opex, titulos in seed_demo.CENARIOS
    ]

    assert corpo["cenarios"] == do_seed


def test_gate4_o_exemplo_dos_cenarios_tem_tres_alternativas_com_os_riscos_do_seed(cenario, db):
    corpo = json.loads(EXEMPLO_CENARIOS.read_text(encoding="utf-8"))
    ids = {r.titulo: r.id for r in db.scalars(select(Risco))}

    por_nome = {c["nome"]: c["riscos_ids"] for c in corpo["cenarios"]}

    assert por_nome == {
        "MANTER": [ids[TITULO_CRITICO], ids[TITULO_MEDIO]],
        "RENOVAR": [ids[TITULO_MEDIO]],
        "MIGRAR_ASSINATURA": [],
    }


def test_gate4_tudo_o_que_o_gate_criou_e_sintetico_e_tem_auditoria(cenario, db):
    for modelo in (Risco, Recomendacao, FornecedorAvaliacao):
        assert {r.data_source for r in db.scalars(select(modelo))} == {"sintetico"}
    auditados = {
        entidade: set(
            db.scalars(
                select(AuditLog.entidade_id).where(
                    AuditLog.entidade == entidade,
                    AuditLog.operacao == "CRIAR",
                    AuditLog.resultado == "SUCESSO",
                    AuditLog.usuario_id.is_not(None),
                )
            )
        )
        for entidade in ("risco", "recomendacao", "fornecedor", "fornecedor_avaliacao")
    }
    assert set(db.scalars(select(Risco.id))) <= auditados["risco"]
    assert set(db.scalars(select(Recomendacao.id))) <= auditados["recomendacao"]
    assert set(db.scalars(select(Fornecedor.id))) <= auditados["fornecedor"]
    # uma auditoria por fornecedor avaliado, no id da primeira linha, que lista todas as dele
    primeiras = {
        db.scalar(
            select(func.min(FornecedorAvaliacao.id)).where(
                FornecedorAvaliacao.fornecedor_id == fornecedor_id
            )
        )
        for fornecedor_id in db.scalars(select(FornecedorAvaliacao.fornecedor_id).distinct())
    }
    assert len(primeiras) == 3 and primeiras <= auditados["fornecedor_avaliacao"]
    evidencias = db.scalars(
        select(AuditLog.detalhe).where(
            AuditLog.entidade == "recomendacao", AuditLog.operacao == "CRIAR"
        )
    ).one()
    assert len(evidencias["evidencias"]) == 4


def test_gate4_partindo_de_um_banco_so_com_o_seed_anterior_cria_so_o_que_falta(importado, db):
    autor = seed_demo.verificar_prerequisitos(db)
    anterior = seed_demo._semear_gates_2_e_3(db, autor)  # o seed como era antes do Gate 4
    assert _contar(db, Risco) == 0 and _contar(db, Recomendacao) == 0
    assert anterior["fornecedores"] == 1 and "riscos" not in anterior
    tabelas = (
        Setor,
        Responsavel,
        Ativo,
        Licenca,
        LicencaVinculo,
        HistoricoTransferencia,
        BaixaAtivo,
    )
    antes = {t.__tablename__: _contar(db, t) for t in tabelas}
    fornecedores_antes = _contar(db, Fornecedor)

    nova = seed_demo.semear_demo(db)

    assert nova == {
        **dict.fromkeys(ESPERADO, 0),
        "fornecedores": 2,
        "riscos": 2,
        "avaliacoes": 3,
        "recomendacoes": 1,
    }
    assert {t.__tablename__: _contar(db, t) for t in tabelas} == antes  # nada do anterior mexeu
    assert _contar(db, Fornecedor) == fornecedores_antes + 2
    assert _contar(db, Recomendacao) == 1 and _contar(db, Evidencia) == 4
    assert seed_demo.semear_demo(db) == dict.fromkeys(ESPERADO, 0)  # e a seguinte não cria nada


def test_gate4_retoma_a_recomendacao_que_faltou_sem_duplicar_o_resto(cenario, db):
    db.execute(text("DELETE FROM recomendacao"))  # as evidências saem em cascata
    db.commit()
    assert _contar(db, Evidencia) == 0

    reposto = seed_demo.semear_demo(db)

    assert reposto == {**dict.fromkeys(ESPERADO, 0), "recomendacoes": 1}
    assert _contar(db, Risco) == 2 and _contar(db, FornecedorAvaliacao) == 3 * len(PESOS)
    assert _contar(db, Evidencia) == 4


def test_gate4_retoma_o_que_faltou_depois_de_uma_execucao_interrompida_no_scorecard(cenario, db):
    db.execute(text("DELETE FROM recomendacao"))
    db.execute(text("DELETE FROM fornecedor_avaliacao"))
    db.execute(text("DELETE FROM risco WHERE titulo = :t"), {"t": TITULO_MEDIO})
    db.commit()

    reposto = seed_demo.semear_demo(db)

    assert reposto == {
        **dict.fromkeys(ESPERADO, 0),
        "riscos": 1,
        "avaliacoes": 3,
        "recomendacoes": 1,
    }


def test_gate4_o_que_o_gate_cria_nao_altera_os_ativos_e_licencas_do_cenario_anterior(cenario, db):
    antes = db.execute(select(Ativo.id, Ativo.status, Ativo.atualizado_em).order_by(Ativo.id)).all()

    seed_demo.semear_demo(db)

    assert (
        db.execute(select(Ativo.id, Ativo.status, Ativo.atualizado_em).order_by(Ativo.id)).all()
        == antes
    )


def test_gate4_refaz_as_recusas_do_roteiro_ao_vivo_ac048_e_ac051(cenario, db, client):
    """Corpos de `docs/guia/demonstracao.md`: pesos somando 95% e recomendação sem evidência."""
    forn = {f.razao_social: f.id for f in db.scalars(select(Fornecedor))}
    pesos_95 = {**PESOS, "Aderência contratual": Decimal("10")}
    corpo_scorecard = {
        "periodo": "DEMO-AO-VIVO",
        "criterios": [{"nome": n, "peso": str(p)} for n, p in pesos_95.items()],
        "avaliacoes": [
            {
                "fornecedor_id": forn["DEMO-Software Alfa LTDA"],
                "notas": dict.fromkeys(PESOS, "8"),
            }
        ],
    }
    responsavel = db.scalars(select(Responsavel).order_by(Responsavel.id)).first()
    corpo_recomendacao = {
        "titulo": "Regularizar o licenciamento de software",
        "contexto": "Antivírus vencido e licença de escritório em 50 de 50.",
        "recomendacao": "Regularizar o licenciamento.",
        "responsavel_id": responsavel.id,
        "evidencias": [],
    }
    auditoria_antes = _contar(db, AuditLog, AuditLog.resultado == "RECUSADO")

    sem_peso = client.post(
        "/api/v1/fornecedores/scorecard", headers=cenario["headers"], json=corpo_scorecard
    )
    sem_evidencia = client.post(
        "/api/v1/recomendacoes", headers=cenario["headers"], json=corpo_recomendacao
    )

    assert (sem_peso.status_code, sem_peso.json()["regra"]) == (409, "BR-029")
    assert (sem_evidencia.status_code, sem_evidencia.json()["regra"]) == (409, "BR-027")
    assert _contar(db, AuditLog, AuditLog.resultado == "RECUSADO") == auditoria_antes + 2
    assert _contar(db, Recomendacao) == 1 and _contar(db, FornecedorAvaliacao) == 3 * len(PESOS)


def test_as_rotas_de_risco_scorecard_e_recomendacao_seguem_manual_a_origem_nao_vira_campo(
    client, db
):
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
    risco = client.post(
        "/api/v1/riscos",
        headers=headers,
        json={
            "titulo": "Risco API",
            "categoria": "LEGAL",
            "probabilidade": 2,
            "impacto": 2,
            "resposta": "MITIGAR",
            "data_source": "sintetico",
        },
    ).json()
    client.post(
        "/api/v1/fornecedores/scorecard",
        headers=headers,
        json={
            "periodo": "API",
            "criterios": [{"nome": "Preço", "peso": "100"}],
            "avaliacoes": [{"fornecedor_id": forn["id"], "notas": {"Preço": "7"}}],
            "data_source": "sintetico",
        },
    )
    recomendacao = client.post(
        "/api/v1/recomendacoes",
        headers=headers,
        json={
            "titulo": "Recomendação API",
            "contexto": "c",
            "recomendacao": "r",
            "responsavel_id": responsavel["id"],
            "evidencias": [{"tipo": "RISCO", "referencia_id": risco["id"]}],
            "data_source": "sintetico",
        },
    ).json()

    assert risco["data_source"] == "manual"
    assert recomendacao["data_source"] == "manual"
    assert {a.data_source for a in db.scalars(select(FornecedorAvaliacao))} == {"manual"}

"""Seed de demonstração dos Gates 2 e 3 (docs/guia/demonstracao.md).

Uso: `python -m app.seed_demo` (ou `scripts/seed_demo.sh`), depois do seed básico e da importação
dos 92 ativos de `dataset/demo/inventario_demo.csv`. Roda dentro da aplicação e chama os
services, como `app/seed.py`: nada de SQL direto, nada de HTTP, e regra de negócio, trigger e
auditoria valem como em qualquer cadastro.

O que cria (tudo `sintetico`, com identificadores `DEMO-`; o setor não tem `data_source`, então
os três setores só levam o prefixo `DEMO-`):
- 3 setores, 6 responsáveis e 1 fornecedor fictícios;
- responsável para os 92 ativos reais (`compras_gov`), menos 3 deixados sem de propósito;
- Gate 2: um notebook com atribuição inicial e 3 transferências, e um notebook para o AC-015
  (R$ 6.000,00, 60 meses, 12 decorridos, residual R$ 4.800,00);
- Gate 3: um software com licença de 50 unidades e 50 vínculos em máquinas reais (o 51º fica para
  a demonstração ao vivo), uma licença vencida há 40 dias, uma perto de vencer e um ativo baixado.

Idempotente: cada passo confere se o registro `DEMO-` já existe e só cria o que falta, então a
segunda execução não cria nem altera nada. As datas dos ativos `DEMO-` saem do dia da primeira
execução e ficam gravadas; para reconferir o AC-015 em outro dia, recrie o banco.
"""

import os
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.ativo import Ativo
from app.models.baixa import BaixaAtivo
from app.models.categoria import Categoria
from app.models.enums import (
    DestinacaoBaixa,
    MotivoBaixa,
    StatusAtivo,
    TipoAtivo,
    TipoLicenciamento,
)
from app.models.fornecedor import Fornecedor
from app.models.historico import HistoricoTransferencia
from app.models.importacao import LoteImportacao  # noqa: F401  (registra a FK de ativo)
from app.models.licenca import Licenca, LicencaVinculo
from app.models.responsavel import Responsavel
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.ativo import AtivoCreate
from app.schemas.baixa import BaixaCreate
from app.schemas.fornecedor import FornecedorCreate
from app.schemas.historico import VinculoCreate
from app.schemas.licenca import LicencaCreate, VinculoLicencaCreate
from app.schemas.responsavel import ResponsavelCreate
from app.schemas.setor import SetorCreate
from app.services.ativo_service import criar_ativo
from app.services.baixa_service import registrar_baixa
from app.services.fornecedor_service import criar_fornecedor
from app.services.licenca_service import criar_licenca, vincular
from app.services.responsavel_service import atribuir_responsavel, criar_responsavel
from app.services.setor_service import criar_setor
from app.utils.datas import hoje

ORIGEM = "sintetico"
AUTOR = "admin"  # criado pelo seed básico
ATIVOS_REAIS = 92
# Posições (na ordem do número de série) dos 3 ativos reais que ficam sem responsável de propósito.
SEM_RESPONSAVEL = (7, 41, 77)
MAQUINAS_DA_LICENCA = 50
CATEGORIAS = ("Notebook", "Impressora", "Software perpétuo")

SETORES = [
    ("DEMO-Financeiro", "DEMO-FIN"),
    ("DEMO-Tecnologia", "DEMO-TI"),
    ("DEMO-Operações", "DEMO-OPS"),
]
# (matrícula, nome fictício, cargo, posição do setor em SETORES)
RESPONSAVEIS = [
    ("DEMO-001", "Helena Duarte Pinheiro", "Analista financeira", 0),
    ("DEMO-002", "Rafael Quintanilha Reis", "Contador", 0),
    ("DEMO-003", "Marta Albuquerque Lins", "Analista de infraestrutura", 1),
    ("DEMO-004", "Otávio Brandão Serra", "Administrador de sistemas", 1),
    ("DEMO-005", "Isadora Valente Prado", "Coordenadora de operações", 2),
    ("DEMO-006", "Caio Menezes Tavares", "Assistente de operações", 2),
]
FORNECEDOR = ("DEMO-Fornecedor de Demonstração LTDA", "00.000.000/0001-91")

SERIE_TRANSFERENCIAS = "DEMO-HW-TRANSF"
SERIE_AC015 = "DEMO-HW-AC015"
SERIE_BAIXADO = "DEMO-HW-BAIXA"
CHAVE_SOFTWARE = "DEMO-SW-OFFICE-KEY-0001"
CHAVE_LICENCA_50 = "DEMO-LIC-PERPETUA-0050"
CHAVE_VENCIDA = "DEMO-LIC-VENCIDA-0040"
CHAVE_A_VENCER = "DEMO-LIC-A-VENCER-0025"
# Dias depois da aquisição de cada passo do ativo das transferências: atribuição inicial e 3
# transferências, em datas sucessivas e posteriores à aquisição.
PASSOS_TRANSFERENCIA = (30, 120, 210, 300)
RESPONSAVEIS_TRANSFERENCIA = (0, 2, 4, 1)


class ErroSeedDemo(Exception):
    """Pré-requisito ausente: nada foi criado."""


def menos_meses(data: date, meses: int) -> date:
    """`data` menos `meses`, com o dia limitado ao último do mês de destino. Contado pela regra do
    projeto (`utils.depreciacao.meses_entre`), o resultado até `data` dá exatamente `meses`."""
    indice = data.year * 12 + data.month - 1 - meses
    ano, mes = divmod(indice, 12)
    mes += 1
    proximo = date(ano + (mes == 12), mes % 12 + 1, 1)
    ultimo_dia = (proximo - timedelta(days=1)).day
    return date(ano, mes, min(data.day, ultimo_dia))


def ativos_reais(db: Session) -> list[Ativo]:
    """Os ativos importados do Compras.gov.br, na ordem do número de série (seleção fixa)."""
    return list(
        db.scalars(
            select(Ativo).where(Ativo.data_source == "compras_gov").order_by(Ativo.numero_serie)
        )
    )


def verificar_prerequisitos(db: Session) -> Usuario:
    """Confere o seed básico e a importação; devolve o autor. Sem efeito no banco."""
    faltas = []
    autor = db.scalar(select(Usuario).where(Usuario.login == AUTOR))
    if autor is None:
        faltas.append("usuário 'admin' ausente: rode o seed básico (scripts/seed.sh)")
    existentes = set(db.scalars(select(Categoria.nome).where(Categoria.nome.in_(CATEGORIAS))))
    if existentes != set(CATEGORIAS):
        faltas.append("categorias do seed básico ausentes (scripts/seed.sh)")
    reais = db.scalar(select(func.count()).where(Ativo.data_source == "compras_gov")) or 0
    if reais != ATIVOS_REAIS:
        faltas.append(
            f"esperados {ATIVOS_REAIS} ativos compras_gov, há {reais}: importe "
            "dataset/demo/inventario_demo.csv (docs/guia/importacao.md)"
        )
    if faltas:
        raise ErroSeedDemo("Seed de demonstração recusado: " + "; ".join(faltas) + ".")
    assert autor is not None
    return autor


def _ativo_demo(
    db: Session, autor: Usuario, contagem: dict[str, int], **campos
) -> tuple[Ativo, bool]:
    """O ativo `DEMO-` pelo número de série (ou chave); cria pelo service se não existir."""
    serie, chave = campos.get("numero_serie"), campos.get("chave_licenca")
    condicao = Ativo.numero_serie == serie if serie else Ativo.chave_licenca == chave
    existente = db.scalar(select(Ativo).where(condicao))
    if existente is not None:
        return existente, False
    categoria = db.scalars(select(Categoria).where(Categoria.nome == campos.pop("categoria"))).one()
    ativo = criar_ativo(
        db,
        AtivoCreate(
            categoria_id=categoria.id,
            fornecedor_id=campos.pop("fornecedor_id"),
            data_aquisicao=campos.pop("aquisicao"),
            **campos,
        ),
        autor,
        origem=ORIGEM,
    )
    contagem["ativos_demo"] += 1
    return ativo, True


def _atribuir(
    db: Session,
    autor: Usuario,
    contagem: dict[str, int],
    ativo: Ativo,
    responsavel: Responsavel,
    data_inicio: date,
    motivo: str,
) -> None:
    assert responsavel.setor_id is not None  # os responsáveis do seed pertencem a um setor
    atribuir_responsavel(
        db,
        ativo.id,
        VinculoCreate(
            responsavel_id=responsavel.id,
            setor_id=responsavel.setor_id,
            data_inicio=data_inicio,
            motivo=motivo,
        ),
        autor,
        origem=ORIGEM,
    )
    contagem["vinculos_responsavel"] += 1


def _tem_vinculo(db: Session, ativo: Ativo) -> bool:
    return (
        db.scalar(
            select(HistoricoTransferencia.id)
            .where(HistoricoTransferencia.ativo_id == ativo.id)
            .limit(1)
        )
        is not None
    )


def _licenca(db: Session, autor: Usuario, contagem: dict[str, int], chave: str, **campos):
    existente = db.scalar(select(Licenca).where(Licenca.chave_licenca == chave))
    if existente is not None:
        return existente
    criada = criar_licenca(db, LicencaCreate(chave_licenca=chave, **campos), autor, origem=ORIGEM)
    contagem["licencas"] += 1
    return db.get(Licenca, criada.id)


def semear_demo(db: Session) -> dict[str, int]:
    """Cria o que falta do cenário e devolve quantos registros criou de cada tipo."""
    autor = verificar_prerequisitos(db)
    dia = hoje()
    contagem = dict.fromkeys(
        (
            "setores",
            "responsaveis",
            "fornecedores",
            "ativos_demo",
            "vinculos_responsavel",
            "licencas",
            "vinculos_licenca",
            "baixas",
        ),
        0,
    )

    fornecedor = db.scalar(select(Fornecedor).where(Fornecedor.cnpj == FORNECEDOR[1]))
    if fornecedor is None:
        fornecedor = criar_fornecedor(
            db,
            FornecedorCreate(razao_social=FORNECEDOR[0], cnpj=FORNECEDOR[1], data_source=ORIGEM),
            autor,
        )
        contagem["fornecedores"] += 1

    setores = []
    for nome, sigla in SETORES:
        setor = db.scalar(select(Setor).where(Setor.nome == nome))
        if setor is None:
            setor = criar_setor(db, SetorCreate(nome=nome, sigla=sigla), autor)
            contagem["setores"] += 1
        setores.append(setor)

    responsaveis = []
    for matricula, nome, cargo, posicao_setor in RESPONSAVEIS:
        responsavel = db.scalar(select(Responsavel).where(Responsavel.matricula == matricula))
        if responsavel is None:
            responsavel = criar_responsavel(
                db,
                ResponsavelCreate(
                    nome=nome,
                    matricula=matricula,
                    email=f"{matricula.lower()}@demo.invalid",
                    cargo=cargo,
                    setor_id=setores[posicao_setor].id,
                ),
                autor,
                origem=ORIGEM,
            )
            contagem["responsaveis"] += 1
        responsaveis.append(responsavel)

    # Cenário base: responsável para os ativos reais, menos 3 (SEM_RESPONSAVEL).
    reais = ativos_reais(db)
    for posicao, ativo in enumerate(reais):
        if posicao in SEM_RESPONSAVEL or _tem_vinculo(db, ativo):
            continue
        _atribuir(
            db,
            autor,
            contagem,
            ativo,
            responsaveis[posicao % len(responsaveis)],
            ativo.data_aquisicao,
            "DEMO: atribuição inicial",
        )

    # Gate 2: atribuição inicial e 3 transferências em datas sucessivas.
    transferencias, _ = _ativo_demo(
        db,
        autor,
        contagem,
        nome="DEMO-Notebook com transferências",
        tipo=TipoAtivo.HARDWARE,
        categoria="Notebook",
        fornecedor_id=fornecedor.id,
        numero_serie=SERIE_TRANSFERENCIAS,
        valor_compra=Decimal("7500.00"),
        aquisicao=menos_meses(dia, 15),
    )
    ja_feitos = db.scalar(
        select(func.count()).where(HistoricoTransferencia.ativo_id == transferencias.id)
    )
    for passo in range(ja_feitos or 0, len(PASSOS_TRANSFERENCIA)):
        _atribuir(
            db,
            autor,
            contagem,
            transferencias,
            responsaveis[RESPONSAVEIS_TRANSFERENCIA[passo]],
            transferencias.data_aquisicao + timedelta(days=PASSOS_TRANSFERENCIA[passo]),
            "DEMO: atribuição inicial" if passo == 0 else f"DEMO: transferência {passo}",
        )

    # Gate 2: AC-015, R$ 6.000,00, 60 meses, 12 decorridos, residual R$ 4.800,00.
    ac015, _ = _ativo_demo(
        db,
        autor,
        contagem,
        nome="DEMO-Notebook conferência AC-015",
        tipo=TipoAtivo.HARDWARE,
        categoria="Notebook",
        fornecedor_id=fornecedor.id,
        numero_serie=SERIE_AC015,
        valor_compra=Decimal("6000.00"),
        vida_util_meses=60,
        aquisicao=menos_meses(dia, 12),
    )
    if not _tem_vinculo(db, ac015):
        _atribuir(
            db,
            autor,
            contagem,
            ac015,
            responsaveis[3],
            ac015.data_aquisicao,
            "DEMO: atribuição inicial",
        )

    # Gate 3: software com licença de 50 unidades e 50 vínculos em máquinas reais.
    software, _ = _ativo_demo(
        db,
        autor,
        contagem,
        nome="DEMO-Suíte de escritório (software)",
        tipo=TipoAtivo.SOFTWARE,
        categoria="Software perpétuo",
        fornecedor_id=fornecedor.id,
        chave_licenca=CHAVE_SOFTWARE,
        valor_compra=Decimal("12000.00"),
        aquisicao=dia - timedelta(days=200),
    )
    if not _tem_vinculo(db, software):
        _atribuir(
            db,
            autor,
            contagem,
            software,
            responsaveis[5],
            software.data_aquisicao,
            "DEMO: atribuição inicial",
        )
    licenca = _licenca(
        db,
        autor,
        contagem,
        CHAVE_LICENCA_50,
        tipo_licenciamento=TipoLicenciamento.PERPETUA,
        ativo_id=software.id,
        fornecedor_id=fornecedor.id,
        quantidade_contratada=MAQUINAS_DA_LICENCA,
        data_inicio_vigencia=dia - timedelta(days=120),
        data_expiracao=dia + timedelta(days=1825),
    )
    maquinas = [a for a in reais if a.tipo == TipoAtivo.HARDWARE and a.status == StatusAtivo.ATIVO]
    for maquina in maquinas[:MAQUINAS_DA_LICENCA]:
        ja_vinculada = db.scalar(
            select(LicencaVinculo.id).where(
                LicencaVinculo.licenca_id == licenca.id, LicencaVinculo.ativo_id == maquina.id
            )
        )
        if ja_vinculada is None:
            vincular(
                db, licenca.id, VinculoLicencaCreate(ativo_id=maquina.id), autor, origem=ORIGEM
            )
            contagem["vinculos_licenca"] += 1

    # Gate 3: uma licença vencida há 40 dias e outra que dispara o alerta de vencimento próximo.
    janela = get_settings().janela_alerta_licenca_dias
    _licenca(
        db,
        autor,
        contagem,
        CHAVE_VENCIDA,
        tipo_licenciamento=TipoLicenciamento.SUBSCRICAO,
        software="DEMO-Antivírus corporativo",
        fornecedor_id=fornecedor.id,
        quantidade_contratada=10,
        valor_total=Decimal("1200.00"),
        data_inicio_vigencia=dia - timedelta(days=405),
        data_expiracao=dia - timedelta(days=40),
    )
    _licenca(
        db,
        autor,
        contagem,
        CHAVE_A_VENCER,
        tipo_licenciamento=TipoLicenciamento.SUBSCRICAO,
        software="DEMO-Backup em nuvem",
        fornecedor_id=fornecedor.id,
        quantidade_contratada=10,
        valor_total=Decimal("3600.00"),
        data_inicio_vigencia=dia - timedelta(days=340),
        data_expiracao=dia + timedelta(days=janela - 5),
    )

    # Gate 3: ativo baixado, com motivo, data e destinação.
    baixado, _ = _ativo_demo(
        db,
        autor,
        contagem,
        nome="DEMO-Impressora baixada",
        tipo=TipoAtivo.HARDWARE,
        categoria="Impressora",
        fornecedor_id=fornecedor.id,
        numero_serie=SERIE_BAIXADO,
        valor_compra=Decimal("2500.00"),
        aquisicao=menos_meses(dia, 30),
    )
    if db.scalar(select(BaixaAtivo.id).where(BaixaAtivo.ativo_id == baixado.id)) is None:
        registrar_baixa(
            db,
            baixado.id,
            BaixaCreate(
                motivo=MotivoBaixa.FIM_VIDA_UTIL,
                data_baixa=dia - timedelta(days=30),
                destinacao=DestinacaoBaixa.RECICLAGEM_CERTIFICADA,
            ),
            autor,
            origem=ORIGEM,
        )
        contagem["baixas"] += 1
    return contagem


def main() -> None:
    if os.environ.get("ENVIRONMENT") == "producao":
        raise SystemExit("Seed de demonstração recusado: não roda com ENVIRONMENT=producao.")
    with SessionLocal() as db:
        try:
            criados = semear_demo(db)
        except ErroSeedDemo as erro:
            raise SystemExit(str(erro)) from erro
    print("Seed de demonstração: " + ", ".join(f"{n} {tipo}" for tipo, n in criados.items()))


if __name__ == "__main__":
    main()

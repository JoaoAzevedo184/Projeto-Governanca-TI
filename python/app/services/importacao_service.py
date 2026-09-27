import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ErroValidacaoArquivo
from app.models.ativo import Ativo
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.importacao import ErroImportacao, LoteImportacao
from app.models.usuario import Usuario

COLUNAS_OBRIGATORIAS = ["nome", "tipo", "categoria", "fornecedor", "data_aquisicao", "valor_compra"]
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024
LINHAS_MAXIMAS = 5_000


def _ler_planilha(nome_arquivo: str, conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    if nome_arquivo.lower().endswith(".csv"):
        return pd.read_csv(buffer, dtype=str, keep_default_na=False)
    return pd.read_excel(buffer, dtype=str).fillna("")


def _validar_cabecalho(colunas: list[str]) -> None:
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in colunas]
    if faltantes:
        raise ErroValidacaoArquivo(
            f"Cabeçalho inválido: colunas obrigatórias ausentes: {', '.join(faltantes)} (AC-045)."
        )


def _validar_linha(
    db: Session,
    linha: dict[str, str],
    numero_linha: int,
    numeros_serie_vistos: set[str],
) -> tuple[Ativo | None, list[dict]]:
    erros: list[dict] = []

    def registrar_erro(campo: str, valor: str, motivo: str) -> None:
        erros.append({"campo": campo, "valor_recebido": valor, "motivo": motivo})

    nome = linha.get("nome", "").strip()
    if len(nome) < 3:
        registrar_erro("nome", nome, "Nome deve ter ao menos 3 caracteres.")

    tipo = linha.get("tipo", "").strip().upper()
    if tipo not in {"HARDWARE", "SOFTWARE"}:
        registrar_erro("tipo", tipo, "Tipo deve ser HARDWARE ou SOFTWARE.")

    nome_categoria = linha.get("categoria", "").strip()
    categoria = db.scalar(select(Categoria).where(Categoria.nome == nome_categoria))
    if categoria is None:
        registrar_erro("categoria", nome_categoria, "Categoria não encontrada.")

    nome_fornecedor = linha.get("fornecedor", "").strip()
    fornecedor = db.scalar(select(Fornecedor).where(Fornecedor.razao_social == nome_fornecedor))
    if fornecedor is None:
        registrar_erro("fornecedor", nome_fornecedor, "Fornecedor não encontrado.")

    numero_serie = linha.get("numero_serie", "").strip() or None
    chave_licenca = linha.get("chave_licenca", "").strip() or None
    if tipo == "HARDWARE" and not numero_serie:
        registrar_erro("numero_serie", "", "Obrigatório para ativos do tipo HARDWARE (BR-002).")
    if tipo == "SOFTWARE" and not chave_licenca:
        registrar_erro("chave_licenca", "", "Obrigatória para ativos do tipo SOFTWARE (BR-002).")

    if numero_serie:
        if numero_serie in numeros_serie_vistos:
            registrar_erro(
                "numero_serie", numero_serie, "Duplicado dentro do próprio arquivo (AC-046)."
            )
        elif db.scalar(select(Ativo).where(Ativo.numero_serie == numero_serie)) is not None:
            registrar_erro("numero_serie", numero_serie, "Já cadastrado na base (BR-001).")

    valor_data_aquisicao = linha.get("data_aquisicao", "").strip()
    data_aquisicao: date | None = None
    try:
        data_aquisicao = datetime.strptime(valor_data_aquisicao, "%Y-%m-%d").date()
        if data_aquisicao > date.today():
            registrar_erro("data_aquisicao", valor_data_aquisicao, "Não pode ser futura (BR-003).")
    except ValueError:
        registrar_erro("data_aquisicao", valor_data_aquisicao, "Formato esperado AAAA-MM-DD.")

    valor_valor_compra = linha.get("valor_compra", "").strip()
    valor_compra: Decimal | None = None
    try:
        valor_compra = Decimal(valor_valor_compra)
        if valor_compra <= 0:
            registrar_erro("valor_compra", valor_valor_compra, "Deve ser maior que zero (BR-004).")
    except InvalidOperation:
        registrar_erro("valor_compra", valor_valor_compra, "Valor decimal inválido.")

    if erros:
        return None, [{"numero_linha": numero_linha, **erro} for erro in erros]

    assert categoria is not None
    assert fornecedor is not None
    assert data_aquisicao is not None
    assert valor_compra is not None

    if numero_serie:
        numeros_serie_vistos.add(numero_serie)

    ativo = Ativo(
        nome=nome,
        tipo=tipo,
        categoria_id=categoria.id,
        fornecedor_id=fornecedor.id,
        numero_serie=numero_serie,
        chave_licenca=chave_licenca,
        data_aquisicao=data_aquisicao,
        valor_compra=valor_compra,
        vida_util_meses=categoria.vida_util_meses,
        localizacao=linha.get("localizacao", "").strip() or None,
        data_source="importacao",
    )
    return ativo, []


def processar_importacao(
    db: Session, nome_arquivo: str, conteudo: bytes, usuario: Usuario
) -> LoteImportacao:
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise ErroValidacaoArquivo("Arquivo excede o limite de 5 MB.")

    tabela = _ler_planilha(nome_arquivo, conteudo)
    _validar_cabecalho(list(tabela.columns))

    if len(tabela) > LINHAS_MAXIMAS:
        raise ErroValidacaoArquivo("Arquivo excede o limite de 5.000 linhas.")

    lote = LoteImportacao(
        nome_arquivo=nome_arquivo, usuario_id=usuario.id, total_processado=len(tabela)
    )
    db.add(lote)
    db.flush()

    numeros_serie_vistos: set[str] = set()
    aceitos: list[Ativo] = []
    erros: list[dict] = []

    for indice, linha_bruta in enumerate(tabela.to_dict(orient="records"), start=2):
        ativo, erros_linha = _validar_linha(db, linha_bruta, indice, numeros_serie_vistos)
        if ativo is not None:
            aceitos.append(ativo)
        else:
            erros.extend(erros_linha)

    for ativo in aceitos:
        ativo.lote_importacao_id = lote.id
        db.add(ativo)
    for erro in erros:
        db.add(ErroImportacao(lote_id=lote.id, **erro))

    lote.total_aceito = len(aceitos)
    lote.total_rejeitado = len(erros)
    db.commit()
    db.refresh(lote)
    return lote

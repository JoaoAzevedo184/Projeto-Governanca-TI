import io
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import registrar_auditoria
from app.core.exceptions import ErroValidacaoArquivo
from app.core.metrics import IMPORTACOES_TOTAL
from app.models.ativo import Ativo
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.importacao import ErroImportacao, LoteImportacao
from app.models.usuario import Usuario
from app.utils.datas import hoje
from app.utils.mascaramento import mascarar_chave

COLUNAS_OBRIGATORIAS = ["nome", "tipo", "categoria", "fornecedor", "data_aquisicao", "valor_compra"]
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024
LINHAS_MAXIMAS = 5_000
# Origens que uma linha pode declarar na coluna opcional `data_source` (FR-008, AC-071). Das
# origens do projeto (enumeracoes.md), são as que existem para `ativo` (modelo-fisico.md): `manual`
# é o cadastro pela API, e `endoflife`, `nvd` e `sintetico` são de outras tabelas.
ORIGEM_PADRAO = "importacao"
ORIGENS_ACEITAS = ("compras_gov", ORIGEM_PADRAO)


def _coluna(atributo, propriedade: str) -> int:
    """Propriedade (`length`, `precision`, `scale`) do tipo da coluna no modelo: os limites do
    importador vêm do banco, não de um número repetido aqui."""
    return int(getattr(atributo.type, propriedade))


# Texto que o importador grava em `ativo`: recusado na linha se passar do tamanho da coluna.
LIMITE_TEXTO = {
    campo: _coluna(getattr(Ativo, campo), "length")
    for campo in ("nome", "numero_serie", "chave_licenca", "localizacao")
}
# O que `valor_recebido` do relatório de erros comporta: o valor mostrado é cortado nele.
LIMITE_VALOR_RECEBIDO = _coluna(ErroImportacao.valor_recebido, "length")
CASAS_DECIMAIS = _coluna(Ativo.valor_compra, "scale")
DIGITOS_INTEIROS = _coluna(Ativo.valor_compra, "precision") - CASAS_DECIMAIS
CENTAVO = Decimal(1).scaleb(-CASAS_DECIMAIS)


def _ler_planilha(nome_arquivo: str, conteudo: bytes) -> pd.DataFrame:
    nome = nome_arquivo.lower()
    if not nome.endswith((".csv", ".xlsx")):
        raise ErroValidacaoArquivo("Extensão não suportada: envie um arquivo .csv ou .xlsx.")
    buffer = io.BytesIO(conteudo)
    try:
        if nome.endswith(".csv"):
            return pd.read_csv(buffer, dtype=str, keep_default_na=False)
        return pd.read_excel(buffer, dtype=str).fillna("")
    except (ValueError, zipfile.BadZipFile, pd.errors.OptionError) as exc:
        # ValueError cobre o que o pandas levanta ao ler: bytes que não são UTF-8
        # (UnicodeDecodeError), CSV sem colunas ou malformado (EmptyDataError, ParserError) e
        # conteúdo que não é XLSX. BadZipFile: XLSX truncado. OptionError: zip que não é planilha.
        raise ErroValidacaoArquivo(
            "Arquivo ilegível: envie um CSV em UTF-8 ou um XLSX válido."
        ) from exc


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
    chaves_vistas: set[str],
) -> tuple[Ativo | None, list[dict]]:
    erros: list[dict] = []

    def registrar_erro(campo: str, valor: str, motivo: str) -> None:
        erros.append(
            {"campo": campo, "valor_recebido": valor[:LIMITE_VALOR_RECEBIDO], "motivo": motivo}
        )

    def acima_do_limite(campo: str, valor: str, mostrado: str | None = None) -> bool:
        if len(valor) <= LIMITE_TEXTO[campo]:
            return False
        registrar_erro(
            campo,
            valor if mostrado is None else mostrado,
            f"Excede o limite de {LIMITE_TEXTO[campo]} caracteres.",
        )
        return True

    nome = linha.get("nome", "").strip()
    if len(nome) < 3:
        registrar_erro("nome", nome, "Nome deve ter ao menos 3 caracteres.")
    else:
        acima_do_limite("nome", nome)

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

    if numero_serie and not acima_do_limite("numero_serie", numero_serie):
        if numero_serie in numeros_serie_vistos:
            registrar_erro(
                "numero_serie", numero_serie, "Duplicado dentro do próprio arquivo (AC-046)."
            )
        elif db.scalar(select(Ativo).where(Ativo.numero_serie == numero_serie)) is not None:
            registrar_erro("numero_serie", numero_serie, "Já cadastrado na base (BR-001).")

    # O relatório de erros guarda a chave mascarada, também quando é longa demais (RI-08).
    if chave_licenca and not acima_do_limite(
        "chave_licenca", chave_licenca, mascarar_chave(chave_licenca)
    ):
        # BR-039.
        if chave_licenca in chaves_vistas:
            registrar_erro(
                "chave_licenca",
                mascarar_chave(chave_licenca),
                "Duplicada dentro do próprio arquivo (BR-039).",
            )
        elif db.scalar(select(Ativo.id).where(Ativo.chave_licenca == chave_licenca)) is not None:
            registrar_erro(
                "chave_licenca", mascarar_chave(chave_licenca), "Já cadastrada na base (BR-039)."
            )

    localizacao = linha.get("localizacao", "").strip() or None
    if localizacao:
        acima_do_limite("localizacao", localizacao)

    valor_origem = linha.get("data_source", "").strip()
    origem = valor_origem.lower() or ORIGEM_PADRAO
    if origem not in ORIGENS_ACEITAS:
        registrar_erro(
            "data_source", valor_origem, f"Origem deve ser {' ou '.join(ORIGENS_ACEITAS)}."
        )

    valor_data_aquisicao = linha.get("data_aquisicao", "").strip()
    data_aquisicao: date | None = None
    try:
        data_aquisicao = datetime.strptime(valor_data_aquisicao, "%Y-%m-%d").date()
        if data_aquisicao > hoje():
            registrar_erro("data_aquisicao", valor_data_aquisicao, "Não pode ser futura (BR-003).")
    except ValueError:
        registrar_erro("data_aquisicao", valor_data_aquisicao, "Formato esperado AAAA-MM-DD.")

    valor_valor_compra = linha.get("valor_compra", "").strip()
    valor_compra: Decimal | None = None
    try:
        valor_compra = Decimal(valor_valor_compra)
        if valor_compra <= 0:
            registrar_erro("valor_compra", valor_valor_compra, "Deve ser maior que zero (BR-004).")
        elif valor_compra.adjusted() + 1 > DIGITOS_INTEIROS:
            registrar_erro(
                "valor_compra",
                valor_valor_compra,
                f"Parte inteira acima de {DIGITOS_INTEIROS} dígitos inteiros (limite da coluna).",
            )
        # `quantize` levanta InvalidOperation para Infinity (e `<=` para NaN): "valor inválido".
        elif valor_compra != valor_compra.quantize(CENTAVO):
            registrar_erro(
                "valor_compra",
                valor_valor_compra,
                f"Mais de {CASAS_DECIMAIS} casas decimais (o valor não é arredondado).",
            )
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
    if chave_licenca:
        chaves_vistas.add(chave_licenca)

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
        localizacao=localizacao,
        data_source=origem,
    )
    return ativo, []


def processar_importacao(
    db: Session, nome_arquivo: str, conteudo: bytes, usuario: Usuario
) -> LoteImportacao:
    """Importa o arquivo e conta o resultado em `itam_importacoes_total`."""
    try:
        lote = _processar(db, nome_arquivo, conteudo, usuario)
    except ErroValidacaoArquivo:
        IMPORTACOES_TOTAL.labels(resultado="arquivo_invalido").inc()
        raise
    if lote.total_rejeitado == 0:
        resultado = "sucesso"
    else:
        resultado = "parcial" if lote.total_aceito else "rejeitada"
    IMPORTACOES_TOTAL.labels(resultado=resultado).inc()
    return lote


def _processar(db: Session, nome_arquivo: str, conteudo: bytes, usuario: Usuario) -> LoteImportacao:
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise ErroValidacaoArquivo("Arquivo excede o limite de 5 MB.")

    if not conteudo.strip():
        raise ErroValidacaoArquivo("Arquivo vazio: envie um arquivo com cabeçalho e linhas.")

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
    chaves_vistas: set[str] = set()
    aceitos: list[Ativo] = []
    erros: list[dict] = []

    for indice, linha_bruta in enumerate(tabela.to_dict(orient="records"), start=2):
        ativo, erros_linha = _validar_linha(
            db, linha_bruta, indice, numeros_serie_vistos, chaves_vistas
        )
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
    db.flush()  # atribui o id de cada ativo, que a auditoria precisa

    # BR-030 / AC-057: auditoria na mesma transação do lote (um único commit): se algo falhar,
    # ativos, lote e auditorias saem juntos. Mesma operação e entidade de `criar_ativo`.
    for ativo in aceitos:
        registrar_auditoria(
            db,
            usuario_id=usuario.id,
            operacao="CRIAR",
            entidade="ativo",
            entidade_id=ativo.id,
            detalhe={"lote_importacao_id": lote.id, "data_source": ativo.data_source},
        )
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        operacao="CRIAR",
        entidade="lote_importacao",
        entidade_id=lote.id,
        detalhe={
            "nome_arquivo": nome_arquivo,
            "total_processado": lote.total_processado,
            "total_aceito": lote.total_aceito,
            "total_rejeitado": lote.total_rejeitado,
        },
    )
    db.commit()
    db.refresh(lote)
    return lote

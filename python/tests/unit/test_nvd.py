"""Coletor `nvd` (D.4): contagem de CVEs por produto, ciclo e severidade CVSS v3, sem arquivo pela
metade e sem a chave da API em lugar nenhum.

Sem rede: o httpx responde com `httpx.MockTransport` servindo as respostas reais gravadas em
`tests/fixtures/nvd/coleta_2026-10-06/` (ver ORIGEM.md). O que não é resposta da API (erro de
transporte, 403/503 sem corpo, corpo que não é da API) é construído no teste, porque a API real
não devolve isso sob demanda. A chave usada nos testes é falsa.
"""

import json
from pathlib import Path

import httpx
import pytest

from collectors import endoflife, nvd
from collectors.nvd import Ciclo, Configuracao, ErroColeta, Produto

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
COLETA = FIXTURES / "nvd" / "coleta_2026-10-06"
ARQUIVOS = {p.name: p.read_bytes() for p in sorted(COLETA.glob("*.json"))}
CHAVE_FALSA = "chave-falsa-0000-nao-e-segredo"
CPE_PG = "cpe:2.3:a:postgresql:postgresql"
PG16 = Ciclo(ciclo="16", cpe=CPE_PG, de="16.0", ate="17.0")
WIN = Ciclo(ciclo="2022", cpe="cpe:2.3:o:microsoft:windows_server_2022")


def _configuracao(**ajustes) -> Configuracao:
    base = {
        "base_url": "https://services.nvd.nist.gov",
        "endpoint": "/rest/json/cves/2.0",
        "produtos": [Produto("postgresql", [PG16]), Produto("windows-server", [WIN])],
        "intervalo_segundos": 6.5,
        "intervalo_com_chave_segundos": 0.7,
        "tentativas": 4,
        "espera_inicial_segundos": 2.0,
        "espera_maxima_segundos": 60.0,
    }
    return Configuracao(**{**base, **ajustes})


def _cliente(handler, **kw) -> tuple[httpx.Client, list[httpx.Request]]:
    pedidos: list[httpx.Request] = []

    def registrar(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return handler(pedido)

    cliente = httpx.Client(
        base_url="https://services.nvd.nist.gov", transport=httpx.MockTransport(registrar), **kw
    )
    return cliente, pedidos


def _chave(parametros) -> tuple:
    """Os parâmetros como o servidor os vê: tudo texto, em ordem fixa."""
    return tuple(sorted((k, str(v)) for k, v in parametros.items()))


def _por_parametros(configuracao: Configuracao) -> dict[tuple, str]:
    """Os parâmetros que o coletor envia -> o arquivo real gravado para eles."""
    mapa = {}
    for produto in configuracao.produtos:
        for ciclo in produto.ciclos:
            for severidade in (*nvd.SEVERIDADES, None):
                chave = _chave(nvd.parametros(configuracao, ciclo, severidade))
                mapa[chave] = nvd.nome_arquivo(produto.produto, ciclo.ciclo, severidade)
    return mapa


def _api(configuracao: Configuracao):
    mapa = _por_parametros(configuracao)

    def handler(pedido: httpx.Request) -> httpx.Response:
        chave = _chave(dict(pedido.url.params))
        return httpx.Response(200, content=ARQUIVOS[mapa[chave]])

    return handler


def test_a_coleta_gravada_tem_so_respostas_pequenas_no_formato_da_api():
    assert ARQUIVOS, "coleta gravada ausente"
    for nome, corpo in ARQUIVOS.items():
        dados = json.loads(corpo)
        assert isinstance(dados["totalResults"], int), nome
        assert (
            dados["resultsPerPage"] <= 1 and len(dados["vulnerabilities"]) <= 1
        ), nome  # 0 sem CVE
    assert sum(len(c) for c in ARQUIVOS.values()) < 5 * 1024 * 1024  # poucos MB, não centenas


def test_configuracao_real_respeita_os_limites_da_api_e_o_volume():
    configuracao = nvd.carregar_configuracao()

    assert configuracao.tamanho_pagina == 1  # só o total interessa: volume mínimo por consulta
    # sem chave: 5 requisições por 30 s; com chave: 50 por 30 s
    assert configuracao.intervalo_segundos >= 30 / 5
    assert 30 / 50 <= configuracao.intervalo_com_chave_segundos < configuracao.intervalo_segundos
    assert configuracao.base_url.startswith("https://")
    nomes = [p.produto for p in configuracao.produtos]
    assert nomes and len(set(nomes)) == len(nomes)
    for produto in configuracao.produtos:
        assert produto.ciclos
        for ciclo in produto.ciclos:
            assert ciclo.cpe.startswith("cpe:2.3:")
            assert (ciclo.de is None) == (ciclo.ate is None)  # faixa de versão, ou nenhuma
    consultas = sum(len(p.ciclos) for p in configuracao.produtos) * 5
    assert consultas <= 100  # sem consulta genérica: poucas, uma por produto, ciclo e severidade


def test_a_configuracao_do_nvd_so_cita_produtos_e_ciclos_do_endoflife():
    produtos_eol = endoflife.carregar_configuracao().produtos
    pasta = FIXTURES / "endoflife" / "coleta_2026-10-06"

    for produto in nvd.carregar_configuracao().produtos:
        assert produto.produto in produtos_eol
        ciclos_eol = {
            c["cycle"] for c in json.loads((pasta / f"{produto.produto}.json").read_text())
        }
        assert {c.ciclo for c in produto.ciclos} <= ciclos_eol


def test_toda_consulta_da_configuracao_real_tem_resposta_gravada():
    configuracao = nvd.carregar_configuracao()

    esperados = set(_por_parametros(configuracao).values())

    assert esperados == set(ARQUIVOS)


@pytest.mark.parametrize(
    "ajuste",
    [
        {"tentativas": 0},
        {"produtos": []},
        {"tamanho_pagina": 0},
        {"tamanho_pagina": 11},
        {"intervalo_segundos": 5.9},
        {"intervalo_com_chave_segundos": 0.5},
        {"produtos": [Produto("a", [PG16]), Produto("a", [WIN])]},
        {"produtos": [Produto("a", [])]},
        {"produtos": [Produto("a", [PG16, PG16])]},
        {"produtos": [Produto("a", [Ciclo("1", "cpe:2.3:a:x:y", de="1.0")])]},
        {"produtos": [Produto("a", [Ciclo("1", "texto qualquer")])]},
    ],
    ids=[
        "sem-tentativas",
        "sem-produtos",
        "pagina-zero",
        "pagina-grande-demais",
        "abaixo-do-limite-sem-chave",
        "abaixo-do-limite-com-chave",
        "produto-repetido",
        "produto-sem-ciclos",
        "ciclo-repetido",
        "faixa-so-com-inicio",
        "cpe-invalido",
    ],
)
def test_configuracao_invalida_e_recusada(ajuste):
    with pytest.raises(ErroColeta):
        _configuracao(**ajuste)


def test_configuracao_sem_produtos_no_arquivo_e_recusada(tmp_path):
    arquivo = tmp_path / "config.yaml"
    arquivo.write_text("nvd:\n  base_url: https://x\n  endpoint: /e\n  produtos: []\n")

    with pytest.raises(ErroColeta, match="produtos vazio"):
        nvd.carregar_configuracao(arquivo)


def test_parametros_com_faixa_de_versao_e_severidade():
    configuracao = _configuracao()

    assert nvd.parametros(configuracao, PG16, "HIGH") == {
        "virtualMatchString": CPE_PG,
        "versionStart": "16.0",
        "versionStartType": "including",
        "versionEnd": "17.0",
        "versionEndType": "excluding",
        "cvssV3Severity": "HIGH",
        "resultsPerPage": 1,
    }


def test_parametros_sem_faixa_e_sem_severidade_para_o_total():
    configuracao = _configuracao()

    assert nvd.parametros(configuracao, WIN, None) == {
        "virtualMatchString": "cpe:2.3:o:microsoft:windows_server_2022",
        "resultsPerPage": 1,
    }


def test_nome_do_arquivo_inclui_produto_ciclo_e_severidade_ou_total():
    assert nvd.nome_arquivo("postgresql", "16", "HIGH") == "postgresql_16_HIGH.json"
    assert nvd.nome_arquivo("windows-server", "2022", None) == "windows-server_2022_total.json"
    assert nvd.nome_arquivo("mysql", "8.4", "LOW") == "mysql_8.4_LOW.json"


def test_coleta_as_cinco_consultas_do_ciclo_na_ordem_com_o_corpo_bruto_e_o_intervalo():
    configuracao = _configuracao()
    cliente, pedidos = _cliente(_api(configuracao))
    esperas: list[float] = []

    arquivos = nvd.coletar_ciclo(cliente, configuracao, "postgresql", PG16, esperas.append, 6.5)

    assert [nome for nome, _ in arquivos] == [
        "postgresql_16_LOW.json",
        "postgresql_16_MEDIUM.json",
        "postgresql_16_HIGH.json",
        "postgresql_16_CRITICAL.json",
        "postgresql_16_total.json",
    ]
    assert all(corpo == ARQUIVOS[nome] for nome, corpo in arquivos)  # byte a byte
    assert len(pedidos) == 5
    assert esperas == [6.5] * 4  # entre as consultas, nenhuma depois da última


def test_executar_grava_tudo_inteiro_deixa_o_total_por_ultimo_e_nao_deixa_temporario(
    tmp_path, monkeypatch
):
    configuracao = _configuracao()
    cliente, _ = _cliente(_api(configuracao))
    ordem: list[str] = []
    original = nvd.gravar_atomico
    monkeypatch.setattr(nvd, "gravar_atomico", lambda d, c: (ordem.append(d.name), original(d, c)))
    destino = tmp_path / "raw" / "nvd" / "2026-10-06"

    resultado = nvd.executar(configuracao, destino, cliente, lambda _: None)

    assert resultado.falhas == {} and resultado.pulados == []
    assert ordem[:5] == [  # o total é o marcador: vai por último, dentro de cada ciclo
        "postgresql_16_total.json",
        "postgresql_16_CRITICAL.json",
        "postgresql_16_HIGH.json",
        "postgresql_16_MEDIUM.json",
        "postgresql_16_LOW.json",
    ]
    assert len(resultado.gravados) == 10
    for arquivo in destino.iterdir():
        assert arquivo.read_bytes() == ARQUIVOS[arquivo.name]
    assert not [p for p in destino.iterdir() if p.name.endswith(".tmp")]


def test_rodar_de_novo_no_mesmo_dia_pula_o_ciclo_completo_sem_pedir_nada(tmp_path):
    configuracao = _configuracao()
    destino = tmp_path / "2026-10-06"
    cliente, _ = _cliente(_api(configuracao))
    nvd.executar(configuracao, destino, cliente, lambda _: None)
    cliente2, pedidos = _cliente(_api(configuracao))

    resultado = nvd.executar(configuracao, destino, cliente2, lambda _: None)

    assert sorted(resultado.pulados) == ["postgresql_16", "windows-server_2022"]
    assert resultado.gravados == [] and pedidos == []


def test_o_intervalo_vale_entre_consultas_e_entre_ciclos_e_o_do_cliente_prevalece(tmp_path):
    configuracao = _configuracao()
    cliente, _ = _cliente(_api(configuracao))
    esperas: list[float] = []

    nvd.executar(configuracao, tmp_path / "d", cliente, esperas.append, intervalo_segundos=0.7)

    assert esperas == [0.7] * 9  # 5 consultas + 5 consultas, com uma pausa entre cada par


@pytest.mark.parametrize(
    ("respostas", "esperas"),
    [
        pytest.param([503, 503, 200], [2.0, 4.0], id="espera-dobra-a-cada-tentativa"),
        pytest.param([429, 200], [2.0], id="429-e-repetido"),
    ],
)
def test_erros_temporarios_sao_repetidos_com_espera_crescente(respostas, esperas):
    configuracao = _configuracao()
    fila = list(respostas)

    def handler(pedido):
        status = fila.pop(0)
        if status == 200:
            return httpx.Response(200, content=ARQUIVOS["postgresql_16_total.json"])
        return httpx.Response(status)

    cliente, pedidos = _cliente(handler)
    dormidas: list[float] = []

    corpo = nvd.consultar(
        cliente, configuracao, nvd.parametros(configuracao, PG16, None), dormidas.append
    )

    assert corpo == ARQUIVOS["postgresql_16_total.json"]
    assert len(pedidos) == len(respostas)
    assert dormidas == esperas


def test_403_do_limite_de_requisicoes_nao_e_repetido_e_nao_grava_nada(tmp_path):
    configuracao = _configuracao()
    cliente, pedidos = _cliente(lambda _: httpx.Response(403))
    destino = tmp_path / "2026-10-06"

    resultado = nvd.executar(configuracao, destino, cliente, lambda _: None)

    assert set(resultado.falhas) == {"postgresql_16", "windows-server_2022"}
    assert all(m.startswith("HTTP 403") for m in resultado.falhas.values())
    assert len(pedidos) == 2  # uma por ciclo: sem insistir contra o bloqueio
    assert not destino.exists()


def test_erro_no_meio_do_ciclo_nao_deixa_nenhuma_das_consultas_anteriores_no_disco(tmp_path):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])], tentativas=1)
    mapa = _por_parametros(configuracao)

    def handler(pedido):
        chave = _chave(dict(pedido.url.params))
        if mapa[chave].endswith("HIGH.json"):
            raise httpx.ConnectError("conexão caiu", request=pedido)
        return httpx.Response(200, content=ARQUIVOS[mapa[chave]])

    cliente, _ = _cliente(handler)
    destino = tmp_path / "2026-10-06"

    resultado = nvd.executar(configuracao, destino, cliente, lambda _: None)

    assert resultado.falhas == {"postgresql_16": "rede: ConnectError após 1 tentativas"}
    assert not destino.exists()


@pytest.mark.parametrize(
    "corpo",
    [
        b"<html>em manutencao</html>",
        b"[]",
        b"{}",
        b'{"totalResults": "4", "vulnerabilities": []}',
        b'{"totalResults": 4}',
        b'{"totalResults": 4, "vulnerabilities": {}}',
        b'{"totalResults": -1, "vulnerabilities": []}',
    ],
    ids=[
        "nao-json",
        "json-nao-e-objeto",
        "sem-campos",
        "total-nao-e-inteiro",
        "sem-vulnerabilities",
        "vulnerabilities-nao-e-lista",
        "total-negativo",
    ],
)
def test_resposta_200_fora_do_formato_da_api_e_recusada_sem_gravar(tmp_path, corpo):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    cliente, _ = _cliente(lambda _: httpx.Response(200, content=corpo))
    destino = tmp_path / "2026-10-06"

    resultado = nvd.executar(configuracao, destino, cliente, lambda _: None)

    assert "formato" in resultado.falhas["postgresql_16"]
    assert not destino.exists()


def test_a_falha_de_um_ciclo_nao_impede_os_outros(tmp_path):
    configuracao = _configuracao()
    mapa = _por_parametros(configuracao)

    def handler(pedido):
        chave = _chave(dict(pedido.url.params))
        if mapa[chave].startswith("postgresql"):
            return httpx.Response(403)
        return httpx.Response(200, content=ARQUIVOS[mapa[chave]])

    cliente, _ = _cliente(handler)
    destino = tmp_path / "2026-10-06"

    resultado = nvd.executar(configuracao, destino, cliente, lambda _: None)

    assert list(resultado.falhas) == ["postgresql_16"]
    assert len(resultado.gravados) == 5
    assert all(p.name.startswith("windows-server_2022_") for p in destino.iterdir())


def _main_com(monkeypatch, tmp_path, configuracao, handler, chave=None):
    cliente_real = httpx.Client
    clientes: list[httpx.Client] = []

    def fabrica(**kw):
        cliente = cliente_real(transport=httpx.MockTransport(handler), **kw)
        clientes.append(cliente)
        return cliente

    monkeypatch.setattr(nvd, "carregar_configuracao", lambda: configuracao)
    monkeypatch.setattr(nvd, "DATASET_DIR", tmp_path)
    monkeypatch.setattr(nvd.httpx, "Client", fabrica)
    esperas: list[float] = []
    monkeypatch.setattr(nvd.time, "sleep", esperas.append)
    if chave is None:
        monkeypatch.delenv("NVD_API_KEY", raising=False)
    else:
        monkeypatch.setenv("NVD_API_KEY", chave)
    return esperas


def test_main_sem_chave_nao_envia_cabecalho_e_usa_o_intervalo_sem_chave(
    tmp_path, monkeypatch, capsys
):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    cabecalhos: list[dict] = []
    api = _api(configuracao)

    def handler(pedido):
        cabecalhos.append(dict(pedido.headers))
        return api(pedido)

    esperas = _main_com(monkeypatch, tmp_path, configuracao, handler)

    codigo = nvd.main()

    data = nvd.date.today().isoformat()
    assert codigo == 0
    assert (tmp_path / "raw" / "nvd" / data / "postgresql_16_total.json").exists()
    assert all("apikey" not in c for c in cabecalhos)
    assert esperas == [6.5] * 4
    assert "5 arquivos" in capsys.readouterr().out


def test_main_com_chave_envia_o_cabecalho_e_usa_o_intervalo_com_chave(tmp_path, monkeypatch):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    cabecalhos: list[dict] = []
    api = _api(configuracao)

    def handler(pedido):
        cabecalhos.append(dict(pedido.headers))
        return api(pedido)

    esperas = _main_com(monkeypatch, tmp_path, configuracao, handler, chave=CHAVE_FALSA)

    assert nvd.main() == 0

    assert all(c["apikey"] == CHAVE_FALSA for c in cabecalhos) and len(cabecalhos) == 5
    assert esperas == [0.7] * 4


@pytest.mark.parametrize("chave", ["", "   "], ids=["vazia", "so-espacos"])
def test_chave_vazia_e_tratada_como_ausente(tmp_path, monkeypatch, chave):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    cabecalhos: list[dict] = []
    api = _api(configuracao)

    def handler(pedido):
        cabecalhos.append(dict(pedido.headers))
        return api(pedido)

    esperas = _main_com(monkeypatch, tmp_path, configuracao, handler, chave=chave)

    assert nvd.main() == 0

    assert all("apikey" not in c for c in cabecalhos)
    assert esperas == [6.5] * 4


@pytest.mark.parametrize(
    "falha",
    [
        pytest.param(lambda p: httpx.Response(403), id="403"),
        pytest.param(lambda p: httpx.Response(503), id="503"),
        pytest.param(lambda p: httpx.Response(200, content=b"<html>"), id="formato"),
        pytest.param(
            lambda p: (_ for _ in ()).throw(httpx.ConnectError("x", request=p)), id="rede"
        ),
    ],
)
def test_a_chave_nunca_aparece_na_saida_nem_nas_mensagens_de_erro(
    tmp_path, monkeypatch, capsys, falha
):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])], tentativas=2)
    _main_com(monkeypatch, tmp_path, configuracao, falha, chave=CHAVE_FALSA)

    codigo = nvd.main()

    saida = capsys.readouterr()
    assert codigo == 1
    assert CHAVE_FALSA not in saida.out + saida.err
    assert not (tmp_path / "raw").exists()


def test_a_chave_nunca_vai_para_os_arquivos_gravados_nem_para_a_configuracao(
    tmp_path, monkeypatch, capsys
):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    _main_com(monkeypatch, tmp_path, configuracao, _api(configuracao), chave=CHAVE_FALSA)

    assert nvd.main() == 0

    gravados = list((tmp_path / "raw" / "nvd").rglob("*"))
    assert gravados and all(
        CHAVE_FALSA.encode() not in p.read_bytes() for p in gravados if p.is_file()
    )
    assert CHAVE_FALSA not in capsys.readouterr().out
    assert CHAVE_FALSA not in repr(configuracao)


def test_main_sai_com_1_e_mostra_a_falha_quando_algum_ciclo_falha(tmp_path, monkeypatch, capsys):
    configuracao = _configuracao(produtos=[Produto("postgresql", [PG16])])
    _main_com(monkeypatch, tmp_path, configuracao, lambda _: httpx.Response(403))

    codigo = nvd.main()

    saida = capsys.readouterr()
    assert codigo == 1
    assert "falha em postgresql_16: HTTP 403" in saida.err
    assert not (tmp_path / "raw").exists()

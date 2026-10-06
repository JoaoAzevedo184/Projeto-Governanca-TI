"""Coletor `endoflife` (D.3): um arquivo por produto, como a API respondeu, sem arquivo pela metade.

Sem rede: o httpx responde com `httpx.MockTransport` servindo as respostas reais gravadas em
`tests/fixtures/endoflife/coleta_2026-10-06/` (ver ORIGEM.md). O que não é resposta da API
(erro de transporte, 404/503 sem corpo, corpo que não é da API) é construído no teste, porque a
API real não devolve isso sob demanda.
"""

import json
import os
from pathlib import Path

import httpx
import pytest

from collectors import endoflife
from collectors.endoflife import Configuracao, ErroColeta

COLETA = Path(__file__).resolve().parents[1] / "fixtures" / "endoflife" / "coleta_2026-10-06"
ARQUIVOS = {p.stem: p.read_bytes() for p in sorted(COLETA.glob("*.json"))}


def _configuracao(**ajustes) -> Configuracao:
    base = {
        "base_url": "https://endoflife.date",
        "endpoint": "/api/{produto}.json",
        "produtos": ["postgresql", "nginx"],
        "intervalo_segundos": 1.5,
        "tentativas": 4,
        "espera_inicial_segundos": 2.0,
        "espera_maxima_segundos": 60.0,
    }
    return Configuracao(**{**base, **ajustes})


def _cliente(handler) -> tuple[httpx.Client, list[httpx.Request]]:
    pedidos: list[httpx.Request] = []

    def registrar(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return handler(pedido)

    return httpx.Client(
        base_url="https://endoflife.date", transport=httpx.MockTransport(registrar)
    ), pedidos


def _api(pedido: httpx.Request) -> httpx.Response:
    """A API gravada: `/api/<produto>.json` devolve o arquivo do produto; os demais, 404."""
    produto = pedido.url.path.removeprefix("/api/").removesuffix(".json")
    if produto in ARQUIVOS:
        return httpx.Response(200, content=ARQUIVOS[produto])
    return httpx.Response(404, content=b"Not Found")


def test_a_coleta_gravada_existe_e_cada_arquivo_e_a_lista_de_ciclos_da_api():
    assert 6 <= len(ARQUIVOS) <= 8
    for produto, corpo in ARQUIVOS.items():
        ciclos = json.loads(corpo)
        assert isinstance(ciclos, list) and ciclos, produto
        assert all({"cycle", "releaseDate", "eol"} <= set(c) for c in ciclos), produto


def test_configuracao_real_tem_de_6_a_8_produtos_unicos_e_os_da_coleta_gravada():
    configuracao = endoflife.carregar_configuracao()

    assert 6 <= len(configuracao.produtos) <= 8
    assert len(set(configuracao.produtos)) == len(configuracao.produtos)
    assert sorted(configuracao.produtos) == sorted(ARQUIVOS)
    assert configuracao.base_url.startswith("https://")
    assert "{produto}" in configuracao.endpoint


@pytest.mark.parametrize(
    "ajuste",
    [
        {"tentativas": 0},
        {"produtos": []},
        {"produtos": ["nginx", "nginx"]},
        {"endpoint": "/api/produto.json"},
    ],
    ids=["sem-tentativas", "sem-produtos", "produto-repetido", "endpoint-sem-marcador"],
)
def test_configuracao_invalida_e_recusada(ajuste):
    with pytest.raises(ErroColeta):
        _configuracao(**ajuste)


def test_configuracao_sem_produtos_no_arquivo_e_recusada(tmp_path):
    arquivo = tmp_path / "config.yaml"
    arquivo.write_text(
        "endoflife:\n  base_url: https://x\n  endpoint: /api/{produto}.json\n  produtos: []\n"
    )

    with pytest.raises(ErroColeta, match="produtos vazio"):
        endoflife.carregar_configuracao(arquivo)


def test_coleta_o_corpo_bruto_do_produto_sem_transformacao():
    cliente, pedidos = _cliente(_api)

    corpo = endoflife.coletar_produto(cliente, _configuracao(), "postgresql", lambda _: None)

    assert corpo == ARQUIVOS["postgresql"]  # byte a byte
    assert [p.url.path for p in pedidos] == ["/api/postgresql.json"]


def test_executar_grava_um_arquivo_por_produto_inteiro_e_sem_temporario(tmp_path):
    cliente, _ = _cliente(_api)
    destino = tmp_path / "raw" / "endoflife" / "2026-10-06"
    dormidas: list[float] = []

    resultado = endoflife.executar(_configuracao(), destino, cliente, dormidas.append)

    assert resultado.falhas == {} and resultado.pulados == []
    assert sorted(resultado.gravados) == ["nginx.json", "postgresql.json"]
    for produto in ("postgresql", "nginx"):
        assert (destino / f"{produto}.json").read_bytes() == ARQUIVOS[produto]
    assert sorted(p.name for p in destino.iterdir()) == ["nginx.json", "postgresql.json"]
    assert dormidas == [1.5]  # uma pausa entre os dois produtos, nenhuma antes do primeiro


def test_rodar_de_novo_no_mesmo_dia_pula_o_que_ja_esta_gravado_sem_pedir_nada(tmp_path):
    destino = tmp_path / "2026-10-06"
    cliente, _ = _cliente(_api)
    endoflife.executar(_configuracao(), destino, cliente, lambda _: None)
    cliente2, pedidos = _cliente(_api)

    resultado = endoflife.executar(_configuracao(), destino, cliente2, lambda _: None)

    assert sorted(resultado.pulados) == ["nginx", "postgresql"] and resultado.gravados == []
    assert pedidos == []


@pytest.mark.parametrize(
    ("respostas", "esperas"),
    [
        pytest.param([503, 503, 200], [2.0, 4.0], id="espera-dobra-a-cada-tentativa"),
        pytest.param([429, 200], [2.0], id="429-e-repetido"),
    ],
)
def test_erros_temporarios_sao_repetidos_com_espera_crescente(respostas, esperas):
    fila = list(respostas)

    def handler(pedido):
        status = fila.pop(0)
        if status == 200:
            return httpx.Response(200, content=ARQUIVOS["postgresql"])
        return httpx.Response(status)

    cliente, pedidos = _cliente(handler)
    dormidas: list[float] = []

    corpo = endoflife.coletar_produto(cliente, _configuracao(), "postgresql", dormidas.append)

    assert corpo == ARQUIVOS["postgresql"]
    assert len(pedidos) == len(respostas)
    assert dormidas == esperas


def test_produto_inexistente_na_fonte_e_falha_sem_arquivo_e_nao_e_repetido(tmp_path):
    cliente, pedidos = _cliente(_api)
    destino = tmp_path / "2026-10-06"

    resultado = endoflife.executar(
        _configuracao(produtos=["produto-que-nao-existe"]), destino, cliente, lambda _: None
    )

    assert resultado.falhas == {"produto-que-nao-existe": "HTTP 404 em {}"}
    assert len(pedidos) == 1
    assert not destino.exists()


def test_redirecionamento_nao_e_seguido_nem_gravado(tmp_path):
    """A API redireciona um nome antigo (301) para o novo; o coletor não segue: o produto
    configurado tem de ser o nome certo, e o corpo de um redirecionamento nunca vira coleta."""
    cliente, _ = _cliente(lambda _: httpx.Response(301, headers={"Location": "/api/outro.json"}))
    destino = tmp_path / "2026-10-06"

    resultado = endoflife.executar(_configuracao(), destino, cliente, lambda _: None)

    assert set(resultado.falhas) == {"postgresql", "nginx"}
    assert all(m.startswith("HTTP 301") for m in resultado.falhas.values())
    assert not destino.exists()


def test_esgotadas_as_tentativas_a_falha_nao_grava_nada(tmp_path):
    cliente, pedidos = _cliente(lambda _: httpx.Response(503))
    dormidas: list[float] = []
    destino = tmp_path / "2026-10-06"

    resultado = endoflife.executar(
        _configuracao(produtos=["postgresql"]), destino, cliente, dormidas.append
    )

    assert resultado.falhas == {"postgresql": "HTTP 503 em {}"}
    assert len(pedidos) == 4  # `tentativas`
    assert dormidas == [2.0, 4.0, 8.0]  # sem espera depois da última tentativa
    assert not destino.exists()


def test_erro_de_rede_e_repetido_e_depois_vira_falha_sem_arquivo(tmp_path):
    def handler(pedido):
        raise httpx.ReadTimeout("sem resposta", request=pedido)

    cliente, pedidos = _cliente(handler)
    destino = tmp_path / "2026-10-06"

    resultado = endoflife.executar(
        _configuracao(produtos=["postgresql"], tentativas=3), destino, cliente, lambda _: None
    )

    assert resultado.falhas == {"postgresql": "rede: ReadTimeout após 3 tentativas"}
    assert len(pedidos) == 3
    assert not destino.exists()


@pytest.mark.parametrize(
    "corpo",
    [
        b"<html>em manutencao</html>",
        b"{}",
        b"[]",
        b'[{"cycle": "1"}]',
        b'[{"eol": false}]',
        b"[1, 2]",
    ],
    ids=["nao-json", "objeto", "lista-vazia", "sem-eol", "sem-cycle", "itens-nao-sao-objetos"],
)
def test_resposta_200_fora_do_formato_da_api_e_recusada_sem_gravar(tmp_path, corpo):
    cliente, _ = _cliente(lambda _: httpx.Response(200, content=corpo))
    destino = tmp_path / "2026-10-06"

    resultado = endoflife.executar(
        _configuracao(produtos=["postgresql"]), destino, cliente, lambda _: None
    )

    assert "formato" in resultado.falhas["postgresql"]
    assert not destino.exists()


def test_a_falha_de_um_produto_nao_impede_os_outros(tmp_path):
    cliente, _ = _cliente(_api)
    destino = tmp_path / "2026-10-06"
    dormidas: list[float] = []

    resultado = endoflife.executar(
        _configuracao(produtos=["produto-que-nao-existe", "nginx"]),
        destino,
        cliente,
        dormidas.append,
    )

    assert list(resultado.falhas) == ["produto-que-nao-existe"]
    assert resultado.gravados == ["nginx.json"]
    assert (destino / "nginx.json").read_bytes() == ARQUIVOS["nginx"]
    assert dormidas == [1.5]  # o intervalo vale também depois de um produto que falhou


def test_queda_na_gravacao_nao_deixa_arquivo_pela_metade(tmp_path, monkeypatch):
    cliente, _ = _cliente(_api)
    destino = tmp_path / "2026-10-06"
    trocar = os.replace

    def replace_que_falha(origem, alvo):
        if str(alvo).endswith("nginx.json"):
            raise OSError("queda")
        trocar(origem, alvo)

    monkeypatch.setattr(os, "replace", replace_que_falha)
    with pytest.raises(OSError, match="queda"):
        endoflife.executar(_configuracao(), destino, cliente, lambda _: None)
    assert sorted(p.name for p in destino.iterdir()) == ["postgresql.json"]  # sem .tmp

    monkeypatch.setattr(os, "replace", trocar)
    resultado = endoflife.executar(_configuracao(), destino, cliente, lambda _: None)

    assert resultado.pulados == ["postgresql"] and resultado.gravados == ["nginx.json"]


def test_main_grava_em_raw_com_a_data_do_dia_e_sai_com_0(tmp_path, monkeypatch, capsys):
    cliente_real = httpx.Client
    monkeypatch.setattr(endoflife, "carregar_configuracao", lambda: _configuracao())
    monkeypatch.setattr(endoflife, "DATASET_DIR", tmp_path)
    monkeypatch.setattr(
        endoflife.httpx,
        "Client",
        lambda **kw: cliente_real(transport=httpx.MockTransport(_api), **kw),
    )
    monkeypatch.setattr(endoflife.time, "sleep", lambda _: None)

    codigo_saida = endoflife.main()

    data = endoflife.date.today().isoformat()
    assert codigo_saida == 0
    assert (tmp_path / "raw" / "endoflife" / data / "nginx.json").read_bytes() == ARQUIVOS["nginx"]
    assert "2 arquivos" in capsys.readouterr().out


def test_main_sai_com_1_e_mostra_a_falha_quando_algum_produto_falha(tmp_path, monkeypatch, capsys):
    cliente_real = httpx.Client
    monkeypatch.setattr(
        endoflife, "carregar_configuracao", lambda: _configuracao(produtos=["nao-existe"])
    )
    monkeypatch.setattr(endoflife, "DATASET_DIR", tmp_path)
    monkeypatch.setattr(
        endoflife.httpx,
        "Client",
        lambda **kw: cliente_real(transport=httpx.MockTransport(_api), **kw),
    )

    codigo_saida = endoflife.main()

    saida = capsys.readouterr()
    assert codigo_saida == 1
    assert "falha no produto nao-existe: HTTP 404" in saida.err
    assert not (tmp_path / "raw").exists()

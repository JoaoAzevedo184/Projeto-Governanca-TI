"""Coletor `compras_gov` (D.1): paginação, novas tentativas e gravação sem arquivo pela metade.

Sem rede: o httpx responde com `httpx.MockTransport` servindo as respostas reais gravadas em
`tests/fixtures/compras_gov/` (ver ORIGEM.md). O que não é resposta da API (erro de transporte,
status 503/429 sem corpo, corpo que não é da API) é construído no teste, porque a API real não
devolve isso sob demanda.
"""

import json
from pathlib import Path

import httpx
import pytest

from collectors import compras_gov
from collectors.compras_gov import Configuracao, ErroColeta

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "compras_gov"
P1 = (FIXTURES / "codigoPdm_237_p001.json").read_bytes()
P2 = (FIXTURES / "codigoPdm_237_p002.json").read_bytes()
ALEM = (FIXTURES / "pagina_alem_do_fim.json").read_bytes()
ERRO_400 = (FIXTURES / "erro_tamanho_pagina_minimo.json").read_bytes()
NOME_P1, NOME_P2 = "codigoPdm_237_p001.json", "codigoPdm_237_p002.json"


def _configuracao(**ajustes) -> Configuracao:
    base = {
        "base_url": "https://dadosabertos.compras.gov.br",
        "endpoint": "/modulo-pesquisa-preco/1_consultarMaterial",
        "tipo_codigo": "codigoPdm",
        "codigos": [237],
        "tamanho_pagina": 10,
        "max_paginas_por_codigo": 2,
        "intervalo_segundos": 1.5,
        "tentativas": 4,
        "espera_inicial_segundos": 2.0,
        "espera_maxima_segundos": 60.0,
    }
    return Configuracao(**{**base, **ajustes})


def _cliente(configuracao: Configuracao, handler) -> tuple[httpx.Client, list[httpx.Request]]:
    pedidos: list[httpx.Request] = []

    def registrar(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return handler(pedido)

    cliente = httpx.Client(base_url=configuracao.base_url, transport=httpx.MockTransport(registrar))
    return cliente, pedidos


def _api(pedido: httpx.Request) -> httpx.Response:
    """A API gravada: páginas 1 e 2 do PDM 237, `pagina_alem_do_fim` para as demais e o 400 real
    para o código 999 (o corpo gravado é de `tamanhoPagina=5`; o teste cobre o status)."""
    if pedido.url.params["codigo"] == "999":  # a API recusa com 400; aqui, por código
        return httpx.Response(400, content=ERRO_400)
    corpo = {"1": P1, "2": P2}.get(pedido.url.params["pagina"], ALEM)
    return httpx.Response(200, content=corpo)


def test_configuracao_real_tem_codigos_e_respeita_os_limites_da_api():
    configuracao = compras_gov.carregar_configuracao()

    assert configuracao.codigos and all(isinstance(c, int) for c in configuracao.codigos)
    assert len(set(configuracao.codigos)) == len(configuracao.codigos)
    assert configuracao.tipo_codigo in {"codigoPdm", "codigoItemCatalogo"}
    assert 10 <= configuracao.tamanho_pagina <= 500  # limites medidos na API (erro 400 fora)
    assert configuracao.max_paginas_por_codigo >= 1
    assert configuracao.base_url.startswith("https://")


@pytest.mark.parametrize(
    "ajuste",
    [
        {"tentativas": 0},
        {"tamanho_pagina": 9},
        {"tamanho_pagina": 501},
        {"max_paginas_por_codigo": 0},
    ],
)
def test_configuracao_com_valor_fora_do_limite_e_recusada(ajuste):
    with pytest.raises(ErroColeta):
        _configuracao(**ajuste)


def test_configuracao_sem_codigos_e_recusada(tmp_path):
    arquivo = tmp_path / "config.yaml"
    arquivo.write_text(
        "compras_gov:\n  base_url: https://x\n  endpoint: /e\n  tipo_codigo: codigoPdm\n"
        "  catmat_codigos: []\n"
    )

    with pytest.raises(ErroColeta, match="catmat_codigos vazio"):
        compras_gov.carregar_configuracao(arquivo)


def test_coleta_as_paginas_na_ordem_com_o_corpo_bruto_e_o_intervalo_entre_elas():
    configuracao = _configuracao()
    cliente, pedidos = _cliente(configuracao, _api)
    esperas: list[float] = []

    paginas = compras_gov.coletar_codigo(cliente, configuracao, 237, esperas.append)

    assert paginas == [(NOME_P1, P1), (NOME_P2, P2)]  # byte a byte, sem transformação
    assert [dict(p.url.params) for p in pedidos] == [
        {"tipo": "codigoPdm", "codigo": "237", "pagina": "1", "tamanhoPagina": "10"},
        {"tipo": "codigoPdm", "codigo": "237", "pagina": "2", "tamanhoPagina": "10"},
    ]
    assert esperas == [1.5]  # uma pausa entre as duas requisições, nenhuma depois da última


def test_o_teto_de_paginas_por_codigo_limita_as_requisicoes():
    configuracao = _configuracao(max_paginas_por_codigo=1)
    cliente, pedidos = _cliente(configuracao, _api)

    paginas = compras_gov.coletar_codigo(cliente, configuracao, 237, lambda _: None)

    assert [nome for nome, _ in paginas] == [NOME_P1]
    assert len(pedidos) == 1  # a fonte tem 152 páginas; o teto manda


def test_codigo_sem_resultado_grava_so_a_pagina_1_vazia(tmp_path):
    configuracao = _configuracao()
    cliente, pedidos = _cliente(configuracao, lambda _: httpx.Response(200, content=ALEM))

    paginas = compras_gov.coletar_codigo(cliente, configuracao, 237, lambda _: None)

    assert len(paginas) == 2  # totalPaginas 152 no corpo gravado, teto 2: duas requisições
    assert all(json.loads(corpo)["resultado"] == [] for _, corpo in paginas)


def test_executar_grava_os_arquivos_inteiros_e_deixa_p001_por_ultimo(tmp_path, monkeypatch):
    configuracao = _configuracao()
    cliente, _ = _cliente(configuracao, _api)
    ordem: list[str] = []
    original = compras_gov.gravar_atomico
    monkeypatch.setattr(
        compras_gov, "gravar_atomico", lambda d, c: (ordem.append(d.name), original(d, c))
    )
    destino = tmp_path / "raw" / "compras_gov" / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert ordem == [NOME_P2, NOME_P1]
    assert resultado.falhas == {} and resultado.pulados == []
    assert (destino / NOME_P1).read_bytes() == P1
    assert (destino / NOME_P2).read_bytes() == P2
    assert sorted(p.name for p in destino.iterdir()) == [NOME_P1, NOME_P2]  # sem .tmp


def test_rodar_de_novo_no_mesmo_dia_pula_o_codigo_completo_sem_pedir_nada(tmp_path):
    configuracao = _configuracao()
    destino = tmp_path / "2026-10-05"
    cliente, _ = _cliente(configuracao, _api)
    compras_gov.executar(configuracao, destino, cliente, lambda _: None)
    cliente2, pedidos = _cliente(configuracao, _api)

    resultado = compras_gov.executar(configuracao, destino, cliente2, lambda _: None)

    assert resultado.pulados == [237] and resultado.gravados == []
    assert pedidos == []
    assert (destino / NOME_P1).read_bytes() == P1  # o arquivo anterior segue intacto


@pytest.mark.parametrize(
    ("respostas", "esperas"),
    [
        pytest.param([503, 503, 200], [2.0, 4.0], id="espera-dobra-a-cada-tentativa"),
        pytest.param([429, 200], [2.0], id="429-e-repetido"),
    ],
)
def test_erros_temporarios_sao_repetidos_com_espera_crescente(respostas, esperas):
    configuracao = _configuracao(max_paginas_por_codigo=1)
    fila = list(respostas)

    def handler(pedido):
        status = fila.pop(0)
        return httpx.Response(200, content=P1) if status == 200 else httpx.Response(status)

    cliente, pedidos = _cliente(configuracao, handler)
    dormidas: list[float] = []

    paginas = compras_gov.coletar_codigo(cliente, configuracao, 237, dormidas.append)

    assert paginas == [(NOME_P1, P1)]
    assert len(pedidos) == len(respostas)
    assert dormidas == esperas


def test_retry_after_maior_que_a_espera_prevalece_e_a_espera_tem_teto():
    configuracao = _configuracao(max_paginas_por_codigo=1, espera_maxima_segundos=10.0)
    fila = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(503, headers={"Retry-After": "300"}),
        httpx.Response(200, content=P1),
    ]
    cliente, _ = _cliente(configuracao, lambda _: fila.pop(0))
    dormidas: list[float] = []

    compras_gov.coletar_codigo(cliente, configuracao, 237, dormidas.append)

    assert dormidas == [7.0, 10.0]  # 7 > 2 (espera inicial); 300 limitado a 10


def test_esgotadas_as_tentativas_a_falha_nao_grava_nada(tmp_path):
    configuracao = _configuracao()
    cliente, pedidos = _cliente(configuracao, lambda _: httpx.Response(503))
    dormidas: list[float] = []
    destino = tmp_path / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, dormidas.append)

    assert resultado.falhas == {
        237: "HTTP 503 em {'tipo': 'codigoPdm', 'codigo': 237, " "'pagina': 1, 'tamanhoPagina': 10}"
    }
    assert len(pedidos) == 4  # `tentativas`
    assert dormidas == [2.0, 4.0, 8.0]  # sem espera depois da última tentativa
    assert not destino.exists()


def test_erro_de_rede_e_repetido_e_depois_vira_falha_sem_arquivo(tmp_path):
    configuracao = _configuracao(tentativas=3)

    def handler(pedido):
        raise httpx.ReadTimeout("sem resposta", request=pedido)

    cliente, pedidos = _cliente(configuracao, handler)
    destino = tmp_path / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert resultado.falhas == {237: "rede: ReadTimeout após 3 tentativas"}
    assert len(pedidos) == 3
    assert not destino.exists()


def test_erro_da_pagina_2_nao_deixa_a_pagina_1_no_disco(tmp_path):
    """Falha no meio do código: nada do código é gravado, nem a página que chegou."""
    configuracao = _configuracao(tentativas=2)

    def handler(pedido):
        if pedido.url.params["pagina"] == "1":
            return httpx.Response(200, content=P1)
        raise httpx.ConnectError("conexão caiu", request=pedido)

    cliente, _ = _cliente(configuracao, handler)
    destino = tmp_path / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert list(resultado.falhas) == [237]
    assert not destino.exists()


def test_erro_400_real_da_api_nao_e_repetido(tmp_path):
    configuracao = _configuracao(codigos=[999])
    cliente, pedidos = _cliente(configuracao, _api)
    destino = tmp_path / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert resultado.falhas[999].startswith("HTTP 400")
    assert len(pedidos) == 1
    assert not destino.exists()


@pytest.mark.parametrize(
    "corpo",
    [b"<html>em manutencao</html>", b"{}", b'{"resultado": {}, "totalPaginas": 1}', b"[]"],
    ids=["nao-json", "sem-campos", "resultado-nao-e-lista", "json-nao-e-objeto"],
)
def test_resposta_200_fora_do_formato_da_api_e_recusada_sem_gravar(tmp_path, corpo):
    configuracao = _configuracao()
    cliente, _ = _cliente(configuracao, lambda _: httpx.Response(200, content=corpo))
    destino = tmp_path / "2026-10-05"

    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert "formato" in resultado.falhas[237]
    assert not destino.exists()


def test_a_falha_de_um_codigo_nao_impede_os_outros(tmp_path):
    configuracao = _configuracao(codigos=[999, 237], max_paginas_por_codigo=1)

    def handler(pedido):
        if pedido.url.params["codigo"] == "999":
            return httpx.Response(400, content=ERRO_400)
        return httpx.Response(200, content=P1)

    cliente, _ = _cliente(configuracao, handler)
    destino = tmp_path / "2026-10-05"
    dormidas: list[float] = []

    resultado = compras_gov.executar(configuracao, destino, cliente, dormidas.append)

    assert list(resultado.falhas) == [999]
    assert resultado.gravados == [NOME_P1]
    assert (destino / NOME_P1).read_bytes() == P1
    assert dormidas == [1.5]  # o intervalo vale também entre códigos


def test_gravar_atomico_nao_deixa_arquivo_nem_temporario_se_a_escrita_falha(tmp_path, monkeypatch):
    destino = tmp_path / "a" / "x.json"
    monkeypatch.setattr(compras_gov.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("disco")))

    with pytest.raises(OSError, match="disco"):
        compras_gov.gravar_atomico(destino, b"conteudo")

    assert list(destino.parent.iterdir()) == []


def test_queda_na_gravacao_antes_do_marcador_nao_conta_como_coletado(tmp_path, monkeypatch):
    """p002 é gravada e a troca da p001 falha (disco, queda): sem p001 o código não está completo
    e a próxima execução o coleta de novo em vez de pulá-lo."""
    configuracao = _configuracao()
    cliente, _ = _cliente(configuracao, _api)
    destino = tmp_path / "2026-10-05"
    trocar = compras_gov.os.replace

    def replace_que_falha_na_p001(origem, alvo):
        if str(alvo).endswith(NOME_P1):
            raise OSError("queda")
        trocar(origem, alvo)

    monkeypatch.setattr(compras_gov.os, "replace", replace_que_falha_na_p001)
    with pytest.raises(OSError, match="queda"):
        compras_gov.executar(configuracao, destino, cliente, lambda _: None)
    assert sorted(p.name for p in destino.iterdir()) == [NOME_P2]  # sem p001 e sem .tmp

    monkeypatch.setattr(compras_gov.os, "replace", trocar)
    resultado = compras_gov.executar(configuracao, destino, cliente, lambda _: None)

    assert resultado.pulados == []
    assert sorted(p.name for p in destino.iterdir()) == [NOME_P1, NOME_P2]


def test_main_grava_em_raw_com_a_data_do_dia_e_sai_com_0(tmp_path, monkeypatch, capsys):
    configuracao = _configuracao(max_paginas_por_codigo=1)
    cliente_real = httpx.Client
    monkeypatch.setattr(compras_gov, "carregar_configuracao", lambda: configuracao)
    monkeypatch.setattr(compras_gov, "DATASET_DIR", tmp_path)
    monkeypatch.setattr(
        compras_gov.httpx, "Client", lambda **kw: cliente_real(transport=_mock(_api), **kw)
    )
    monkeypatch.setattr(compras_gov.time, "sleep", lambda _: None)

    codigo_saida = compras_gov.main()

    data = compras_gov.date.today().isoformat()
    assert codigo_saida == 0
    assert (tmp_path / "raw" / "compras_gov" / data / NOME_P1).read_bytes() == P1
    assert "1 arquivos" in capsys.readouterr().out


def test_main_sai_com_1_e_mostra_a_falha_quando_algum_codigo_falha(tmp_path, monkeypatch, capsys):
    configuracao = _configuracao(codigos=[999])
    cliente_real = httpx.Client
    monkeypatch.setattr(compras_gov, "carregar_configuracao", lambda: configuracao)
    monkeypatch.setattr(compras_gov, "DATASET_DIR", tmp_path)
    monkeypatch.setattr(
        compras_gov.httpx, "Client", lambda **kw: cliente_real(transport=_mock(_api), **kw)
    )

    codigo_saida = compras_gov.main()

    saida = capsys.readouterr()
    assert codigo_saida == 1
    assert "falha no código 999: HTTP 400" in saida.err
    assert not (tmp_path / "raw").exists()


def _mock(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)

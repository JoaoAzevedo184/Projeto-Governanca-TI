import io


def _csv(linhas: list[str]) -> bytes:
    return ("\n".join(linhas) + "\n").encode("utf-8")


def _importar(client, token, conteudo: bytes, nome_arquivo: str = "inventario.csv"):
    return client.post(
        "/api/v1/importacoes",
        headers={"Authorization": f"Bearer {token}"},
        files={"arquivo": (nome_arquivo, io.BytesIO(conteudo), "text/csv")},
    )


def test_ac044_importa_csv_com_linhas_invalidas(client, token_admin, categoria, fornecedor):
    cat, forn = categoria.nome, fornecedor.razao_social
    linhas = ["nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra"]
    for i in range(92):
        linhas.append(f"Notebook {i},HARDWARE,{cat},{forn},SN-{i:03d},2025-01-10,1000.00")
    for i in range(8):
        linhas.append(f"Sem serie {i},HARDWARE,{cat},{forn},,2025-01-10,1000.00")

    resposta = _importar(client, token_admin, _csv(linhas))
    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["total_processado"] == 100
    assert corpo["total_aceito"] == 92
    assert corpo["total_rejeitado"] == 8

    headers = {"Authorization": f"Bearer {token_admin}"}
    erros = client.get(f"/api/v1/importacoes/{corpo['lote_id']}/erros", headers=headers)
    assert erros.status_code == 200
    assert len(erros.json()) == 8


def test_ac045_recusa_cabecalho_divergente_sem_processar_linhas(client, token_admin):
    resposta = _importar(client, token_admin, _csv(["coluna_errada,outra", "x,y"]))
    assert resposta.status_code == 422

    lotes = client.get("/api/v1/importacoes", headers={"Authorization": f"Bearer {token_admin}"})
    assert lotes.json() == []


def test_ac046_rejeita_numero_serie_duplicado_dentro_do_arquivo(
    client, token_admin, categoria, fornecedor
):
    cat, forn = categoria.nome, fornecedor.razao_social
    linhas = [
        "nome,tipo,categoria,fornecedor,numero_serie,data_aquisicao,valor_compra",
        f"Notebook A,HARDWARE,{cat},{forn},SN-DUP,2025-01-10,1000.00",
        f"Notebook B,HARDWARE,{cat},{forn},SN-DUP,2025-01-10,1000.00",
    ]
    resposta = _importar(client, token_admin, _csv(linhas))
    assert resposta.status_code == 202
    corpo = resposta.json()
    assert corpo["total_aceito"] == 1
    assert corpo["total_rejeitado"] == 1

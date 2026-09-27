def test_login_com_credenciais_validas_retorna_token(client, db):
    from app.core.security import hash_senha
    from app.models.enums import PerfilUsuario
    from app.models.usuario import Usuario

    db.add(
        Usuario(
            login="admin",
            senha_hash=hash_senha("admin123"),
            nome="Admin",
            perfil=PerfilUsuario.ADMIN,
        )
    )
    db.commit()

    resposta = client.post("/api/v1/auth/login", json={"login": "admin", "senha": "admin123"})
    assert resposta.status_code == 200
    assert resposta.json()["access_token"]


def test_login_com_senha_incorreta_retorna_401(client, db):
    from app.core.security import hash_senha
    from app.models.enums import PerfilUsuario
    from app.models.usuario import Usuario

    db.add(
        Usuario(
            login="admin",
            senha_hash=hash_senha("admin123"),
            nome="Admin",
            perfil=PerfilUsuario.ADMIN,
        )
    )
    db.commit()

    resposta = client.post("/api/v1/auth/login", json={"login": "admin", "senha": "errada"})
    assert resposta.status_code == 401


def test_ac056_endpoint_protegido_com_token_invalido_retorna_401(client):
    resposta = client.get("/api/v1/ativos", headers={"Authorization": "Bearer token-invalido"})
    assert resposta.status_code == 401


def test_me_retorna_usuario_autenticado(client, token_admin):
    resposta = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_admin}"})
    assert resposta.status_code == 200
    assert resposta.json()["perfil"] == "ADMIN"

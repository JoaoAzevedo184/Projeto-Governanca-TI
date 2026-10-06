# Guia — Preparo do ambiente de demonstração

Passo a passo para sair de um banco vazio e chegar ao cenário dos Gates 1, 2, 3 e 4, usando só o terminal. Todos os comandos foram executados em 2026-10-05 num PC com Linux, Docker e Python 3.

O roteiro do que mostrar em cada gate está em [`demonstracao.md`](demonstracao.md). Este guia cobre só o preparo.

## Antes de começar

- Docker e Docker Compose instalados.
- Arquivo `.env` na raiz do projeto, com `SECRET_KEY` e as variáveis `SEED_*_PASSWORD` preenchidas.
- Os comandos partem da raiz do projeto, salvo indicação.
- A ordem dos passos é obrigatória. O seed de demonstração recusa rodar se os 92 ativos não estiverem importados.

## 1. Subir o ambiente do zero

```bash
docker compose down -v
docker compose up -d --build
docker compose ps
```

O `down -v` apaga o banco. Tudo o que foi carregado antes (fornecedores, ativos) some e precisa ser refeito a partir do passo 2.

Espere a `api` aparecer como `healthy` antes de continuar.

## 2. Criar usuários e categorias

```bash
./scripts/seed.sh
```

Esperado: `Seed: 4 usuário(s) e 11 categoria(s) criados.`

Se a saída disser `0 usuário(s)`, o banco não é novo e a senha do `admin` é a que valia quando os usuários foram criados. Volte ao passo 1.

## 3. Preparar o ambiente Python (só na primeira vez)

O carregador de fornecedores roda no PC, não no contêiner, porque a imagem da API não inclui a pasta `etl/`.

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install httpx
cd ..
```

Nas próximas vezes, basta `source python/.venv/bin/activate`.

## 4. Carregar os fornecedores

Troque `SUA_SENHA` pelo valor de `SEED_ADMIN_PASSWORD` do `.env`.

```bash
cd python
ITAM_API_LOGIN=admin ITAM_API_SENHA='SUA_SENHA' python -m etl.carregar_fornecedores
cd ..
```

Esperado: `Fornecedores: 17 criados, 0 já existiam.` (o número acompanha o arquivo `dataset/demo/fornecedores_demo.csv`).

## 5. Fazer login e guardar o token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "content-type: application/json" \
  -d '{"login":"admin","senha":"SUA_SENHA"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

O `echo` deve mostrar um texto longo começando com `eyJ`. Se sair uma linha vazia, o login falhou: rode o `curl` sem a parte depois do `|` para ver o erro.

**Alternativa pelo Swagger** (sem `curl`; serve para o roteiro da [demonstração](demonstracao.md), que é feito no Swagger): abra http://localhost:8000/docs e

1. em `POST /api/v1/auth/login`, clique em **Try it out**, informe `{"login": "admin", "senha": "SUA_SENHA"}` e clique em **Execute**;
2. copie o valor de `access_token` da resposta, sem aspas;
3. clique em **Authorize** (cadeado, no alto da página), cole o token no campo **Value**, clique em **Authorize** e depois em **Close**.

As rotas protegidas passam a enviar `Authorization: Bearer <token>`; teste com `GET /api/v1/auth/me`. O passo 6 (importação) usa `curl` com o arquivo e continua precisando da variável `TOKEN`; no Swagger, o mesmo envio é `POST /api/v1/importacoes`, com **Try it out** e o arquivo `dataset/demo/inventario_demo.csv`.

Três cuidados:

- `TOKEN` é uma variável do terminal. Ela não vai no `.env` e some ao fechar a janela.
- O token vale por 1 hora. Se uma chamada responder 401, repita este passo.
- Para guardar um valor, o formato é `NOME='valor'`. O `$` só é usado na hora de ler.

## 6. Importar o inventário de demonstração

```bash
curl -X POST http://localhost:8000/api/v1/importacoes \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@dataset/demo/inventario_demo.csv"
```

Esperado: `"total_processado":100,"total_aceito":92,"total_rejeitado":8`.

Para ver os 8 erros, linha a linha (troque `1` pelo `lote_id` da resposta):

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/importacoes/1/erros" | python3 -m json.tool
```

Se `total_aceito` vier 0 e os erros disserem "Fornecedor não encontrado", o passo 4 não foi feito neste banco. Refaça o passo 4 e importe de novo: nenhum ativo foi criado, então repetir é seguro.

## 7. Criar o cenário dos Gates 2, 3 e 4

```bash
./scripts/seed_demo.sh
```

Esperado: `Seed de demonstração: 3 setores, 6 responsaveis, 3 fornecedores, 4 ativos_demo, 95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas, 2 riscos, 3 avaliacoes, 1 recomendacoes`.

A segunda execução devolve tudo em `0`. Num banco em que o seed antigo (Gates 2 e 3) já rodou, a execução cria só `2 fornecedores, 2 riscos, 3 avaliacoes, 1 recomendacoes`.

## 8. Conferir

```bash
./scripts/smoke_test.sh
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/compliance/alertas" | python3 -m json.tool | head -12
```

Esperado nos alertas: `"total": 5`, com 1 `CRITICO` e 4 `ALTO`.

Com isso o ambiente está pronto para o roteiro de [`demonstracao.md`](demonstracao.md).

## Endereços

| Serviço | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

## Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| `Comando 'python' não encontrado` | O sistema só tem `python3` | Use `python3`, ou ative o ambiente virtual do passo 3 |
| `No module named 'httpx'` | Ambiente virtual não ativado | `source python/.venv/bin/activate` |
| Login responde 401 | Senha diferente da usada na criação do usuário | Confira `SEED_ADMIN_PASSWORD`; se mudou depois do seed, refaça do passo 1 |
| Chamada responde 401 com token | Variável `TOKEN` vazia ou token vencido | `echo $TOKEN`; repita o passo 5 |
| Importação com 0 aceitas | Fornecedores não carregados neste banco | Passo 4 e depois passo 6 |
| `seed_demo` recusa rodar | Faltam o seed básico ou os 92 ativos | Siga a ordem dos passos |
| Contêiner `api` sai ao iniciar | `SECRET_KEY` vazia ou padrão | `docker compose logs api` e ajuste o `.env` |

## Antes de uma apresentação

As datas dos registros de demonstração são relativas ao dia em que o `seed_demo` roda pela primeira vez. Para o valor residual do ativo `DEMO-HW-AC015` continuar em R$ 4.800,00, refaça todos os passos num banco novo perto da data da apresentação.
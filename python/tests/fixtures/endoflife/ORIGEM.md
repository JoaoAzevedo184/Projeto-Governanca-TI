# Fixtures do coletor `endoflife`

Respostas reais de `GET https://endoflife.date/api/<produto>.json`, gravadas em 2026-10-06 pelo
próprio `python -m collectors.endoflife` em `dataset/raw/endoflife/2026-10-06/` e copiadas byte a
byte para `coleta_2026-10-06/`, sem edição. Nenhum arquivo foi escrito ou ajustado à mão. A API
não pede chave.

| Arquivo | Produto | Ciclos na resposta |
|---|---|---|
| `mongodb.json` | MongoDB | 33 |
| `mysql.json` | MySQL | 16 |
| `nginx.json` | nginx | 23 |
| `office.json` | Microsoft Office | 10 |
| `postgresql.json` | PostgreSQL | 29 |
| `redis.json` | Redis | 12 |
| `tomcat.json` | Apache Tomcat | 9 |
| `windows-server.json` | Windows Server | 20 |

O que não é resposta da API (404, 301 e 503 sem corpo, erro de rede, corpo que não é da API) é
construído nos testes (`tests/unit/test_endoflife.py`), porque a API real não devolve isso sob
demanda. O slug `apache` redireciona (HTTP 301) para outro nome e por isso o Tomcat o substitui.

Os dados mudam na fonte; refazer a gravação gera arquivos diferentes. Os testes do coletor não
dependem dos valores de negócio, só do formato (`cycle`, `releaseDate`, `eol`). O ETL
(`etl/normalizar.py`) usa esta coleta como entrada e o teste `test_normalizar.py` confere
`dataset/processed/` contra ela.

Verificação antes de versionar (2026-10-06): sem dado pessoal (a resposta traz só produto, ciclo,
datas, versão e links públicos) e sem chave ou segredo; `tests/unit/test_fixtures_sem_segredos.py`
repete a conferência.

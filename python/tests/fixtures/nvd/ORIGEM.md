# Fixtures do coletor `nvd`

Respostas reais de `GET https://services.nvd.nist.gov/rest/json/cves/2.0`, gravadas em 2026-10-06
pelo próprio `python -m collectors.nvd` em `dataset/raw/nvd/2026-10-06/` e copiadas byte a byte
para `coleta_2026-10-06/`, sem edição. Nenhum arquivo foi escrito ou ajustado à mão. A coleta
rodou **sem** `NVD_API_KEY` (a variável não estava definida), com 6,5 s entre consultas, 70
consultas, nenhuma falha e nenhum `403`.

Cada ciclo (14, de 7 produtos) tem 5 arquivos, `<produto>_<ciclo>_<severidade>.json`, com
`severidade` = `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (consulta com `cvssV3Severity`) ou `total`
(sem filtro de severidade). Todas pedem `resultsPerPage=1` e `virtualMatchString` com o CPE de
`python/collectors/config.yaml` mais, quando há, `versionStart` e `versionEnd` do ciclo. Só o
`totalResults` é usado. Total: 70 arquivos, cerca de 0,58 MB.

| Produto | Ciclos | CPE |
|---|---|---|
| `postgresql` | 16, 13 | `cpe:2.3:a:postgresql:postgresql` |
| `mysql` | 8.4, 8.0 | `cpe:2.3:a:oracle:mysql` |
| `nginx` | 1.30, 1.28 | `cpe:2.3:a:f5:nginx` |
| `mongodb` | 8.0, 6.0 | `cpe:2.3:a:mongodb:mongodb` |
| `tomcat` | 10.1, 9.0 | `cpe:2.3:a:apache:tomcat` |
| `redis` | 7.2, 6.2 | `cpe:2.3:a:redis:redis` |
| `windows-server` | 2022, 2019 | `cpe:2.3:o:microsoft:windows_server_2022` e `..._2019` |

O nginx 1.28 e o 1.30 devolveram 0 CVEs; conferido em 2026-10-06 que o CPE antigo
`cpe:2.3:a:nginx:nginx` também dá 0 para as duas faixas (o `f5:nginx` sem faixa de versão tem 41
CVEs de outros ciclos). É contagem real, não falha da consulta.

O que não é resposta da API (403/429/503 sem corpo, erro de rede, corpo que não é da API) é
construído nos testes (`tests/unit/test_nvd.py`), porque a API real não devolve isso sob demanda.
A chave usada nos testes é falsa (`chave-falsa-...`).

Os dados mudam todo dia na fonte; refazer a gravação gera arquivos diferentes. Os testes do coletor
não dependem dos valores de negócio, só do formato (`totalResults`, `vulnerabilities`). O ETL
(`etl/normalizar.py`) usa esta coleta como entrada e `tests/unit/test_normalizar.py` confere
`dataset/processed/` contra ela.

## Verificação antes de versionar (2026-10-06)

- **Chave e segredo:** nenhuma ocorrência de `apiKey` ou nome de chave nos 70 arquivos; a
  coleta não usou chave. `tests/unit/test_fixtures_sem_segredos.py` repete a conferência e procura
  o valor real da `NVD_API_KEY` (do ambiente ou do `.env`), se houver.
- **CPF:** nenhum número com formato de CPF (`000.000.000-00` ou 11 dígitos soltos).
- **Dado pessoal:** a resposta do NVD traz identificadores de CVE, descrições técnicas, métricas,
  configurações (CPE) e links públicos. Os únicos e-mails são 11 endereços **institucionais**
  (caixas de segurança e listas de distribuição de CNAs e fornecedores, como
  `secalert@redhat.com`, `security@apache.org`, `cna@mongodb.com`, `nvd@nist.gov` e
  `package-announce@lists.fedoraproject.org`), no campo `sourceIdentifier` e nas referências. Não
  são dado pessoal de pessoa física; o teste de guarda tem uma lista fechada deles e falha se
  aparecer qualquer outro endereço, para uma nova coleta ser revista antes de ir ao git.

# Guia — Demonstração dos Gates 2, 3 e 4

Parte do [Guia — ITAM](README.md). Roteiro para demonstrar, com a API no ar, o que cada gate pede. Os dados vêm do seed de demonstração (`python/app/seed_demo.py`), que **só cria registros `sintetico`** com identificadores `DEMO-`.

## Preparo (uma vez, banco novo)

```bash
scripts/seed.sh                                   # migra e cria usuários e categorias
cd python
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores
# importar dataset/demo/inventario_demo.csv como ADMIN (docs/guia/importacao.md): 92 aceitos, 8 rejeitados
cd .. && scripts/seed_demo.sh                     # cenário dos Gates 2, 3 e 4
```

O `seed_demo` exige o seed básico e os 92 ativos importados; se faltar algo, encerra com a mensagem do que falta e não cria nada. Recusa `ENVIRONMENT=producao`. É idempotente: a segunda execução não cria nem altera nada, e uma execução interrompida retoma de onde parou.

Resultado esperado da primeira execução: `3 setores, 6 responsaveis, 3 fornecedores, 4 ativos_demo, 95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas, 2 riscos, 3 avaliacoes, 1 recomendacoes`.

Num banco em que o seed dos Gates 2 e 3 já rodou, a nova execução cria só o que é do Gate 4 (`2 fornecedores, 2 riscos, 3 avaliacoes, 1 recomendacoes`).

As datas dos ativos `DEMO-` partem do dia da primeira execução e ficam gravadas. Para repetir a conferência do AC-015 em outro dia, recrie o banco.

### Autenticar no Swagger

As rotas protegidas usam **HTTP Bearer**. No Swagger (`/docs`):

1. Em `POST /api/v1/auth/login` use **Try it out** com o corpo `{"login": "admin", "senha": "..."}` e **Execute**.
2. Copie só o valor de `access_token` da resposta (sem aspas).
3. Clique em **Authorize** (cadeado, no alto da página), cole o token no campo **Value**, clique em **Authorize** e depois em **Close**.
4. Chame qualquer rota protegida (por exemplo `GET /api/v1/auth/me`): o Swagger envia `Authorization: Bearer <token>`.

O token expira em cerca de uma hora; repita o passo 1 quando uma rota passar a responder 401. Sem token, ou com token inválido, a API responde 401 no formato de erro do projeto.

## O que o seed cria

| Registro | Identificador | Para que serve |
|---|---|---|
| 3 setores | `DEMO-Financeiro`, `DEMO-Tecnologia`, `DEMO-Operações` | Pessoas e setores fictícios |
| 6 responsáveis | matrículas `DEMO-001` a `DEMO-006` (e-mails `@demo.invalid`) | Idem |
| 1 fornecedor | `DEMO-Fornecedor de Demonstração LTDA` (sem CNPJ) | Fornecedor das licenças e dos ativos `DEMO-` |
| 2 fornecedores de software | `DEMO-Software Alfa LTDA` e `DEMO-Software Beta LTDA` (sem CNPJ) | Gate 4: três fornecedores no scorecard |
| 2 riscos | `uso de software sem licença válida` (4 x 5) e `saturação da licença de escritório` (3 x 3) | Gate 4: risco crítico e risco médio |
| 1 scorecard | período `DEMO-LICENCIAMENTO`, 3 fornecedores, 5 critérios | Gate 4: Alfa 8,55, Demonstração 7,00, Beta 5,90 |
| 1 recomendação | `Regularizar o licenciamento de software`, 4 evidências | Gate 4: rastreabilidade |
| Ativo das transferências | número de série `DEMO-HW-TRANSF` | Gate 2: linha do tempo |
| Ativo do AC-015 | número de série `DEMO-HW-AC015` | Gate 2: conferência da depreciação |
| Software | chave `DEMO-SW-OFFICE-KEY-0001` | Gate 3: ativo da licença de 50 unidades |
| Licença de 50 unidades | chave `DEMO-LIC-PERPETUA-0050` | Gate 3: 50 de 50 |
| Licença vencida | chave `DEMO-LIC-VENCIDA-0040` | Gate 3: vencida há 40 dias |
| Licença a vencer | chave `DEMO-LIC-A-VENCER-0025` | Gate 3: vence dentro da janela de alerta |
| Ativo baixado | número de série `DEMO-HW-BAIXA` | Gate 3: baixa com motivo, data e destinação |

Os três fornecedores `DEMO-` não têm CNPJ (nenhum identificador de empresa real); o seed os identifica pelo nome. Um banco semeado antes dessa mudança, em que o fornecedor de demonstração tem o CNPJ antigo, continua funcionando: o seed o reconhece pelo nome e não o altera.

Riscos e recomendação não têm campo de identificador: são `sintetico` pela origem, e a descrição dos riscos começa com `DEMO:`.

Além disso, 89 dos 92 ativos reais (`compras_gov`) recebem responsável. Os outros 3 ficam sem, de propósito: `CG-11037226-001`, `CG-12413209-001` e `CG-12832490-001`. Os ativos reais seguem `compras_gov`.

**Setor não tem `data_source`** (nem categoria e usuário). Os setores `DEMO-` são sintéticos pelo prefixo no nome.

O arquivo de demonstração não tem fornecedores que são pessoa física (microempreendedor individual); são 17 fornecedores, carregados por `python -m etl.carregar_fornecedores` antes da importação.

Os `id` abaixo são os de um banco novo, com a importação feita antes do seed; confira pelo número de série.

## Gate 2: responsabilidade e valor

Faça login como `admin` e use as rotas de `GET /api/v1/...`.

1. **Linha do tempo de três transferências (AC-010, AC-012, AC-013).** Abra o ativo `DEMO-HW-TRANSF` (`id` 93) e consulte `GET /ativos/93/historico`. Esperado: **4 vínculos** (atribuição inicial e 3 transferências), do mais recente ao mais antigo; cada vínculo anterior termina na data em que o seguinte começa, sem sobreposição; só o último tem `data_fim` vazio. A ordem dos responsáveis é Helena Duarte Pinheiro (`DEMO-Financeiro`), Marta Albuquerque Lins (`DEMO-Tecnologia`), Isadora Valente Prado (`DEMO-Operações`) e Rafael Quintanilha Reis (`DEMO-Financeiro`).
2. **Imutabilidade (AC-013).** Tente alterar ou excluir um vínculo encerrado: a operação é negada (trigger do banco, NFR-AUD-01).
3. **Depreciação do AC-015.** Abra o ativo `DEMO-HW-AC015` (`id` 94) e consulte `GET /ativos/94/depreciacao`. Esperado: valor de compra `6000.00`, vida útil `60` meses, `12` meses decorridos, depreciação acumulada `1200.00` e **valor residual `4800.00`** (6.000 x 12 / 60 = 1.200; 6.000 - 1.200 = 4.800), percentual depreciado `20.00`. A conta se confere à mão.

## Gate 3: conformidade e evento surpresa

4. **Painel de compliance (AC-021 a AC-023, AC-039).** `GET /compliance/alertas`. Esperado: **5 alertas**, 1 Crítico e 4 Altos:
   - Crítico, `CP-01`: licença `DEMO-Antivírus corporativo` (vencida há 40 dias);
   - Alto, `CP-03`: licença `DEMO-Backup em nuvem` (vence dentro da janela de alerta, 30 dias por padrão);
   - Alto, `CP-04`, exatamente **3** ativos sem responsável: os três números de série da seção anterior.
   A licença de 50 unidades não aparece (50 de 50 é conforme).
5. **Licença em 50 de 50 (AC-021).** `GET /licencas/1`: `quantidade_contratada` 50, `quantidade_em_uso` 50, `status_conformidade` `CONFORME`. Os 50 vínculos estão nas 50 primeiras máquinas reais (hardware ativo) em ordem de número de série, de `CG-10236527-001` a `CG-12584331-001`.
6. **O 51º vínculo, ao vivo (BR-018, NFR-AUD-05).** Use a máquina **`CG-12598222-001`** (`SERVIDOR HPE`, `id` 52), que é a 51ª na mesma ordem e não tem a licença:

   ```bash
   curl -X POST http://localhost:8000/api/v1/licencas/1/vinculos \
     -H "Authorization: Bearer $TOKEN" -H "content-type: application/json" \
     -d '{"ativo_id": 52}'
   ```

   Esperado: **HTTP 409**, `regra: "BR-018"`, detalhe "A quantidade em uso não pode exceder a quantidade contratada (50).". A tentativa fica na auditoria como `CRIAR` / `RECUSADO` / `BR-018` em `licenca_vinculo`, e `quantidade_em_uso` segue 50.
7. **Baixa com destinação (AC-019, AC-033).** Abra `DEMO-HW-BAIXA` (`id` 96): status `BAIXADO`, motivo `FIM_VIDA_UTIL`, destinação `RECICLAGEM_CERTIFICADA`, baixa 30 dias antes da execução do seed; `GET /ativos/96/depreciacao` devolve o valor residual congelado na data da baixa (`989.58` na execução de 2026-10-05, que muda com o dia).

## Gate 4: decisão e defesa

A história é uma só: a licença `DEMO-Antivírus corporativo` está vencida e a da suíte de escritório está em 50 de 50 (Gate 3). O Gate 4 mostra como o sistema leva dessa constatação a uma decisão rastreável. Os `id` abaixo são os de um banco novo, na ordem do preparo; confira pela lista.

8. **Indicador com fórmula e amostra (AC-047).** `GET /indicadores`, item `KPI-03` (Conformidade de licenças). Esperado: `valor` `66.67`, `amostra` `3`, `formula` "licenças com uso <= contratado e não vencidas / total de licenças * 100", `atende_meta` `false` (meta 100).
9. **Risco 4 x 5 é crítico (AC-050).** `GET /riscos`. Esperado: `uso de software sem licença válida` com `probabilidade` 4, `impacto` 5, `score` `20`, `classificacao` `CRITICO`; e `saturação da licença de escritório` com `score` 9, `MEDIO`. Os ids são 1 e 2.
10. **Scorecard ordenado e a recusa de pesos (AC-048, AC-049).** O seed grava o scorecard do período `DEMO-LICENCIAMENTO` e a API não tem consulta de scorecard: o ranking sai na resposta de `POST /fornecedores/scorecard`. Para ver o ranking ao vivo, envie o corpo abaixo (período `DEMO-AO-VIVO`; os ids dos fornecedores vêm de `GET /fornecedores`, procure os `DEMO-`: `18`, `19` e `20`). Esperado: `201`, ranking Alfa `8.55`, Demonstração `7.00`, Beta `5.90`. Reenviar acrescenta linhas de histórico, não altera as do seed.

   ```json
   {"periodo": "DEMO-AO-VIVO",
    "criterios": [{"nome": "Preço", "peso": "30"}, {"nome": "Prazo de entrega", "peso": "15"},
                  {"nome": "Qualidade do suporte", "peso": "25"}, {"nome": "Taxa de defeitos", "peso": "15"},
                  {"nome": "Aderência contratual", "peso": "15"}],
    "avaliacoes": [
      {"fornecedor_id": 19, "notas": {"Preço": "8", "Prazo de entrega": "9", "Qualidade do suporte": "9", "Taxa de defeitos": "8", "Aderência contratual": "9"}},
      {"fornecedor_id": 18, "notas": {"Preço": "7", "Prazo de entrega": "6", "Qualidade do suporte": "7", "Taxa de defeitos": "7", "Aderência contratual": "8"}},
      {"fornecedor_id": 20, "notas": {"Preço": "6", "Prazo de entrega": "7", "Qualidade do suporte": "5", "Taxa de defeitos": "6", "Aderência contratual": "6"}}]}
   ```

   **Recusa ao vivo (AC-048).** Corpo abaixo, com o peso de `Aderência contratual` em `10` (30 + 15 + 25 + 15 + 10 = 95%). Esperado: **HTTP 409**, `regra: "BR-029"`, detalhe "Os pesos dos critérios somam 95%, e devem somar exatamente 100%.". A recusa fica na auditoria (`CRIAR` / `RECUSADO` / `BR-029` em `fornecedor_avaliacao`) e nenhuma linha é gravada.

    ```json
    {"periodo": "DEMO-AO-VIVO",
     "criterios": [{"nome": "Preço", "peso": "30"}, {"nome": "Prazo de entrega", "peso": "15"},
                   {"nome": "Qualidade do suporte", "peso": "25"}, {"nome": "Taxa de defeitos", "peso": "15"},
                   {"nome": "Aderência contratual", "peso": "10"}],
     "avaliacoes": [
       {"fornecedor_id": 19, "notas": {"Preço": "8", "Prazo de entrega": "9", "Qualidade do suporte": "9", "Taxa de defeitos": "8", "Aderência contratual": "9"}}]}
    ```
11. **Recomendação sem evidência é recusada (AC-051).** `POST /recomendacoes` com o corpo abaixo (`responsavel_id` `4` é `DEMO-004`; confira em `GET /responsaveis`). Esperado: **HTTP 409**, `regra: "BR-027"`, detalhe "Nenhuma recomendação pode ser registrada sem ao menos uma evidência.", registrada na auditoria.

    ```json
    {"titulo": "Renovar o antivírus", "contexto": "Antivírus vencido há 40 dias.",
     "recomendacao": "Renovar a licença.", "responsavel_id": 4, "evidencias": []}
    ```
12. **Cenários ordenados, sem escolha (AC-052).** Cenários não são gravados: `POST /cenarios/comparar` com o conteúdo de [`exemplos/cenarios_gate4.json`](exemplos/cenarios_gate4.json). As três alternativas usam os nomes da API: `MANTER` (manter), `RENOVAR` (renovar com o fornecedor atual) e `MIGRAR_ASSINATURA` (trocar de fornecedor). Esperado: **HTTP 200**, ordem `MANTER` (TCO `20000.00`, risco 29), `RENOVAR` (`42000.00`, risco 9), `MIGRAR_ASSINATURA` (`51000.00`, risco 0), `ordenado_por` `["tco_5_anos", "score_risco"]`, nenhum cenário marcado como escolhido e a observação de que a decisão é humana e se registra em `/recomendacoes`. O TCO é `capex + opex_anual x 5`.

    **Conferir os ids dos riscos.** O arquivo usa `riscos_ids` 1 e 2, os de um banco novo. Num banco em que os riscos têm outros ids, abra `GET /riscos` e troque pelos `id` de `uso de software sem licença válida` (crítico) e `saturação da licença de escritório` (médio). Id que não existe devolve **404** `Risco N não encontrado.`
13. **A recomendação aberta, com cada evidência (defesa, 3:50 a 4:30).** `GET /recomendacoes/1`: `Regularizar o licenciamento de software`, status `PROPOSTA`, `data_source` `sintetico`, quatro evidências:
    - `RISCO`, `referencia_id` 1: abra `GET /riscos/1` (o crítico, score 20);
    - `SCORECARD`, `referencia_id` 19: `DEMO-Software Alfa LTDA`, o mais bem avaliado (passo 10);
    - `INDICADOR`: descrição com o `KPI-03`, 66,67% em 3 licenças, a mesma do passo 8;
    - `CENARIO`: descrição com os TCO e riscos do passo 12 e a frase "Nenhuma alternativa foi escolhida pelo sistema.".

    Indicador e cenário não têm registro próprio (são calculados), por isso levam o valor no momento do registro em vez de `referencia_id` (FR-013).
14. **`/health` e `/metrics` (AC-053, AC-054).** `GET /health`: `{"status": "UP", ..., "database": {"status": "UP"}}`. `GET /metrics`: formato de exposição Prometheus, com as séries `itam_`.
15. **Grafana (FR-014).** http://localhost:3000 (usuário e senha de `GRAFANA_USER` e `GRAFANA_PASSWORD` do `.env`), pasta **Governança de TI**, dashboard **ITAM — Observabilidade**, provisionado com o Prometheus como fonte.

## Refazer a demonstração

Recrie o banco (`scripts/reset.sh` e o preparo acima). Rodar o `seed_demo` de novo no mesmo banco não repõe o que foi gasto na demonstração (o 51º vínculo recusado, por exemplo, não cria nada, mas a auditoria da recusa fica).

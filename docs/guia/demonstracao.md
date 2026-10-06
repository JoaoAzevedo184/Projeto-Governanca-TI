# Guia — Demonstração dos Gates 2 e 3

Parte do [Guia — ITAM](README.md). Roteiro para demonstrar, com a API no ar, o que cada gate pede. Os dados vêm do seed de demonstração (`python/app/seed_demo.py`), que **só cria registros `sintetico`** com identificadores `DEMO-`.

## Preparo (uma vez, banco novo)

```bash
scripts/seed.sh                                   # migra e cria usuários e categorias
cd python
ITAM_API_LOGIN=admin ITAM_API_SENHA=... python -m etl.carregar_fornecedores
# importar dataset/demo/inventario_demo.csv como ADMIN (docs/guia/importacao.md): 92 aceitos, 8 rejeitados
cd .. && scripts/seed_demo.sh                     # cenário dos Gates 2 e 3
```

O `seed_demo` exige o seed básico e os 92 ativos importados; se faltar algo, encerra com a mensagem do que falta e não cria nada. Recusa `ENVIRONMENT=producao`. É idempotente: a segunda execução não cria nem altera nada, e uma execução interrompida retoma de onde parou.

Resultado esperado da primeira execução: `3 setores, 6 responsaveis, 1 fornecedores, 4 ativos_demo, 95 vinculos_responsavel, 3 licencas, 50 vinculos_licenca, 1 baixas`.

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
| 1 fornecedor | CNPJ `00.000.000/0001-91` | Fornecedor das licenças e dos ativos `DEMO-` |
| Ativo das transferências | número de série `DEMO-HW-TRANSF` | Gate 2: linha do tempo |
| Ativo do AC-015 | número de série `DEMO-HW-AC015` | Gate 2: conferência da depreciação |
| Software | chave `DEMO-SW-OFFICE-KEY-0001` | Gate 3: ativo da licença de 50 unidades |
| Licença de 50 unidades | chave `DEMO-LIC-PERPETUA-0050` | Gate 3: 50 de 50 |
| Licença vencida | chave `DEMO-LIC-VENCIDA-0040` | Gate 3: vencida há 40 dias |
| Licença a vencer | chave `DEMO-LIC-A-VENCER-0025` | Gate 3: vence dentro da janela de alerta |
| Ativo baixado | número de série `DEMO-HW-BAIXA` | Gate 3: baixa com motivo, data e destinação |

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

## Refazer a demonstração

Recrie o banco (`scripts/reset.sh` e o preparo acima). Rodar o `seed_demo` de novo no mesmo banco não repõe o que foi gasto na demonstração (o 51º vínculo recusado, por exemplo, não cria nada, mas a auditoria da recusa fica).

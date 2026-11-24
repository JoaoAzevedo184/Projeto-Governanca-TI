# Roteiro de Defesa — 5 minutos

Item 5.9 do backlog (`docs/BACKLOG_E_GATES.md`), pendência da Sprint 5 em `docs/ROADMAP.md:188`.

**Regra da rubrica:** sem demonstração funcional, a nota tem teto 70. Por isso este roteiro é uma **demonstração ao vivo**, não uma sequência de slides. Cada bloco tem uma tela ou um comando que sustenta a fala.

**Regra da defesa** (`BACKLOG_E_GATES.md` §5): qualquer integrante deve conseguir explicar qualquer trecho. A divisão abaixo é de fala, não de conhecimento.

Tempos e sequência seguem o `BACKLOG_E_GATES.md` §5, que soma exatamente 300 s.

---

## Antes de entrar na sala

Pré-voo, na máquina da apresentação e na segunda máquina do plano B2. O tempo do fluxo completo (itens 2 e 3) está no `CHECKLIST_ENTREGA.md`, seção 4, e define a hora de chegada.

**Na véspera:** construir a imagem da API (`docker compose build`), para que a recriação do banco na manhã da apresentação leve segundos em vez de minutos. Medido em 2026-11-23 na máquina de desenvolvimento: com a imagem pronta, o fluxo dos itens 2 e 3 levou 20,4 s, contra 142,7 s com o build, quase todo ele gasto construindo a imagem. Na manhã, suba com `docker compose up -d`, sem `--build`.

1. **Portas livres.** As quatro portas publicadas vêm do `.env` (`API_PORT`, `DB_PORT`, `PROMETHEUS_PORT`, `GRAFANA_PORT`), sem editar o `docker-compose.yml` (`docs/guia/execucao-local.md`, seção "Portas publicadas pelo Docker Compose"). O conflito aconteceu de fato na verificação de 2026-11-23: as portas 5432 e 8000 estavam ocupadas por outro projeto. Se alguma estiver ocupada:

   ```bash
   # .env
   API_PORT=18000
   DB_PORT=15432
   ```

2. **Ambiente no ar e banco recriado no dia da apresentação.** O seed de demonstração grava datas relativas ao dia em que roda. Num banco semeado em 2026-10-06 e consultado em 2026-11-23, os números já mudaram: o ativo do AC-015 mostra 13 meses e residual R$ 4.700,00, e não R$ 4.800,00. Também aparecem 2 alertas críticos em vez de 1, porque a licença "a vencer" já venceu, e o KPI-03 cai para 33,33%. Siga `docs/guia/preparo-da-demonstracao.md` do passo 1 ao 8, **no mesmo dia**, começando por `scripts/reset.sh`.
3. **Verificar os 6 números.** `scripts/verificar_demo.sh` deve terminar com `verificação da demonstração OK`: residual R$ 4.800,00 no `DEMO-HW-AC015`, 1 licença vencida há 40 dias, 1 a vencer em 25 dias, 1 em 50 de 50, 3 ativos sem responsável e 1 ativo baixado. Qualquer `✗` significa banco semeado em outro dia: volte ao item 2.
4. Rodar `scripts/smoke_test.sh` e ver `smoke test OK`.
5. Abrir em abas: Swagger (`http://localhost:${API_PORT}/docs`, já autorizado com o token do `admin`), Grafana (`http://localhost:${GRAFANA_PORT}`, pasta **Governança de TI**) e um terminal com `TOKEN` e `API` exportados:

   ```bash
   export API=http://localhost:${API_PORT:-8000}/api/v1
   export TOKEN=...   # passo 5 do preparo
   ```

6. Conferir os `id` do banco recém-criado pelo número de série (`docs/guia/demonstracao.md`, "Os `id` abaixo são os de um banco novo").

---

## Blocos

| # | Tempo | Quem fala | Frente | Tema |
|---|---|---|---|---|
| 1 | 0:00–0:40 | Vinícius Alencar Murta Costa | Documentação | O problema e o escopo |
| 2 | 0:40–1:20 | Edilson Pereira da Silva Filho | ETL e dados | Importação do arquivo real do Compras.gov.br |
| 3 | 1:20–2:10 | Gabriel Leal de Andrade Pereira | Backend | Transferência e linha do tempo imutável |
| 4 | 2:10–3:00 | Paulo Gabriel Morais Santana da Silva | Backend e scripts | O 51º vínculo numa licença de 50 |
| 5 | 3:00–3:50 | João Victor Azevedo de Sena | Infra e observabilidade | Painel de compliance e Grafana |
| 6 | 3:50–4:30 | Gabriel Leal de Andrade Pereira | Backend | Recomendação aberta, com cada evidência |
| 7 | 4:30–5:00 | Vinícius Alencar Murta Costa | Documentação | Aderência a COBIT BAI09, ITIL e ISO/IEC 19770 |

[A EQUIPE CONFIRMA: distribuição de falas. Os blocos 3 e 6 e os blocos 1 e 7 repetem o orador porque são 7 blocos para 5 pessoas.]

### Bloco 1 — O problema e o escopo (40 s)

**Tela:** `README.md` ou `docs/prd/escopo.md`.

**Fala:**

- O problema: inventário em planilha, licenças sem controle e valor patrimonial congelado.
- O ITAM é uma camada de governança sobre os dados que a organização já tem. Não é ERP nem descoberta automática (OUT-02, OUT-04).
- São 15 requisitos funcionais, 71 critérios de aceite e 1012 testes. Cada teste de critério carrega o identificador no nome (`test_ac###_`, ADR-010).

### Bloco 2 — Importação do Compras.gov.br (40 s)

**Tela:** Swagger, `GET /api/v1/importacoes` e `GET /api/v1/importacoes/{id}/erros`.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/importacoes" | python3 -m json.tool
curl -s -H "Authorization: Bearer $TOKEN" "$API/importacoes/1/erros" | python3 -m json.tool
```

**Esperado:** lote com `total_processado` 100, `total_aceito` 92 e `total_rejeitado` 8, e as 8 linhas de erro com campo e motivo:

- nome curto;
- tipo inválido;
- categoria inexistente;
- fornecedor inexistente;
- hardware sem série (BR-002);
- série duplicada no arquivo (AC-046);
- data futura (BR-003);
- valor zero (BR-004).

Os 8 erros foram medidos no ambiente em 2026-11-23.

**Fala:**

- São 100 itens reais de compras públicas federais, com 8 erros inseridos de propósito (`dataset/demo/inventario_demo.LEIAME.md`).
- Cada linha rejeitada diz qual regra violou.
- Isso é o critério de liberação do Gate 1 (FR-008, AC-044).

**Por que não importar ao vivo:** o arquivo é importado no preparo, porque o `seed_demo` exige os 92 ativos. Reenviar o mesmo arquivo ao banco já carregado rejeita os 92 válidos como duplicados (BR-001). Se o professor pedir, reenvie e mostre isso: é o bloqueio de duplicidade do critério 1 funcionando.

### Bloco 3 — Transferência e linha do tempo imutável (50 s)

**Tela:** Swagger, `GET /api/v1/ativos/{id}/historico` do ativo `DEMO-HW-TRANSF`.

**Esperado:** 4 vínculos (a atribuição inicial e 3 transferências). Cada vínculo termina no dia em que o seguinte começa, e só o último tem `data_fim` vazio. Esse ponto foi medido no ambiente em 2026-11-23.

**Fala:**

- O responsável atual não é uma coluna do ativo. É o vínculo aberto do histórico (ADR-003).
- O banco recusa um segundo vínculo aberto pelo índice `ux_vinculo_aberto` (BR-007, ADR-006).
- O banco também recusa UPDATE e DELETE de vínculo encerrado pelo trigger `permitir_apenas_encerramento` (AC-013, ADR-005).
- A garantia está no banco, não na disciplina da equipe.

**Prova opcional:** `GET /ativos/{id}/depreciacao` do `DEMO-HW-AC015`. Com o banco recriado no dia, esperado: 6.000 × 12 ÷ 60 = 1.200 de depreciação e residual de R$ 4.800,00 (AC-015).

### Bloco 4 — O 51º vínculo numa licença de 50 (50 s)

**Tela:** terminal.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/licencas/1" | python3 -m json.tool | grep quantidade
curl -s -X POST "$API/licencas/1/vinculos" \
  -H "Authorization: Bearer $TOKEN" -H "content-type: application/json" \
  -d '{"ativo_id": 52}'
```

**Esperado:**

- `quantidade_contratada` 50 e `quantidade_em_uso` 50.
- A tentativa responde **HTTP 409**, `"regra": "BR-018"`, com a mensagem "A quantidade em uso não pode exceder a quantidade contratada (50).".
- O uso continua em 50.

Confira que o `ativo_id` 52 é a máquina `CG-12598222-001` no banco recriado.

**Fala:**

- O sistema **bloqueou** e **registrou** a tentativa: a auditoria tem `CRIAR / RECUSADO / BR-018` (NFR-AUD-05).
- A regra é citada pelo identificador.
- É o critério de liberação do Gate 3 e a resposta ao evento-surpresa de "licença de 50 levada a 53".

### Bloco 5 — Painel de compliance e Grafana (50 s)

**Tela:** `GET /api/v1/compliance/alertas`, depois o Grafana em **Governança de TI → ITAM - Gestão**.

**Esperado (banco recriado no dia):** 5 alertas, sendo 1 crítico (CP-01, licença vencida há 40 dias) e 4 altos (CP-03, licença a vencer; CP-04, 3 ativos sem responsável). O painel "Alertas de compliance por severidade" mostra os mesmos números.

**Fala:**

- Os números do painel saem de `/metrics` (`itam_compliance_alertas`, `itam_licencas_por_conformidade`, `itam_patrimonio_reais`, `itam_ativos_sem_responsavel`), coletados pelo Prometheus a cada 15 s.
- O dashboard técnico `itam-tecnico` mostra disponibilidade, latência e operações bloqueadas por regra (`itam_regras_violadas_total`).
- O BR-018 recém-recusado no bloco 4 aparece nesse contador.

### Bloco 6 — Recomendação aberta (40 s)

**Tela:** Swagger, `GET /api/v1/recomendacoes/1`.

**Esperado:** "Regularizar o licenciamento de software", status `PROPOSTA`, 4 evidências: `RISCO` 1 (crítico, 4 × 5 = 20), `SCORECARD` 19 (fornecedor Alfa, 8,55), `INDICADOR` KPI-03 e `CENARIO` com os 3 TCO. Medido no ambiente em 2026-11-23.

**Fala:**

- Cada evidência abre no sistema: `GET /riscos/1` e, ao vivo, `POST /cenarios/comparar` com `docs/guia/exemplos/cenarios_gate4.json`.
- O cenário ordena por TCO e não escolhe. A resposta diz que "a seleção da alternativa é decisão humana" (BR-028, AC-052).
- Sem evidência, a recomendação é recusada com 409 BR-027 (AC-051).

### Bloco 7 — Aderência a frameworks (30 s)

**Tela:** `docs/prd/anexos.md`, matriz de aderência.

**Fala:**

- **COBIT 2019 BAI09** (Gerenciar Ativos): FR-001, FR-003, FR-005, FR-009.
- **ITIL 4**, prática de Gestão de Ativos de TI: FR-001, FR-002, FR-005.
- **ISO/IEC 19770-1** (ciclo de vida e propriedade): FR-001, FR-002, FR-005, FR-006.
- **ISO/IEC 19770-3** (direitos de uso de software): FR-004, FR-007.
- Complementares: APO10 (fornecedores, FR-011), APO12 (riscos, FR-012) e APO06 (custos, FR-010).

---

## Plano B

### B2 — Segunda máquina com o ambiente no ar

Uma segunda máquina, de outro integrante, fica ligada com o mesmo ambiente do Docker Compose já no ar e semeado. Se a máquina principal falhar, a demonstração continua nela, do bloco em que parou.

- **Preparo no dia da apresentação, num banco novo.** As duas máquinas seguem `docs/guia/preparo-da-demonstracao.md` no mesmo dia, cada uma com `scripts/reset.sh` antes. Um banco semeado em outro dia mostra outros números (ver item 2 de "Antes de entrar na sala").
- **Mesma conferência nas duas.** `scripts/verificar_demo.sh` com `verificação da demonstração OK` e `scripts/smoke_test.sh` com `smoke test OK`.
- **Abas e terminal já abertos** como na máquina principal (Swagger autorizado, Grafana, `TOKEN` e `API` exportados).
- **Os `id` podem diferir.** Confira pelo número de série antes da troca.

[A EQUIPE CONFIRMA: quem leva a segunda máquina e como ela se liga ao projetor.]

### B3 — Gravação de tela, como último recurso

Só se as duas máquinas falharem.

- [A EQUIPE PREENCHE: gravação de tela do roteiro completo (blocos 1 a 7), feita na véspera, num banco recém-semeado.]
- A saída da suíte (`pytest -v -k "ac021 or ac015 or ac051 or ac052 or gate1"`).
- O CI verde no GitHub Actions.

A gravação não é demonstração funcional ao vivo e não afasta o teto 70. Serve só para não perder o resto da nota.

### Por que o perfil SQLite não é plano B

O RI-10 prevê o perfil local com SQLite (`docs/guia/execucao-local.md`). Ele não serve de plano B, por dois motivos:

1. **O SQLite não tem o que a demonstração mostra.** Não tem o trigger de imutabilidade (bloco 3), o lock de linha da licença (bloco 4) nem as FKs (`PRAGMA foreign_keys` = 0). O bloco 5 também fica sem Grafana.
2. **As migrações não rodam até o fim.** Achado da verificação de 2026-11-23, num banco SQLite descartável: `alembic upgrade head` para na migração `python/alembic/versions/a7c1e5d90b21_sprint_5_risco.py` com `sqlite3.OperationalError: near "(": syntax error`. A causa é `server_default=sa.text('now()')`, que o SQLite não aceita. O mesmo padrão está em `b3d8f2a61c47` e `c9e4a7d25f83`. É a mesma falha da entrada 05 da seção 5 do `REGISTRO_USO_DE_IA.md`, corrigida na época só em `c8365ce7e5e4`.

**Decisão da equipe:** a migração não será corrigida para a defesa, porque nem corrigido o SQLite mostraria os blocos 3 e 4. A limitação fica registrada como achado no `RELATORIO_TECNICO_AV2.md`.

---

## Perguntas prováveis do professor

**Por que só Python, e não dual Python/Java como na baseline?**
A entrega só em Python foi aprovada pelo professor. As referências a Java saíram da baseline no commit `deabe82` (2026-09-02). O que tornaria uma segunda implementação barata já existe: o contrato `python/api/openapi.yaml` está congelado e sincronizado com o app, e os testes de contrato com schemathesis (`tests/contract/test_contrato_schemathesis.py`) rodam contra o arquivo, não contra o código Python. Uma API Java passaria pela mesma suíte de contrato (RE-01, RI-05).

**Por que a depreciação não é persistida?**
ADR-002. O valor depreciado muda todo mês. Gravar o valor exigiria um job de recálculo e criaria divergência entre o valor armazenado e a data corrente. A função pura `utils/depreciacao.py` calcula sob demanda com `Decimal` e `ROUND_HALF_UP` (BR-017). A exceção é a baixa: o residual é congelado na `data_baixa` (BR-015, AC-019).

**Por que não existe `responsavel_id` no ativo?**
ADR-003. Seriam duas fontes de verdade: a coluna e o histórico. O responsável atual é o vínculo com `data_fim` nula, e o índice único parcial `ux_vinculo_aberto` garante no máximo um por ativo (BR-007, ADR-006).

**Por que a BR-027 é garantida no serviço e não no banco?**
A regra é "recomendação com ao menos uma evidência", e a evidência fica em outra tabela. Um `CHECK` não enxerga outra tabela. Garantir a regra no banco exigiria um trigger deferido. No serviço, a recomendação e as evidências são gravadas na mesma transação, e a recusa sai como 409 com `regra = BR-027`, auditada e contada em `itam_regras_violadas_total` (ADR-009). Ver `python/app/services/recomendacao_service.py:53-64`.

**O que ficou fora do MVP e por quê?**

- CP-05 a CP-09: deriváveis ou sem disparo no modelo atual.
- KPI-01, KPI-04 e KPI-05: não são calculáveis só com o banco.
- Relatórios de depreciação, baixas e histórico: sem critério de aceite.
- Carga do pipeline no banco: substituída pelo seed de demonstração.
- Transição de status da recomendação.

Tudo está registrado com o motivo em `docs/ROADMAP.md:156-159` e na seção 4.2 do `RELATORIO_TECNICO_AV1.md`.

**Como sei que os testes testam o que dizem?**

- Cada critério tem teste com o identificador no nome. São 71 de 71 ACs com teste `test_ac###_`.
- O CI conta esses testes.
- Os testes foram revisados contra falso positivo por mutação deliberada: o `REGISTRO_USO_DE_IA.md` registra as falhas 06, 21, 22 e 27, achadas assim.

# Checklist de Entrega — 2ª AV

Item 5.8 do backlog (`docs/BACKLOG_E_GATES.md`). Este checklist lista o que precisa estar pronto, e enviado ao Drive, antes da apresentação. Marque cada item com `[x]` quando a pessoa da frente responsável tiver conferido.

Frentes, conforme o anexo dos relatórios:

- **ETL**: Edilson Pereira da Silva Filho.
- **Backend**: Gabriel Leal de Andrade Pereira.
- **Infra**: João Victor Azevedo de Sena.
- **Backend/Scripts**: Paulo Gabriel Morais Santana da Silva.
- **Docs**: Vinícius Alencar Murta Costa.

---

## 1. Artefatos do repositório

- [x] Alterações de 2026-11-23 revisadas e versionadas nos commits `5db2b3a` a `59d5da7` (portas, teste do AC-008, `verificar_demo.sh`, links, os 4 documentos novos, ROADMAP e registro, e a fixação de `pydantic` e `starlette` no `requirements.txt`). — **Infra**
- [ ] Revisar e versionar os preenchimentos feitos depois do `59d5da7`, ainda sem commit: `docs/guia/equipe-e-ia.md`, `docs/REGISTRO_USO_DE_IA.md`, `docs/ROADMAP.md`, os 2 relatórios, este checklist, o `ROTEIRO_DEFESA.md`, `python/collectors/config.yaml`, `python/etl/exportar_inventario_demo.py` e `docs/guia/preparo-da-demonstracao.md`. — **Infra**
- [x] `material_aluno/RUBRICA.md` revertido ao `HEAD` em 2026-11-23: é arquivo do professor, e `material_aluno/` não tem diff. A rubrica que vale é a do ITAM, na segunda metade do arquivo. — **Docs**
- [x] CI verde no GitHub Actions depois do push (qualidade, testes com cobertura ≥ 70% global e 100% em `utils/` + `services/`, contagem `test_ac`): run 45274407153, commit `59d5da7`, 2026-11-23 (https://github.com/JoaoAzevedo184/Projeto-Governanca-TI/actions/runs/45274407153). — **Infra**
- [x] `docs/guia/equipe-e-ia.md` preenchido em 2026-11-23 com as 5 frentes do anexo (`ROADMAP.md:56`). — **Docs**
- [x] Coluna "Responsável" do `docs/REGISTRO_USO_DE_IA.md` preenchida em 2026-11-23: entradas 40 a 43 com João Victor Azevedo de Sena; entradas 01 a 39, a seção 4 e os campos em aberto (entradas 24, 25, 34, 35 e 39, falhas 38 a 40 e 46) como "não registrado à época". A regra 1 da seção 7 passou a valer a partir da entrada 40. — **Docs**
- [x] Links para `RESOLUCAO_PENDENCIAS_SPRINT2.md` resolvidos em 2026-11-23: o arquivo nunca entrou no git (nenhum commit em `git log --all`), então cada link em `docs/` foi trocado pela decisão do item citado e por um link para a seção da Sprint 2 do `ROADMAP.md` (`REGISTRO_USO_DE_IA.md`, entrada 43). O `README.md` não citava o arquivo. — **Docs**
- [ ] Perfil SQLite fora do plano B: decidido em 2026-11-23 não corrigir as migrações `a7c1e5d90b21`, `b3d8f2a61c47` e `c9e4a7d25f83`. O SQLite não tem trigger, lock de linha nem FKs, que são o que a demonstração mostra. Achado registrado no `RELATORIO_TECNICO_AV2.md` e no `ROTEIRO_DEFESA.md`. Falta o Backend conferir e marcar. — **Backend**
- [ ] **Definition of Done, revisão cruzada:** outro integrante revisa os itens das Sprints 3, 4 e 5 (`BACKLOG_E_GATES.md` §4, primeiro item; `ROADMAP.md:43`). — **todas as frentes**, cada uma revisando a de outra pessoa
- [ ] Preencher as marcações `[A EQUIPE PREENCHE]` e `[A EQUIPE CONFIRMA]` que restam. As que dependiam só do repositório foram preenchidas em 2026-11-23. Faltam: as datas de corte da 1ª e da 2ª AV e a data e o resultado de cada gate demonstrado (dependem do professor); quem executou cada atividade (AV1, seção 6), a distribuição das falas, quem leva a segunda máquina e a gravação de tela (dependem da equipe). — **Docs**

## 2. Artefatos do Drive

- [ ] `RELATORIO_TECNICO_AV1` exportado (PDF ou documento) e enviado ao Drive do projeto. — **Docs**
- [ ] `RELATORIO_TECNICO_AV2` exportado e enviado ao Drive. — **Docs**
- [ ] `ROTEIRO_DEFESA` disponível para a equipe (no Drive ou impresso). — **Docs**
- [ ] Gravação de tela do roteiro completo (plano B3), feita na véspera num banco recém-semeado, no Drive. — **Infra**
- [x] Link do repositório e do último run do CI no relatório da AV2: seção 1.2, run 45274407153. — **Infra**

## 3. Ambiente

- [ ] **Na véspera**, construir a imagem da API (`docker compose build`), para que a recriação do banco na manhã da apresentação leve segundos em vez de minutos. Medido em 2026-11-23 na máquina de desenvolvimento: com a imagem pronta, o fluxo completo levou 20,4 s, contra 142,7 s com o build. Na manhã, suba com `docker compose up -d`, sem `--build`. — **Infra**
- [ ] **No dia da apresentação**, recriar o banco e refazer o preparo completo (`docs/guia/preparo-da-demonstracao.md`, passos 1 a 8). Um banco semeado em outro dia mostra números diferentes dos do roteiro. Na verificação de 2026-11-23, o banco de 2026-10-06 já mostrava residual R$ 4.700,00 no AC-015 e 2 alertas críticos. — **Infra**
- [ ] **Na manhã da apresentação**, depois de recriar e semear o banco: `scripts/verificar_demo.sh` com `verificação da demonstração OK` (os 6 números do roteiro, todos com ✓), na máquina da apresentação e na segunda máquina. — **Infra**
- [ ] `scripts/smoke_test.sh` com `smoke test OK` na máquina da apresentação. — **Infra**
- [ ] Segunda máquina (plano B2 do roteiro) com o ambiente no ar, preparada no mesmo dia, num banco novo, e com os mesmos números conferidos. — **Infra** [A EQUIPE CONFIRMA: quem leva a máquina]
- [ ] Portas livres na máquina da sala, ou ajustadas no `.env` (`API_PORT`, `DB_PORT`, `PROMETHEUS_PORT`, `GRAFANA_PORT`). — **Infra**
- [ ] Conferência manual do valor residual do Gate 2, feita por quem não escreveu o código: 6.000 × 12 ÷ 60 = 1.200 de depreciação; residual 4.800,00 (AC-015, `ROADMAP.md:17,27`). — **ETL**
- [ ] Ids do banco recriado conferidos pelo número de série (`DEMO-HW-TRANSF`, `DEMO-HW-AC015`, `CG-12598222-001`, licença `DEMO-LIC-PERPETUA-0050`, fornecedores `DEMO-`, riscos 1 e 2). — **Backend/Scripts**
- [ ] Grafana com os dois dashboards na pasta **Governança de TI** (`itam-tecnico` e `itam-gestao`), com dados, cerca de 1 minuto depois do seed. — **Infra**

## 4. Ensaio e gates

Nenhum gate foi formalmente **liberado**: todos estão "pronto para demonstrar" (`ROADMAP.md:16-19`). Rodar o ambiente localmente com Docker Compose conta como deploy, conforme confirmado com o professor. Ainda assim, cada gate só é liberado depois que a equipe demonstra.

- [ ] **Gate 1** demonstrado: lote de 100 linhas com 92 aceitas e 8 erros linha a linha. — **ETL**
- [ ] **Gate 2** demonstrado: linha do tempo com 3 transferências sem sobreposição e residual conferido à mão. — **Backend**
- [ ] **Gate 3** demonstrado: 51º vínculo bloqueado com BR-018 e registrado na auditoria. — **Backend/Scripts**
- [ ] **Evento-surpresa do Gate 3** preparado. A equipe ensaia detectar, explicar e propor correção para pelo menos os dois cenários citados no `BACKLOG_E_GATES.md` (Gate 3): um lote de vínculos levando uma licença de 50 a 53, e uma licença vencida há 40 dias. Para cada um, saber qual rota mostra o problema (`/compliance/alertas`, `/licencas/{id}`, auditoria), qual regra foi violada (BR-018, BR-020, CP-01) e qual evidência sustenta a correção. — **todas as frentes**
- [ ] **Gate 4** demonstrado: recomendação aberta, com cada evidência exibida ao vivo. — **Backend**
- [x] Fluxo completo de recriação do banco cronometrado na máquina de desenvolvimento (Linux, 12 CPUs, 15 GB de RAM), em 2026-11-23: **142,7 s**, do `scripts/reset.sh` até `verificação da demonstração OK` (código 0). Desse total, 130,9 s foram do `docker compose up -d --build`: build da imagem da API mais a subida dos contêineres até a API ficar saudável, já com as migrações aplicadas. Os outros passos: `reset.sh` 2,4 s, seed básico 3,4 s, fornecedores 1,7 s, login e importação 0,5 s (100 processadas, 92 aceitas, 8 rejeitadas), `seed_demo` 3,2 s e verificação 0,5 s. Com a imagem já construída, o mesmo fluxo levou **20,4 s**: `reset.sh` 1,8 s, `docker compose up -d` 12,3 s, seed básico 2,4 s, fornecedores 0,6 s, login e importação 0,4 s, `seed_demo` 2,2 s e verificação 0,5 s. — **Infra**
- [ ] Cronometrar o mesmo fluxo na máquina da sala, que é o número que define a hora de chegada no dia. O build pode levar outro tempo lá. — **Infra**
- [ ] Ensaio cronometrado do `ROTEIRO_DEFESA.md` com as 5 pessoas, dentro de 5 minutos. — **todas as frentes**
- [ ] Cada integrante responde às perguntas prováveis do roteiro sem consultar o texto. — **todas as frentes**

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

- [ ] Revisar e versionar as alterações de 2026-11-23, que estão só no diretório de trabalho e sem commit: `docker-compose.yml`, `.env.example`, `scripts/smoke_test.sh`, `docs/guia/execucao-local.md`, `docs/guia/solucao-de-problemas.md`, `python/tests/integration/test_ativos.py` (teste do AC-008) os 4 documentos novos em `docs/` (`RELATORIO_TECNICO_AV1.md`, `RELATORIO_TECNICO_AV2.md`, `ROTEIRO_DEFESA.md`, `CHECKLIST_ENTREGA.md`), `scripts/verificar_demo.sh`, `docs/guia/preparo-da-demonstracao.md`, `docs/ROADMAP.md` e `docs/REGISTRO_USO_DE_IA.md`. — **Infra**
- [x] `material_aluno/RUBRICA.md` revertido ao `HEAD` em 2026-11-23: é arquivo do professor, e `material_aluno/` não tem diff. A rubrica que vale é a do ITAM, na segunda metade do arquivo. — **Docs**
- [ ] CI verde no GitHub Actions depois do push (qualidade, testes com cobertura ≥ 70% global e 100% em `utils/` + `services/`, contagem `test_ac`). — **Infra**
- [ ] Preencher `docs/guia/equipe-e-ia.md`: a tabela de papéis ainda tem `*(preencher)*` nas 5 linhas (`ROADMAP.md:56`, passo 5 de "Próximos passos"). — **Docs**
- [ ] Preencher a coluna "Responsável" do `docs/REGISTRO_USO_DE_IA.md`, que está `*(preencher)*` em todas as entradas, e os campos em aberto das entradas 24, 25, 34 e 39 e das falhas 38 a 40. — **Docs**
- [x] Links para `RESOLUCAO_PENDENCIAS_SPRINT2.md` resolvidos em 2026-11-23: o arquivo nunca entrou no git (nenhum commit em `git log --all`), então cada link em `docs/` foi trocado pela decisão do item citado e por um link para a seção da Sprint 2 do `ROADMAP.md` (`REGISTRO_USO_DE_IA.md`, entrada 43). O `README.md` não citava o arquivo. — **Docs**
- [ ] Perfil SQLite fora do plano B: decidido em 2026-11-23 não corrigir as migrações `a7c1e5d90b21`, `b3d8f2a61c47` e `c9e4a7d25f83`. O SQLite não tem trigger, lock de linha nem FKs, que são o que a demonstração mostra. Achado registrado no `RELATORIO_TECNICO_AV2.md` e no `ROTEIRO_DEFESA.md`. Falta o Backend conferir e marcar. — **Backend**
- [ ] **Definition of Done, revisão cruzada:** outro integrante revisa os itens das Sprints 3, 4 e 5 (`BACKLOG_E_GATES.md` §4, primeiro item; `ROADMAP.md:43`). — **todas as frentes**, cada uma revisando a de outra pessoa
- [ ] Preencher as datas de corte `[A EQUIPE PREENCHE]` em `RELATORIO_TECNICO_AV1.md` e `RELATORIO_TECNICO_AV2.md`, e as demais marcações desse tipo. — **Docs**

## 2. Artefatos do Drive

- [ ] `RELATORIO_TECNICO_AV1` exportado (PDF ou documento) e enviado ao Drive do projeto. — **Docs**
- [ ] `RELATORIO_TECNICO_AV2` exportado e enviado ao Drive. — **Docs**
- [ ] `ROTEIRO_DEFESA` disponível para a equipe (no Drive ou impresso). — **Docs**
- [ ] Gravação de tela do roteiro completo (plano B3), feita na véspera num banco recém-semeado, no Drive. — **Infra**
- [ ] Link do repositório e do último run do CI no relatório da AV2 ou no Drive. — **Infra**

## 3. Ambiente

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
- [ ] Cronometrar o fluxo completo de recriação do banco (`scripts/reset.sh`, subida do ambiente com as migrações, seed básico, fornecedores, importação, `seed_demo` e `scripts/verificar_demo.sh`) e anotar o tempo medido: [A EQUIPE PREENCHE: tempo medido, data e máquina]. Esse número define a hora de chegada na sala no dia. — **Infra**
- [ ] Ensaio cronometrado do `ROTEIRO_DEFESA.md` com as 5 pessoas, dentro de 5 minutos. — **todas as frentes**
- [ ] Cada integrante responde às perguntas prováveis do roteiro sem consultar o texto. — **todas as frentes**

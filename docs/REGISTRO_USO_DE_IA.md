# Registro de Uso de IA — ITAM

Documento vivo. Cada uso de ferramenta de IA na construção deste projeto é registrado aqui, com o artefato gerado e a revisão humana aplicada.

**Princípio:** a ferramenta produz rascunho; a equipe produz entrega. Todo artefato aqui listado é de responsabilidade integral de quem assina a revisão, e qualquer integrante deve conseguir explicá-lo na defesa sem consultar este registro.

---

## 1. Ferramentas autorizadas pela equipe

| Ferramenta | Uso previsto | Uso vedado |
|---|---|---|
| Assistentes de chat (Claude, ChatGPT, Gemini) | Rascunho de documentação, revisão de texto, exploração de alternativas de modelagem | Gerar código que entra no repositório sem leitura linha a linha |
| Assistentes de código (Copilot, Cursor, Claude Code) | Autocompletar, gerar testes a partir de critérios de aceite, refatoração mecânica | Gerar regra de negócio sem conferência contra o `PRD-ITAM.md` |
| Geradores de dados | Produzir datasets sintéticos de demonstração | Produzir dados que a equipe não consiga explicar ou reproduzir |

---

## 2. Níveis de revisão

Todo registro classifica a revisão em um dos três níveis:

| Nível | Significado | Quando é suficiente |
|---|---|---|
| **R1 — Leitura** | Lido integralmente, sem alteração | Texto descritivo, sem afirmação técnica verificável |
| **R2 — Verificação** | Conferido contra uma fonte (PRD, norma, documentação oficial) e corrigido | Documentação técnica, decisões de modelagem, citação de frameworks |
| **R3 — Execução** | Executado, testado e o resultado conferido | Todo código, script, migração, consulta SQL e dataset |

Nenhum artefato de código pode ficar abaixo de R3. Nenhum documento que cite norma ou framework pode ficar abaixo de R2.

---

## 3. Registro

| # | Data | Ferramenta | Artefato gerado | O que foi pedido | Revisão humana aplicada | Nível | Responsável |
|---|---|---|---|---|---|---|---|
| 01 | 2026-09-20 | Claude | `docs/PRD-ITAM.md` | PRD completo a partir dos requisitos FR-001 a FR-007 definidos pela equipe | Conferida a aderência a COBIT BAI09, ITIL 4 e ISO/IEC 19770 nas fontes originais; vida útil das categorias verificada contra a IN RFB 1.700/2017; ajustadas as personas ao contexto da organização do cenário | R2 | *(preencher)* |
| 02 | 2026-09-20 | Claude | `SPEC.md` | Especificação técnica para stack Python/FastAPI | Versões das dependências verificadas na documentação oficial e fixadas; contrato da API conferido endpoint a endpoint contra o PRD | R2 | *(preencher)* |
| 03 | 2026-09-20 | Claude | `README.md` | Documentação de execução do repositório | Comandos executados em máquina limpa; seção de troubleshooting validada provocando cada erro | R3 | *(preencher)* |
| 04 | 2026-09-20 | Claude | `docs/ARQUITETURA.md`, `docs/MODELO_DE_DADOS.md`, `docs/BACKLOG_E_GATES.md` | Documentos de arquitetura, modelo de dados e planejamento | Diagramas Mermaid renderizados e conferidos; DDL das constraints e triggers executado em PostgreSQL; consultas SQL de referência executadas contra o dataset | R3 | *(preencher)* |
| 05 | 2026-09-20 | Claude | `scripts/gerar_datasets.py`, `scripts/validar_datasets.py`, `datasets/*.csv` | Gerador e validador dos datasets de demonstração | Script executado; validador apontou vínculos encerrados após a data de baixa e o gerador foi corrigido; deslocamento nos índices de fornecedor identificado e corrigido; contagem de desvios conferida manualmente | R3 | *(preencher)* |
| 06 | — | — | — | — | — | — | — |

---

## 4. O que a equipe produziu sem IA

Esta seção existe para deixar explícito o que é autoria direta, e é tão importante quanto a tabela acima.

| Item | Autor | Descrição |
|---|---|---|
| Escolha do tema (ITAM) e definição dos requisitos FR-001 a FR-007 | Equipe | Levantamento do problema e delimitação do escopo funcional |
| Decisão de adotar Python/FastAPI como stack | Equipe | Avaliação de domínio técnico disponível na equipe |
| *(preencher)* | | |

---

## 5. Falhas encontradas em saídas de IA

Registrar erros corrigidos é a evidência mais forte de que houve revisão real. Esta seção conta a favor na defesa.

| # | Artefato | Erro na saída original | Como foi detectado | Correção |
|---|---|---|---|---|
| 01 | `gerar_datasets.py` | Vínculos de responsável encerrando após a data de baixa do ativo | Validador de coerência referencial | Datas de baixa passaram a ser calculadas antes das transferências, servindo de limite superior |
| 02 | `gerar_datasets.py` | Índices de fornecedor deslocados: Microsoft 365 atribuído à Adobe | Inspeção manual da amostra de `licencas.csv` | Índices corrigidos na lista de softwares |
| 03 | *(preencher)* | | | |

---

## 6. Como preencher

Um registro por sessão de uso, não por mensagem trocada. O critério é: **gerou artefato que entrou no repositório?** Então registra.

Campos obrigatórios:

- **Artefato gerado** — caminho do arquivo, não descrição genérica;
- **O que foi pedido** — em uma linha, o objetivo, não o prompt literal;
- **Revisão humana aplicada** — o que foi *conferido* e contra o quê. "Revisado" não é revisão; "vida útil conferida contra a IN RFB 1.700" é;
- **Nível** — R1, R2 ou R3, conforme a seção 2;
- **Responsável** — quem assina a revisão e responde pelo artefato na defesa.

---

## 7. Política de autoria

1. Nenhum artefato entra no repositório sem um responsável nomeado neste registro.
2. Código gerado por IA passa obrigatoriamente por R3 — executado e testado — antes do commit.
3. Afirmação sobre norma, framework ou taxa legal é verificada na fonte primária. Modelos de linguagem erram números e confundem versões de norma com frequência suficiente para que isso seja regra, não precaução.
4. Se um integrante não consegue explicar um trecho na defesa, o trecho é reescrito ou removido antes da entrega.
5. Este documento é entregue junto com o projeto. Omitir uso de IA é mais grave do que usá-la.

---

*Documento exigido pelo Gate 0. Mantido atualizado ao longo de todas as sprints.*
# PRD — Fluxos de Negócio

Parte de [PRD — ITAM](README.md).

## 15. Fluxos de Negócio

### 15.1 Cadastro de Ativo

```
[Início]
   │
   ▼
Usuário informa dados do ativo
   │
   ▼
Tipo = HARDWARE? ──Sim──► Número de série informado? ──Não──► [Erro: campo obrigatório]
   │                                  │
   Não                               Sim
   │                                  ▼
   ▼                        Número de série já existe? ──Sim──► [Erro: duplicidade]
Chave de licença informada?                │
   │                                      Não
   ├──Não──► [Erro: campo obrigatório]     │
   │                                       │
  Sim ◄────────────────────────────────────┘
   │
   ▼
Data de aquisição válida e valor > 0? ──Não──► [Erro: validação]
   │
  Sim
   │
   ▼
Herdar vida útil da categoria
   │
   ▼
Persistir ativo com status = ATIVO
   │
   ▼
Registrar na trilha de auditoria
   │
   ▼
Calcular depreciação para a data corrente
   │
   ▼
Ativo possui responsável? ──Não──► Sinalizar alerta CP-04
   │
  Sim
   │
   ▼
[Fim: exibir detalhe do ativo]
```

### 15.2 Transferência de Responsável

```
[Início]
   │
   ▼
Localizar ativo
   │
   ▼
Status = BAIXADO? ──Sim──► [Erro: BR-009 — ativo baixado não recebe responsável]
   │
  Não
   │
   ▼
Informar novo responsável, setor e data
   │
   ▼
Data ≥ data de aquisição? ──Não──► [Erro: BR-010]
   │
  Sim
   │
   ▼
┌─── INÍCIO DA TRANSAÇÃO ───┐
│  Existe vínculo aberto?   │
│      │            │        │
│     Sim          Não       │
│      │            │        │
│      ▼            │        │
│  Encerrar vínculo │        │
│  (data_fim = data)│        │
│      │            │        │
│      └─────┬──────┘        │
│            ▼               │
│  Criar novo vínculo aberto │
│            ▼               │
│  Registrar auditoria       │
└─── FIM DA TRANSAÇÃO ──────┘
   │
   ▼
[Fim: linha do tempo atualizada]
```

### 15.3 Baixa de Ativo

```
[Início]
   │
   ▼
Localizar ativo
   │
   ▼
Status = BAIXADO? ──Sim──► [Erro: BR-024 — baixa já registrada]
   │
  Não
   │
   ▼
Informar motivo, data, destinação e justificativa
   │
   ▼
Motivo = OUTRO e justificativa vazia? ──Sim──► [Erro: BR-023]
   │
  Não
   │
   ▼
Data válida (não futura, ≥ aquisição)? ──Não──► [Erro: BR-022]
   │
  Sim
   │
   ▼
┌─── INÍCIO DA TRANSAÇÃO ─────────────┐
│  Calcular valor residual na data    │
│  Persistir BaixaAtivo               │
│  Encerrar vínculo de responsável    │
│  Encerrar vínculos de licença       │
│  Alterar status para BAIXADO        │
│  Registrar auditoria                │
└─── FIM DA TRANSAÇÃO ────────────────┘
   │
   ▼
Ativo sai do inventário ativo, histórico preservado
(BR-031 e BR-036: os assentos de licença da máquina, ou da licença do software baixado, voltam ao saldo, cada encerramento auditado)
   │
   ▼
[Fim]
```

### 15.4 Renovação de Licença

```
[Início: alerta CP-03 — licença expira em ≤ 30 dias]
   │
   ▼
Administrador consulta detalhe da licença
   │
   ▼
Verificar quantidade em uso vs. contratada
   │
   ├──► Uso < 50% do contratado ──► Sinalizar subutilização
   │                                (oportunidade de redução)
   │
   ├──► Uso entre 50% e 100% ────► Renovar quantitativo atual
   │
   └──► Uso = contratado ────────► Avaliar ampliação
   │
   ▼
Comparar cenários de renovação (FR-010)
   │
   ▼
Registrar recomendação com evidências (FR-013)
   │
   ▼
Evidência vinculada? ──Não──► [Erro: BR-027]
   │
  Sim
   │
   ▼
Decisão registrada → nova licença cadastrada ou licença atual atualizada
   │
   ▼
[Fim: alerta cessa automaticamente]
```

### 15.5 Avaliação de Compliance

```
[Gatilho: acesso ao painel ou geração de relatório]
   │
   ▼
Para cada licença:
   ├── expirada?                 ──► CP-01 Crítico
   ├── uso > contratado?         ──► CP-02 Crítico
   └── expira em ≤ 30 dias?      ──► CP-03 Alto
   │
   ▼
Para cada ativo com status ATIVO (MVP: só CP-04; CP-05, CP-06, CP-08 e CP-09 estão fora do MVP, ver FR-007):
   ├── sem vínculo aberto?       ──► CP-04 Alto
   ├── 100% depreciado?          ──► CP-05 Médio
   ├── EM_MANUTENCAO > 90 dias?  ──► CP-06 Médio
   ├── sem movimentação 12 meses?──► CP-08 Baixo
   └── valor de compra ausente?  ──► CP-09 Baixo
   │
   ▼
Para cada ativo baixado (CP-07 fora do MVP: nunca dispara, a destinação é obrigatória):
   └── sem destinação?           ──► CP-07 Médio
   │
   ▼
Agrupar por severidade (Crítico → Alto → Médio → Baixo)
   │
   ▼
Exibir painel com link para o registro de origem
   │
   ▼
[Fim: exportação opcional como relatório datado]
```


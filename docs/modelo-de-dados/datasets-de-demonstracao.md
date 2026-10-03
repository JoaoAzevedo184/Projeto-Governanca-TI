# Modelo de Dados — Datasets de Demonstração

Parte de [Modelo de Dados — ITAM](README.md).

## 8. Datasets de demonstração

Os datasets do projeto anterior (`alertas.csv`, `slos.csv`, `dashboard_referencia.csv` no formato de observabilidade) **não têm equivalência neste modelo** e devem ser substituídos. O mapeamento novo:

| Arquivo | Tabela destino | Volume sugerido | Gate |
|---|---|---|---|
| `categorias.csv` | `categoria` | 11 | Gate 1 |
| `fornecedores.csv` | `fornecedor` | 12 | Gate 1 |
| `setores.csv` | `setor` | 8 | Gate 1 |
| `responsaveis.csv` | `responsavel` | 60 | Gate 2 |
| `inventario.csv` | `ativo` | 300 | Gate 1 |
| `inventario_com_erros.csv` | `ativo` | 100 (8 inválidas) | Gate 1 |
| `transferencias.csv` | `historico_transferencia` | 450 | Gate 2 |
| `licencas.csv` | `licenca` | 25 | Gate 3 |
| `licenca_vinculos.csv` | `licenca_vinculo` | 380 | Gate 3 |
| `baixas.csv` | `baixa_ativo` | 40 | Gate 3 |
| `riscos.csv` | `risco` | 15 | Gate 4 |
| `custos_cenarios.csv` | entrada de `/cenarios/comparar` | 3 cenários | Gate 4 |

### Desvios plantados deliberadamente

O dataset só demonstra governança se contiver desconformidade. Ao gerá-lo, plantar:

| Situação | Quantidade | Alerta que dispara |
|---|---|---|
| Licença vencida | 2 | CP-01 |
| Licença com uso acima do contratado | 1 | CP-02 |
| Licença expirando em ≤ 30 dias | 3 | CP-03 |
| Ativo ativo sem vínculo de responsável | 12 | CP-04 |
| Ativo 100% depreciado ainda em operação | 18 | CP-05 |
| Ativo em manutenção há mais de 90 dias | 4 | CP-06 |
| Baixa sem destinação (para validar a recusa) | — | CP-07 |
| Ativo sem movimentação há mais de 12 meses | 25 | CP-08 |
| Licença subutilizada (uso ≤ 50%) | 3 | Alerta Baixo |

As linhas CP-05 a CP-09 e "Alerta Baixo" desta tabela não geram alerta no MVP (regras fora do MVP, ver FR-007); só CP-01 a CP-04 aparecem no painel.

Sem esses desvios o painel de compliance aparece vazio na defesa, e um painel vazio não prova que a regra funciona — prova apenas que ninguém a testou.

### Coerência exigida do dataset

- Toda `data_inicio` de transferência ≥ `data_aquisicao` do ativo (BR-010);
- Nenhum ativo com dois vínculos abertos (BR-007);
- Todo ativo em `baixas.csv` com status `BAIXADO` em `inventario.csv`;
- Nenhum vínculo de responsável iniciando após a data de baixa;
- Nenhum vínculo de licença ativo (`ativo_vinculo = true`) em ativo `BAIXADO` (BR-031, BR-032), nenhum vínculo ativo em licença cujo ativo `SOFTWARE` esteja `BAIXADO` (BR-036, BR-037), e `ativo_id` de `licenca_vinculo` sempre `HARDWARE` (BR-033);
- `data_expiracao` > `data_aquisicao` em toda licença (BR-019);
- Números de série únicos no arquivo inteiro (BR-001).

Um gerador em Python é preferível a planilha manual: mantém a coerência referencial e permite regenerar com semente fixa, o que torna a demonstração reprodutível.


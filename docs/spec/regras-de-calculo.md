# SPEC — Regras de Cálculo

Parte de [SPEC — ITAM](README.md).

## 7. Regras de Cálculo

### 7.1 Depreciação linear (FR-003)

```python
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import date

CENTAVO = Decimal("0.01")

def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)   # BR-017

def meses_entre(inicio: date, fim: date) -> int:
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    if fim.day < inicio.day:
        meses -= 1
    return max(meses, 0)

@dataclass(frozen=True)
class Depreciacao:
    valor_compra: Decimal
    vida_util_meses: int
    meses_decorridos: int
    meses_efetivos: int
    depreciacao_mensal: Decimal
    depreciacao_acumulada: Decimal
    valor_residual: Decimal
    percentual_depreciado: Decimal

def calcular(valor_compra: Decimal, data_aquisicao: date,
             vida_util_meses: int, data_referencia: date) -> Depreciacao:
    decorridos = meses_entre(data_aquisicao, data_referencia)
    efetivos = min(decorridos, vida_util_meses)
    mensal = _arredondar(valor_compra / Decimal(vida_util_meses))
    acumulada = _arredondar(mensal * efetivos)
    if acumulada > valor_compra:
        acumulada = valor_compra                       # BR-014
    residual = _arredondar(valor_compra - acumulada)
    percentual = _arredondar(acumulada / valor_compra * Decimal(100))
    return Depreciacao(valor_compra, vida_util_meses, decorridos, efetivos,
                       mensal, acumulada, residual, percentual)
```

**Pontos obrigatórios:**

- `Decimal` em todo cálculo monetário. `float` introduz erro de representação e quebra a conciliação contábil (KPI-05). Colunas mapeadas como `Numeric(12, 2)`, nunca `Float`.
- Função pura, sem sessão de banco e sem acesso a `date.today()` internamente — a `data_referencia` é sempre injetada, o que torna os casos AC-015 a AC-020 testáveis sem manipular o relógio.
- `data_referencia` = `date.today()` para ativos em operação; `baixa.data_baixa` para ativos baixados (BR-015, AC-019).

### 7.2 Conformidade de licença (FR-004)

```
saldo             = quantidade_contratada − quantidade_em_uso
dias_expiracao    = (data_expiracao − hoje).days

CP-02 CRITICO  se  quantidade_em_uso > quantidade_contratada
CP-01 CRITICO  se  dias_expiracao < 0
CP-03 ALTO     se  0 <= dias_expiracao <= JANELA_ALERTA_DIAS
      MEDIO    se  saldo == 0
      BAIXO    se  quantidade_em_uso <= contratada * 0.5 e idade > 6 meses
```

`JANELA_ALERTA_DIAS` é configurável (padrão 30, QA-07 em aberto).

### 7.3 Score de risco (FR-012)

`score = probabilidade × impacto`, ambos de 1 a 5. Faixas: 1–4 baixo, 5–9 médio, 10–14 alto, 15–25 crítico (AC-050).

### 7.4 Scorecard de fornecedores (FR-011)

```
validar: soma(pesos) == 100          → senão 422 citando BR-029 (AC-048)
validar: 0 <= nota <= 10 para todos os critérios
pontuacao(f) = soma(nota[f][c] * peso[c] / 100)
ranking = ordenar por pontuacao desc
```

A comparação de soma de pesos usa `Decimal`, não `float` — `0.3 + 0.3 + 0.4 != 1.0` em ponto flutuante binário.

### 7.5 TCO de cenários (FR-010)

```
tco_5_anos           = capex + (opex_anual * 5)
custo_por_ativo_ano  = tco_5_anos / (quantidade_ativos * 5)
economia_vs_baseline = tco_baseline − tco_cenario
score_risco          = soma dos scores dos riscos vinculados ao cenário
```


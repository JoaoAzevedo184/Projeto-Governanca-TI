# PRD — Modelo Conceitual de Dados

Parte de [PRD — ITAM](README.md).

## 14. Modelo Conceitual de Dados

> Cada entidade abaixo que é povoada a partir de coleta externa ou geração sintética carrega `data_source`; o dicionário físico completo, com o tipo e a origem de cada coluna, está em [`docs/modelo-de-dados/`](../modelo-de-dados/README.md), não duplicado aqui.

### 14.1 Entidades

| Entidade | Descrição | Atributos principais |
|---|---|---|
| **Ativo** | Item de hardware ou software sob gestão | nome, tipo, número de série, chave de licença, data de aquisição, valor de compra, status, vida útil, localização |
| **Categoria** | Classificação do ativo, portadora da vida útil padrão | nome, descrição, vida útil em meses, tipo aplicável |
| **Fornecedor** | Origem da aquisição | razão social, CNPJ, contato, telefone, e-mail |
| **Responsavel** | Pessoa a quem um ativo pode ser atribuído | nome, matrícula, e-mail, cargo, situação |
| **Setor** | Unidade organizacional | nome, sigla, responsável pelo setor |
| **Licenca** | Direito de uso de software, com quantitativo e vigência | software, chave, quantidade contratada, quantidade em uso, data de aquisição, data de expiração, valor, tipo |
| **HistoricoTransferencia** | Vínculo temporal entre ativo e responsável | ativo, responsável, setor, data de início, data de fim, motivo, registrado por |
| **BaixaAtivo** | Evento terminal do ciclo de vida do ativo | ativo, motivo, justificativa, data da baixa, destinação, valor residual congelado, registrado por |
| **Usuario** | Operador do sistema | login, senha (hash), perfil, situação |
| **LoteImportacao** | Registro de uma execução de importação | arquivo, data, usuário, total processado, aceitos, rejeitados |
| **ErroImportacao** | Falha em uma linha específica | lote, número da linha, campo, motivo |
| **Risco** | Exposição registrada formalmente | título, categoria, probabilidade, impacto, score, resposta, responsável, status, gatilho |
| **Fornecedor_Avaliacao** | Nota de um fornecedor em um critério | fornecedor, critério, peso, nota, período |
| **Recomendacao** | Decisão proposta, sustentada por evidências | título, contexto, recomendação, responsável, data, status |
| **Evidencia** | Elo entre recomendação e o dado que a sustenta | recomendação, tipo de origem, identificador da origem, descrição |
| **AuditLog** | Trilha imutável de operações | usuário, operação, entidade, identificador, carimbo de tempo, resultado |

### 14.2 Relacionamentos

```
Categoria      1 ──── N  Ativo
Fornecedor     1 ──── N  Ativo
Fornecedor     1 ──── N  Licenca
Fornecedor     1 ──── N  Fornecedor_Avaliacao

Ativo          1 ──── N  HistoricoTransferencia
Responsavel    1 ──── N  HistoricoTransferencia
Setor          1 ──── N  HistoricoTransferencia
Setor          1 ──── N  Responsavel

Ativo          1 ──── 0..1  BaixaAtivo
Licenca        N ──── N  Ativo            (via vínculo de instalação)

LoteImportacao 1 ──── N  ErroImportacao
LoteImportacao 1 ──── N  Ativo            (procedência do registro)

Recomendacao   1 ──── N  Evidencia
Usuario        1 ──── N  AuditLog
Usuario        1 ──── N  HistoricoTransferencia   (como registrador)
Usuario        1 ──── N  BaixaAtivo               (como registrador)
```

### 14.3 Notas de modelagem

- **Responsável atual não é atributo do Ativo.** É derivado do `HistoricoTransferencia` com `data_fim` nula. Guardar o responsável diretamente no ativo criaria uma fonte de verdade concorrente com o histórico e permitiria divergência entre os dois.
- **Depreciação não é persistida.** É calculada sob demanda a partir de `valor_compra`, `data_aquisicao` e `vida_util_meses`. A única exceção é o `valor_residual_baixa`, congelado no momento da baixa por ser um fato contábil datado.
- **`quantidade_em_uso` da licença é derivada** da contagem de vínculos de instalação. O campo pode ser materializado por desempenho, mas nunca editado diretamente.
- **`HistoricoTransferencia`, `BaixaAtivo` e `AuditLog` são append-only.** A camada de persistência deve impedir UPDATE e DELETE nessas tabelas, preferencialmente por restrição no próprio banco, não apenas por convenção de código.
- **Períodos de vínculo não se sobrepõem.** A invariante "no máximo um vínculo aberto por ativo" deve ser garantida por índice único parcial, não apenas por validação na aplicação.


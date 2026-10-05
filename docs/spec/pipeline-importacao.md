# SPEC — Pipeline de Importação (FR-008)

Parte de [SPEC — ITAM](README.md).

## 10. Pipeline de Importação (FR-008)

### 10.1 Esquema do arquivo de ativos

| Coluna | Obrigatória | Formato |
|---|---|---|
| `nome` | Sim | texto, 3–120 (o máximo vem da coluna `ativo.nome`) |
| `tipo` | Sim | `HARDWARE` ou `SOFTWARE` |
| `categoria` | Sim | nome da categoria existente |
| `fornecedor` | Sim | razão social existente |
| `numero_serie` | Condicional | texto, até o tamanho da coluna (80) |
| `chave_licenca` | Condicional | texto, até o tamanho da coluna (200) |
| `data_aquisicao` | Sim | `AAAA-MM-DD` |
| `valor_compra` | Sim | decimal, ponto como separador, até 10 dígitos inteiros e 2 casas decimais (`NUMERIC(12,2)`); mais casas é recusado, não arredondado |
| `localizacao` | Não | texto, até o tamanho da coluna (120) |

### 10.2 Etapas

```
1. Ler arquivo (pandas: read_csv | read_excel)
   └── vazio, extensão diferente de .csv/.xlsx, CSV fora de UTF-8 ou XLSX inválido → 422 `/erros/arquivo-invalido`, nenhum lote criado
2. Validar cabeçalhos
   └── divergente → 422, arquivo inteiro recusado, nenhuma linha processada (AC-045)
3. Para cada linha:
   ├── normalizar (trim, upper em enums, parse de data e decimal)
   ├── validar campos obrigatórios e domínios
   ├── validar tamanho dos textos e o intervalo do valor (AC-068, AC-069)
   ├── resolver categoria e fornecedor por nome
   ├── verificar duplicidade contra o arquivo já lido
   ├── verificar duplicidade contra a base (AC-046)
   ├── válida   → acumular em lote_aceitos
   └── inválida → registrar ErroImportacao (linha, campo, valor, motivo)
4. Persistir aceitos em transação única, com lote_importacao_id
5. Persistir LoteImportacao e ErroImportacao
6. Retornar resumo com URL dos erros
```

**Isolamento por registro (FR-008):** uma linha inválida não impede as demais. Erros de validação são acumulados, não lançados.

**Limites vêm do modelo.** Os tamanhos de texto e a precisão do valor são lidos das colunas de `ativo` (e o tamanho do valor mostrado, de `erro_importacao.valor_recebido`, 255), não repetidos no importador. O valor mostrado no relatório é cortado nesse tamanho. A `chave_licenca` aparece sempre mascarada no relatório (RI-08), inclusive quando é longa demais.

**Limite:** arquivos acima de 5 MB ou 5.000 linhas são recusados no MVP. Processamento assíncrono fica para a V2.


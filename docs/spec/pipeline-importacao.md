# SPEC — Pipeline de Importação (FR-008)

Parte de [SPEC — ITAM](README.md).

## 10. Pipeline de Importação (FR-008)

### 10.1 Esquema do arquivo de ativos

| Coluna | Obrigatória | Formato |
|---|---|---|
| `nome` | Sim | texto, 3–120 |
| `tipo` | Sim | `HARDWARE` ou `SOFTWARE` |
| `categoria` | Sim | nome da categoria existente |
| `fornecedor` | Sim | razão social existente |
| `numero_serie` | Condicional | texto |
| `chave_licenca` | Condicional | texto |
| `data_aquisicao` | Sim | `AAAA-MM-DD` |
| `valor_compra` | Sim | decimal, ponto como separador |
| `localizacao` | Não | texto |

### 10.2 Etapas

```
1. Ler arquivo (pandas: read_csv | read_excel)
   └── vazio, extensão diferente de .csv/.xlsx, CSV fora de UTF-8 ou XLSX inválido → 422 `/erros/arquivo-invalido`, nenhum lote criado
2. Validar cabeçalhos
   └── divergente → 422, arquivo inteiro recusado, nenhuma linha processada (AC-045)
3. Para cada linha:
   ├── normalizar (trim, upper em enums, parse de data e decimal)
   ├── validar campos obrigatórios e domínios
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

**Limite:** arquivos acima de 5 MB ou 5.000 linhas são recusados no MVP. Processamento assíncrono fica para a V2.


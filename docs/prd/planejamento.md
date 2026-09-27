# PRD — Riscos, Roadmap e Perguntas em Aberto (RI-, RE-, QA-)

Parte de [PRD — ITAM](README.md).

## 17. Riscos e Restrições

### 17.1 Riscos do produto

| ID | Risco | Prob. | Impacto | Score | Mitigação |
|---|---|---|---|---|---|
| RI-01 | Dados iniciais de inventário incompletos ou inconsistentes, comprometendo a confiança no sistema | 4 | 4 | 16 | Importação com validação e relatório de erros (FR-008); indicador de cobertura como métrica de adoção |
| RI-02 | Usuários deixarem de registrar transferências, tornando o histórico irreal | 4 | 4 | 16 | Formulário de transferência com no máximo 4 campos (NFR-USA-02); interface responsiva para registro em campo |
| RI-03 | Divergência entre o valor residual do sistema e o registro contábil | 3 | 4 | 12 | Método linear explícito e parametrizado; relatório conciliável; vida útil alinhada à IN RFB 1.700 |
| RI-04 | Bloqueio de excedente de licença sendo contornado por cadastro paralelo | 3 | 4 | 12 | Registro da tentativa bloqueada na auditoria (NFR-AUD-05); relatório de conformidade periódico |
| RI-05 | Divergência funcional entre as implementações Python e Java | 3 | 3 | 9 | Contrato OpenAPI único; suíte de testes de contrato executada contra ambas |
| RI-06 | Perda de histórico por exclusão indevida | 2 | 5 | 10 | Tabelas append-only com restrição no banco; RBAC sem permissão de exclusão para nenhum perfil |
| RI-07 | Escopo expandindo para funcionalidades de ERP durante o desenvolvimento | 3 | 3 | 9 | Seção 7.2 como referência contratual; mudança de escopo exige registro formal |
| RI-08 | Vazamento de chaves de licença armazenadas em texto claro | 2 | 4 | 8 | Acesso à chave restrito ao perfil `ADMIN`; mascaramento na listagem |
| RI-09 | Degradação de desempenho com crescimento da base | 2 | 3 | 6 | Paginação obrigatória; índices definidos nas migrações (NFR-PER-05) |
| RI-10 | Indisponibilidade do ambiente durante a demonstração | 2 | 4 | 8 | Perfil de execução local com SQLite/H2, independente de infraestrutura externa; smoke test antes da apresentação |

### 17.2 Restrições

| ID | Restrição | Natureza |
|---|---|---|
| RE-01 | As implementações Python e Java devem obedecer ao mesmo contrato de API | Técnica — definida pela baseline da disciplina |
| RE-02 | Moeda única (BRL) e organização única no MVP | Escopo |
| RE-03 | Método de depreciação restrito ao linear | Escopo |
| RE-04 | Nenhuma integração com sistemas externos (AD, ERP, SCCM) | Escopo |
| RE-05 | Execução obrigatória via Docker Compose com um comando | Técnica |
| RE-06 | A decisão de investimento permanece humana; o sistema não escolhe automaticamente | Governança — princípio da baseline |
| RE-07 | Toda recomendação exige evidência vinculada | Governança — princípio da baseline |
| RE-08 | O sistema é uma camada de apoio à governança, não um simulador de infraestrutura real | Posicionamento — definido pelo guia de orquestração |

---

## 18. Roadmap

### 18.1 MVP — versão 1.0

**Objetivo:** inventário confiável, responsabilidade rastreável e conformidade visível.

| Sprint | Entrega |
|---|---|
| Sprint 0 | Discovery, modelo de dados, contrato OpenAPI, ambiente Docker Compose |
| Sprint 1 | FR-001, FR-008, FR-015 — cadastro, importação, autenticação e RBAC |
| Sprint 2 | FR-002, FR-003 — responsáveis, histórico e depreciação |
| Sprint 3 | FR-004, FR-005 — licenças, alertas e baixas |
| Sprint 4 | FR-006, FR-007, FR-009, FR-014 — relatórios, compliance, indicadores e dashboard |
| Sprint 5 | FR-010 a FR-013 — cenários, scorecard, riscos e recomendação rastreável; testes, documentação e defesa |

### 18.2 V2 — consolidação operacional

- Geração e leitura de **QR Code** por ativo, para inventário físico assistido por celular;
- **Upload de nota fiscal**, manuais e fotos, com armazenamento de anexos;
- **Termo de responsabilidade** gerado em PDF, com assinatura digital;
- **Renovação assistida de licenças**, com fluxo de aprovação;
- **Gestão de garantia e contratos de manutenção**, com alertas próprios;
- Métodos adicionais de depreciação (soma dos dígitos, unidades produzidas);
- Suporte a **múltiplas filiais** e centros de custo;
- Notificações por e-mail para alertas críticos.

### 18.3 V3 — automação e inteligência

- **Inventário automático via agente** instalado nas estações;
- **Integração com Microsoft Intune** para sincronização de dispositivos gerenciados;
- **Integração com Active Directory / LDAP** para autenticação e base de responsáveis;
- **Integração com ERP** para conciliação patrimonial automática;
- **Modelo preditivo de substituição de ativos**, estimando o momento ótimo de troca a partir de idade, histórico de manutenção e custo acumulado;
- Detecção de anomalias de uso de licenças;
- API pública para consumo por sistemas de terceiros.

---

## 19. Perguntas em Aberto

| ID | Pergunta | Impacto se não respondida | Responsável por responder |
|---|---|---|---|
| QA-01 | Haverá múltiplas filiais ou unidades com inventários segregados? | Afeta o modelo de dados (entidade Unidade) e o escopo dos relatórios | Patrocinador |
| QA-02 | Haverá necessidade de múltiplas moedas para ativos importados? | Afeta os campos monetários e o cálculo de depreciação | Patrimônio |
| QA-03 | Haverá integração com ERP para conciliação patrimonial, ainda que por exportação? | Define o formato de exportação exigido | Patrimônio / TI |
| QA-04 | Qual o formato do inventário legado a ser importado? | Define o parser e o mapeamento de colunas do FR-008 | Administrador de TI |
| QA-05 | A vida útil deve seguir a tabela fiscal ou uma política interna própria? | Afeta a parametrização padrão das categorias | Contabilidade |
| QA-06 | Software adquirido deve ser modelado como Ativo, como Licença ou como ambos? | Afeta o modelo de dados e a interpretação dos indicadores | Arquitetura / Patrimônio |
| QA-07 | A janela de alerta de vencimento de licença é fixa em 30 dias ou varia por fornecedor? | Define se o parâmetro é global ou por licença | Administrador de TI |
| QA-08 | Ativos compartilhados (impressoras, projetores) devem ter pessoa responsável ou apenas setor? | Afeta a obrigatoriedade do campo responsável no FR-002 | Administrador de TI |
| QA-09 | Deve existir estorno de baixa, ou a operação é definitiva? | Afeta a imutabilidade assumida no BR-024 | Patrimônio / Auditoria |
| QA-10 | Colaboradores terão acesso de consulta aos próprios ativos? | Cria um quinto perfil de acesso, hoje fora do escopo | Patrocinador |
| QA-11 | Qual a política de retenção do histórico e da trilha de auditoria? | Afeta o volume da base e eventual expurgo | Compliance |
| QA-12 | Qual o destinatário formal dos relatórios de conformidade e com que periodicidade? | Define automação de geração e envio | Compliance |

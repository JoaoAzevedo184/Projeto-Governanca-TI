[PYTHON_BADGE]: https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white
[FASTAPI_BADGE]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[POSTGRES_BADGE]: https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[SQLALCHEMY_BADGE]: https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white
[DOCKER_BADGE]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[PROMETHEUS_BADGE]: https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white
[GRAFANA_BADGE]: https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white
[ACADEMICO_BADGE]: https://img.shields.io/badge/uso-acad%C3%AAmico-informational?style=for-the-badge

<h1 align="center" style="font-weight: bold;">ITAM — Gestão de Ativos de TI 💻</h1>

<p align="center">

![python][PYTHON_BADGE]
![fastapi][FASTAPI_BADGE]
![postgresql][POSTGRES_BADGE]
![sqlalchemy][SQLALCHEMY_BADGE]
![docker][DOCKER_BADGE]
![prometheus][PROMETHEUS_BADGE]
![grafana][GRAFANA_BADGE]
![uso acadêmico][ACADEMICO_BADGE]

</p>

<p align="center">
  <b>Sistema de apoio à governança do parque de TI: inventário, responsáveis, depreciação, licenças, conformidade e apoio à decisão.</b>
</p>

<p align="center">
  Projeto da disciplina <b>Governança de TI</b> — Bacharelado em Sistemas de Informação, UNINASSAU Olinda.
</p>

<details open="open">
<summary>Sumário</summary>

- [📖 Sobre o projeto](#sobre)
- [✨ Funcionalidades](#funcionalidades)
- [🚀 Como executar](#executar)
  - [Pré-requisitos](#pre-requisitos)
  - [Clonando](#clonando)
  - [Variáveis de ambiente](#variaveis)
  - [Iniciando](#iniciando)
  - [Ambiente de demonstração](#demonstracao)
- [📍 Rotas da API](#rotas)
- [👥 Perfis de acesso](#perfis)
- [🗂️ Dados](#dados)
- [📚 Documentação](#documentacao)
- [🤝 Equipe](#equipe)
- [📫 Como contribuir](#contribuir)
- [📄 Licença](#licenca)

</details>

<h2 id="sobre">📖 Sobre o projeto</h2>

O ITAM reúne os dados dos ativos de TI de uma organização e os transforma em indicadores, alertas e recomendações para apoiar decisões. Não é um sistema de descoberta automática de inventário nem um ERP patrimonial.

| Problema | Resposta do sistema |
|---|---|
| Inventário espalhado em planilhas | Base única, com importação validada de CSV e XLSX |
| Equipamentos sem responsável | Vínculo de responsável com histórico que não pode ser alterado |
| Licenças usadas acima do contratado | Bloqueio da operação e alerta de conformidade |
| Valor patrimonial parado no valor de compra | Depreciação linear calculada automaticamente |
| Descarte sem rastreabilidade | Baixa com motivo, data e destinação |

**Princípios**

1. Nenhuma recomendação sem evidência.
2. A decisão é humana: o sistema ordena as alternativas e não escolhe.
3. O histórico não se apaga: transferências, baixas e auditoria só aceitam inclusão.
4. Todo dado declara a sua origem.

<h2 id="funcionalidades">✨ Funcionalidades</h2>

| Código | Funcionalidade |
|---|---|
| FR-001 | Cadastro de ativos de hardware e software |
| FR-002 | Vinculação de responsável com histórico de transferências |
| FR-003 | Depreciação linear e valor residual |
| FR-004 | Controle de licenças com alerta de excedente e de vencimento |
| FR-005 | Baixa e descarte com motivo, data e destinação |
| FR-006 | Relatório de inventário com filtros e exportação |
| FR-007 | Painel de alertas de conformidade |
| FR-008 | Importação de inventário em CSV e XLSX com relatório de erros |
| FR-009 | Indicadores de ITAM |
| FR-010 | Comparação de cenários com custo total de 5 anos |
| FR-011 | Scorecard ponderado de fornecedores |
| FR-012 | Registro de riscos com probabilidade e impacto |
| FR-013 | Recomendações vinculadas a evidências |
| FR-014 | Painel gerencial e observabilidade técnica |
| FR-015 | Autenticação e controle de acesso por perfil |

O que ficou fora desta versão está descrito no [roadmap](docs/ROADMAP.md).

<h2 id="executar">🚀 Como executar</h2>

<h3 id="pre-requisitos">Pré-requisitos</h3>

- [Docker Engine 24+](https://docs.docker.com/engine/install/) e Docker Compose v2
- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/), só para carregar os dados de demonstração

<h3 id="clonando">Clonando</h3>

```bash
git clone <url-do-repositorio> itam-api
cd itam-api
```

<h3 id="variaveis">Variáveis de ambiente</h3>

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

| Variável | Para que serve |
|---|---|
| `SECRET_KEY` | Chave de assinatura dos tokens. Obrigatória |
| `SEED_ADMIN_PASSWORD`, `SEED_OPERADOR_PASSWORD`, `SEED_GESTOR_PASSWORD`, `SEED_AUDITOR_PASSWORD` | Senhas dos quatro usuários de demonstração |
| `GRAFANA_USER`, `GRAFANA_PASSWORD` | Acesso ao Grafana |
| `NVD_API_KEY` | Opcional. Só para refazer a coleta de dados públicos |

Para gerar a `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

O `.env` nunca deve ser enviado ao repositório.

<h3 id="iniciando">Iniciando</h3>

```bash
./scripts/start.sh        # sobe API, banco, Prometheus e Grafana
./scripts/seed.sh         # cria os usuários de demonstração e as categorias
./scripts/smoke_test.sh   # confere se tudo está no ar
```

| Serviço | Endereço |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

<h3 id="demonstracao">Ambiente de demonstração</h3>

Depois do `seed.sh`, o banco tem usuários e categorias, mas nenhum ativo. Para montar o cenário completo usado nas demonstrações (92 ativos reais, responsáveis, licenças, alertas, riscos e recomendação), siga o passo a passo:

- [Preparo do ambiente de demonstração](docs/guia/preparo-da-demonstracao.md)
- [Roteiro de demonstração por gate](docs/guia/demonstracao.md)

<h2 id="rotas">📍 Rotas da API</h2>

Todas as rotas ficam em `/api/v1`. A lista completa, com exemplos, está no Swagger.

| Rota | Descrição |
|---|---|
| <kbd>POST /auth/login</kbd> | Autentica e devolve o token. Ver [detalhes](#login) |
| <kbd>GET /auth/me</kbd> | Dados do usuário autenticado |
| <kbd>GET · POST · PATCH /ativos</kbd> | Consulta, cadastro e edição de ativos |
| <kbd>POST /ativos/{id}/responsavel</kbd> | Atribui ou transfere o responsável |
| <kbd>GET /ativos/{id}/historico</kbd> | Linha do tempo de responsáveis |
| <kbd>GET /ativos/{id}/depreciacao</kbd> | Depreciação e valor residual |
| <kbd>POST /ativos/{id}/baixa</kbd> | Baixa do ativo |
| <kbd>GET · POST · PATCH /licencas</kbd> | Licenças de software |
| <kbd>POST /licencas/{id}/vinculos</kbd> | Vincula uma licença a uma máquina |
| <kbd>POST /importacoes</kbd> | Importa inventário em CSV ou XLSX |
| <kbd>GET /compliance/alertas</kbd> | Alertas de conformidade por severidade |
| <kbd>GET /indicadores</kbd> | Indicadores, com fórmula e amostra |
| <kbd>GET /relatorios/inventario</kbd> | Relatório de inventário (JSON, CSV ou XLSX) |
| <kbd>POST /cenarios/comparar</kbd> | Compara cenários pelo custo total de 5 anos |
| <kbd>POST /fornecedores/scorecard</kbd> | Avalia fornecedores com pesos |
| <kbd>GET · POST /riscos</kbd> | Registro de riscos |
| <kbd>GET · POST /recomendacoes</kbd> | Recomendações com evidências |

Fora do prefixo: <kbd>GET /health</kbd> e <kbd>GET /metrics</kbd>.

<h3 id="login">POST /auth/login</h3>

**Requisição**

```json
{
  "login": "admin",
  "senha": "sua-senha"
}
```

**Resposta**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Usando o token no Swagger**

1. Execute o login em <kbd>POST /auth/login</kbd> pelo botão **Try it out**.
2. Copie o valor de `access_token`.
3. Clique em **Authorize**, cole o token e confirme.

O token vale por cerca de uma hora.

<h2 id="perfis">👥 Perfis de acesso</h2>

| Login | Perfil | Pode |
|---|---|---|
| `admin` | ADMIN | Tudo, inclusive importar inventário |
| `operador` | OPERADOR | Cadastrar ativos, transferir responsáveis, registrar baixas e editar licenças |
| `gestor` | GESTOR | Consultar, comparar cenários e registrar riscos, avaliações e recomendações |
| `auditor` | AUDITOR | Somente leitura |

As senhas são as definidas no `.env`.

<h2 id="dados">🗂️ Dados</h2>

O projeto usa dados públicos reais sempre que eles existem, e dados sintéticos só para pessoas e eventos internos, que nenhuma fonte pública traz.

| Fonte | Uso no projeto |
|---|---|
| [Compras.gov.br](https://compras.dados.gov.br/) | Equipamentos do inventário de demonstração. É a única fonte carregada no banco |
| [endoflife.date](https://endoflife.date/) | Referência de ciclo de vida de software. Não é carregada no banco |
| [NVD](https://nvd.nist.gov/) | Referência de vulnerabilidades. Não é carregada no banco |
| Seed de demonstração | Responsáveis, licenças, riscos e demais registros fictícios, marcados como `sintetico` |

Cada registro guarda a sua origem no campo `data_source`. Detalhes em [Fontes de dados](docs/FONTES_DE_DADOS.md).

<h2 id="documentacao">📚 Documentação</h2>

| Documento | Conteúdo |
|---|---|
| [Requisitos (PRD)](docs/prd/README.md) | Visão do produto, requisitos, regras de negócio e critérios de aceite |
| [Especificação técnica](docs/spec/README.md) | Arquitetura, modelo de dados, contrato da API e testes |
| [Guias](docs/guia/README.md) | Execução, demonstração, coleta de dados, importação e testes |
| [Backlog e gates](docs/BACKLOG_E_GATES.md) | Planejamento das entregas |
| [Roadmap](docs/ROADMAP.md) | Situação atual de cada entrega |
| [Critérios de aceite](docs/CRITERIOS_DE_ACEITE.md) | Critérios de avaliação da disciplina |
| [Decisões de arquitetura](docs/adr/) | Registro das decisões e seus motivos |
| [Registro de uso de IA](docs/REGISTRO_USO_DE_IA.md) | Como ferramentas de IA foram usadas no projeto |

<h2 id="equipe">🤝 Equipe</h2>

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/JoaoAzevedo184">
        <img src="https://github.com/JoaoAzevedo184.png" width="100px;" alt="Foto de João Victor Azevedo"/><br>
        <sub>
          <b>João Victor Azevedo</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="#">
        <img src="https://github.com/ghost.png" width="100px;" alt="Foto do integrante"/><br>
        <sub>
          <b>Nome do integrante</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="#">
        <img src="https://github.com/ghost.png" width="100px;" alt="Foto do integrante"/><br>
        <sub>
          <b>Nome do integrante</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

<h2 id="contribuir">📫 Como contribuir</h2>

1. Crie uma branch: `git checkout -b feat/nome-da-mudanca`
2. Siga o padrão de commits do projeto, por exemplo `feat(importacao): ...` ou `fix(auth): ...`
3. Rode os testes antes de enviar (veja o [guia de testes](docs/guia/testes.md))
4. Se usou ferramenta de IA, registre em [`docs/REGISTRO_USO_DE_IA.md`](docs/REGISTRO_USO_DE_IA.md)
5. Abra um Pull Request explicando o que mudou e por quê

<h2 id="licenca">📄 Licença</h2>

Projeto acadêmico, sem fins comerciais, para uso educacional.

Os dados públicos pertencem às respectivas fontes: Compras.gov.br (dados abertos do Governo Federal), endoflife.date (licença MIT) e NVD/NIST (domínio público). Os dados sintéticos não representam pessoas reais.
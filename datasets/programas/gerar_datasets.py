#!/usr/bin/env python3
"""
Gerador de datasets de demonstração — ITAM (Gestão de Ativos de TI)

Produz os 12 arquivos CSV de demonstração com coerência referencial e
desvios plantados deliberadamente, conforme a seção 8 de
docs/MODELO_DE_DADOS.md.

Semente fixa: a mesma execução sempre gera os mesmos dados, o que torna
a demonstração e os testes reprodutíveis.

Uso:
    python gerar_datasets.py [--saida datasets/] [--semente 42]
"""

from __future__ import annotations

import argparse
import csv
import random
import unicodedata
from dataclasses import dataclass, asdict, fields
from datetime import date, timedelta
from pathlib import Path

DATA_REFERENCIA = date(2026, 9, 20)
SEMENTE_PADRAO = 42

# --------------------------------------------------------------------------
# Catálogos base
# --------------------------------------------------------------------------

CATEGORIAS = [
    ("Notebook", "HARDWARE", 60, "Computadores portáteis corporativos"),
    ("Desktop", "HARDWARE", 60, "Estações de trabalho fixas"),
    ("Servidor", "HARDWARE", 60, "Servidores físicos de datacenter"),
    ("Monitor", "HARDWARE", 60, "Monitores e displays"),
    ("Switch", "HARDWARE", 60, "Switches de rede"),
    ("Roteador", "HARDWARE", 60, "Roteadores e firewalls"),
    ("Impressora", "HARDWARE", 48, "Impressoras e multifuncionais"),
    ("Smartphone", "HARDWARE", 36, "Celulares corporativos"),
    ("Tablet", "HARDWARE", 36, "Tablets corporativos"),
    ("Nobreak", "HARDWARE", 60, "Nobreaks e estabilizadores"),
    ("Software perpetuo", "SOFTWARE", 60, "Licencas de software perpetuas"),
]

FORNECEDORES = [
    ("Dell Computadores do Brasil Ltda", "72.381.189/0001-10", "Marcos Pereira", "(11) 4004-0000", "corporativo@dell.exemplo.br"),
    ("Lenovo Tecnologia Brasil Ltda", "07.275.920/0001-61", "Ana Beatriz Souza", "(11) 3958-0000", "vendas@lenovo.exemplo.br"),
    ("HP Brasil Industria e Comercio", "61.797.924/0001-55", "Ricardo Alves", "(11) 3004-0000", "contas@hp.exemplo.br"),
    ("Positivo Tecnologia S.A.", "81.243.735/0001-48", "Fernanda Lima", "(41) 3316-0000", "corporativo@positivo.exemplo.br"),
    ("Cisco do Brasil Ltda", "01.480.353/0001-57", "Paulo Menezes", "(11) 5508-0000", "br-sales@cisco.exemplo.br"),
    ("Intelbras S.A.", "82.901.000/0001-27", "Juliana Castro", "(48) 2106-0000", "vendas@intelbras.exemplo.br"),
    ("Samsung Eletronica da Amazonia", "00.280.273/0001-37", "Carlos Eduardo Reis", "(11) 5644-0000", "b2b@samsung.exemplo.br"),
    ("APC by Schneider Electric Brasil", "33.126.412/0001-70", "Renata Barbosa", "(11) 2165-0000", "apc@schneider.exemplo.br"),
    ("Microsoft Informatica Ltda", "60.316.817/0001-03", "Tiago Nogueira", "(11) 5504-0000", "licenciamento@microsoft.exemplo.br"),
    ("Adobe Systems Brasil Ltda", "04.723.583/0001-02", "Mariana Pires", "(11) 3054-0000", "vlp@adobe.exemplo.br"),
    ("TechSupri Distribuidora de TI Ltda", "18.442.907/0001-84", "Jose Ferreira", "(81) 3421-0000", "comercial@techsupri.exemplo.br"),
    ("Nordeste Solucoes Corporativas ME", "29.115.660/0001-19", "Sandra Melo", "(81) 3033-0000", "contato@nordestesol.exemplo.br"),
]

SETORES = [
    ("Tecnologia da Informacao", "TI"),
    ("Financeiro", "FIN"),
    ("Recursos Humanos", "RH"),
    ("Comercial", "COM"),
    ("Operacoes", "OPE"),
    ("Juridico", "JUR"),
    ("Marketing", "MKT"),
    ("Diretoria", "DIR"),
]

NOMES = [
    "Ana Carolina Ribeiro", "Bruno Tavares Lima", "Camila Nunes Andrade", "Diego Amaral Souza",
    "Eduarda Freitas Melo", "Felipe Cardoso Rocha", "Gabriela Martins Dias", "Henrique Barbosa Pinto",
    "Isabela Correia Nunes", "Joao Victor Azevedo", "Karina Lopes Ferreira", "Leandro Mendes Costa",
    "Mariana Duarte Alves", "Nathalia Gomes Silva", "Otavio Pereira Ramos", "Patricia Moreira Luz",
    "Rafael Antunes Braga", "Rosangela Lima Santos", "Samuel Oliveira Cruz", "Tatiana Vieira Rego",
    "Ubiratan Nogueira Sa", "Vanessa Cunha Teixeira", "Wagner Brito Macedo", "Yasmin Farias Leal",
    "Zeca Monteiro Prado", "Adriana Bastos Carneiro", "Bernardo Queiroz Lins", "Carla Dantas Moura",
    "Daniel Xavier Peixoto", "Elaine Rocha Bezerra", "Fabio Guimaraes Neto", "Giovana Pires Sampaio",
    "Hugo Teixeira Valadares", "Ingrid Almeida Furtado", "Jorge Luiz Cavalcanti", "Kelly Ramos Siqueira",
    "Lucas Beltrao Figueiredo", "Marcos Tavares Junior", "Natalia Coelho Aragao", "Olavo Mendonca Pires",
    "Priscila Fonseca Maia", "Quiteria Santana Rocha", "Ricardo Salles Mendes", "Simone Batista Lira",
    "Thiago Penha Miranda", "Ursula Campos Azevedo", "Victor Hugo Serrano", "Wanessa Paiva Cordeiro",
    "Xavier Brandao Pontes", "Yuri Carvalho Diniz", "Zilda Marques Prado", "Alexandre Nobrega Fialho",
    "Beatriz Cardim Ventura", "Cesar Augusto Trindade", "Debora Pimentel Rosa", "Emanuel Souto Aguiar",
    "Flavia Ronchi Bittar", "Gustavo Falcao Mesquita", "Helena Drummond Paes", "Igor Salgado Vilela",
]

CARGOS = [
    "Analista de Sistemas", "Analista Financeiro", "Assistente Administrativo", "Coordenador",
    "Gerente", "Analista de RH", "Executivo de Contas", "Analista de Suporte",
    "Advogado", "Analista de Marketing", "Diretor", "Estagiario",
    "Tecnico de Infraestrutura", "Analista de Dados", "Supervisor",
]

MODELOS_HW = {
    "Notebook": [("Dell Latitude 5440", 6200), ("Lenovo ThinkPad E14", 5400), ("HP ProBook 450 G10", 5800),
                 ("Dell Vostro 3520", 4100), ("Lenovo IdeaPad 3", 3200)],
    "Desktop": [("Dell OptiPlex 7010", 4800), ("HP EliteDesk 800 G9", 5200), ("Positivo Master D2300", 3400)],
    "Servidor": [("Dell PowerEdge R650", 48000), ("HP ProLiant DL380 Gen10", 52000), ("Dell PowerEdge T350", 21000)],
    "Monitor": [("Dell P2422H 24", 1100), ("Samsung LF24T350 24", 850), ("LG 24MK430H", 780)],
    "Switch": [("Cisco Catalyst 1000-24T", 4200), ("Intelbras SG 2404 MR", 1400)],
    "Roteador": [("Cisco ISR 1111", 7800), ("Intelbras RF 1200", 620)],
    "Impressora": [("HP LaserJet Pro M404dn", 2400), ("Samsung SL-M4020ND", 2100)],
    "Smartphone": [("Samsung Galaxy A54", 1900), ("Samsung Galaxy S23", 4300), ("Motorola Edge 40", 2400)],
    "Tablet": [("Samsung Galaxy Tab S9", 4100), ("Samsung Galaxy Tab A8", 1300)],
    "Nobreak": [("APC Smart-UPS 1500VA", 3900), ("Intelbras XNB 1400VA", 980)],
}

SOFTWARES = [
    ("Microsoft 365 Business Standard", 8, "SUBSCRICAO"), ("Microsoft Windows 11 Pro", 8, "OEM"),
    ("Microsoft SQL Server Standard", 8, "PERPETUA"), ("Adobe Creative Cloud", 9, "SUBSCRICAO"),
    ("Adobe Acrobat Pro", 9, "SUBSCRICAO"), ("AutoCAD LT", 10, "SUBSCRICAO"),
    ("CorelDRAW Graphics Suite", 10, "PERPETUA"), ("JetBrains All Products Pack", 10, "SUBSCRICAO"),
    ("Kaspersky Endpoint Security", 11, "SUBSCRICAO"), ("Veeam Backup Essentials", 11, "PERPETUA"),
    ("VMware vSphere Standard", 11, "PERPETUA"), ("Zoom Workplace Business", 10, "SUBSCRICAO"),
    ("Slack Pro", 10, "SUBSCRICAO"), ("Atlassian Jira Software", 10, "SUBSCRICAO"),
    ("TeamViewer Corporate", 11, "SUBSCRICAO"), ("Nitro PDF Pro", 10, "PERPETUA"),
    ("SolarWinds NPM", 11, "PERPETUA"), ("Oracle Database Standard", 11, "PERPETUA"),
    ("Red Hat Enterprise Linux", 11, "SUBSCRICAO"), ("Bitdefender GravityZone", 11, "SUBSCRICAO"),
    ("Docusign Business Pro", 10, "SUBSCRICAO"), ("Tableau Creator", 10, "SUBSCRICAO"),
    ("SAP Crystal Reports", 11, "PERPETUA"), ("Figma Organization", 10, "SUBSCRICAO"),
    ("Notion Business", 10, "SUBSCRICAO"),
]

LOCALIZACOES = [
    "Bloco A - Sala 101", "Bloco A - Sala 204", "Bloco A - Recepcao", "Bloco B - Sala 302",
    "Bloco B - Sala 310", "Bloco B - Almoxarifado", "Anexo I - Sala 12", "Anexo II - Sala 05",
    "Datacenter - Rack 01", "Datacenter - Rack 02", "Home office", "Deposito de TI",
]


# --------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------

@dataclass
class Ativo:
    id: int
    nome: str
    tipo: str
    categoria: str
    fornecedor: str
    numero_serie: str
    chave_licenca: str
    data_aquisicao: str
    valor_compra: str
    status: str
    localizacao: str


def escrever_csv(caminho: Path, cabecalho: list[str], linhas: list[list]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas)
    print(f"  {caminho.name:<28} {len(linhas):>4} linhas")


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def serie(rng: random.Random, prefixo: str) -> str:
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return prefixo + "".join(rng.choice(alfabeto) for _ in range(8))


def chave(rng: random.Random) -> str:
    grupo = lambda: "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789") for _ in range(5))
    return "-".join(grupo() for _ in range(5))


def meses_atras(base: date, meses: int) -> date:
    ano = base.year - (meses + 11 - base.month) // 12 if meses >= base.month else base.year
    total = base.year * 12 + base.month - 1 - meses
    ano, mes = divmod(total, 12)
    dia = min(base.day, 28)
    return date(ano, mes + 1, dia)


# --------------------------------------------------------------------------
# Geração
# --------------------------------------------------------------------------

def gerar(saida: Path, semente: int) -> None:
    rng = random.Random(semente)
    hoje = DATA_REFERENCIA
    vida_util = {c[0]: c[2] for c in CATEGORIAS}

    print("\nGerando datasets de demonstracao do ITAM")
    print(f"  data de referencia: {hoje.isoformat()}  |  semente: {semente}\n")

    # ---- 1. categorias -------------------------------------------------
    escrever_csv(
        saida / "categorias.csv",
        ["nome", "tipo_aplicavel", "vida_util_meses", "descricao"],
        [[n, t, v, d] for n, t, v, d in CATEGORIAS],
    )

    # ---- 2. fornecedores -----------------------------------------------
    escrever_csv(
        saida / "fornecedores.csv",
        ["razao_social", "cnpj", "contato", "telefone", "email"],
        [list(f) for f in FORNECEDORES],
    )

    # ---- 3. setores ----------------------------------------------------
    escrever_csv(saida / "setores.csv", ["nome", "sigla"], [list(s) for s in SETORES])

    # ---- 4. responsaveis -----------------------------------------------
    responsaveis = []
    for i, nome in enumerate(NOMES, start=1):
        setor = SETORES[rng.randrange(len(SETORES))][0]
        primeiro = sem_acento(nome.split()[0]).lower()
        ultimo = sem_acento(nome.split()[-1]).lower()
        responsaveis.append([
            f"MAT{i:04d}", nome, f"{primeiro}.{ultimo}@empresa.exemplo.br",
            CARGOS[rng.randrange(len(CARGOS))], setor, "true",
        ])
    escrever_csv(
        saida / "responsaveis.csv",
        ["matricula", "nome", "email", "cargo", "setor", "ativo"],
        responsaveis,
    )

    # ---- 5. inventario -------------------------------------------------
    # Plano de composição dos 300 ativos:
    #   40 baixados | 12 em manutencao (4 antigos) | 12 sem responsavel
    #   18 totalmente depreciados em operacao | 25 sem movimentacao 12m
    TOTAL = 300
    ativos: list[Ativo] = []
    series_usadas: set[str] = set()
    catalogo_hw = [(cat, mod, preco) for cat, lst in MODELOS_HW.items() for mod, preco in lst]

    def nova_serie(prefixo: str) -> str:
        while True:
            s = serie(rng, prefixo)
            if s not in series_usadas:
                series_usadas.add(s)
                return s

    # 260 hardware + 40 software
    for i in range(1, TOTAL + 1):
        if i <= 260:
            cat, modelo, preco_base = catalogo_hw[rng.randrange(len(catalogo_hw))]
            tipo = "HARDWARE"
            num = nova_serie(cat[:2].upper())
            chv = ""
            nome = modelo
            fornecedor = FORNECEDORES[rng.randrange(8)][0]
        else:
            cat = "Software perpetuo"
            tipo = "SOFTWARE"
            sw, idx_forn, _ = SOFTWARES[rng.randrange(len(SOFTWARES))]
            nome = sw
            num = ""
            chv = chave(rng)
            preco_base = rng.choice([890, 1200, 2400, 3600, 5800])
            fornecedor = FORNECEDORES[idx_forn][0]

        # Idade: a maioria entre 3 e 48 meses
        idade = rng.randint(1, 48)
        valor = round(preco_base * rng.uniform(0.88, 1.12), 2)

        ativos.append(Ativo(
            id=i, nome=nome, tipo=tipo, categoria=cat, fornecedor=fornecedor,
            numero_serie=num, chave_licenca=chv,
            data_aquisicao=meses_atras(hoje, idade).isoformat(),
            valor_compra=f"{valor:.2f}", status="ATIVO",
            localizacao=LOCALIZACOES[rng.randrange(len(LOCALIZACOES))],
        ))

    # --- desvio CP-05: 18 ativos totalmente depreciados ainda em operacao
    idx_depreciados = rng.sample(range(120, 260), 18)
    for i in idx_depreciados:
        a = ativos[i]
        vu = vida_util[a.categoria]
        a.data_aquisicao = meses_atras(hoje, vu + rng.randint(6, 30)).isoformat()

    # --- 40 baixados
    idx_baixados = rng.sample([i for i in range(TOTAL) if i not in idx_depreciados], 40)
    for i in idx_baixados:
        ativos[i].status = "BAIXADO"

    # Datas de baixa definidas aqui para servirem de limite aos vinculos
    datas_baixa: dict[int, date] = {}
    for i in idx_baixados:
        aq = date.fromisoformat(ativos[i].data_aquisicao)
        dias_max = max(60, (hoje - aq).days - 5)
        data_b = aq + timedelta(days=rng.randint(min(180, dias_max), dias_max))
        if data_b > hoje:
            data_b = hoje - timedelta(days=rng.randint(1, 60))
        if data_b <= aq:
            data_b = aq + timedelta(days=45)
        datas_baixa[i] = data_b

    restantes = [i for i in range(TOTAL) if i not in idx_baixados]

    # --- 12 em manutencao (4 deles ha mais de 90 dias  -> CP-06)
    idx_manutencao = rng.sample(restantes, 12)
    for i in idx_manutencao:
        ativos[i].status = "EM_MANUTENCAO"

    escrever_csv(
        saida / "inventario.csv",
        ["nome", "tipo", "categoria", "fornecedor", "numero_serie", "chave_licenca",
         "data_aquisicao", "valor_compra", "status", "localizacao"],
        [[a.nome, a.tipo, a.categoria, a.fornecedor, a.numero_serie, a.chave_licenca,
          a.data_aquisicao, a.valor_compra, a.status, a.localizacao] for a in ativos],
    )

    # ---- 6. inventario_com_erros ---------------------------------------
    # 100 linhas: 92 validas + 8 invalidas, uma por tipo de erro
    linhas_erro = []
    for i in range(92):
        cat, modelo, preco = catalogo_hw[rng.randrange(len(catalogo_hw))]
        linhas_erro.append([
            modelo, "HARDWARE", cat, FORNECEDORES[rng.randrange(8)][0],
            nova_serie("IM"), "", meses_atras(hoje, rng.randint(1, 36)).isoformat(),
            f"{preco * rng.uniform(0.9, 1.1):.2f}", "ATIVO",
            LOCALIZACOES[rng.randrange(len(LOCALIZACOES))],
        ])

    serie_dup = nova_serie("ER")
    serie_existente = ativos[0].numero_serie
    invalidas = [
        # 1. data de aquisicao futura (BR-003)
        ["Dell Latitude 5440", "HARDWARE", "Notebook", FORNECEDORES[0][0], nova_serie("ER"), "",
         (hoje + timedelta(days=45)).isoformat(), "6200.00", "ATIVO", "Bloco A - Sala 101"],
        # 2. valor de compra zerado (BR-004)
        ["HP ProBook 450 G10", "HARDWARE", "Notebook", FORNECEDORES[2][0], nova_serie("ER"), "",
         meses_atras(hoje, 6).isoformat(), "0.00", "ATIVO", "Bloco B - Sala 302"],
        # 3. hardware sem numero de serie (BR-002)
        ["Monitor Dell P2422H 24", "HARDWARE", "Monitor", FORNECEDORES[0][0], "", "",
         meses_atras(hoje, 12).isoformat(), "1100.00", "ATIVO", "Bloco A - Sala 204"],
        # 4. numero de serie duplicado dentro do proprio arquivo
        ["Lenovo ThinkPad E14", "HARDWARE", "Notebook", FORNECEDORES[1][0], serie_dup, "",
         meses_atras(hoje, 9).isoformat(), "5400.00", "ATIVO", "Anexo I - Sala 12"],
        ["Lenovo ThinkPad E14", "HARDWARE", "Notebook", FORNECEDORES[1][0], serie_dup, "",
         meses_atras(hoje, 9).isoformat(), "5400.00", "ATIVO", "Anexo II - Sala 05"],
        # 5. numero de serie ja existente na base (BR-001)
        ["Dell OptiPlex 7010", "HARDWARE", "Desktop", FORNECEDORES[0][0], serie_existente, "",
         meses_atras(hoje, 4).isoformat(), "4800.00", "ATIVO", "Bloco B - Sala 310"],
        # 6. categoria inexistente
        ["Webcam Logitech C920", "HARDWARE", "Periferico", FORNECEDORES[10][0], nova_serie("ER"), "",
         meses_atras(hoje, 3).isoformat(), "450.00", "ATIVO", "Bloco A - Recepcao"],
        # 7. formato de data invalido
        ["Samsung Galaxy A54", "HARDWARE", "Smartphone", FORNECEDORES[6][0], nova_serie("ER"), "",
         "14/03/2025", "1900.00", "ATIVO", "Home office"],
    ]
    # 8. tipo invalido — substitui a ultima posicao livre
    invalidas.append(
        ["Nobreak APC Smart-UPS 1500VA", "EQUIPAMENTO", "Nobreak", FORNECEDORES[7][0], nova_serie("ER"), "",
         meses_atras(hoje, 18).isoformat(), "3900.00", "ATIVO", "Datacenter - Rack 01"]
    )

    # Intercala as invalidas em posicoes conhecidas
    for offset, linha in enumerate(invalidas):
        pos = min(7 + offset * 11, len(linhas_erro))
        linhas_erro.insert(pos, linha)
    linhas_erro = linhas_erro[:100]

    escrever_csv(
        saida / "inventario_com_erros.csv",
        ["nome", "tipo", "categoria", "fornecedor", "numero_serie", "chave_licenca",
         "data_aquisicao", "valor_compra", "status", "localizacao"],
        linhas_erro,
    )

    # ---- 7. transferencias ---------------------------------------------
    # Regras: data_inicio >= data_aquisicao; sem sobreposicao; no maximo um
    # vinculo aberto por ativo; ativo baixado nao tem vinculo aberto.
    transferencias = []
    idx_sem_responsavel = rng.sample(
        [i for i in restantes if i not in idx_manutencao], 12)          # CP-04
    candidatos_parados = [i for i in restantes
                          if i not in idx_sem_responsavel]
    idx_sem_movimento = rng.sample(candidatos_parados, 25)              # CP-08

    for i, a in enumerate(ativos):
        if i in idx_sem_responsavel:
            continue                                                    # CP-04

        aquisicao = date.fromisoformat(a.data_aquisicao)
        limite = datas_baixa.get(i, hoje)

        dias_disponiveis = (limite - aquisicao).days
        if dias_disponiveis < 15:
            n_vinculos = 1
        elif i in idx_sem_movimento:
            n_vinculos = 1
        else:
            n_vinculos = rng.choices([1, 2, 3], weights=[55, 32, 13])[0]

        # Pontos de corte crescentes dentro da janela disponivel
        cursor = aquisicao + timedelta(days=rng.randint(0, max(1, min(20, dias_disponiveis))))
        if i in idx_sem_movimento:
            # vinculo aberto iniciado ha mais de 12 meses
            cursor = meses_atras(hoje, rng.randint(14, 30))
            if cursor < aquisicao:
                cursor = aquisicao

        for k in range(n_vinculos):
            resp = rng.randrange(len(responsaveis))
            setor = responsaveis[resp][4]
            ultimo = (k == n_vinculos - 1)
            if ultimo and a.status != "BAIXADO":
                data_fim = ""
            else:
                restante = (limite - cursor).days
                if restante <= 5:
                    data_fim = limite.isoformat()
                else:
                    data_fim = (cursor + timedelta(days=rng.randint(30, max(31, restante)))).isoformat()
                    if date.fromisoformat(data_fim) > limite:
                        data_fim = limite.isoformat()

            transferencias.append([
                a.numero_serie or a.chave_licenca, responsaveis[resp][0], setor,
                cursor.isoformat(), data_fim,
                rng.choice(["Entrega inicial", "Mudanca de setor", "Substituicao de equipamento",
                            "Desligamento do colaborador", "Remanejamento interno", ""]),
            ])
            if data_fim:
                cursor = date.fromisoformat(data_fim)

    escrever_csv(
        saida / "transferencias.csv",
        ["identificador_ativo", "matricula_responsavel", "setor", "data_inicio", "data_fim", "motivo"],
        transferencias,
    )

    # ---- 8. licencas ---------------------------------------------------
    # Desvios: 2 vencidas | 3 vencendo em <=30d | 1 acima do contratado
    #          3 subutilizadas
    licencas = []
    perfis = (["VENCIDA"] * 2 + ["VENCENDO"] * 3 + ["EXCEDENTE"] * 1
              + ["SUBUTILIZADA"] * 3 + ["NORMAL"] * 16)
    rng.shuffle(perfis)

    for (software, idx_forn, tipo_lic), perfil in zip(SOFTWARES, perfis):
        contratada = rng.choice([10, 15, 20, 25, 30, 40, 50, 60, 80, 100])
        aquisicao = meses_atras(hoje, rng.randint(8, 30))

        if perfil == "VENCIDA":
            expiracao = hoje - timedelta(days=rng.randint(8, 95))
            em_uso = rng.randint(int(contratada * 0.6), contratada)
        elif perfil == "VENCENDO":
            expiracao = hoje + timedelta(days=rng.randint(4, 29))
            em_uso = rng.randint(int(contratada * 0.7), contratada)
        elif perfil == "EXCEDENTE":
            expiracao = hoje + timedelta(days=rng.randint(120, 400))
            em_uso = contratada + rng.randint(2, 4)
        elif perfil == "SUBUTILIZADA":
            expiracao = hoje + timedelta(days=rng.randint(90, 500))
            em_uso = max(1, int(contratada * rng.uniform(0.18, 0.48)))
        else:
            expiracao = hoje + timedelta(days=rng.randint(60, 700))
            em_uso = rng.randint(int(contratada * 0.55), contratada - 1)

        if expiracao <= aquisicao:
            aquisicao = expiracao - timedelta(days=400)

        valor_unit = rng.choice([180, 320, 540, 890, 1400, 2600])
        licencas.append({
            "software": software,
            "fornecedor": FORNECEDORES[idx_forn][0],
            "chave_licenca": chave(rng),
            "quantidade_contratada": contratada,
            "data_aquisicao": aquisicao.isoformat(),
            "data_expiracao": expiracao.isoformat(),
            "valor_total": f"{valor_unit * contratada:.2f}",
            "tipo_licenciamento": tipo_lic,
            "_em_uso": em_uso,
            "_perfil": perfil,
        })

    escrever_csv(
        saida / "licencas.csv",
        ["software", "fornecedor", "chave_licenca", "quantidade_contratada",
         "data_aquisicao", "data_expiracao", "valor_total", "tipo_licenciamento"],
        [[l["software"], l["fornecedor"], l["chave_licenca"], l["quantidade_contratada"],
          l["data_aquisicao"], l["data_expiracao"], l["valor_total"], l["tipo_licenciamento"]]
         for l in licencas],
    )

    # ---- 9. licenca_vinculos -------------------------------------------
    hardware_operante = [a for a in ativos if a.tipo == "HARDWARE" and a.status != "BAIXADO"]
    vinculos_lic = []
    for l in licencas:
        alvos = rng.sample(hardware_operante, min(l["_em_uso"], len(hardware_operante)))
        base = date.fromisoformat(l["data_aquisicao"])
        for alvo in alvos:
            aq = date.fromisoformat(alvo.data_aquisicao)
            inicio = max(base, aq)
            dias = max(1, (hoje - inicio).days)
            vinculos_lic.append([
                l["software"], alvo.numero_serie,
                (inicio + timedelta(days=rng.randint(0, dias))).isoformat(), "true",
            ])

    escrever_csv(
        saida / "licenca_vinculos.csv",
        ["software", "numero_serie_ativo", "data_vinculo", "ativo_vinculo"],
        vinculos_lic,
    )

    # ---- 10. baixas ----------------------------------------------------
    motivos = ["OBSOLESCENCIA", "DEFEITO", "FURTO_ROUBO", "FIM_VIDA_UTIL", "OUTRO"]
    destinos = ["RECICLAGEM_CERTIFICADA", "DOACAO", "DEVOLUCAO_FORNECEDOR", "VENDA", "DESCARTE"]
    justificativas = {
        "OBSOLESCENCIA": "Equipamento fora do ciclo de suporte do fabricante",
        "DEFEITO": "Falha de hardware com orcamento acima de 70% do valor residual",
        "FURTO_ROUBO": "Boletim de ocorrencia registrado e comunicado ao seguro",
        "FIM_VIDA_UTIL": "Vida util contabil esgotada e desempenho insuficiente",
        "OUTRO": "Equipamento devolvido ao fornecedor por erro de especificacao na compra",
    }

    baixas = []
    for i in idx_baixados:
        a = ativos[i]
        aq = date.fromisoformat(a.data_aquisicao)
        vu = vida_util[a.categoria]
        motivo = rng.choices(motivos, weights=[30, 30, 8, 27, 5])[0]
        data_baixa = datas_baixa[i]

        meses = (data_baixa.year - aq.year) * 12 + (data_baixa.month - aq.month)
        meses = max(0, min(meses, vu))
        valor = float(a.valor_compra)
        residual = max(round(valor - (valor / vu) * meses, 2), 0.0)

        baixas.append([
            a.numero_serie or a.chave_licenca, motivo,
            justificativas[motivo] if motivo == "OUTRO" else justificativas[motivo],
            data_baixa.isoformat(), rng.choice(destinos), f"{residual:.2f}",
        ])

    escrever_csv(
        saida / "baixas.csv",
        ["identificador_ativo", "motivo", "justificativa", "data_baixa", "destinacao", "valor_residual_baixa"],
        baixas,
    )

    # ---- 11. riscos ----------------------------------------------------
    riscos = [
        ("Licencas em uso acima do quantitativo contratado", "LEGAL", 4, 5,
         "MITIGAR", "Auditoria de fabricante pode resultar em autuacao retroativa",
         "Alerta CP-02 disparado no painel de compliance"),
        ("Inventario desatualizado por falta de registro de transferencias", "OPERACIONAL", 4, 4,
         "MITIGAR", "Equipamentos sem responsavel identificavel em caso de extravio",
         "Cobertura de responsaveis abaixo de 95%"),
        ("Divergencia entre valor residual do sistema e o registro contabil", "FINANCEIRO", 3, 4,
         "MITIGAR", "Balanco com ativo imobilizado incorreto",
         "Divergencia superior a 1% na conciliacao mensal"),
        ("Parque com mais de 30% dos ativos totalmente depreciados", "FINANCEIRO", 4, 3,
         "MITIGAR", "Necessidade de investimento nao planejado em substituicao",
         "Indicador de percentual depreciado acima de 30%"),
        ("Ausencia de registro de destinacao no descarte de equipamentos", "LEGAL", 3, 4,
         "MITIGAR", "Nao conformidade com a Politica Nacional de Residuos Solidos",
         "Alerta CP-07 com baixas sem destinacao"),
        ("Licenca critica com renovacao nao negociada ate o vencimento", "OPERACIONAL", 3, 5,
         "MITIGAR", "Interrupcao do uso de software essencial a operacao",
         "Alerta CP-03 sem tratativa registrada em 15 dias"),
        ("Chaves de licenca acessiveis a perfis sem necessidade", "SEGURANCA", 2, 4,
         "MITIGAR", "Vazamento de ativo de licenciamento",
         "Acesso de perfil nao ADMIN a campo de chave completa"),
        ("Colaborador desligado sem devolucao de equipamento registrada", "OPERACIONAL", 4, 3,
         "MITIGAR", "Perda patrimonial sem responsavel identificado",
         "Vinculo aberto com responsavel inativo"),
        ("Equipamento em manutencao por periodo superior a 90 dias", "OPERACIONAL", 3, 2,
         "ACEITAR", "Indisponibilidade prolongada e custo de equipamento reserva",
         "Alerta CP-06"),
        ("Dependencia de fornecedor unico para categoria critica", "OPERACIONAL", 2, 4,
         "MITIGAR", "Exposicao a reajuste e a prazo de entrega",
         "Mais de 60% dos ativos de uma categoria em um unico fornecedor"),
        ("Ausencia de backup do inventario em caso de falha do banco", "CONTINUIDADE", 2, 5,
         "MITIGAR", "Perda do historico de responsabilidade e de auditoria",
         "Rotina de backup sem execucao ha mais de 7 dias"),
        ("Importacao em lote com dados incorretos aceita sem revisao", "OPERACIONAL", 3, 3,
         "MITIGAR", "Inventario contaminado por registros invalidos",
         "Lote com taxa de rejeicao acima de 15%"),
        ("Subutilizacao de licencas contratadas", "FINANCEIRO", 4, 2,
         "MITIGAR", "Custo recorrente sem contrapartida de uso",
         "Uso abaixo de 50% do contratado por mais de 6 meses"),
        ("Acesso ao sistema sem revisao periodica de perfis", "SEGURANCA", 3, 3,
         "MITIGAR", "Privilegio excessivo mantido apos mudanca de funcao",
         "Revisao de acessos com mais de 180 dias"),
        ("Equipamento fora da politica de uso institucional", "LEGAL", 2, 3,
         "MITIGAR", "Uso de ativo corporativo para finalidade nao autorizada",
         "Alerta CP-09 ou apontamento em auditoria"),
    ]
    escrever_csv(
        saida / "riscos.csv",
        ["titulo", "categoria", "probabilidade", "impacto", "resposta", "descricao", "gatilho"],
        [[t, c, p, im, r, d, g] for t, c, p, im, r, d, g in riscos],
    )

    # ---- 12. custos_cenarios -------------------------------------------
    cenarios = [
        ["MANTER", "Prorrogar o uso do parque atual por mais 24 meses",
         "0.00", "198400.00", "Manutencao corretiva crescente e sem garantia", "16"],
        ["RENOVAR", "Substituir 120 equipamentos fora da vida util por equivalentes novos",
         "684000.00", "92000.00", "CAPEX concentrado, garantia de 36 meses", "9"],
        ["MIGRAR_ASSINATURA", "Substituir aquisicao por locacao corporativa com suporte incluso",
         "48000.00", "247000.00", "Sem CAPEX, custo recorrente maior no horizonte", "12"],
    ]
    escrever_csv(
        saida / "custos_cenarios.csv",
        ["cenario", "descricao", "capex", "opex_anual", "premissas", "score_risco"],
        cenarios,
    )

    # ---- Resumo dos desvios --------------------------------------------
    vencidas = sum(1 for l in licencas if date.fromisoformat(l["data_expiracao"]) < hoje)
    vencendo = sum(1 for l in licencas
                   if 0 <= (date.fromisoformat(l["data_expiracao"]) - hoje).days <= 30)
    excedentes = sum(1 for l in licencas if l["_em_uso"] > l["quantidade_contratada"])
    subutil = sum(1 for l in licencas if l["_em_uso"] <= l["quantidade_contratada"] * 0.5)
    depreciados = sum(
        1 for a in ativos
        if a.status == "ATIVO"
        and (hoje.year - date.fromisoformat(a.data_aquisicao).year) * 12
            + (hoje.month - date.fromisoformat(a.data_aquisicao).month) >= vida_util[a.categoria]
    )

    print("\n  Desvios plantados (devem aparecer no painel de compliance):")
    print(f"    CP-01  licencas vencidas .................. {vencidas}")
    print(f"    CP-02  licencas acima do contratado ....... {excedentes}")
    print(f"    CP-03  licencas vencendo em <= 30 dias .... {vencendo}")
    print(f"    CP-04  ativos sem responsavel ............. {len(idx_sem_responsavel)}")
    print(f"    CP-05  totalmente depreciados em operacao . {depreciados}")
    print(f"    CP-06  em manutencao (4 com > 90 dias) .... {len(idx_manutencao)}")
    print(f"    CP-08  sem movimentacao ha > 12 meses ..... {len(idx_sem_movimento)}")
    print(f"    Baixo  licencas subutilizadas ............. {subutil}")
    print(f"\n  Total de ativos: {len(ativos)}  |  baixados: {len(baixas)}"
          f"  |  vinculos de responsavel: {len(transferencias)}"
          f"  |  vinculos de licenca: {len(vinculos_lic)}\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Gera os datasets de demonstracao do ITAM")
    p.add_argument("--saida", default="datasets", help="diretorio de saida")
    p.add_argument("--semente", type=int, default=SEMENTE_PADRAO, help="semente do gerador")
    args = p.parse_args()
    gerar(Path(args.saida), args.semente)


if __name__ == "__main__":
    main()

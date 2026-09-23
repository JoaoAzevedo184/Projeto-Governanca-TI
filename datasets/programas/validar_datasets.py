#!/usr/bin/env python3
"""
Validador dos datasets de demonstração — ITAM

Verifica a coerência referencial exigida em docs/MODELO_DE_DADOS.md, seção 8.
Sai com código 1 se encontrar qualquer inconsistência, o que permite usar o
script no pipeline de CI.

Uso:
    python validar_datasets.py [--datasets datasets/]
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HOJE = date(2026, 9, 20)


def ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d(valor: str) -> date | None:
    try:
        return date.fromisoformat(valor)
    except (ValueError, TypeError):
        return None


def validar(base: Path) -> int:
    erros: list[str] = []
    avisos: list[str] = []

    categorias = ler(base / "categorias.csv")
    fornecedores = ler(base / "fornecedores.csv")
    setores = ler(base / "setores.csv")
    responsaveis = ler(base / "responsaveis.csv")
    inventario = ler(base / "inventario.csv")
    transferencias = ler(base / "transferencias.csv")
    licencas = ler(base / "licencas.csv")
    lic_vinculos = ler(base / "licenca_vinculos.csv")
    baixas = ler(base / "baixas.csv")

    nomes_categoria = {c["nome"] for c in categorias}
    nomes_fornecedor = {f["razao_social"] for f in fornecedores}
    nomes_setor = {s["nome"] for s in setores}
    matriculas = {r["matricula"] for r in responsaveis}
    vida_util = {c["nome"]: int(c["vida_util_meses"]) for c in categorias}

    # ---- inventario ----------------------------------------------------
    series = [a["numero_serie"] for a in inventario if a["numero_serie"]]
    duplicadas = [s for s, n in Counter(series).items() if n > 1]
    if duplicadas:
        erros.append(f"BR-001: numeros de serie duplicados no inventario: {duplicadas[:5]}")

    ativos_por_id: dict[str, dict] = {}
    for a in inventario:
        ident = a["numero_serie"] or a["chave_licenca"]
        ativos_por_id[ident] = a

        if a["categoria"] not in nomes_categoria:
            erros.append(f"categoria inexistente em inventario: {a['categoria']}")
        if a["fornecedor"] not in nomes_fornecedor:
            erros.append(f"fornecedor inexistente em inventario: {a['fornecedor']}")
        if a["tipo"] == "HARDWARE" and not a["numero_serie"]:
            erros.append(f"BR-002: hardware sem numero de serie: {a['nome']}")
        if a["tipo"] == "SOFTWARE" and not a["chave_licenca"]:
            erros.append(f"BR-002: software sem chave de licenca: {a['nome']}")
        aq = d(a["data_aquisicao"])
        if aq is None:
            erros.append(f"data de aquisicao invalida: {a['data_aquisicao']}")
        elif aq > HOJE:
            erros.append(f"BR-003: data de aquisicao futura: {ident} ({aq})")
        if float(a["valor_compra"]) <= 0:
            erros.append(f"BR-004: valor de compra nao positivo: {ident}")

    # ---- responsaveis --------------------------------------------------
    for r in responsaveis:
        if r["setor"] not in nomes_setor:
            erros.append(f"setor inexistente em responsaveis: {r['setor']}")

    # ---- transferencias ------------------------------------------------
    por_ativo: dict[str, list[dict]] = defaultdict(list)
    for t in transferencias:
        ident = t["identificador_ativo"]
        if ident not in ativos_por_id:
            erros.append(f"transferencia referencia ativo inexistente: {ident}")
            continue
        if t["matricula_responsavel"] not in matriculas:
            erros.append(f"transferencia com matricula inexistente: {t['matricula_responsavel']}")
        if t["setor"] not in nomes_setor:
            erros.append(f"transferencia com setor inexistente: {t['setor']}")
        por_ativo[ident].append(t)

    for ident, lista in por_ativo.items():
        ativo = ativos_por_id[ident]
        aquisicao = d(ativo["data_aquisicao"])
        lista.sort(key=lambda x: x["data_inicio"])

        abertos = [t for t in lista if not t["data_fim"]]
        if len(abertos) > 1:
            erros.append(f"BR-007: {ident} tem {len(abertos)} vinculos abertos")
        if ativo["status"] == "BAIXADO" and abertos:
            erros.append(f"BR-012: ativo baixado com vinculo aberto: {ident}")

        anterior_fim: date | None = None
        for t in lista:
            inicio = d(t["data_inicio"])
            fim = d(t["data_fim"]) if t["data_fim"] else None
            if inicio is None:
                erros.append(f"data_inicio invalida em {ident}")
                continue
            if aquisicao and inicio < aquisicao:
                erros.append(f"BR-010: vinculo antes da aquisicao em {ident} "
                             f"({inicio} < {aquisicao})")
            if fim and fim < inicio:
                erros.append(f"BR-008: data_fim antes de data_inicio em {ident}")
            if anterior_fim and inicio < anterior_fim:
                erros.append(f"BR-008: periodos sobrepostos em {ident} "
                             f"(inicio {inicio} < fim anterior {anterior_fim})")
            anterior_fim = fim

    # ---- baixas --------------------------------------------------------
    identificadores_baixa = [b["identificador_ativo"] for b in baixas]
    repetidas = [i for i, n in Counter(identificadores_baixa).items() if n > 1]
    if repetidas:
        erros.append(f"BR-024: ativo com mais de uma baixa: {repetidas}")

    for b in baixas:
        ident = b["identificador_ativo"]
        ativo = ativos_por_id.get(ident)
        if ativo is None:
            erros.append(f"baixa referencia ativo inexistente: {ident}")
            continue
        if ativo["status"] != "BAIXADO":
            erros.append(f"ativo em baixas.csv com status {ativo['status']}: {ident}")
        data_baixa = d(b["data_baixa"])
        aquisicao = d(ativo["data_aquisicao"])
        if data_baixa is None:
            erros.append(f"data de baixa invalida: {ident}")
            continue
        if data_baixa > HOJE:
            erros.append(f"BR-022: data de baixa futura: {ident}")
        if aquisicao and data_baixa < aquisicao:
            erros.append(f"BR-022: baixa antes da aquisicao: {ident}")
        if b["motivo"] == "OUTRO" and len(b["justificativa"]) < 10:
            erros.append(f"BR-023: motivo OUTRO sem justificativa: {ident}")
        if not b["destinacao"]:
            erros.append(f"BR-026: baixa sem destinacao: {ident}")
        if float(b["valor_residual_baixa"]) < 0:
            erros.append(f"BR-014: valor residual negativo: {ident}")

        # o ultimo vinculo deve encerrar ate a data da baixa
        for t in por_ativo.get(ident, []):
            fim = d(t["data_fim"]) if t["data_fim"] else None
            if fim and fim > data_baixa:
                erros.append(f"vinculo encerrado apos a baixa em {ident}")

    # ---- licencas ------------------------------------------------------
    licencas_por_nome = {l["software"]: l for l in licencas}
    for l in licencas:
        aq, exp = d(l["data_aquisicao"]), d(l["data_expiracao"])
        if aq is None or exp is None:
            erros.append(f"datas invalidas na licenca {l['software']}")
            continue
        if exp <= aq:
            erros.append(f"BR-019: expiracao <= aquisicao em {l['software']}")
        if int(l["quantidade_contratada"]) < 1:
            erros.append(f"quantidade contratada invalida em {l['software']}")
        if l["fornecedor"] not in nomes_fornecedor:
            erros.append(f"fornecedor inexistente na licenca {l['software']}")

    uso = Counter(v["software"] for v in lic_vinculos if v["ativo_vinculo"] == "true")
    for v in lic_vinculos:
        if v["software"] not in licencas_por_nome:
            erros.append(f"vinculo de licenca inexistente: {v['software']}")
        alvo = ativos_por_id.get(v["numero_serie_ativo"])
        if alvo is None:
            erros.append(f"vinculo de licenca em ativo inexistente: {v['numero_serie_ativo']}")
        elif alvo["status"] == "BAIXADO":
            erros.append(f"licenca vinculada a ativo baixado: {v['numero_serie_ativo']}")

    # ---- desvios plantados (avisos, nao erros) -------------------------
    vencidas = [l["software"] for l in licencas if d(l["data_expiracao"]) < HOJE]
    vencendo = [l["software"] for l in licencas
                if 0 <= (d(l["data_expiracao"]) - HOJE).days <= 30]
    excedentes = [s for s, n in uso.items()
                  if n > int(licencas_por_nome[s]["quantidade_contratada"])]
    sem_resp = [i for i, a in ativos_por_id.items()
                if a["status"] == "ATIVO"
                and not any(not t["data_fim"] for t in por_ativo.get(i, []))]

    print("\nDesvios detectados no dataset")
    print(f"  CP-01  licencas vencidas ................. {len(vencidas)}  {vencidas}")
    print(f"  CP-02  acima do contratado ............... {len(excedentes)}  {excedentes}")
    print(f"  CP-03  vencendo em ate 30 dias ........... {len(vencendo)}")
    print(f"  CP-04  ativos sem responsavel ............ {len(sem_resp)}")

    if not vencidas:
        avisos.append("nenhuma licenca vencida — o alerta CP-01 nao sera demonstravel")
    if not excedentes:
        avisos.append("nenhuma licenca acima do contratado — CP-02 nao sera demonstravel")
    if not sem_resp:
        avisos.append("nenhum ativo sem responsavel — CP-04 nao sera demonstravel")

    # ---- inventario_com_erros ------------------------------------------
    com_erros = ler(base / "inventario_com_erros.csv")
    invalidas = 0
    vistos: set[str] = set()
    for linha in com_erros:
        problema = False
        aq = d(linha["data_aquisicao"])
        if aq is None or aq > HOJE:
            problema = True
        if linha["tipo"] not in {"HARDWARE", "SOFTWARE"}:
            problema = True
        if linha["categoria"] not in nomes_categoria:
            problema = True
        if linha["tipo"] == "HARDWARE" and not linha["numero_serie"]:
            problema = True
        try:
            if float(linha["valor_compra"]) <= 0:
                problema = True
        except ValueError:
            problema = True
        ns = linha["numero_serie"]
        if ns and (ns in vistos or ns in ativos_por_id):
            problema = True
        if ns:
            vistos.add(ns)
        invalidas += problema

    print(f"\ninventario_com_erros.csv: {len(com_erros)} linhas, {invalidas} invalidas")
    if invalidas < 8:
        avisos.append(f"esperadas 8 linhas invalidas, encontradas {invalidas}")

    # ---- resultado -----------------------------------------------------
    print()
    if avisos:
        print("AVISOS")
        for a in avisos:
            print(f"  ! {a}")
        print()
    if erros:
        print(f"FALHOU — {len(erros)} inconsistencia(s):")
        for e in erros[:40]:
            print(f"  x {e}")
        if len(erros) > 40:
            print(f"  ... e mais {len(erros) - 40}")
        return 1

    print("OK — dataset coerente: nenhuma violacao de regra de negocio encontrada.")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Valida os datasets de demonstracao do ITAM")
    p.add_argument("--datasets", default="datasets", help="diretorio dos CSV")
    args = p.parse_args()
    sys.exit(validar(Path(args.datasets)))


if __name__ == "__main__":
    main()

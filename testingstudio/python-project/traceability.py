"""Derivação estruturada de CTs e RTM bidirecional, sem dependências externas.

Rastrear um requisito prova um vínculo no planejamento, não sua execução ou correção.
"""
from __future__ import annotations

import csv
import copy
import hashlib
import io
import json
import re

FLOW_TYPES = {"principal": "Principal", "alternativo": "Alternativo", "excecao": "Exceção"}
STATUSES = ("Não executado", "Aprovado", "Reprovado", "Bloqueado")
MAX_JSON = 180000

LIBRARY_SCENARIO = {
    "title": "Biblioteca universitária",
    "source": "Aula_Teste_I_14102026.pdf · páginas 3–6",
    "assumptions": [
        "CT01, CT02 e CT03 seguem o rastreio do slide 5; CT04 e CT05 são extensões propostas para os fluxos alternativo e principal.",
        "O PDF não define formato/validação de ISBN, duplicidade, categoria no cadastro, prazo de devolução, arredondamento de dias, indisponibilidade de livros ou falha do serviço de e-mail. Esses pontos exigem refinamento.",
        "Na multa, os dados usam dias inteiros de atraso já determinados: 0, 1 e 2. Não se presume como datas e atrasos parciais são convertidos em dias.",
        "O comprovante por e-mail é resultado esperado de uma integração a testar. Este laboratório não envia mensagens nem implementa um sistema de biblioteca.",
    ],
    "requirements": [
        {"id": "REQ01", "description": "Cadastro de novos livros informando ISBN, Título e Autor."},
        {"id": "REQ02", "description": "Validação de pendências financeiras do usuário antes de realizar o empréstimo."},
        {"id": "REQ03", "description": "Cálculo automático da multa de R$ 2,00 por dia de atraso na devolução."},
        {"id": "REQ04", "description": "Busca de livros por título ou categoria."},
        {"id": "REQ05", "description": "Emissão de comprovante digital de reserva por e-mail."},
    ],
    "use_cases": [
        {"id": "UC01", "title": "Cadastrar, localizar e reservar um livro", "actor": "Bibliotecário e usuário",
         "preconditions": ["Acesso ao cadastro e ao catálogo disponível.", "Usuário com e-mail de teste e livro disponível para reserva."],
         "flows": [
             {"id": "FP01", "type": "principal", "title": "Cadastro, busca por título e comprovante", "test_id": "CT01",
              "requirements": ["REQ01", "REQ04", "REQ05"],
              "steps": ["Cadastrar livro com ISBN, título e autor de teste.", "Buscar o título cadastrado.", "Selecionar o livro e confirmar sua reserva.", "Conferir o comprovante na caixa de e-mail de teste."],
              "expected": "Livro cadastrado com os dados informados, encontrado pelo título e reservado; comprovante digital da reserva recebido no e-mail do usuário.",
              "data": [{"ISBN": "9788535902778", "título": "Dom Casmurro", "autor": "Machado de Assis", "e-mail": "leitor@example.com"}]},
             {"id": "FA01", "type": "alternativo", "title": "Localizar livro por categoria", "test_id": "CT04",
              "requirements": ["REQ04"], "steps": ["Preparar catálogo com um livro associado a Literatura e outro a Computação.", "Buscar pela categoria Literatura."],
              "expected": "A busca por categoria retorna o livro de Literatura e não inclui o de Computação.",
              "data": [{"categoria": "Literatura"}], "note": "Extensão proposta; a preparação das categorias depende de regra ainda não detalhada no PDF."},
         ]},
        {"id": "UC02", "title": "Solicitar empréstimo", "actor": "Usuário e atendente",
         "preconditions": ["Usuário identificado e livro disponível para empréstimo."],
         "flows": [
             {"id": "FE01", "type": "excecao", "title": "Bloquear usuário com dívida", "test_id": "CT02",
              "requirements": ["REQ02"], "steps": ["Preparar usuário com pendência financeira.", "Solicitar o empréstimo do livro.", "Conferir a negativa e a ausência de registro do empréstimo."],
              "expected": "O sistema valida a pendência antes da operação e bloqueia o empréstimo; nenhum empréstimo é registrado.",
              "data": [{"pendência financeira": "R$ 10,00"}]},
             {"id": "FP02", "type": "principal", "title": "Validar usuário sem pendências", "test_id": "CT05",
              "requirements": ["REQ02"], "steps": ["Preparar usuário sem pendências financeiras e com os demais critérios de empréstimo atendidos.", "Solicitar o empréstimo.", "Conferir a validação financeira anterior ao registro."],
              "expected": "A validação financeira é realizada e permite prosseguir, respeitadas as demais regras do empréstimo.",
              "data": [{"pendência financeira": "R$ 0,00"}], "note": "Extensão proposta para complementar o bloqueio de CT02."},
         ]},
        {"id": "UC03", "title": "Devolver livro e calcular multa", "actor": "Usuário e atendente",
         "preconditions": ["Empréstimo existente; dias inteiros de atraso conhecidos."],
         "flows": [
             {"id": "FA02", "type": "alternativo", "title": "Fronteira entre devolução no prazo e com atraso", "test_id": "CT03",
              "requirements": ["REQ03"], "steps": ["Preparar uma devolução para cada quantidade de dias de atraso da tabela.", "Registrar a devolução e consultar a multa calculada automaticamente.", "Comparar cada valor com o resultado esperado de R$ 2,00 por dia."],
              "expected": "No prazo: R$ 0,00; 1 dia de atraso: R$ 2,00; 2 dias: R$ 4,00. Não há cobrança positiva quando os dias de atraso são zero.",
              "data": [{"dias de atraso": 0, "multa esperada": "R$ 0,00"}, {"dias de atraso": 1, "multa esperada": "R$ 2,00"}, {"dias de atraso": 2, "multa esperada": "R$ 4,00"}]},
         ]},
    ],
}


class TraceabilityError(ValueError):
    pass


def _text(value, label, limit=6000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise TraceabilityError(f"{label}: informe texto não vazio de até {limit} caracteres.")
    return value.strip()


def _identifier(value, label):
    value = _text(value, label, 40)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value):
        raise TraceabilityError(f"{label}: use letras, números, hífen ou sublinhado; comece por letra.")
    return value


def _list(value, label, maximum=100, empty=True):
    if not isinstance(value, list) or len(value) > maximum or (not empty and not value):
        raise TraceabilityError(f"{label}: use uma lista com {'1' if not empty else '0'} a {maximum} itens.")
    return value


def _texts(value, label, maximum=40, empty=True):
    return [_text(v, label) for v in _list(value, label, maximum, empty)]


def validate_scenario(scenario):
    if not isinstance(scenario, dict):
        raise TraceabilityError("O cenário deve ser um objeto JSON.")
    if len(json.dumps(scenario, ensure_ascii=False, allow_nan=False)) > MAX_JSON:
        raise TraceabilityError("O cenário excede o limite de 180.000 caracteres.")
    result = {"title": _text(scenario.get("title"), "Título", 200),
              "source": str(scenario.get("source", "Cenário do usuário"))[:500],
              "assumptions": _texts(scenario.get("assumptions", []), "Premissas"),
              "requirements": [], "use_cases": []}
    seen_req, seen_uc, seen_flow, seen_test = set(), set(), set(), set()
    for req in _list(scenario.get("requirements"), "Requisitos", 100, False):
        if not isinstance(req, dict):
            raise TraceabilityError("Cada requisito deve ser um objeto.")
        rid = _identifier(req.get("id"), "ID do requisito")
        if rid in seen_req:
            raise TraceabilityError(f"Requisito duplicado: {rid}.")
        seen_req.add(rid)
        result["requirements"].append({"id": rid, "description": _text(req.get("description"), rid)})
    for uc in _list(scenario.get("use_cases"), "Casos de uso", 40):
        if not isinstance(uc, dict):
            raise TraceabilityError("Cada caso de uso deve ser um objeto.")
        uid = _identifier(uc.get("id"), "ID do caso de uso")
        if uid in seen_uc:
            raise TraceabilityError(f"Caso de uso duplicado: {uid}.")
        seen_uc.add(uid)
        clean = {"id": uid, "title": _text(uc.get("title"), uid, 300),
                 "actor": _text(uc.get("actor"), "Ator", 300),
                 "preconditions": _texts(uc.get("preconditions", []), "Pré-condições"), "flows": []}
        for flow in _list(uc.get("flows"), "Fluxos", 40, False):
            if not isinstance(flow, dict):
                raise TraceabilityError("Cada fluxo deve ser um objeto.")
            fid = _identifier(flow.get("id"), "ID do fluxo")
            if fid in seen_flow:
                raise TraceabilityError(f"Fluxo duplicado: {fid}.")
            seen_flow.add(fid)
            kind = flow.get("type")
            if kind not in FLOW_TYPES:
                raise TraceabilityError(f"{fid}: tipo deve ser principal, alternativo ou excecao.")
            tids = flow.get("test_id")
            if tids is not None:
                tids = _identifier(tids, "ID do CT")
                if tids in seen_test:
                    raise TraceabilityError(f"ID de CT duplicado: {tids}.")
                seen_test.add(tids)
            reqs = _texts(flow.get("requirements", []), "Vínculos de requisitos", 100)
            if len(reqs) != len(set(reqs)) or any(r not in seen_req for r in reqs):
                raise TraceabilityError(f"{fid}: vínculo de requisito duplicado ou inexistente.")
            data = _list(flow.get("data", []), "Dados de teste", 30)
            if any(not isinstance(row, dict) or len(row) > 20 or any(not isinstance(k,str) or len(k)>200 or not isinstance(v,(str,int,float,bool,type(None))) for k,v in row.items()) for row in data):
                raise TraceabilityError(f"{fid}: dados devem ser objetos simples, com até 20 campos por linha.")
            clean["flows"].append({"id": fid, "type": kind, "title": _text(flow.get("title"), fid, 300),
                                  "test_id": tids, "requirements": reqs,
                                  "steps": _texts(flow.get("steps"), "Passos", 40, False),
                                  "expected": _text(flow.get("expected"), "Resultado esperado"),
                                  "data": copy.deepcopy(data), "note": str(flow.get("note", ""))[:3000]})
        result["use_cases"].append(clean)
    if sum(len(u["flows"]) for u in result["use_cases"]) > 150:
        raise TraceabilityError("O limite é de 150 fluxos por cenário.")
    return result


def derive_cases(scenario):
    """Um CT por fluxo explícito. IDs reservados preservam o mapeamento dos slides."""
    reserved = {f["test_id"] for u in scenario["use_cases"] for f in u["flows"] if f["test_id"]}
    cases, index = [], 1
    for uc in scenario["use_cases"]:
        for flow in uc["flows"]:
            tid = flow["test_id"]
            if tid is None:
                while f"CT{index:02d}" in reserved:
                    index += 1
                tid = f"CT{index:02d}"; reserved.add(tid); index += 1
            cases.append({"id": tid, "title": flow["title"], "use_case": uc["id"], "flow": flow["id"],
                          "flow_type": FLOW_TYPES[flow["type"]], "actor": uc["actor"],
                          "preconditions": uc["preconditions"][:], "requirements": flow["requirements"][:],
                          "steps": flow["steps"][:], "expected": flow["expected"], "data": copy.deepcopy(flow["data"]),
                          "note": flow["note"], "status": "Não executado", "evidence": ""})
    return sorted(cases, key=lambda c: c["id"])


def analyze_traceability(scenario, executions=None):
    scenario = validate_scenario(scenario)
    cases = derive_cases(scenario)
    executions = {} if executions is None else executions
    if not isinstance(executions, dict) or any(k not in {c['id'] for c in cases} for k in executions):
        raise TraceabilityError("Execuções: informe um objeto indexado por IDs de CT existentes.")
    for case in cases:
        execution = executions.get(case["id"], {})
        if not isinstance(execution, dict):
            raise TraceabilityError(f"{case['id']}: execução inválida.")
        status = execution.get("status", "Não executado")
        evidence = execution.get("evidence", "")
        if status not in STATUSES or not isinstance(evidence, str) or len(evidence) > 6000:
            raise TraceabilityError(f"{case['id']}: situação ou evidência inválida.")
        if status != "Não executado" and not evidence.strip():
            raise TraceabilityError(f"{case['id']}: registre uma evidência/justificativa para alterar a situação.")
        case.update(status=status, evidence=evidence.strip())
    req_rows = []
    for req in scenario["requirements"]:
        linked = [c for c in cases if req["id"] in c["requirements"]]
        req_rows.append({**req, "tests": [c["id"] for c in linked],
                         "use_cases": sorted({c["use_case"] for c in linked}),
                         "covered": bool(linked), "approved": bool(linked) and all(c["status"] == "Aprovado" for c in linked)})
    uncovered = [r["id"] for r in req_rows if not r["covered"]]
    orphan = [c["id"] for c in cases if not c["requirements"]]
    executed = sum(c["status"] != "Não executado" and c["status"] != "Bloqueado" for c in cases)
    canonical = json.dumps(scenario, ensure_ascii=False, sort_keys=True)
    result = {"scenario": scenario, "scenario_hash": hashlib.sha256(canonical.encode()).hexdigest(),
              "cases": cases, "requirements": req_rows, "uncovered_requirements": uncovered, "orphan_tests": orphan,
              "coverage": round(100*(len(req_rows)-len(uncovered))/len(req_rows), 1),
              "execution": {"total": len(cases), "executed": executed,
                            **{status: sum(c["status"] == status for c in cases) for status in STATUSES}},
              "flow_counts": {kind: sum(c["flow_type"] == label for c in cases) for kind,label in FLOW_TYPES.items()},
              "method": "Cobertura RTM mede requisitos com pelo menos um CT vinculado. Não comprova completude dos cenários, execução nem correção do produto. A derivação usa os fluxos estruturados informados; não interpreta automaticamente texto livre."}
    result["report"] = traceability_markdown(result)
    result["matrix_csv"] = matrix_csv(result)
    return result


def matrix_csv(result):
    out = io.StringIO(newline="")
    raw_writer = csv.writer(out, delimiter=";")
    class SafeWriter:
        def writerow(self, row):
            raw_writer.writerow(["'" + str(v) if str(v).startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in row])
    writer = SafeWriter()
    writer.writerow(["Requisito", "Descrição", "Casos de uso"] + [c["id"] for c in result["cases"]] + ["Planejado", "Todos os CTs aprovados"])
    for req in result["requirements"]:
        writer.writerow([req["id"], req["description"], ", ".join(req["use_cases"])] +
                        ["X" if req["id"] in c["requirements"] else "" for c in result["cases"]] +
                        ["Sim" if req["covered"] else "Não", "Sim" if req["approved"] else "Não"])
    return "\ufeff" + out.getvalue()


def _md(value):
    return str(value).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")


def traceability_markdown(result):
    s = result["scenario"]
    lines = [f"# TestingStudio · Requisitos e RTM · {_md(s['title'])}", "", f"Fonte: {_md(s['source'])}",
             f"Cenário SHA-256: {result['scenario_hash']}", "", "## Cobertura de planejamento", "",
             f"{result['coverage']}% dos requisitos possuem CT vinculado. {result['execution']['executed']}/{len(result['cases'])} CTs executados (registros manuais).", "", result["method"], "",
             "## Matriz bidirecional", "", "| Requisito | Descrição | Caso de uso | CTs |", "| --- | --- | --- | --- |"]
    for r in result["requirements"]:
        lines.append(f"| {_md(r['id'])} | {_md(r['description'])} | {', '.join(r['use_cases']) or '—'} | {', '.join(r['tests']) or 'SEM CT'} |")
    lines += ["", "Requisitos sem CT: " + (", ".join(result["uncovered_requirements"]) or "Nenhum"),
              "CTs sem requisito: " + (", ".join(result["orphan_tests"]) or "Nenhum"), "", "## Premissas e pontos de refinamento", ""]
    lines.extend("- " + _md(a) for a in s["assumptions"])
    for c in result["cases"]:
        lines += ["", f"## {_md(c['id'])} · {_md(c['title'])}",
                  f"Rastreio: {_md(c['use_case'])} / {_md(c['flow'])} ({c['flow_type']}) → {', '.join(c['requirements']) or 'SEM REQUISITO'}", "",
                  f"Ator: {_md(c['actor'])}", "", "Pré-condições:"]
        lines.extend("- " + _md(a) for a in c["preconditions"])
        lines += ["", "Passos:"] + [f"{i}. {_md(step)}" for i,step in enumerate(c["steps"], 1)]
        lines += ["", "Dados: " + _md(json.dumps(c["data"], ensure_ascii=False)), "", "Esperado: " + _md(c["expected"]),
                  "", "Situação: " + c["status"], "Evidência: " + (_md(c["evidence"]) or "Não informada.")]
        if c["note"]:
            lines.append("Nota: " + _md(c["note"]))
    return "\n".join(lines) + "\n"


def browser_traceability(payload_json):
    try:
        if not isinstance(payload_json,str) or len(payload_json) > MAX_JSON*2:
            raise TraceabilityError("Entrada RTM excede o limite didático.")
        payload = json.loads(payload_json)
        result = analyze_traceability(payload["scenario"], payload.get("executions"))
        return json.dumps({"ok": True, "result": result}, ensure_ascii=False, allow_nan=False)
    except (TraceabilityError, ValueError, TypeError, KeyError, RecursionError):
        import sys
        error = sys.exc_info()[1]
        return json.dumps({"ok": False, "error": str(error) or "Confira o JSON do cenário RTM."}, ensure_ascii=False)

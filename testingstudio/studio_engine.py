"""Motor educacional comum ao Streamlit e ao Python/WASM do GitHub Pages.

Analisa funções numéricas com atribuições, if/else e return. Nunca executa o
fonte recebido com eval/exec. O interpretador percorre somente ASTs validadas.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import html
import json
import re
from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from analysis import expected_value, test_cases

MAX_SOURCE = 24000
MAX_STATEMENTS = 90
MAX_MUTANTS = 60

CORRECTED_SAMPLE = '''def calcula_item(p1, p2, p3):
    if p1 is None:
        p1 = 0
    if p2 is None:
        p2 = 0
    if p3 is None:
        p3 = 0
    if p1 < 0 or p2 < 0 or p3 < 0:
        return -1
    resultado = (p1 * p2) + p3
    return resultado
'''


class AnalysisError(ValueError):
    pass


def fmt(value, precision=2):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return str(value)
    return f"{value:.{precision}f}".replace(".", ",")


def decimal_value(value):
    if value is None or value == "NULL":
        return None
    try:
        number = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        raise AnalysisError("O caso deve conter números ou null.") from None
    if not number.is_finite() or abs(number) > Decimal("10000000000"):
        raise AnalysisError("Número inválido ou fora do limite didático de 10 bilhões.")
    return number


def informix_to_python(source):
    match = re.search(r"(?is)\bFUNCTION\s+cad0001_calcula_valor\s*\(([^)]*)\)(.*?)\bEND\s+FUNCTION", source)
    if not match:
        raise AnalysisError("Não foi encontrada a função cad0001_calcula_valor no fonte Informix.")
    args = [x.strip() for x in match.group(1).split(",")]
    if not all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", a) for a in args):
        raise AnalysisError("Parâmetros Informix não reconhecidos.")
    body = match.group(2)
    cleaned = "\n".join(re.split(r"#|--", line)[0] for line in body.splitlines())
    cleaned = re.sub(r"(?i)\bTHEN\s+(?=LET\b|RETURN\b)", "THEN\n", cleaned)
    cleaned = re.sub(r"(?i)\s+ELSE\s+", "\nELSE\n", cleaned)
    cleaned = re.sub(r"(?i)\s+END\s+IF\b", "\nEND IF", cleaned)
    lines = [f"def cad0001_calcula_valor({', '.join(args)}):"]
    indent = 1
    declaring = False

    def expression(text, condition=False):
        text = re.sub(r"(?i)\bIS\s+NOT\s+NULL\b", "is not None", text)
        text = re.sub(r"(?i)\bIS\s+NULL\b", "is None", text)
        for old, new in [("OR", "or"), ("AND", "and"), ("NOT", "not"), ("TRUE", "True"), ("FALSE", "False")]:
            text = re.sub(rf"(?i)\b{old}\b", new, text)
        text = text.replace("<>", "!=")
        if condition:
            text = re.sub(r"(?<![<>=!])=(?!=)", "==", text)
        return text.strip()

    for raw in cleaned.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"(?i)^DEFINE\b", line):
            declaring = True
            continue
        if not re.match(r"(?i)^(IF\b|ELSE\b|END\s+IF\b|LET\b|RETURN\b)", line):
            if declaring and re.fullmatch(r"(?i)[\w\s,()]+", line):
                continue
            raise AnalysisError(f"Instrução Informix fora do subconjunto suportado: {line[:80]}")
        declaring = False
        if re.fullmatch(r"(?i)END\s+IF", line):
            indent -= 1
            if indent < 1:
                raise AnalysisError("END IF sem IF correspondente.")
            continue
        if re.fullmatch(r"(?i)ELSE", line):
            indent -= 1
            if indent < 1:
                raise AnalysisError("ELSE sem IF correspondente.")
            lines.append("    " * indent + "else:")
            indent += 1
            continue
        conditional = re.fullmatch(r"(?i)IF\s+(.+?)\s+THEN", line)
        if conditional:
            lines.append("    " * indent + "if " + expression(conditional.group(1), True) + ":")
            indent += 1
            continue
        assignment = re.fullmatch(r"(?i)LET\s+([A-Za-z]\w*)\s*=\s*(.+)", line)
        if assignment:
            lines.append("    " * indent + assignment.group(1) + " = " + expression(assignment.group(2)))
            continue
        returned = re.fullmatch(r"(?i)RETURN\s+(.+)", line)
        if returned:
            lines.append("    " * indent + "return " + expression(returned.group(1)))
            continue
        raise AnalysisError(f"Instrução Informix não reconhecida: {line[:80]}")
    if indent != 1:
        raise AnalysisError("IF não encerrado na função Informix.")
    return "\n".join(lines) + "\n"


def prepare(source):
    if not source.strip():
        raise AnalysisError("Cole uma unidade de código para analisar.")
    if len(source) > MAX_SOURCE:
        raise AnalysisError("O limite didático é de 24.000 caracteres.")
    is_informix = bool(re.search(r"(?i)\bFUNCTION\s+cad0001_calcula_valor", source))
    translated = informix_to_python(source) if is_informix else source
    try:
        tree = ast.parse(translated)
    except (SyntaxError, RecursionError) as exc:
        raise AnalysisError(f"Código inválido: {getattr(exc, 'msg', 'expressão muito profunda')}.") from None
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise AnalysisError("Use uma única função Python (def), sem imports, chamadas ou código externo.")
    fn = tree.body[0]
    if fn.decorator_list or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or fn.args.defaults:
        raise AnalysisError("Use parâmetros posicionais simples, sem decoradores ou valores padrão.")
    names = [a.arg for a in fn.args.posonlyargs + fn.args.args]
    if not 1 <= len(names) <= 6:
        raise AnalysisError("A função deve ter de 1 a 6 parâmetros numéricos.")
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant) and isinstance(fn.body[0].value.value, str):
        fn.body.pop(0)
    allowed = (ast.FunctionDef, ast.arguments, ast.arg, ast.Assign, ast.Name, ast.Store,
               ast.Load, ast.If, ast.Return, ast.Pass, ast.Constant, ast.BinOp,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.UnaryOp, ast.USub,
               ast.UAdd, ast.Not, ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
               ast.Eq, ast.NotEq, ast.Is, ast.IsNot, ast.BoolOp, ast.And, ast.Or)
    nodes = list(ast.walk(fn))
    predicate_booleans = {id(n) for statement in ast.walk(fn) if isinstance(statement, ast.If)
                          for n in ast.walk(statement.test) if isinstance(n, ast.BoolOp)}
    if len(nodes) > 1200:
        raise AnalysisError("Unidade de código grande demais para a análise didática.")
    statements = sum(isinstance(n, ast.stmt) for n in nodes)
    if statements > MAX_STATEMENTS:
        raise AnalysisError("O limite é de 90 instruções por função.")
    for index, node in enumerate(nodes):
        node._point = index
        if not isinstance(node, allowed):
            raise AnalysisError(f"Recurso não suportado: {type(node).__name__}. Use atribuições, if/else e return; loops, imports e chamadas não são executados.")
        if isinstance(node, ast.Name) and (node.id.startswith("_") or len(node.id) > 80):
            raise AnalysisError("Identificador não permitido.")
        if isinstance(node, ast.Assign) and (len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name)):
            raise AnalysisError("Use uma única variável no lado esquerdo da atribuição.")
        if isinstance(node, ast.Compare) and len(node.ops) != 1:
            raise AnalysisError("Separe comparações encadeadas usando and.")
        if isinstance(node, ast.BoolOp) and id(node) not in predicate_booleans:
            raise AnalysisError("Neste motor, and/or são aceitos nos predicados de if. Separe a lógica booleana de atribuições e retornos.")
        if isinstance(node, ast.Constant):
            if node.value is not None and not isinstance(node.value, (int, float, bool)):
                raise AnalysisError("Somente constantes numéricas, booleanas e None são aceitas.")
            if isinstance(node.value, (int, float)) and abs(node.value) > 10**12:
                raise AnalysisError("Constante numérica muito grande.")
    if not any(isinstance(n, ast.Return) for n in nodes):
        raise AnalysisError("A função precisa de ao menos um return.")
    return fn, translated, names, is_informix


def names_used(node):
    return sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)})


class FlowGraph:
    def __init__(self, fn, args):
        self.nodes = []
        self.edges = []
        self.exit = self.add("Saída", "exit", 0)
        first = self.block(fn.body, self.exit)
        self.entry = self.add("Entrada · " + ", ".join(args), "entry", 0, defs=args)
        self.connect(self.entry, first)
        # Instruções depois de um return incondicional não entram na métrica.
        reachable = set()
        pending = [self.entry]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(e["to"] for e in self.edges if e["from"] == current)
        self.nodes = [n for n in self.nodes if n["id"] in reachable]
        self.edges = [e for e in self.edges if e["from"] in reachable and e["to"] in reachable]

    def add(self, label, kind, line, defs=(), uses=()):
        identifier = f"N{len(self.nodes)}"
        self.nodes.append({"id": identifier, "label": label, "kind": kind, "line": line,
                           "defs": list(defs), "uses": list(uses)})
        return identifier

    def connect(self, start, end, branch=""):
        self.edges.append({"from": start, "to": end, "branch": branch})

    def condition(self, expr, true_target, false_target):
        if isinstance(expr, ast.BoolOp):
            current = false_target if isinstance(expr.op, ast.Or) else true_target
            for child in reversed(expr.values):
                if isinstance(expr.op, ast.Or):
                    current = self.condition(child, true_target, current)
                else:
                    current = self.condition(child, current, false_target)
            return current
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
            return self.condition(expr.operand, false_target, true_target)
        identifier = self.add(ast.unparse(expr), "decision", expr.lineno, uses=names_used(expr))
        expr._cfg = identifier
        self.connect(identifier, true_target, "V")
        self.connect(identifier, false_target, "F")
        return identifier

    def block(self, statements, next_node):
        current = next_node
        for statement in reversed(statements):
            if isinstance(statement, ast.If):
                yes = self.block(statement.body, current)
                no = self.block(statement.orelse, current)
                current = self.condition(statement.test, yes, no)
            else:
                defs = [statement.targets[0].id] if isinstance(statement, ast.Assign) else []
                value = getattr(statement, "value", None)
                identifier = self.add(ast.unparse(statement), "return" if isinstance(statement, ast.Return) else "statement",
                                      statement.lineno, defs=defs, uses=names_used(value) if value else [])
                statement._cfg = identifier
                self.connect(identifier, self.exit if isinstance(statement, ast.Return) else current)
                current = identifier
        return current

    def result(self):
        n, e = len(self.nodes), len(self.edges)
        decisions = sum(node["kind"] == "decision" for node in self.nodes)
        vg = e - n + 2
        paths, stack = [], [(self.entry, [self.entry])]
        truncated = False
        while stack:
            current, path = stack.pop()
            if current == self.exit:
                if len(paths) < 128:
                    paths.append(path)
                else:
                    truncated = True
                    break
            else:
                stack.extend((edge["to"], path + [edge["to"]]) for edge in self.edges if edge["from"] == current)
        return {"nodes": self.nodes, "edges": self.edges, "N": n, "E": e, "P": 1,
                "vg": vg, "decisions": decisions, "predicate_check": decisions + 1,
                "formula": f"V(G) = E − N + 2P = {e} − {n} + 2 × 1 = {vg}",
                "paths": paths, "paths_truncated": truncated,
                "convention": "Grafo conectado, entrada/saída únicas; and/or decompostos por curto-circuito. Caminhos listados são estruturais, sem prova de viabilidade."}


class SafeInterpreter:
    def __init__(self, fn, args, graph=None):
        self.fn, self.args, self.graph = fn, args, graph

    def run(self, values):
        self.env = dict(zip(self.args, values))
        self.definition = {name: self.graph.entry if self.graph else "entrada" for name in self.args}
        self.pairs = set()
        self.path = [self.graph.entry] if self.graph else []
        self.steps = 0
        self.current = "entrada"
        result, returned = self.block(self.fn.body)
        if self.graph:
            self.path.append(self.graph.exit)
        return result if returned else None, self.path, self.pairs

    def tick(self):
        self.steps += 1
        if self.steps > 2000:
            raise AnalysisError("Limite de passos atingido.")

    def expr(self, node):
        self.tick()
        if isinstance(node, ast.Name):
            if node.id not in self.env:
                raise AnalysisError(f"Variável sem definição: {node.id}.")
            self.pairs.add((node.id, self.definition[node.id], self.current))
            return self.env[node.id]
        if isinstance(node, ast.Constant):
            return Decimal(str(node.value)) if type(node.value) in (int, float) else node.value
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand)
            if isinstance(node.op, ast.Not):
                return not value
            return -value if isinstance(node.op, ast.USub) else +value
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self.condition(v) for v in node.values)
            return any(self.condition(v) for v in node.values)
        if isinstance(node, ast.BinOp):
            left, right = self.expr(node.left), self.expr(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            return left % right
        if isinstance(node, ast.Compare):
            left, right = self.expr(node.left), self.expr(node.comparators[0])
            operator = node.ops[0]
            if isinstance(operator, ast.Is):
                return left is right
            if isinstance(operator, ast.IsNot):
                return left is not right
            if isinstance(operator, ast.Eq):
                return left == right
            if isinstance(operator, ast.NotEq):
                return left != right
            if isinstance(operator, ast.Lt):
                return left < right
            if isinstance(operator, ast.LtE):
                return left <= right
            if isinstance(operator, ast.Gt):
                return left > right
            return left >= right
        raise AnalysisError("Expressão não suportada.")

    def condition(self, expr):
        if isinstance(expr, ast.BoolOp):
            return self.expr(expr)
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
            return not self.condition(expr.operand)
        self.current = getattr(expr, "_cfg", "condição")
        self.path.append(self.current)
        return bool(self.expr(expr))

    def block(self, statements):
        for node in statements:
            self.tick()
            if isinstance(node, ast.If):
                result, returned = self.block(node.body if self.condition(node.test) else node.orelse)
                if returned:
                    return result, True
            else:
                self.current = getattr(node, "_cfg", f"L{node.lineno}")
                self.path.append(self.current)
                if isinstance(node, ast.Return):
                    return self.expr(node.value) if node.value is not None else None, True
                if isinstance(node, ast.Assign):
                    name = node.targets[0].id
                    value = self.expr(node.value)
                    self.env[name] = value
                    self.definition[name] = self.current
        return None, False


def reaching_pairs(graph):
    nodes = {node["id"]: node for node in graph.nodes}
    incoming, outgoing = {key: set() for key in nodes}, {key: set() for key in nodes}
    for _ in range(len(nodes) + 1):
        changed = False
        for identifier, node in nodes.items():
            reached = set()
            for edge in graph.edges:
                if edge["to"] == identifier:
                    reached |= outgoing[edge["from"]]
            new = {pair for pair in reached if pair[0] not in node["defs"]}
            new |= {(var, identifier) for var in node["defs"]}
            if reached != incoming[identifier] or new != outgoing[identifier]:
                changed = True
            incoming[identifier], outgoing[identifier] = reached, new
        if not changed:
            break
    pairs = []
    for identifier, node in nodes.items():
        for variable in node["uses"]:
            definitions = sorted(definition for name, definition in incoming[identifier] if name == variable)
            if not definitions:
                pairs.append({"variable": variable, "definition": "sem definição", "use": identifier,
                              "type": "p-use" if node["kind"] == "decision" else "c-use", "potential_error": True})
            for definition in definitions:
                pairs.append({"variable": variable, "definition": definition, "use": identifier,
                              "type": "p-use" if node["kind"] == "decision" else "c-use", "potential_error": False})
    return pairs


def generated_cases(args, lower, epsilon):
    if len(args) == 3 and lower == 0 and epsilon == Decimal("0.01"):
        mapping = {f"val_param{i+1}": name for i, name in enumerate(args)}
        return [{"id": c.id, "point": c.point, "target": mapping.get(c.target, c.target), "values": c.values} for c in test_cases()]
    base = [lower + Decimal("10")] * len(args)
    cases = []
    for index, arg in enumerate(args):
        for label, value in [("On-Point", lower), ("Off-Point", lower - epsilon),
                             ("Vizinho válido", lower + epsilon), ("Interior", lower + 100),
                             ("Exterior", lower - 100), ("NULL", None)]:
            values = base[:]
            values[index] = value
            cases.append({"id": f"CT{len(cases)+1:02d}", "point": label, "target": arg, "values": tuple(values)})
    return cases


def outcome(interpreter, values, precision):
    try:
        value, path, pairs = interpreter.run(values)
        if isinstance(value, Decimal):
            if not value.is_finite() or abs(value) > Decimal("1e24"):
                raise AnalysisError("Resultado fora do limite didático.")
            value = value.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
        return {"value": value, "error": None, "path": path, "pairs": pairs}
    except (ArithmeticError, TypeError, ValueError) as exc:
        return {"value": None, "error": f"{type(exc).__name__}: {str(exc)[:120]}", "path": [], "pairs": set()}


def mutation_candidates(fn, epsilon):
    choices = []
    arithmetic = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add, ast.Div: ast.Mult, ast.Mod: ast.Mult}
    relational = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
                  ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is}
    for node in ast.walk(fn):
        if isinstance(node, ast.BinOp) and type(node.op) in arithmetic:
            choices.append((node._point, "op", arithmetic[type(node.op)](), "AOR", node.lineno))
        elif isinstance(node, ast.Compare) and type(node.ops[0]) in relational:
            choices.append((node._point, "ops", [relational[type(node.ops[0])]()], "ROR", node.lineno))
        elif isinstance(node, ast.BoolOp):
            choices.append((node._point, "op", ast.Or() if isinstance(node.op, ast.And) else ast.And(), "LCR", node.lineno))
        elif isinstance(node, ast.Return) and node.value is not None:
            if not (isinstance(node.value, ast.Constant) and node.value.value == 0):
                choices.append((node._point, "value", ast.Constant(value=0), "RVR", node.lineno))
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float) and node.value == 0:
            choices.append((node._point, "value", float(epsilon), "CRP", node.lineno))
    return choices[:MAX_MUTANTS], len(choices) > MAX_MUTANTS


def run_mutations(fn, args, cases, baselines, precision, equivalent_ids):
    choices, truncated = mutation_candidates(fn, Decimal(1).scaleb(-precision))
    valid_ids = {f"M{number:02d}" for number in range(1, len(choices)+1)}
    if equivalent_ids - valid_ids:
        raise AnalysisError("ID de mutante equivalente inexistente: " + ", ".join(sorted(equivalent_ids - valid_ids)))
    results = []
    eligible = [i for i, base in enumerate(baselines) if base["error"] is None]
    for number, (point, field, replacement, operator, line) in enumerate(choices, 1):
        identifier = f"M{number:02d}"
        mutant = copy.deepcopy(fn)
        original_node = next(n for n in ast.walk(fn) if getattr(n, "_point", None) == point)
        target = next(n for n in ast.walk(mutant) if getattr(n, "_point", None) == point)
        before = ast.unparse(original_node)
        setattr(target, field, replacement)
        after = ast.unparse(target)
        interpreter = SafeInterpreter(mutant, args)
        killers = []
        for index in eligible:
            changed = outcome(interpreter, cases[index]["values"], precision)
            if changed["error"] or changed["value"] != baselines[index]["value"]:
                killers.append(cases[index]["id"])
        excluded = identifier in equivalent_ids
        # Não é matematicamente possível excluir como equivalente um mutante já distinguido.
        if excluded and killers:
            raise AnalysisError(f"{identifier} foi morto pela suíte e não pode ser marcado equivalente.")
        results.append({"id": identifier, "operator": operator, "line": line, "before": before,
                        "after": after, "status": "Equivalente declarado" if excluded else
                        ("Morto" if killers else ("Sobrevivente" if eligible else "Não avaliável")),
                        "killers": killers, "source": ast.unparse(mutant)})
    generated = len(results)
    equivalent = sum(r["status"] == "Equivalente declarado" for r in results)
    killed = sum(r["status"] == "Morto" for r in results)
    denominator = generated - equivalent
    score = round(killed / denominator * 100, 2) if eligible and denominator else None
    return {"mutants": results, "generated": generated, "killed": killed,
            "equivalent": equivalent, "survived": sum(r["status"] == "Sobrevivente" for r in results),
            "score": score, "denominator": denominator, "truncated": truncated,
            "valid_baseline_cases": len(eligible), "excluded_baseline_cases": len(cases) - len(eligible),
            "formula": f"MS = mortos / (gerados − equivalentes declarados) × 100 = {killed}/({generated}−{equivalent}) × 100",
            "method": "Comparação diferencial com a execução da unidade de referência no interpretador restrito. Sobreviventes não são automaticamente equivalentes; o score não prova correção da referência."}


def graph_svg(flow):
    nodes = {n["id"]: n for n in flow["nodes"]}
    indegree = {key: 0 for key in nodes}
    rank = {key: 0 for key in nodes}
    for edge in flow["edges"]:
        indegree[edge["to"]] += 1
    queue = deque(key for key in nodes if not indegree[key])
    while queue:
        current = queue.popleft()
        for edge in flow["edges"]:
            if edge["from"] == current:
                rank[edge["to"]] = max(rank[edge["to"]], rank[current] + 1)
                indegree[edge["to"]] -= 1
                if not indegree[edge["to"]]:
                    queue.append(edge["to"])
    rows = defaultdict(list)
    for key in nodes:
        rows[rank[key]].append(key)
    positions = {}
    y = 55
    for level in sorted(rows):
        keys = rows[level]
        for offset in range(0, len(keys), 3):
            group = keys[offset:offset+3]
            for index, key in enumerate(group):
                positions[key] = (450 + (index - (len(group)-1)/2) * 295, y)
            y += 105
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {y+20}" role="img" aria-label="Grafo de fluxo de controle" style="background:#0c1018">',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6e849e"/></marker></defs>']
    for edge in flow["edges"]:
        x1, y1 = positions[edge["from"]]
        x2, y2 = positions[edge["to"]]
        color = "#49d7b0" if edge["branch"] == "V" else "#ef9d6c" if edge["branch"] == "F" else "#6e849e"
        if x1 == x2 and y2-y1 > 130:
            # Desvios que saltam um bloco passam ao lado dos nós intermediários.
            side = -1 if x1 > 650 else 1
            bus = x1 + side * 205
            route = f'M{x1+side*135},{y1} H{bus} V{y2} H{x2+side*135}'
            label_x = bus + (9 if side > 0 else -17)
        else:
            route = f'M{x1},{y1+28} C{x1},{(y1+y2)/2} {x2},{(y1+y2)/2} {x2},{y2-28}'
            label_x = (x1+x2)/2+8
        svg.append(f'<path d="{route}" stroke="{color}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
        if edge["branch"]:
            svg.append(f'<text x="{label_x}" y="{(y1+y2)/2}" font-family="monospace" font-size="13" fill="{color}">{edge["branch"]}</text>')
    for key, node in nodes.items():
        x, yy = positions[key]
        color = "#8a9dff" if node["kind"] == "decision" else "#49d7b0" if node["kind"] in {"entry", "exit"} else "#475b77"
        text = node["label"]
        text = text if len(text) < 36 else text[:33] + "..."
        svg.append(f'<g><title>{html.escape(node["label"])}</title><rect x="{x-135}" y="{yy-28}" width="270" height="56" rx="10" fill="#131c2a" stroke="{color}"/>'
                   f'<text x="{x}" y="{yy-5}" text-anchor="middle" font-family="monospace" font-size="12" fill="#9baaca">{key} · L{node["line"]}</text>'
                   f'<text x="{x}" y="{yy+13}" text-anchor="middle" font-family="monospace" font-size="12" fill="#edf4ff">{html.escape(text)}</text></g>')
    return "".join(svg) + "</svg>"


def analyze(source, precision=None, lower="0", null_policy="zero", oracle_mode="cad0001",
            custom_cases=None, equivalent_ids=None):
    fn, translated, args, informix = prepare(source)
    source_scale = re.search(r"(?i)DECIMAL\s*\(\s*\d+\s*,\s*(\d+)\s*\)", source) if informix else None
    if precision is None:
        precision = int(source_scale.group(1)) if source_scale else 2
    if not isinstance(precision, int) or not 0 <= precision <= 6:
        raise AnalysisError("Use uma precisão inteira de 0 a 6 casas decimais.")
    if null_policy not in {"zero", "reject"} or oracle_mode not in {"cad0001", "differential"}:
        raise AnalysisError("Configuração de análise desconhecida.")
    lower = decimal_value(lower)
    if lower is None:
        raise AnalysisError("O limite inferior precisa ser numérico.")
    epsilon = Decimal(1).scaleb(-precision)
    graph = FlowGraph(fn, args)
    flow = graph.result()
    interpreter = SafeInterpreter(fn, args, graph)
    cases = generated_cases(args, lower, epsilon)
    if custom_cases:
        if not isinstance(custom_cases, list) or len(custom_cases) > 30:
            raise AnalysisError("Casos adicionais: use uma lista JSON de no máximo 30 linhas.")
        for index, values in enumerate(custom_cases):
            if not isinstance(values, list) or len(values) != len(args):
                raise AnalysisError(f"Caso adicional {index+1}: informe {len(args)} valores.")
            cases.append({"id": f"EX{index+1:02d}", "point": "Adicional", "target": "Conjunto",
                          "values": tuple(decimal_value(v) for v in values)})
    bases = [outcome(interpreter, c["values"], precision) for c in cases]
    use_cad_oracle = oracle_mode == "cad0001" and len(args) == 3 and precision == 2 and lower == 0
    rows = []
    covered_pairs = set()
    for case, base in zip(cases, bases):
        expected = expected_value(case["values"], null_policy) if use_cad_oracle else None
        covered_pairs |= base["pairs"]
        comparison = "Erro na referência" if base["error"] else ("Conforme" if expected == base["value"] else "Divergente") if use_cad_oracle else "Sem oráculo externo"
        rows.append({"id": case["id"], "point": case["point"], "target": case["target"],
                     "inputs": [fmt(v, precision) for v in case["values"]],
                     "expected": fmt(expected, precision) if use_cad_oracle else "Não informado",
                     "actual": base["error"] or fmt(base["value"], precision), "status": comparison,
                     "path": base["path"]})
    pairs = reaching_pairs(graph)
    for pair in pairs:
        key = (pair["variable"], pair["definition"], pair["use"])
        pair["covered"] = key in covered_pairs
    mutations = run_mutations(fn, args, cases, bases, precision, set(equivalent_ids or []))
    pce = []
    for arg in args:
        pce.extend([
            {"parameter": arg, "class": "Válida", "domain": f"x ≥ {fmt(lower, precision)}", "representative": fmt(lower+100, precision)},
            {"parameter": arg, "class": "Inválida", "domain": f"x < {fmt(lower, precision)}", "representative": fmt(lower-100, precision)},
            {"parameter": arg, "class": "NULL · hipótese declarada", "domain": "Ausência de valor", "representative": "NULL"},
        ])
    boundaries = [{"point": label, "value": str(v), "display": fmt(v, precision), "valid": v >= lower}
                  for label, v in [("Exterior", lower-100), ("Off-Point", lower-epsilon),
                                   ("On-Point", lower), ("Vizinho válido", lower+epsilon), ("Interior", lower+100)]]
    warnings = ["A execução é feita por um interpretador numérico restrito; não executa Informix/Logix, imports, chamadas ou loops.",
                "O domínio numérico e o limite inferior são requisitos configurados, não inferidos automaticamente de linguagem natural.",
                "A identificação de equivalência de mutantes exige revisão humana; sobrevivência não prova equivalência.",
                "Def-Uso: análise estática por definições alcançantes; cobertura dinâmica restrita à suíte selecionada. Pares potencialmente inviáveis permanecem no denominador."]
    if informix:
        warnings.append("A função CAD0001 foi traduzida pelo adaptador restrito para Python. As linhas e o grafo referem-se à tradução exibida, não ao arquivo Informix completo.")
    if not use_cad_oracle:
        warnings.append("Oráculo CAD0001 não aplicado. A suíte mostra saídas da referência e comparação diferencial dos mutantes; não declara conformidade funcional.")
    if use_cad_oracle and any(r["status"] != "Conforme" for r in rows):
        warnings.append("A referência diverge do oráculo em parte da suíte. Mutation Score é diferencial e não comprova correção contra o requisito do manual.")
    return {"version": "2.0.0", "function": fn.name, "args": args,
            "source_hash": hashlib.sha256(source.encode()).hexdigest(), "language": "Informix-4GL (adaptado)" if informix else "Python restrito",
            "translated_source": translated, "precision": precision, "epsilon": str(epsilon), "lower": str(lower),
            "null_policy": null_policy, "oracle": "CAD0001 / manual" if use_cad_oracle else "Diferencial / sem oráculo externo",
            "pce": pce, "boundaries": boundaries, "cases": rows,
            "conforming": sum(r["status"] == "Conforme" for r in rows),
            "divergent": sum(r["status"] == "Divergente" for r in rows),
            "errors": sum(bool(b["error"]) for b in bases),
            "flow": flow, "graph_svg": graph_svg(flow), "def_use": pairs,
            "def_use_total": len(pairs), "def_use_covered": sum(p["covered"] for p in pairs),
            "mutations": mutations, "warnings": warnings}


def browser_analyze(payload):
    try:
        result = analyze(**json.loads(payload))
        result["report"] = report_markdown(result)
        return json.dumps({"ok": True, "result": result}, ensure_ascii=False)
    except (ValueError, TypeError, RecursionError, ArithmeticError) as exc:
        return json.dumps({"ok": False, "error": str(exc)[:240]}, ensure_ascii=False)


def report_markdown(result):
    flow, mutation = result["flow"], result["mutations"]
    lines = ["# TestingStudio Web · Auditoria integrada", "", f"Função: {result['function']}",
             f"Fonte SHA-256: {result['source_hash']}", f"Linguagem: {result['language']}",
             f"Oráculo: {result['oracle']}; hipótese NULL: {result['null_policy']}", "",
             "## Módulo 1 · Caixa-preta", f"ε = 10^(-{result['precision']}) = {result['epsilon']}",
             f"Casos: {len(result['cases'])}; conformes: {result['conforming']}; divergentes: {result['divergent']}; erros: {result['errors']}",
             "", "| Caso | Entradas | Esperado | Saída do interpretador | Situação |", "| --- | --- | --- | --- | --- |"]
    for row in result["cases"]:
        lines.append(f"| {row['id']} · {row['point']} | {'; '.join(row['inputs'])} | {row['expected']} | {row['actual']} | {row['status']} |")
    lines += ["", "## Módulo 2 · Caixa-branca", flow["formula"], flow["convention"],
              f"Verificação: predicados + 1 = {flow['predicate_check']}",
              f"Caminhos estruturais listados: {len(flow['paths'])}; limite de listagem: 128.",
              "V(G) mede caminhos linearmente independentes, não o número de todos os caminhos nem uma prova de viabilidade.",
              "", "## Módulo 3 · Def-Uso", f"Pares cobertos: {result['def_use_covered']}/{result['def_use_total']}.",
              "", "| Variável | Definição | Uso | Tipo | Coberto |", "| --- | --- | --- | --- | --- |"]
    for row in result["def_use"]:
        lines.append(f"| {row['variable']} | {row['definition']} | {row['use']} | {row['type']} | {'Sim' if row['covered'] else 'Não'} |")
    lines += ["", "## Teste de mutação", mutation["formula"], f"MS: {mutation['score'] if mutation['score'] is not None else 'Não calculável'}%.",
              mutation["method"], f"Casos excluídos por erro na referência: {mutation['excluded_baseline_cases']}",
              "", "| Mutante | Operador | Linha | Situação | Casos que o mataram |", "| --- | --- | --- | --- | --- |"]
    for row in mutation["mutants"]:
        lines.append(f"| {row['id']} | {row['operator']} | {row['line']} | {row['status']} | {', '.join(row['killers']) or '—'} |")
    lines += ["", "## Limites e revisão"] + [f"- {warning}" for warning in result["warnings"]]
    return "\n".join(lines) + "\n"

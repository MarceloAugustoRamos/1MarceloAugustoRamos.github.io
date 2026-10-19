"""PCE, AVL e oráculo da Sprint 1. Não executa código Informix-4GL."""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "cad0001_item_calculo.txt"
ORIGINAL_SHA256 = "ce12d94b9666f87e23fadd5218705e4c0146616f5eb831e6bf832bb3cd42f070"
EPSILON = Decimal("0.01")
MAX_DECIMAL = Decimal("9999999999.99")
PARAMETERS = ("val_param1", "val_param2", "val_param3")
NULL_POLICIES = {"zero": "Normalizar NULL para zero", "reject": "Rejeitar NULL"}


def read_source() -> tuple[str, str, bool]:
    """O arquivo real é obrigatório; não há fonte fictício como fallback."""
    raw = SOURCE_PATH.read_bytes()
    source = raw.decode("utf-8-sig")
    if not source.strip():
        raise ValueError("O arquivo CAD0001 está vazio.")
    digest = hashlib.sha256(raw).hexdigest()
    return source, digest, digest == ORIGINAL_SHA256


def format_decimal(value: Decimal | None) -> str:
    return "NULL" if value is None else f"{value:.2f}".replace(".", ",")


def parse_input(text: str) -> Decimal | None:
    """Entrada sem separadores de milhar; vírgula ou ponto decimal."""
    value = text.strip()
    if not value or value.upper() in {"NULL", "NONE"}:
        return None
    try:
        number = Decimal(value.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Informe um número, NULL ou deixe o campo vazio.") from exc
    if not number.is_finite():
        raise ValueError("O valor precisa ser um número finito.")
    if abs(number) > MAX_DECIMAL:
        raise ValueError("Valor fora do intervalo representável por DECIMAL(12,2).")
    if number != number.quantize(EPSILON):
        raise ValueError("Use no máximo duas casas decimais.")
    return number.quantize(EPSILON)


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(EPSILON, rounding=ROUND_HALF_UP)


def expected_value(values: tuple[Decimal | None, ...], null_policy: str = "zero") -> Decimal:
    """Oráculo: negativos rejeitados; NULL depende da hipótese declarada."""
    if null_policy not in NULL_POLICIES:
        raise ValueError("Política de NULL desconhecida.")
    if null_policy == "reject" and any(v is None for v in values):
        return Decimal("-1.00")
    p1, p2, p3 = (Decimal("0") if v is None else v for v in values)
    if any(v < 0 for v in (p1, p2, p3)):
        return Decimal("-1.00")
    return _rounded(p1 * p2 + p3)


def simulate_original(values: tuple[Decimal | None, ...]) -> Decimal:
    """Réplica didática do TXT original: NULL vira zero; negativos são aceitos."""
    p1, p2, p3 = (Decimal("0") if v is None else v for v in values)
    return _rounded(p1 * p2 + p3)


def pce_rows(null_policy: str = "zero") -> list[dict[str, str]]:
    rows = []
    for index, parameter in enumerate(PARAMETERS, 1):
        rows.extend([
            {"ID": f"P{index}-V", "Parâmetro": parameter, "Classe": "Válida",
             "Domínio": "Numérico ≥ 0,00 (dentro de DECIMAL(12,2))", "Representante": "100,00",
             "Esperado": "Calcular (p1 × p2) + p3"},
            {"ID": f"P{index}-I", "Parâmetro": parameter, "Classe": "Inválida",
             "Domínio": "Numérico < 0,00", "Representante": "-100,00", "Esperado": "Erro: -1"},
            {"ID": f"P{index}-N", "Parâmetro": parameter, "Classe": "NULL: requisito ambíguo",
             "Domínio": "Ausência de valor; não é uma fronteira numérica", "Representante": "NULL",
             "Esperado": "Normalizar para 0,00 e calcular" if null_policy == "zero" else "Erro: -1"},
        ])
    return rows


def boundary_rows() -> list[dict[str, str | float]]:
    return [
        {"Ponto": "Exterior", "Valor": -100.0, "Valor decimal": "-100,00", "Condição": "Região inválida", "Esperado": "Erro: -1"},
        {"Ponto": "Off-Point", "Valor": -0.01, "Valor decimal": "-0,01", "Condição": "0,00 − ε", "Esperado": "Erro: -1"},
        {"Ponto": "On-Point", "Valor": 0.0, "Valor decimal": "0,00", "Condição": "Fronteira válida", "Esperado": "Sucesso: calcular"},
        {"Ponto": "Vizinho válido", "Valor": 0.01, "Valor decimal": "0,01", "Condição": "0,00 + ε (complementar)", "Esperado": "Sucesso: calcular"},
        {"Ponto": "Interior", "Valor": 100.0, "Valor decimal": "100,00", "Condição": "Região válida", "Esperado": "Sucesso: calcular"},
    ]


@dataclass(frozen=True)
class TestCase:
    id: str
    technique: str
    target: str
    point: str
    values: tuple[Decimal | None, Decimal | None, Decimal | None]


def test_cases() -> list[TestCase]:
    """Variar um parâmetro por vez mantém os outros em classes válidas."""
    cases = []
    base = (Decimal("1"), Decimal("10"), Decimal("5"))
    points = [("On-Point", "0"), ("Off-Point", "-0.01"),
              ("Interior", "100"), ("Exterior", "-100"), ("Vizinho válido", "0.01")]
    for index, parameter in enumerate(PARAMETERS):
        for point, number in points:
            values = list(base)
            values[index] = Decimal(number)
            cases.append(TestCase(f"CT{len(cases)+1:02d}", "AVL / PCE", parameter, point, tuple(values)))
    for index, parameter in enumerate(PARAMETERS):
        values = list(base)
        values[index] = None
        cases.append(TestCase(f"CT{len(cases)+1:02d}", "PCE", parameter, "NULL isolado", tuple(values)))
    extras = [
        ("Fórmula", (Decimal("2"), Decimal("3"), Decimal("4"))),
        ("Todos zero", (Decimal("0"), Decimal("0"), Decimal("0"))),
        ("Todos NULL", (None, None, None)),
        ("Dois negativos", (Decimal("-2"), Decimal("-3"), Decimal("4"))),
        ("Negativo com multiplicador zero", (Decimal("-2"), Decimal("0"), Decimal("4"))),
        ("Decimais exatos", (Decimal("1.25"), Decimal("2"), Decimal("0.50"))),
    ]
    for point, values in extras:
        cases.append(TestCase(f"CT{len(cases)+1:02d}", "PCE / combinação", "Conjunto", point, values))
    return cases


def case_rows(null_policy: str = "zero", simulation_available: bool = True) -> list[dict[str, str]]:
    rows = []
    for case in test_cases():
        expected = expected_value(case.values, null_policy)
        simulated = simulate_original(case.values) if simulation_available else None
        status = "Não simulado" if not simulation_available else ("Conforme" if simulated == expected else "Divergente")
        if simulation_available and status == "Conforme" and any(v is not None and v < 0 for v in case.values):
            status = "Coincidência numérica; revisar"
        rows.append({"ID": case.id, "Técnica": case.technique, "Alvo": case.target, "Ponto": case.point,
                     "p1": format_decimal(case.values[0]), "p2": format_decimal(case.values[1]),
                     "p3": format_decimal(case.values[2]), "Esperado (oráculo)": format_decimal(expected),
                     "Simulado (TXT original)": format_decimal(simulated) if simulation_available else "Não simulado",
                     "Comparação": status})
    return rows


def csv_bytes(rows: list[dict]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8-sig")


def markdown_table(rows: list[dict]) -> str:
    columns = list(rows[0])
    def safe(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(safe(row[c]) for c in columns) + " |" for row in rows)
    return "\n".join(lines)


def build_report(digest: str, null_policy: str = "zero", simulation_available: bool = True,
                 gemini_text: str | None = None, model: str | None = None) -> str:
    cases = case_rows(null_policy, simulation_available)
    divergent = sum(row["Comparação"] == "Divergente" for row in cases)
    boundaries = [{k: v for k, v in row.items() if k != "Valor"} for row in boundary_rows()]
    report = f"""# TestingStudio Web - Relatório da Sprint 1

Disciplina: Teste de Software I (62371) | Professor: Frank Piffer | 2026.2

## 1. Escopo e rastreabilidade

Objeto de estudo: `cad0001_item_calculo.txt`, função `cad0001_calcula_valor`.
Fonte lido do arquivo real, preservado sem correções. SHA-256: `{digest}`.
Técnicas: Particionamento em Classes de Equivalência (PCE) e Análise do Valor Limite (AVL).
O oráculo usa a regra do manual: entradas negativas devem retornar -1; demais entradas calculam `(p1 * p2) + p3`.
Os casos de caixa-preta derivam dessa regra, não dos caminhos internos do programa.
A comparação com o TXT é uma inspeção estática complementar e uma simulação didática em Python.

## 2. Ambiguidades e defeitos identificados

**D01 - Ausência de validação de negativos no TXT original.** O exemplo do PDF rejeita
qualquer parâmetro negativo, mas a função do TXT apenas normaliza NULL e aplica a fórmula.
Exemplo: (-0,01; 10,00; 5,00) deveria retornar -1,00; a réplica do TXT retorna 4,90.
Dois negativos podem produzir um resultado positivo: (-2,00; -3,00; 4,00) resulta em 10,00
na réplica, apesar de a regra exigir -1,00.

**A01 - NULL tem requisito contraditório.** A fundamentação do PDF o chama de inválido,
mas tanto seu exemplo de função quanto o TXT convertem NULL para zero.
Hipótese selecionada para este relatório: **{NULL_POLICIES[null_policy]}**.
A decisão precisa ser confirmada com o professor. NULL é uma classe especial, não um ponto AVL.

Essas conclusões estáticas se referem ao TXT original fornecido. Se o arquivo foi alterado,
refaça a inspeção; a aplicação desativa sua réplica para não atribuir resultados ao novo fonte.

## 3. Particionamento em Classes de Equivalência

{markdown_table(pce_rows(null_policy))}

Os parâmetros variam isoladamente, mantendo os demais em classes válidas, para evitar
que uma entrada inválida mascare outra. As classes são limitadas ao domínio de DECIMAL(12,2).
Texto arbitrário não pertence ao tipo de entrada da função e não é tratado como valor monetário.

## 4. AVL e justificativa de épsilon

DECIMAL(12,2) representa duas casas decimais; portanto, ε = 10^(-2) = **0,01**.
A fronteira inferior válida é 0,00. O primeiro valor inválido é 0,00 - ε = -0,01.
Incluímos 0,01 como vizinho válido complementar, além dos quatro pontos pedidos no manual.

{markdown_table(boundaries)}

O gráfico completo cobre -100,00 a 100,00. Um segundo gráfico amplia -0,01 a 0,01,
pois o centavo ficaria visualmente comprimido na escala completa.

## 5. Casos de teste e comparação

Total: {len(cases)} casos. Divergências numéricas da réplica contra o oráculo: {divergent}.
Simulação do TXT original disponível: {"sim" if simulation_available else "não (arquivo modificado)"}.
**Não houve execução de Informix-4GL nem acesso à base Logix.**
"Simulado" designa apenas a réplica da função original em Python; não é resultado observado no sistema alvo.

{markdown_table(cases)}

## 6. Limites e próximos passos

A réplica usa Decimal e ROUND_HALF_UP para duas casas. Os casos fixos evitam resultados
com frações de centavo; a regra de arredondamento do ambiente Informix deve ser confirmada
para entradas adicionais. DECIMAL(12,2) permite até 9.999.999.999,99 em módulo, porém
limite superior, overflow de produto, transações e banco de dados não são cobertos nesta Sprint.
O sentinela -1 pode coincidir com o cálculo de uma entrada inválida; comparação apenas
numérica não prova que a validação foi executada.
Caixa-branca, grafo de fluxo e McCabe ficam para a próxima Sprint, conforme o manual.

## 7. Integração com Gemini

"""
    if gemini_text:
        report += f"Modelo solicitado: `{model}`. Análise recebida pela API e sujeita à revisão humana.\n\n{gemini_text}\n"
    else:
        report += "Este relatório contém a análise local. Nenhuma resposta real do Gemini está incluída.\nPara completar a demonstração da integração, insira sua chave e execute a auditoria com Gemini.\n"
    return report


# Compatibilidade com publicações que selecionaram o módulo de regras como entrada.
# O ponto de entrada recomendado continua sendo app.py; importar analysis não abre UI.
if __name__ == "__main__":
    from studio_app import main
    main()

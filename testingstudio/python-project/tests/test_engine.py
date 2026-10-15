import json
import unittest
from pathlib import Path

from studio_engine import AnalysisError, CORRECTED_SAMPLE, analyze, browser_analyze

ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = analyze((ROOT / "cad0001_item_calculo.txt").read_text())
        cls.corrected = analyze(CORRECTED_SAMPLE)

    def test_original_adapter_and_defect(self):
        self.assertEqual(self.original["language"], "Informix-4GL (adaptado)")
        self.assertEqual(len(self.original["cases"]), 24)
        self.assertEqual(self.original["divergent"], 8)
        self.assertEqual(self.original["flow"]["vg"], 4)
        case = next(c for c in self.original["cases"] if c["id"] == "CT02")
        self.assertEqual(case["expected"], "-1,00")
        self.assertEqual(case["actual"], "4,90")

    def test_corrected_reference(self):
        self.assertEqual(self.corrected["conforming"], 24)
        self.assertEqual(self.corrected["errors"], 0)
        self.assertEqual(self.corrected["flow"]["vg"], 7)
        self.assertEqual(self.corrected["def_use_covered"], self.corrected["def_use_total"])

    def test_mccabe_invariant_and_short_circuit(self):
        for result in (self.original, self.corrected, analyze('def f(a,b):\n    if a > 0 and b > 0:\n        return a+b\n    return 0\n', oracle_mode="differential")):
            flow = result["flow"]
            self.assertEqual(flow["vg"], flow["E"] - flow["N"] + 2 * flow["P"])
            self.assertEqual(flow["vg"], flow["predicate_check"])
            self.assertTrue(flow["paths"])

    def test_paths_follow_real_edges(self):
        flow = self.corrected["flow"]
        edges = {(e["from"], e["to"]) for e in flow["edges"]}
        for path in flow["paths"]:
            self.assertTrue(all(pair in edges for pair in zip(path, path[1:])))
        for case in self.corrected["cases"]:
            self.assertTrue(all(pair in edges for pair in zip(case["path"], case["path"][1:])))

    def test_epsilon_is_computed_from_precision(self):
        result = analyze('def f(a):\n    return a\n', precision=3, lower="2", oracle_mode="differential")
        self.assertEqual(result["epsilon"], "0.001")
        off = next(b for b in result["boundaries"] if b["point"] == "Off-Point")
        self.assertEqual(off["value"], "1.999")
        self.assertFalse(off["valid"])

    def test_redefinition_kills_previous_definition(self):
        result = analyze('def f(a):\n    x = a\n    x = 2\n    return x\n', oracle_mode="differential")
        nodes = {n["id"]: n for n in result["flow"]["nodes"]}
        x_pairs = [p for p in result["def_use"] if p["variable"] == "x"]
        self.assertEqual(len(x_pairs), 1)
        self.assertEqual(nodes[x_pairs[0]["definition"]]["line"], 3)
        self.assertEqual(nodes[x_pairs[0]["use"]]["line"], 4)

    def test_mutation_score_exact_arithmetic(self):
        mutation = self.corrected["mutations"]
        self.assertEqual(mutation["generated"], 17)
        self.assertEqual(mutation["score"], round(100 * mutation["killed"] / mutation["denominator"], 2))
        self.assertTrue(all(m["killers"] for m in mutation["mutants"] if m["status"] == "Morto"))
        self.assertTrue(any("não comprova" in warning for warning in self.original["warnings"]))

    def test_survivor_not_automatically_equivalent(self):
        source = 'def f(a):\n    if a > 1000:\n        return a*2\n    return a+1\n'
        result = analyze(source, oracle_mode="differential")
        survivor = next(m for m in result["mutations"]["mutants"] if m["status"] == "Sobrevivente")
        self.assertEqual(result["mutations"]["equivalent"], 0)
        reviewed = analyze(source, oracle_mode="differential", equivalent_ids=[survivor["id"]])
        self.assertEqual(reviewed["mutations"]["equivalent"], 1)
        self.assertEqual(reviewed["mutations"]["denominator"], reviewed["mutations"]["generated"] - 1)

    def test_killed_mutant_cannot_be_excluded(self):
        killed = next(m["id"] for m in self.corrected["mutations"]["mutants"] if m["status"] == "Morto")
        with self.assertRaises(AnalysisError):
            analyze(CORRECTED_SAMPLE, equivalent_ids=[killed])

    def test_custom_cases_and_wrong_arity(self):
        result = analyze(CORRECTED_SAMPLE, custom_cases=[[2, 3, 4]])
        self.assertEqual(result["cases"][-1]["id"], "EX01")
        self.assertEqual(result["cases"][-1]["actual"], "10,00")
        with self.assertRaises(AnalysisError):
            analyze(CORRECTED_SAMPLE, custom_cases=[[2]])

    def test_unsupported_code_is_never_executed(self):
        attacks = ['def f(a):\n    return __import__("os").getcwd()\n',
                   'def f(a):\n    while True:\n        a=a+1\n    return a\n',
                   'def f(a):\n    return a.__class__\n',
                   'import os\ndef f(a):\n    return a\n']
        for source in attacks:
            with self.subTest(source=source), self.assertRaises(AnalysisError):
                analyze(source)

    def test_reference_errors_do_not_create_fake_score(self):
        result = analyze('def f(a):\n    return a / 0\n', oracle_mode="differential")
        self.assertEqual(result["mutations"]["valid_baseline_cases"], 0)
        self.assertIsNone(result["mutations"]["score"])

    def test_browser_contract_includes_report_and_error(self):
        success = json.loads(browser_analyze(json.dumps({"source": CORRECTED_SAMPLE})))
        self.assertTrue(success["ok"])
        self.assertIn("## Teste de mutação", success["result"]["report"])
        error = json.loads(browser_analyze(json.dumps({"source": ""})))
        self.assertFalse(error["ok"])

    def test_unreachable_nodes_not_counted(self):
        result = analyze('def f(a):\n    return a\n    x = a + 2\n', oracle_mode="differential")
        self.assertEqual(result["flow"]["vg"], 1)
        self.assertTrue(all(n["line"] != 3 for n in result["flow"]["nodes"]))

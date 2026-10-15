import unittest
from decimal import Decimal

from analysis import (ORIGINAL_SHA256, boundary_rows, build_report, case_rows,
                      expected_value, parse_input, pce_rows, read_source,
                      simulate_original, test_cases)


class AnalysisTests(unittest.TestCase):
    def test_real_source_is_preserved(self):
        source, digest, original = read_source()
        self.assertTrue(original)
        self.assertEqual(digest, ORIGINAL_SHA256)
        self.assertIn("DATABASE logix", source)
        self.assertIn("FUNCTION cad0001_excluir()", source)

    def test_negative_rejected_in_every_position(self):
        for index in range(3):
            for negative in (Decimal("-0.01"), Decimal("-100")):
                values = [Decimal("1"), Decimal("10"), Decimal("5")]
                values[index] = negative
                with self.subTest(index=index, negative=negative):
                    self.assertEqual(expected_value(tuple(values)), Decimal("-1.00"))

    def test_zero_and_first_valid_cent_in_every_position(self):
        expected = (("5.00", "5.10"), ("5.00", "5.01"), ("10.00", "10.01"))
        for index in range(3):
            for step, value in enumerate((Decimal("0"), Decimal("0.01"))):
                values = [Decimal("1"), Decimal("10"), Decimal("5")]
                values[index] = value
                with self.subTest(index=index, value=value):
                    self.assertEqual(expected_value(tuple(values)), Decimal(expected[index][step]))

    def test_formula_and_decimal_arithmetic(self):
        self.assertEqual(expected_value((Decimal("2"), Decimal("3"), Decimal("4"))), Decimal("10.00"))
        self.assertEqual(expected_value((Decimal("1.25"), Decimal("2"), Decimal("0.50"))), Decimal("3.00"))

    def test_null_policies_remain_explicit(self):
        for values in ((None, Decimal("10"), Decimal("5")), (None, None, None)):
            with self.subTest(values=values):
                self.assertEqual(expected_value(values, "zero"), simulate_original(values))
                self.assertEqual(expected_value(values, "reject"), Decimal("-1.00"))

    def test_original_defect_is_visible(self):
        values = (Decimal("-0.01"), Decimal("10"), Decimal("5"))
        self.assertEqual(expected_value(values), Decimal("-1.00"))
        self.assertEqual(simulate_original(values), Decimal("4.90"))
        values = (Decimal("-2"), Decimal("-3"), Decimal("4"))
        self.assertEqual(simulate_original(values), Decimal("10.00"))
        self.assertEqual(expected_value(values), Decimal("-1.00"))

    def test_suite_covers_each_requested_boundary(self):
        cases = test_cases()
        self.assertEqual(len(cases), 24)
        for parameter in ("val_param1", "val_param2", "val_param3"):
            points = {case.point for case in cases if case.target == parameter}
            self.assertTrue({"On-Point", "Off-Point", "Interior", "Exterior", "Vizinho válido", "NULL isolado"} <= points)
        self.assertEqual(sum(row["Comparação"] == "Divergente" for row in case_rows()), 8)

    def test_null_hypothesis_changes_expected_cases(self):
        self.assertEqual(sum(row["Comparação"] == "Divergente" for row in case_rows("reject")), 12)
        self.assertEqual(len(pce_rows()), 9)

    def test_modified_source_cannot_receive_original_simulation(self):
        self.assertTrue(all(row["Comparação"] == "Não simulado" for row in case_rows(simulation_available=False)))

    def test_input_parsing(self):
        for text, number in (("0,01", "0.01"), ("-0.01", "-0.01"), ("100", "100.00")):
            with self.subTest(text=text):
                self.assertEqual(parse_input(text), Decimal(number))
        self.assertIsNone(parse_input(""))
        self.assertIsNone(parse_input("NULL"))

    def test_invalid_inputs(self):
        for text in ("abc", "NaN", "Infinity", "0.001", "10000000000", "1.000,00"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_input(text)

    def test_export_identifies_simulation_and_gemini_status(self):
        report = build_report(ORIGINAL_SHA256)
        self.assertIn("Não houve execução de Informix", report)
        self.assertIn("Nenhuma resposta real do Gemini", report)
        self.assertIn("CT24", report)
        self.assertIn("0,01", report)
        self.assertEqual(len(boundary_rows()), 5)


if __name__ == "__main__":
    unittest.main()

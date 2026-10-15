import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analysis import read_source
from gemini_service import AuditError, build_prompt, run_gemini


class GeminiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.digest, cls.original = read_source()

    def call(self, key="chave-ficticia-para-teste"):
        return run_gemini(key, "modelo-teste", self.source, self.digest)

    def test_missing_key_prevents_api_call(self):
        with patch("google.genai.Client") as client:
            with self.assertRaises(AuditError):
                self.call("")
            client.assert_not_called()

    def test_prompt_contains_full_source_and_rules(self):
        prompt = build_prompt(self.source, self.digest, "zero", True)
        self.assertIn(self.source, prompt)
        self.assertIn("ε = 0,01", prompt)
        self.assertIn("não existe", prompt)
        self.assertIn("contradição", prompt)

    def test_sdk_request_and_text_handling(self):
        with patch("google.genai.Client") as factory:
            client = factory.return_value.__enter__.return_value
            client.models.generate_content.return_value = SimpleNamespace(text="  # Auditoria fictícia de teste  ", candidates=[])
            self.assertEqual(self.call(), "# Auditoria fictícia de teste")
            kwargs = client.models.generate_content.call_args.kwargs
            self.assertEqual(kwargs["model"], "modelo-teste")
            self.assertIn(self.source, kwargs["contents"])
            self.assertEqual(factory.call_args.kwargs["http_options"].timeout, 90000)

    def test_empty_response_is_not_success(self):
        with patch("google.genai.Client") as factory:
            factory.return_value.__enter__.return_value.models.generate_content.return_value = SimpleNamespace(text=None, candidates=[])
            with self.assertRaises(AuditError):
                self.call()

    def test_truncated_response_is_not_complete_audit(self):
        with patch("google.genai.Client") as factory:
            factory.return_value.__enter__.return_value.models.generate_content.return_value = SimpleNamespace(
                text="parcial", candidates=[SimpleNamespace(finish_reason="MAX_TOKENS")])
            with self.assertRaises(AuditError):
                self.call()

    def test_api_errors_never_expose_key(self):
        class FakeError(Exception):
            code = 429
        with patch("google.genai.Client") as factory:
            factory.return_value.__enter__.return_value.models.generate_content.side_effect = FakeError("key=segredo")
            with self.assertRaises(AuditError) as captured:
                self.call()
            self.assertIn("cota", str(captured.exception))
            self.assertNotIn("segredo", str(captured.exception))


if __name__ == "__main__":
    unittest.main()

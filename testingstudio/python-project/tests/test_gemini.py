import unittest
import os
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from analysis import read_source
from gemini_service import AuditError, build_prompt, check_gemini_access, run_gemini


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
            self.assertFalse(factory.call_args.kwargs["vertexai"])
            self.assertEqual(factory.call_args.kwargs["http_options"].retry_options.attempts, 1)

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

    def test_obvious_copy_errors_do_not_send_a_request(self):
        for key in ('"chave-ficticia"', '(chave-ficticia)', 'chave com espaços', 'COLE_SUA_CHAVE_AQUI'):
            with self.subTest(key=key), patch('google.genai.Client') as client:
                with self.assertRaises(AuditError):
                    self.call(key)
                client.assert_not_called()

    def test_access_check_only_reads_model_metadata(self):
        with patch('google.genai.Client') as factory:
            client = factory.return_value.__enter__.return_value
            check_gemini_access(' chave-ficticia ', ' modelo-teste ')
            client.models.get.assert_called_once_with(model='modelo-teste')
            client.models.generate_content.assert_not_called()
            self.assertEqual(factory.call_args.kwargs['api_key'], 'chave-ficticia')

    def test_authentication_error_is_safe_and_actionable(self):
        class FakeError(Exception):
            code = 401
        with patch('google.genai.Client') as factory:
            factory.return_value.__enter__.return_value.models.get.side_effect = FakeError('key=segredo')
            with self.assertRaises(AuditError) as captured:
                check_gemini_access('chave-ficticia', 'modelo-teste')
            message = str(captured.exception)
            self.assertIn('HTTP 401', message)
            self.assertIn('GEMINI_API_KEY', message)
            self.assertNotIn('segredo', message)

    def check_with_http_transport(self, handler):
        from google import genai
        original_client = genai.Client

        def client_with_transport(**kwargs):
            kwargs['http_options'] = kwargs['http_options'].model_copy(update={
                'httpx_client': httpx.Client(transport=httpx.MockTransport(handler), trust_env=False),
                'httpx_async_client': httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False),
            })
            return original_client(**kwargs)

        # No actual network: the transport receives every SDK request locally.
        with patch.dict(os.environ, {
            'GOOGLE_GENAI_USE_VERTEXAI': 'true',
            'GOOGLE_GENAI_USE_ENTERPRISE': 'true',
            'GOOGLE_GEMINI_BASE_URL': 'https://incorrect.example/',
        }), patch('google.genai.Client', side_effect=client_with_transport):
            check_gemini_access('chave-ficticia-http', 'modelo-teste')

    def test_sdk_sends_explicit_key_to_ai_studio_even_with_conflicting_environment(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(200, json={'name': 'models/modelo-teste'})

        self.check_with_http_transport(handler)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].method, 'GET')
        self.assertEqual(str(requests[0].url), 'https://generativelanguage.googleapis.com/v1beta/models/modelo-teste')
        self.assertEqual(requests[0].headers['x-goog-api-key'], 'chave-ficticia-http')
        self.assertNotIn('authorization', requests[0].headers)

    def test_quota_error_does_not_trigger_hidden_sdk_retries(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(429, json={'error': {
                'code': 429, 'status': 'RESOURCE_EXHAUSTED', 'message': 'key=segredo',
            }})

        with self.assertRaises(AuditError) as captured:
            self.check_with_http_transport(handler)
        self.assertEqual(len(requests), 1)
        self.assertIn('HTTP 429', str(captured.exception))
        self.assertNotIn('segredo', str(captured.exception))


if __name__ == "__main__":
    unittest.main()

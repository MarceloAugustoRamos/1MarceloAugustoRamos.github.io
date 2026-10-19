import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from gemini_credentials import SavedCredentials

ROOT = Path(__file__).resolve().parents[1]
TEST_KEY = "chave-ficticia-do-servidor-nao-utilizar"


class SavedKeyTests(unittest.TestCase):
    def app(self, key=TEST_KEY, legacy_password=None):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20)
        app.secrets['GEMINI_API_KEY'] = key
        if legacy_password is not None:
            app.secrets['GEMINI_ACCESS_PASSWORD'] = legacy_password
        return app.run().radio(key='view').set_value('Gemini').run()

    def test_public_saved_key_needs_no_password_and_does_not_call_automatically(self):
        with patch('studio_sidebar.check_gemini_access') as verify, patch('studio_app.run_gemini') as generate:
            app = self.app()
            self.assertFalse(app.exception)
            self.assertFalse(app.button(key='verify_gemini').disabled)
            self.assertFalse(any(x.label == 'Senha de acesso' for x in app.text_input))
            verify.assert_not_called()
            generate.assert_not_called()

    def test_saved_key_is_never_rendered_or_exported(self):
        app = self.app()
        self.assertNotIn(TEST_KEY, str(app.session_state))
        self.assertNotIn(TEST_KEY, str([x.value for x in app.text_input]))
        self.assertNotIn(TEST_KEY, str([x.value for x in app.markdown]))
        self.assertNotIn(TEST_KEY, str([x.value for x in app.caption]))
        self.assertNotIn(TEST_KEY, repr(SavedCredentials(TEST_KEY)))
        with patch('studio_app.run_gemini', return_value='Revisão fictícia.') as api:
            app.button(key='run_gemini').click().run()
            self.assertEqual(api.call_args.args[0], TEST_KEY)
            self.assertNotIn(TEST_KEY, str(app.session_state['studio_result']))

    def test_access_check_uses_server_key_without_password(self):
        app = self.app()
        with patch('studio_sidebar.check_gemini_access') as verify:
            app.button(key='verify_gemini').click().run()
            verify.assert_called_once_with(TEST_KEY, 'gemini-3.8-flash')
            self.assertTrue(any('O Google aceitou' in x.value for x in app.success))

    def test_legacy_password_is_ignored(self):
        app = self.app(legacy_password='antiga-senha-ficticia')
        self.assertFalse(app.exception)
        self.assertFalse(app.button(key='verify_gemini').disabled)
        self.assertFalse(any(x.label == 'Senha de acesso' for x in app.text_input))
        self.assertNotIn('_gemini_saved_key_access', app.session_state)

    def test_visitor_can_choose_own_key(self):
        app = self.app().selectbox(key='gemini_key_source').set_value('Informar minha chave').run()
        app.text_input(key='api_key').set_value('chave-ficticia-do-visitante')
        with patch('studio_app.run_gemini', return_value='Teste com chave própria.') as api:
            app.button(key='run_gemini').click().run()
            self.assertEqual(api.call_args.args[0], 'chave-ficticia-do-visitante')

    def test_missing_key_still_allows_local_analysis_and_manual_fallback(self):
        app = self.app(key='')
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '24')
        self.assertEqual(app.text_input(key='api_key').value, '')
        self.assertTrue(app.button(key='verify_gemini').disabled)
        with patch('studio_app.run_gemini') as api:
            app.button(key='run_gemini').click().run()
            api.assert_not_called()
        self.assertTrue(any('API Key' in x.value for x in app.error))

    def test_non_string_secret_is_not_exposed(self):
        app = self.app(key=123)
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key='api_key').value, '')

    def test_failed_access_check_does_not_claim_success(self):
        from gemini_service import AuditError
        app = self.app()
        with patch('studio_sidebar.check_gemini_access', side_effect=AuditError('HTTP 401 · Chave recusada.')):
            app.button(key='verify_gemini').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('HTTP 401' in x.value for x in app.error))
            self.assertFalse(any('O Google aceitou' in x.value for x in app.success))

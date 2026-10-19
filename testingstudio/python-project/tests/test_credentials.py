import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from gemini_credentials import AUTH_STATE, SavedCredentials, is_unlocked

ROOT = Path(__file__).resolve().parents[1]
TEST_KEY = "chave-ficticia-do-servidor-nao-utilizar"
TEST_PASSWORD = "Senha-fictícia-com-acentos-2026"
SUBMIT = "FormSubmitter:gemini_saved_key_form-Usar chave salva"


class SavedKeyTests(unittest.TestCase):
    def app(self, password=TEST_PASSWORD):
        app=AppTest.from_file(str(ROOT/'app.py'), default_timeout=20)
        app.secrets['GEMINI_API_KEY']=TEST_KEY
        app.secrets['GEMINI_ACCESS_PASSWORD']=password
        return app.run().radio(key='view').set_value('Gemini').run()

    def unlock(self, app, password=TEST_PASSWORD):
        app.text_input(key='gemini_access_password').set_value(password)
        return app.button(key=SUBMIT).click().run()

    def test_saved_key_requires_password_before_call(self):
        app=self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='gemini_key_source').value,'Chave salva no app')
        self.assertTrue(app.button(key='verify_gemini').disabled)
        with patch('studio_app.run_gemini') as api:
            app.button(key='run_gemini').click().run()
            api.assert_not_called()
        self.assertTrue(any('senha de acesso' in x.value for x in app.error))

    def test_correct_password_uses_key_without_exposing_it(self):
        app=self.unlock(self.app())
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key='model').value,'gemini-3.8-flash')
        self.assertIn(AUTH_STATE,app.session_state)
        self.assertNotIn(TEST_KEY,str(app.session_state))
        self.assertNotIn(TEST_PASSWORD,str(app.session_state))
        self.assertNotIn(TEST_KEY,str([x.value for x in app.text_input]))
        self.assertNotIn(TEST_KEY,str([x.value for x in app.markdown]))
        with patch('studio_app.run_gemini',return_value='Revisão fictícia para testar a conexão salva.') as api:
            app.button(key='run_gemini').click().run()
            self.assertEqual(api.call_args.args[0],TEST_KEY)
            self.assertNotIn(TEST_KEY,str(app.session_state['studio_result']))
        app.radio(key='view').set_value('Caixa-preta').run()
        app.radio(key='view').set_value('Gemini').run()
        self.assertIn(AUTH_STATE,app.session_state)

    def test_wrong_password_clears_input_and_keeps_locked(self):
        app=self.unlock(self.app(),'senha errada')
        self.assertFalse(app.exception)
        self.assertNotIn(AUTH_STATE,app.session_state)
        self.assertEqual(app.text_input(key='gemini_access_password').value,'')
        self.assertTrue(any('Senha de acesso incorreta' in x.value for x in app.error))

    def test_lock_prevents_further_use(self):
        app=self.unlock(self.app())
        app.button(key='gemini_saved_lock').click().run()
        self.assertFalse(app.exception)
        self.assertNotIn(AUTH_STATE,app.session_state)
        with patch('studio_app.run_gemini') as api:
            app.button(key='run_gemini').click().run()
            api.assert_not_called()

    def test_missing_access_password_never_exposes_server_key(self):
        app=self.app(password='')
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key='api_key').value,'')
        self.assertTrue(app.warning)
        self.assertNotIn(TEST_KEY,str(app.session_state))

    def test_visitor_can_choose_own_key_without_unlocking_server_key(self):
        app=self.app().selectbox(key='gemini_key_source').set_value('Informar minha chave').run()
        app.text_input(key='api_key').set_value('chave-ficticia-do-visitante')
        with patch('studio_app.run_gemini',return_value='Teste com chave própria.') as api:
            app.button(key='run_gemini').click().run()
            self.assertEqual(api.call_args.args[0],'chave-ficticia-do-visitante')
        self.assertNotIn(AUTH_STATE,app.session_state)

    def test_rotated_credentials_invalidate_session(self):
        original=SavedCredentials(TEST_KEY,TEST_PASSWORD)
        state={AUTH_STATE:original.fingerprint}
        self.assertTrue(is_unlocked(original,state))
        self.assertFalse(is_unlocked(SavedCredentials('outra-chave',TEST_PASSWORD),state))
        self.assertFalse(is_unlocked(SavedCredentials(TEST_KEY,'outra-senha-forte-2026'),state))
        self.assertFalse(is_unlocked(SavedCredentials(TEST_KEY,''),state))
        self.assertNotIn(TEST_KEY,repr(original))
        self.assertNotIn(TEST_PASSWORD,repr(original))

    def test_unlock_does_not_verify_or_generate_automatically(self):
        with patch('studio_sidebar.check_gemini_access') as verify, patch('studio_app.run_gemini') as generate:
            app=self.unlock(self.app())
            verify.assert_not_called()
            generate.assert_not_called()
            self.assertTrue(any('liberada' in x.value for x in app.success))
            self.assertFalse(any('O Google aceitou' in x.value for x in app.success))
            app.button(key='verify_gemini').click().run()
            verify.assert_called_once_with(TEST_KEY,'gemini-3.8-flash')
            generate.assert_not_called()
            self.assertTrue(any('O Google aceitou' in x.value for x in app.success))
            self.assertNotIn(TEST_KEY,str([x.value for x in app.success]))

    def test_failed_access_check_never_claims_google_accepted_key(self):
        from gemini_service import AuditError
        app=self.unlock(self.app())
        with patch('studio_sidebar.check_gemini_access',side_effect=AuditError('HTTP 401 · Chave recusada.')):
            app.button(key='verify_gemini').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('HTTP 401' in x.value for x in app.error))
            self.assertFalse(any('O Google aceitou' in x.value for x in app.success))

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

class AppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()

    def gemini_app(self):
        app=self.app()
        return app.radio(key="view").set_value("Gemini").run()

    def test_initial_render_reads_real_file(self):
        app=self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,"24")
        self.assertEqual(app.metric[1].value,"4")
        self.assertIn("DATABASE logix",app.text_area(key="source_editor").value)

    def test_all_modules_render(self):
        app=self.app()
        for view in ["Caixa-preta","Caixa-branca","Def-Uso e mutação","Entrega","Gemini","Requisitos e RTM"]:
            app.radio(key="view").set_value(view).run()
            with self.subTest(view=view):
                self.assertFalse(app.exception)

    def test_audit_without_key_shows_actionable_error(self):
        app=self.gemini_app()
        app.button(key="run_gemini").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("API Key" in item.value for item in app.error))

    def test_fake_api_flow_persists_on_rerun_and_clears(self):
        app=self.gemini_app()
        app.text_input(key="api_key").set_value("chave-ficticia")
        with patch("studio_app.run_gemini",return_value="# Resposta fictícia de teste") as api:
            app.button(key="run_gemini").click().run()
            self.assertEqual(api.call_count,1)
            self.assertIn("gemini_audit",app.session_state)
            app.run()
            self.assertEqual(api.call_count,1)
        app.button(key="clear_gemini").click().run()
        self.assertNotIn("gemini_audit",app.session_state)

    def test_changed_hypothesis_requires_new_analysis(self):
        app=self.gemini_app()
        app.text_input(key="api_key").set_value("chave-ficticia")
        with patch("studio_app.run_gemini",return_value="Resposta fictícia"):
            app.button(key="run_gemini").click().run()
        app.selectbox(key="null_policy").set_value("reject").run()
        self.assertTrue(any("Entrada alterada" in item.value for item in app.warning))
        app.button(key="analyze").click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("gemini_audit",app.session_state)
        self.assertEqual(app.metric[2].value,"12")

    def test_api_failure_has_no_fake_success(self):
        from gemini_service import AuditError
        app=self.gemini_app()
        app.text_input(key="api_key").set_value("chave-ficticia")
        with patch("studio_app.run_gemini",side_effect=AuditError("Falha fictícia controlada")):
            app.button(key="run_gemini").click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("gemini_audit",app.session_state)
        self.assertTrue(any("Falha fictícia" in item.value for item in app.error))

    def test_missing_source_stops_before_analysis(self):
        with patch("studio_app.read_source",side_effect=FileNotFoundError("Arquivo ausente")):
            app=self.app()
        self.assertFalse(app.exception)
        self.assertFalse(app.metric)
        self.assertTrue(any("Não foi possível ler" in item.value for item in app.error))

    def test_corrected_source_and_invalid_source(self):
        app=self.app()
        app.selectbox(key="source_preset").set_value("Exemplo corrigido (Python)").run()
        app.button(key="analyze").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value,"7")
        self.assertEqual(app.metric[2].value,"0")
        app.text_area(key="source_editor").set_value("import os").run()
        app.button(key="analyze").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)

    def test_no_secret_in_export(self):
        app=self.gemini_app()
        app.text_input(key="api_key").set_value("segredo-ficticio")
        with patch("studio_app.run_gemini",return_value="Revisão fictícia") as api:
            app.button(key="run_gemini").click().run()
        self.assertIn("studio_result",api.call_args.kwargs)
        self.assertNotIn("segredo-ficticio",str(app.session_state["studio_result"]))

    def test_rtm_derives_new_requirements_and_marks_stale(self):
        import json
        from traceability import LIBRARY_SCENARIO
        app=self.app().radio(key="view").set_value("Requisitos e RTM").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[2].value,"100.0%")
        scenario=json.loads(json.dumps(LIBRARY_SCENARIO))
        scenario["requirements"].append({"id":"REQ06","description":"Nova regra sem caso."})
        app.text_area(key="rtm_source").set_value(json.dumps(scenario)).run()
        self.assertTrue(any("Cenário editado" in item.value for item in app.warning))
        app.button(key="rtm_derive").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,"6")
        self.assertEqual(app.metric[2].value,"83.3%")

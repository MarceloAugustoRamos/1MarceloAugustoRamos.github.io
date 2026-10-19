import copy
import json
import unittest
from traceability import LIBRARY_SCENARIO, TraceabilityError, analyze_traceability, browser_traceability


class TraceabilityTests(unittest.TestCase):
    def scenario(self):
        return copy.deepcopy(LIBRARY_SCENARIO)

    def test_pdf_mapping_and_coverage(self):
        result = analyze_traceability(self.scenario())
        mapping = {c['id']: c['requirements'] for c in result['cases']}
        self.assertEqual(mapping['CT01'], ['REQ01','REQ04','REQ05'])
        self.assertEqual(mapping['CT02'], ['REQ02'])
        self.assertEqual(mapping['CT03'], ['REQ03'])
        self.assertEqual(result['coverage'], 100)
        self.assertEqual(result['execution']['executed'], 0)
        self.assertTrue(all(not r['approved'] for r in result['requirements']))
        self.assertEqual(result['flow_counts'], {'principal':2,'alternativo':2,'excecao':1})
        self.assertIn('R$ 4,00', result['report'])

    def test_bidirectional_gaps(self):
        s = self.scenario()
        s['requirements'].append({'id':'REQ06','description':'Nova regra sem caso.'})
        s['use_cases'][0]['flows'][0]['requirements'] = []
        r = analyze_traceability(s)
        self.assertEqual(r['coverage'], 50)
        self.assertEqual(r['uncovered_requirements'], ['REQ01','REQ05','REQ06'])
        self.assertEqual(r['orphan_tests'], ['CT01'])
        self.assertIn('SEM REQUISITO', r['report'])

    def test_manual_results_require_evidence_and_are_not_assumed(self):
        with self.assertRaisesRegex(TraceabilityError, 'evidência'):
            analyze_traceability(self.scenario(), {'CT01':{'status':'Aprovado'}})
        r = analyze_traceability(self.scenario(), {'CT01':{'status':'Aprovado','evidence':'Ambiente de teste; dados e captura conferidos.'},'CT02':{'status':'Bloqueado','evidence':'Ambiente indisponível.'}})
        self.assertEqual(r['execution']['executed'],1)
        self.assertEqual(r['execution']['Bloqueado'],1)
        req = {row['id']:row for row in r['requirements']}
        self.assertTrue(req['REQ01']['approved'])
        self.assertFalse(req['REQ04']['approved']) # CT04 also covers it, and remains unexecuted.
        self.assertFalse(req['REQ02']['approved'])

    def test_duplicate_and_unknown_links_rejected(self):
        for edit in ['req','flow','ct','link','type']:
            s=self.scenario()
            if edit=='req':s['requirements'].append(s['requirements'][0].copy())
            if edit=='flow':s['use_cases'][1]['flows'][0]['id']='FP01'
            if edit=='ct':s['use_cases'][1]['flows'][0]['test_id']='CT01'
            if edit=='link':s['use_cases'][0]['flows'][0]['requirements']=['REQ99']
            if edit=='type':s['use_cases'][0]['flows'][0]['type']='inventado'
            with self.subTest(edit=edit), self.assertRaises(TraceabilityError):analyze_traceability(s)

    def test_automatic_ids_avoid_reserved_ids(self):
        s=self.scenario();s['use_cases'][0]['flows'][0].pop('test_id')
        r=analyze_traceability(s)
        self.assertEqual(len({c['id'] for c in r['cases']}),5)
        self.assertIn('CT01',[c['id'] for c in r['cases']])

    def test_empty_tests_and_custom_scenario(self):
        r=analyze_traceability({'title':'Outro domínio','requirements':[{'id':'R1','description':'Entregar resultado.'}],'use_cases':[]})
        self.assertEqual(r['coverage'],0)
        self.assertEqual(r['execution']['total'],0)
        self.assertEqual(r['uncovered_requirements'],['R1'])

    def test_project_round_trip_and_no_input_mutation(self):
        s=self.scenario();before=copy.deepcopy(s)
        r=analyze_traceability(s,{'CT03':{'status':'Reprovado','evidence':'Foi calculado R$ 3,00 para um dia.'}})
        reloaded=analyze_traceability(json.loads(json.dumps(r['scenario'])),{c['id']:{'status':c['status'],'evidence':c['evidence']} for c in r['cases']})
        self.assertEqual(r,reloaded)
        self.assertEqual(s,before)

    def test_browser_errors_and_limits(self):
        for payload in ['{','[]','{"scenario":null}',json.dumps({'scenario':self.scenario(),'executions':{'CT99':{}}})]:
            with self.subTest(payload=payload[:30]):self.assertFalse(json.loads(browser_traceability(payload))['ok'])
        self.assertFalse(json.loads(browser_traceability('x'*360001))['ok'])
        s=self.scenario();s['use_cases'][0]['flows'][0]['steps']=[]
        with self.assertRaises(TraceabilityError):analyze_traceability(s)

    def test_csv_quotes_and_formula_safety(self):
        s=self.scenario();s['requirements'][0]['description']='=HYPERLINK("x";"y")'
        r=analyze_traceability(s)
        self.assertIn("'=HYPERLINK",r['matrix_csv'])
        self.assertIn('REQ01',r['matrix_csv'])

    def test_nonfinite_data_rejected(self):
        s=self.scenario();s['use_cases'][0]['flows'][0]['data']=[{'n':float('nan')}]
        with self.assertRaises(ValueError):analyze_traceability(s)

    def test_browser_rejects_results_from_changed_scenario(self):
        scenario=self.scenario()
        old=analyze_traceability(scenario)["scenario_hash"]
        scenario["title"]="Outro cenário"
        data=json.loads(browser_traceability(json.dumps({"scenario":scenario,"executions":{"CT01":{"status":"Aprovado","evidence":"Evidência anterior."}},"execution_scenario_hash":old})))
        self.assertFalse(data["ok"])
        self.assertIn("outro cenário",data["error"])

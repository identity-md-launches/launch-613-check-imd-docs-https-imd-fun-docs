"""Offline safety and assertion tests. Never contacts IMD."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit
import reporting

class Safety(unittest.TestCase):
    def test_only_permitted_calls(self):
        for method,url in [('POST','https://api.imd.fun/requests/quote'),('POST','https://api.imd.fun/requests/x/submit'),('POST','https://explorer.imd.fun/api/requests/check'),('DELETE','https://api.imd.fun/jobs'),('GET','https://other.example/health'),('GET','http://api.imd.fun/health'),('GET','https://api.imd.fun/requests/%71uote')]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                audit.validate_request({'method':method,'url':url})
        audit.validate_request({'method':'POST','url':'https://api.imd.fun/requests/check'})
        audit.validate_request({'method':'GET','url':'https://api.imd.fun/health'})

    def test_credentials_forbidden(self):
        with self.assertRaises(ValueError):
            audit.validate_request({'method':'GET','url':'https://api.imd.fun/health','headers':{'Authorization':'Bearer forbidden'}})

    def test_redirects_not_followed(self):
        self.assertIsNone(audit.NoRedirect().redirect_request(None,None,302,'',{},'https://api.imd.fun/requests/quote'))

    def test_budget_blocks_before_network(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'results').mkdir();(root/'results/session.json').write_text(json.dumps({'calls':290,'last_finished':0}))
            with patch.object(audit,'ROOT',root), patch('urllib.request.OpenerDirector.open') as network:
                with self.assertRaises(SystemExit):
                    audit.run([{'id':'test','method':'GET','url':'https://api.imd.fun/health'}],root/'out',None)
                network.assert_not_called()

    def test_raw_body_padding_preserved(self):
        self.assertEqual(audit.body_bytes({'body_text':'{}  '}),b'{}  ')

    def test_pacing_after_response_and_exact_request(self):
        clock=[100.0];sleeps=[]
        def sleep(n):sleeps.append(n);clock[0]+=n
        class Response:
            status=200;headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):clock[0]+=3;return b'{"ok":true}'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with patch.object(audit,'ROOT',root),patch('audit.time.time',side_effect=lambda:clock[0]),patch('audit.time.sleep',side_effect=sleep),patch('urllib.request.OpenerDirector.open',return_value=Response()):
                cases=[{'id':str(i),'method':'GET','url':'https://api.imd.fun/health'} for i in range(2)]
                audit.run(cases,root/'out',None)
                a=json.loads((root/'out/0.json').read_text());b=json.loads((root/'out/1.json').read_text())
                self.assertGreaterEqual(b['started_at']-a['finished_at'],2.1-1e-9)
                self.assertEqual(base64.b64decode(a['response']['body_base64']),b'{"ok":true}')
                self.assertEqual(json.loads((root/'results/session.json').read_text())['calls'],2)

class Assertions(unittest.TestCase):
    def record(self,body,status=200,headers=None):
        return {'response':{'status':status,'headers':headers or [],'body':json.dumps(body)}}

    def test_http_200_can_be_refusal(self):
        c={'expect':{'mode':'schema_reject','field':'paths'}}
        self.assertEqual(reporting.evaluate(c,self.record({'blockers':[{'code':'unplannable_steps','detail':'paths required'}]}))[0],'PASS')
        self.assertEqual(reporting.evaluate(c,self.record({'blockers':[]}))[0],'FAIL')
        self.assertEqual(reporting.evaluate(c,self.record({'blockers':[{'detail':'unrelated service unavailable'}]}))[0],'INCONCLUSIVE')

    def test_limit_and_transport_are_not_passes(self):
        c={'expect':{'status':200}}
        self.assertEqual(reporting.evaluate(c,self.record({},429))[0],'INCONCLUSIVE')
        self.assertEqual(reporting.evaluate(c,{'transport_error':'offline'})[0],'INCONCLUSIVE')
        self.assertEqual(reporting.evaluate(c,None)[0],'NOT RUN')

    def test_cors_and_shape(self):
        c={'expect':{'status':200,'keys':['count','jobs'],'cors':True}}
        self.assertEqual(reporting.evaluate(c,self.record({'count':0,'jobs':[]},headers=[('Access-Control-Allow-Origin','*')]))[0],'PASS')
        self.assertEqual(reporting.evaluate(c,self.record({'count':0,'jobs':[]}))[0],'FAIL')

    def test_no_blocker_still_requires_success_status(self):
        c={'expect':{'mode':'no_blocker','contains':'unplannable_steps'}}
        self.assertEqual(reporting.evaluate(c,self.record({'error':'invalid_request'},400))[0],'FAIL')

    def test_required_fact_needs_matching_blocker(self):
        c={'expect':{'mode':'facts','required_missing':['token_name']}}
        data={'facts':[{'id':'token_name','state':'missing','required':True}],'blockers':[]}
        self.assertEqual(reporting.evaluate(c,self.record(data))[0],'FAIL')
        data['blockers']=[{'code':'missing_fact','fact':'token_name'}]
        self.assertEqual(reporting.evaluate(c,self.record(data))[0],'PASS')

    def test_missing_item_fields_are_failures(self):
        c={'expect':{'item_keys':['requests',['panelSize','quorum']]}}
        self.assertEqual(reporting.evaluate(c,self.record({'requests':[{'id':'x'}]}))[0],'FAIL')
        self.assertEqual(reporting.evaluate(c,self.record({'requests':[]}))[0],'INCONCLUSIVE')

if __name__=='__main__':unittest.main()

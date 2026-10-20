import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app


class LiveAPI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app(dict(TESTING=True,DATABASE=str(Path(self.tmp.name)/'app.sqlite'),LIVE_EVAL_RUN_INLINE=True,
              AI_API_KEY='NEVER-PERSIST-SECRET',AI_BASE_URL='https://api.deepseek.com/v1'))
        self.a,self.b=self.app.test_client(),self.app.test_client();self.h={'X-Requested-With':'ExamHub'}
        self.url='/api/tutor/live-evaluations'
        self.payload=dict(requestId='live-eval-request-0001',caseIds=['tcp-misconception','atomicity-reason'],repeats=1,maxCalls=2)

    def tearDown(self):
        for name in ('ai_executor','tutor_executor','live_eval_executor'):
            if name in self.app.extensions:self.app.extensions[name].shutdown(wait=True)
        self.tmp.cleanup()

    def start(self):return self.a.post(self.url,json=self.payload,headers=self.h)

    def test_recursive_credential_redaction_before_serialization_and_raw_content_preservation(self):
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        cases=[('sk-review-test-secret','plain'),('sk-review-test-secret','unicode'),
               ('sk-review-"quote\\secret','plain'),('sk-review-"quote\\secret','nested'),
               ('sk-review-"quote\\secret','all_unicode'),('sk-review-"quote\\secret','object_key'),
               ('sk-review-test-secret','malformed'),('sk-review-test-secret','unmatched_nested'),
               ('sk-review-test-secret','clean')]
        for index,(secret,kind) in enumerate(cases):
            with self.subTest(kind=kind,secret=secret):
                self.app.config['AI_API_KEY']=secret;self.payload['requestId']=f'redaction-request-{index:04}'
                summary=json.dumps({'nested':[secret]}) if kind=='nested' else secret
                if kind=='unmatched_nested':summary='"{"echo":"'+''.join(r'\u%04x'%ord(c) for c in secret)+'"}'
                raw=json.dumps(dict(tool='finish',args=dict(summary=summary)))
                if kind=='all_unicode':raw='{"tool":"finish","args":{"summary":"'+''.join(r'\u%04x'%ord(c) for c in secret)+'"}}'
                if kind=='object_key':raw=json.dumps(dict(tool='finish',args={secret:'echo','summary':secret}))
                if kind=='unicode':raw=raw.replace(secret,r'\u0073'+secret[1:])
                if kind=='malformed':raw='bad protocol '+raw.replace(secret,r'\u0073'+secret[1:])
                if kind=='clean':raw='  {"tool":"finish", "args":{"summary":"normal \\u0066inal"}}  '
                with patch('ai.call_model_response',return_value=dict(content=raw,usage=None,model='fixture-'+secret)):
                    e=self.start().json['evaluation']
                url=self.url+'/'+e['id']
                with sqlite3.connect(self.app.config['DATABASE']) as db:
                    persisted=json.loads(db.execute('SELECT report FROM tutor_live_evaluations WHERE id=?',(e['id'],)).fetchone()[0])
                views=[e['report'],persisted,self.a.get(url).json['evaluation']['report'],
                       self.a.get(self.url).json['evaluations'][0]['report'],self.a.get(url+'/blind').json['package']]
                def assert_safe(value):
                    if isinstance(value,dict):
                        for key,item in value.items():assert_safe(key);assert_safe(item)
                    elif isinstance(value,list):
                        for item in value:assert_safe(item)
                    elif isinstance(value,str):
                        self.assertNotIn(secret,value)
                        try:decoded=json.loads(value)
                        except ValueError:return
                        assert_safe(decoded)
                for view in views:assert_safe(view)
                entry=persisted['trials'][1]['steps'][0]
                if kind=='clean':
                    self.assertEqual(entry['content'],raw)
                    self.assertFalse(entry.get('contentRedacted',False))
                else:
                    self.assertIn('[REDACTED]',entry['content'])
                    self.assertTrue(entry.get('contentRedacted'))
                    if kind!='malformed':self.assertIn('[REDACTED]',json.loads(entry['content'])['args']['summary'])

    def test_unmatched_quotes_cannot_bypass_escaped_content_redaction(self):
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        secret='sk-OFFLINE-FAKE-ONLY';self.app.config['AI_API_KEY']=secret
        for index,text in enumerate((secret,'<think>PRIVATE_REVIEW_THOUGHT</think>')):
            self.payload['requestId']=f'unmatched-quote-request-{index:04}'
            encoded=''.join(r'\u%04x'%ord(c) for c in text)
            raw='"{"tool":"finish","args":{"summary":"'+encoded+'"}}'
            with patch('ai.call_model_response',return_value=dict(content=raw,usage=None,model='fixture')):
                e=self.start().json['evaluation']
            trial=e['report']['trials'][1];entry=trial['steps'][0]
            self.assertEqual(trial['status'],'failed');self.assertEqual(trial['modelCalls'],1)
            self.assertIsNone(entry['action']);self.assertIsNone(entry['result'])
            self.assertTrue(entry.get('contentRedacted'));self.assertIn('[REDACTED]',entry['content'])
            for view in (e,self.a.get(self.url).json,self.a.get(self.url+'/'+e['id']).json,
                         self.a.get(self.url+'/'+e['id']+'/blind').json):
                self.assertNotIn(raw,json.dumps(view,ensure_ascii=False))
                self.assertNotIn(text,json.dumps(view,ensure_ascii=False))
            with sqlite3.connect(self.app.config['DATABASE']) as db:
                saved=json.loads(db.execute('SELECT report FROM tutor_live_evaluations WHERE id=?',(e['id'],)).fetchone()[0])
            self.assertNotEqual(saved['trials'][1]['steps'][0]['content'],raw)

    def test_tagged_reasoning_not_persisted_or_exported_after_protocol_failure(self):
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        for index,raw in enumerate(('<think>PRIVATE_REVIEW_THOUGHT</think>\n{"tool":"finish","args":{"summary":"done"}}',
                                    '<analysis>PRIVATE_REVIEW_THOUGHT')):
            self.payload['requestId']=f'reasoning-request-{index:04}'
            with patch('ai.call_model_response',return_value=dict(content=raw,usage=None,model='fixture')):
                e=self.start().json['evaluation']
            trial=e['report']['trials'][1]
            self.assertEqual(trial['status'],'failed')
            self.assertIsNone(trial['steps'][0]['action'])
            self.assertTrue(trial['steps'][0].get('contentRedacted'))
            for value in (e,self.a.get(self.url).json,self.a.get(self.url+'/'+e['id']).json,
                          self.a.get(self.url+'/'+e['id']+'/blind').json):
                self.assertNotIn('PRIVATE_REVIEW_THOUGHT',json.dumps(value))
            self.assertNotIn(b'PRIVATE_REVIEW_THOUGHT',Path(self.app.config['DATABASE']).read_bytes())

    def test_cancel_wins_after_post_response_active_read_before_atomic_commit(self):
        import tutor_live_api
        self.app.config['LIVE_EVAL_RUN_INLINE']=False
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        checked,release=threading.Event(),threading.Event();original=tutor_live_api.run_report
        def gated(report,call,reserve,checkpoint,active,commit=None):
            def stale_active():
                yes=active();steps=report['trials'][1]['steps']
                if yes and steps and steps[-1].get('content') is not None and not checked.is_set():
                    checked.set();self.assertTrue(release.wait(5))
                return yes
            original(report,call,reserve,checkpoint,stale_active,**({'commit':commit} if commit else {}))
        usage=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5)
        with patch('tutor_live_api.run_report',side_effect=gated),patch('ai.call_model_response',return_value=
                   dict(content='{"tool":"finish","args":{"summary":"LATE_ACTION"}}',usage=usage,model='fixture')):
            e=self.start().json['evaluation']
            try:
                self.assertTrue(checked.wait(2))
                self.assertEqual(self.a.post(self.url+'/'+e['id']+'/cancel',headers=self.h).status_code,200)
            finally:release.set();self.app.extensions['live_eval_executor'].shutdown(wait=True)
        e=self.a.get(self.url+'/'+e['id']).json['evaluation'];trial=e['report']['trials'][1]
        self.assertEqual(e['status'],trial['status']);self.assertEqual(e['status'],'cancelled')
        self.assertEqual(trial['modelCalls'],1);self.assertEqual(trial['usage'],usage)
        self.assertIsNone(trial['steps'][0]['action']);self.assertIsNone(trial['steps'][0]['result'])
        self.assertFalse(trial['session']['trace'])
        self.assertFalse(any(x['type']=='finish' for x in trial['session']['events']))

    def test_cancel_after_reservation_checkpoint_prevents_adapter_dispatch(self):
        import tutor_live_api
        self.app.config['LIVE_EVAL_RUN_INLINE']=False
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        checked,release=threading.Event(),threading.Event();original=tutor_live_api.run_report
        def gated(report,call,reserve,checkpoint,active,commit=None):
            def reserved_checkpoint():
                checkpoint();steps=report['trials'][1]['steps']
                if steps and steps[-1].get('content') is None and not checked.is_set():
                    checked.set();self.assertTrue(release.wait(5))
            original(report,call,reserve,reserved_checkpoint,active,**({'commit':commit} if commit else {}))
        with patch('tutor_live_api.run_report',side_effect=gated),patch('ai.call_model_response',return_value=
                   dict(content='{"tool":"finish","args":{"summary":"late"}}',usage=None,model='fixture')) as adapter:
            e=self.start().json['evaluation']
            try:
                self.assertTrue(checked.wait(2))
                self.assertEqual(self.a.post(self.url+'/'+e['id']+'/cancel',headers=self.h).status_code,200)
            finally:release.set();self.app.extensions['live_eval_executor'].shutdown(wait=True)
        self.assertEqual(adapter.call_count,0)
        e=self.a.get(self.url+'/'+e['id']).json['evaluation'];trial=e['report']['trials'][1]
        self.assertEqual(e['modelCalls'],trial['modelCalls']);self.assertEqual(e['modelCalls'],1)
        self.assertEqual(trial['status'],'cancelled');self.assertIsNone(trial['usage'])
        self.assertFalse(trial['steps'][0].get('dispatchStarted',False))
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tutor_live_calls WHERE evaluation_id=?',(e['id'],)).fetchone()[0],1)

    def test_action_commit_wins_before_cancel_and_persists_entry_with_session(self):
        import tutor_engine
        self.app.config['LIVE_EVAL_RUN_INLINE']=False
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=1)
        applying,release,cancel_started,cancel_done=threading.Event(),threading.Event(),threading.Event(),threading.Event()
        original=tutor_engine.apply_action;responses=[]
        def gated(state,action):
            if action['tool']=='finish' and action['args']['summary']=='COMMITTED_ACTION':
                applying.set();self.assertTrue(release.wait(5))
            return original(state,action)
        with patch('tutor_engine.apply_action',side_effect=gated),patch('ai.call_model_response',return_value=
                   dict(content='{"tool":"finish","args":{"summary":"COMMITTED_ACTION"}}',usage=None,model='fixture')):
            e=self.start().json['evaluation']
            def cancel():
                cancel_started.set();responses.append(self.a.post(self.url+'/'+e['id']+'/cancel',headers=self.h));cancel_done.set()
            thread=threading.Thread(target=cancel)
            try:
                self.assertTrue(applying.wait(2));thread.start();self.assertTrue(cancel_started.wait(2))
                self.assertFalse(cancel_done.wait(.1),'cancel returned while response action was still uncommitted')
            finally:release.set();thread.join(3);self.app.extensions['live_eval_executor'].shutdown(wait=True)
        self.assertTrue(cancel_done.is_set());self.assertEqual(responses[0].status_code,200)
        trial=responses[0].json['evaluation']['report']['trials'][1]
        self.assertEqual(trial['session']['status'],'completed')
        self.assertEqual(trial['steps'][0]['action']['tool'],'finish')
        self.assertIsNotNone(trial['steps'][0]['result'])
        self.assertTrue(any(x['type']=='finish' for x in trial['session']['events']))

    def test_missing_config_validation_owner_and_idempotency_even_after_key_removed(self):
        self.assertEqual(self.a.get(self.url+'/dataset').status_code,200)
        self.app.config['AI_API_KEY']=''
        self.assertEqual(self.start().status_code,400)
        self.app.config['AI_API_KEY']='NEVER-PERSIST-SECRET'
        with patch('ai.call_model_response',return_value=dict(content='{"tool":"read_history","args":{}}',usage=None,model='actual')) as model:
            first=self.start();self.assertEqual(first.status_code,202,first.json)
        evaluation=first.json['evaluation'];self.assertEqual(model.call_count,2)
        self.assertEqual(evaluation['modelCalls'],2)
        self.assertEqual(evaluation['report']['summary']['agent']['trials'],2)
        self.app.config['AI_API_KEY']=''
        retry=self.start();self.assertEqual(retry.status_code,200,retry.json)
        self.assertEqual(retry.json['evaluation']['id'],evaluation['id'])
        self.assertEqual(self.a.post(self.url,json={**self.payload,'maxCalls':3},headers=self.h).status_code,409)
        self.assertEqual(self.b.get(self.url+'/'+evaluation['id']).status_code,404)
        self.assertEqual(self.a.post(self.url,json={**self.payload,'requestId':'new-request-0001','maxCalls':21},headers=self.h).status_code,400)
        raw=Path(self.app.config['DATABASE']).read_bytes()
        self.assertNotIn(b'NEVER-PERSIST-SECRET',raw)

    def test_review_cas_and_blind_export(self):
        with patch('ai.call_model_response',return_value=dict(content='{"tool":"finish","args":{"summary":"done"}}',usage=None,model='actual')):
            e=self.start().json['evaluation']
        url=self.url+'/'+e['id'];package=self.a.get(url+'/blind').json['package']
        blind=package['items'][0]['blindId']
        body=dict(version=e['version'],reviewer='rater-1',reviewerType='human',scores=dict(accuracy=1,grounding=2,diagnosis=0,actionability=1),notes='根据原文核对')
        rated=self.a.put(url+'/reviews/'+blind,json=body,headers=self.h)
        self.assertEqual(rated.status_code,200,rated.json)
        self.assertEqual(self.a.put(url+'/reviews/'+blind,json=body,headers=self.h).status_code,409)
        review=next(t['review'] for t in rated.json['evaluation']['report']['trials'] if t['blindId']==blind)
        self.assertEqual(review['reviewerType'],'human')
        body['version']=rated.json['evaluation']['version'];body['scores']['accuracy']=True
        self.assertEqual(self.a.put(url+'/reviews/'+blind,json=body,headers=self.h).status_code,400)
        self.assertEqual(self.b.get(url+'/blind').status_code,404)

    def test_cancel_late_response_restart_and_hourly_quota(self):
        self.app.config['LIVE_EVAL_RUN_INLINE']=False
        entered,release=threading.Event(),threading.Event()
        def model(*a,**kw):
            entered.set();release.wait(4)
            return dict(content='{"tool":"finish","args":{"summary":"late"}}',usage=None,model='actual')
        with patch('ai.call_model_response',side_effect=model):
            e=self.start().json['evaluation'];self.assertTrue(entered.wait(2))
            try:
                cancelled=self.a.post(self.url+'/'+e['id']+'/cancel',headers=self.h)
                self.assertEqual(cancelled.status_code,200,cancelled.json)
                self.assertEqual(self.a.post(self.url,json={**self.payload,'requestId':'busy-request-0001'},headers=self.h).status_code,409)
            finally:release.set();self.app.extensions['live_eval_executor'].shutdown(wait=True)
        e=self.a.get(self.url+'/'+e['id']).json['evaluation']
        self.assertEqual(e['status'],'cancelled')
        agent=next(t for t in e['report']['trials'] if t['strategy']=='agent')
        self.assertEqual(agent['status'],'cancelled');self.assertEqual(agent['modelCalls'],1)
        self.assertFalse(any(x['type']=='finish' for x in agent['session']['events']))
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.executemany("INSERT INTO tutor_live_calls VALUES (?,datetime('now'))",[(e['id'],)]*40)
            db.execute("UPDATE tutor_live_evaluations SET status='running' WHERE id=?",(e['id'],))
        for name in ('ai_executor','tutor_executor'):self.app.extensions[name].shutdown(wait=True)
        self.app=create_app({**self.app.config,'LIVE_EVAL_RUN_INLINE':True})
        self.assertEqual(self.a.get(self.url+'/'+e['id']).json['evaluation']['status'],'interrupted')
        self.a=self.app.test_client()
        # separate account quotas are tested below; original user is retained by cookie in original client

    def test_guest_login_migrates_report_and_replay(self):
        with patch('ai.call_model_response',return_value=dict(content='bad-json',usage=None,model='m')):e=self.start().json['evaluation']
        self.b.post('/api/auth/register',json=dict(name='Reader',email='live@example.test',password='test-password'),headers=self.h)
        self.assertEqual(self.a.post('/api/auth/login',json=dict(email='live@example.test',password='test-password'),headers=self.h).status_code,200)
        self.assertEqual(self.a.get(self.url+'/'+e['id']).status_code,200)
        self.assertEqual(self.start().json['evaluation']['id'],e['id'])

    def test_real_http_boundary_preserves_usage_and_all_six_tools(self):
        import ai
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        requests=[];reservations=[];database=self.app.config['DATABASE']
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(payload);data=json.loads(payload['messages'][-1]['content'])
                with sqlite3.connect(database) as db:
                    calls,raw_report=db.execute("SELECT model_calls,report FROM tutor_live_evaluations WHERE status='running'").fetchone()
                    ledger=db.execute('SELECT count(*) FROM tutor_live_calls').fetchone()[0]
                trial=next(t for t in json.loads(raw_report)['trials'] if t['status']=='running')
                reservations.append((calls,ledger,trial['steps'][-1]))
                if not data['historyRead']:action=dict(tool='read_history',args={})
                elif data['availableQuestions']:action=dict(tool='ask_question',args=dict(questionId=data['availableQuestions'][0]['id']))
                elif not data['evidence']:action=dict(tool='search_materials',args=dict(query='TCP 转账'))
                elif not data['feedbackGiven']:action=dict(tool='give_feedback',args=dict(message='仅供核对的反馈',evidenceIds=[data['evidence'][0]['evidenceId']]))
                elif not data['followed']:action=dict(tool='ask_followup',args=dict(prompt='解释你的理由'))
                else:action=dict(tool='finish',args=dict(summary='结束'))
                raw=json.dumps(dict(model='local-http-fixture',usage=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5),choices=[dict(message=dict(content=json.dumps(action)))] )).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        original=ai.call_model_response
        def local(settings,messages,**kwargs):return original({**settings,'baseUrl':f'http://127.0.0.1:{server.server_port}'},messages,**kwargs)
        self.payload['maxCalls']=20
        try:
            with patch('ai.call_model_response',side_effect=local):response=self.start()
        finally:server.shutdown();server.server_close();thread.join(2)
        self.assertEqual(response.status_code,202,response.json)
        e=response.json['evaluation'];self.assertEqual(e['modelCalls'],12)
        self.assertEqual(e['report']['summary']['agent']['passed'],2)
        for trial in e['report']['trials']:
            if trial['strategy']=='agent':
                self.assertEqual(trial['usage']['total_tokens'],30)
                tools={step['action']['tool'] for step in trial['steps'] if step['kind']=='model'}
                self.assertEqual(tools,{'read_history','ask_question','search_materials','give_feedback','ask_followup','finish'})
        self.assertTrue(all(r['max_tokens']==2000 and r['thinking']=={'type':'disabled'} for r in requests))
        self.assertEqual([(calls,ledger) for calls,ledger,entry in reservations],[(i,i) for i in range(1,13)])
        for calls,ledger,entry in reservations:
            self.assertTrue(entry['dispatchStarted'])
            self.assertIsNone(entry['content']);self.assertIsNone(entry['action'])
            self.assertIn('messages',entry)

    def test_failed_provider_usage_stays_unknown_and_restart_does_not_resume_reservations(self):
        self.payload.update(caseIds=['tcp-misconception'],maxCalls=2)
        known=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5)
        with patch('ai.call_model_response',side_effect=[
                dict(content='{"tool":"read_history","args":{}}',usage=known,model='fixture'),
                RuntimeError('NEVER-PERSIST-SECRET provider body')]):
            e=self.start().json['evaluation']
        trial=e['report']['trials'][1]
        self.assertEqual(trial['status'],'failed');self.assertIsNone(trial['usage'])
        self.assertEqual(trial['steps'][0]['usage'],known);self.assertIsNone(trial['steps'][1]['usage'])
        self.assertEqual(e['modelCalls'],2);self.assertEqual(trial['modelCalls'],2)
        self.assertNotIn('NEVER-PERSIST-SECRET',json.dumps(e))
        cookie_name=self.app.config['SESSION_COOKIE_NAME'];cookie=self.a.get_cookie(cookie_name).value
        for name in ('ai_executor','tutor_executor','live_eval_executor'):self.app.extensions[name].shutdown(wait=True)
        # Simulate a crash after reservations; startup must retain the ledger, never replay.
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.execute("UPDATE tutor_live_evaluations SET status='running' WHERE id=?",(e['id'],))
        with patch('ai.call_model_response',side_effect=AssertionError('no automatic paid resume')) as adapter:
            self.app=create_app({**self.app.config,'AI_API_KEY':''})
            self.a=self.app.test_client();self.a.set_cookie(cookie_name,cookie)
            restarted=self.a.get(self.url+'/'+e['id']).json['evaluation']
            self.assertEqual(restarted['status'],'interrupted');self.assertEqual(restarted['modelCalls'],2)
            self.assertEqual(self.start().json['evaluation']['id'],e['id'])
            self.assertEqual(adapter.call_count,0)
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tutor_live_calls WHERE evaluation_id=?',(e['id'],)).fetchone()[0],2)

    def test_persistent_hourly_budget_blocks_new_network_calls(self):
        with patch('ai.call_model_response',return_value=dict(content='bad-json',usage=None,model='m')):e=self.start().json['evaluation']
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.executemany("INSERT INTO tutor_live_calls VALUES (?,datetime('now'))",[(e['id'],)]*40)
        self.payload['requestId']='quota-request-0001'
        with patch('ai.call_model_response',side_effect=AssertionError('must not send')) as model:
            r=self.start();self.assertEqual(r.status_code,202,r.json)
        self.assertEqual(model.call_count,0)
        self.assertEqual(r.json['evaluation']['modelCalls'],0)
        self.assertEqual(r.json['evaluation']['report']['summary']['agent']['trials'],2)

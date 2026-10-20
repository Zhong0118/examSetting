"""Teaching sessions exercise real ownership, checkpoints and retry boundaries."""
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app


class TutorAPI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app({'TESTING':True,'DATABASE':str(Path(self.tmp.name)/'app.sqlite'),'TUTOR_RUN_INLINE':True,
                             'AI_API_KEY':'fixture-key','AI_BASE_URL':'https://api.example.com/v1','AI_ALLOWED_HOSTS':['api.example.com']})
        self.a,self.b=self.app.test_client(),self.app.test_client()
        self.headers={'X-Requested-With':'ExamHub'}
        q=lambda id,answer:dict(id=id,type='single',prompt='Which answer for '+id+'?',options=['A','B'],answer=answer,explanation='Original explanation '+id,source='',topic='Topic')
        r=self.a.post('/api/sets',json=dict(title='Tutor original',description='',topic='Topic',visibility='public',questions=[q('one','A'),q('two','B')]),headers=self.headers)
        self.set=r.json['set']
        self.counter=0

    def tearDown(self):
        for key in ('tutor_executor','ai_executor'):
            if key in self.app.extensions:self.app.extensions[key].shutdown(wait=True)
        self.tmp.cleanup()

    def start(self,mode='rule',request_id='session-request-0001',client=None):
        return (client or self.a).post('/api/tutor/sessions',json=dict(requestId=request_id,setId=self.set['id'],goal='Check my understanding',mode=mode,maxQuestions=2),headers=self.headers)

    def command(self,session,type,**extra):
        self.counter+=1
        return self.a.post('/api/tutor/sessions/'+session['id']+'/commands',json=dict(requestId='command-request-'+str(self.counter).zfill(5),version=session['version'],type=type,**extra),headers=self.headers)

    def test_rule_session_answers_snapshot_and_owner_isolation(self):
        response=self.start();self.assertEqual(response.status_code,202,response.json)
        s=response.json['session'];self.assertEqual(s['status'],'waiting')
        self.assertFalse(s['busy']);self.assertNotIn('answer',s['currentQuestion'])
        self.assertNotIn('questions',s)
        self.assertEqual(self.b.get('/api/tutor/sessions/'+s['id']).status_code,404)
        self.assertEqual(self.start().json['session']['id'],s['id'])
        self.assertEqual(self.a.delete('/api/sets/'+self.set['id'],headers=self.headers).status_code,200)
        s=self.command(s,'answer',answer='A',turnId=s['turnId']).json['session']
        self.assertEqual(s['status'],'waiting');self.assertEqual(s['currentQuestion']['id'],'two')
        s=self.command(s,'answer',answer='A',turnId=s['turnId']).json['session']
        self.assertEqual(s['status'],'completed');self.assertEqual(s['summary']['answered'],2)
        self.assertEqual(s['summary']['correct'],1);self.assertEqual(s['modelCalls'],0)

    def test_history_includes_prior_tutoring_answers_and_excludes_other_users(self):
        s=self.start().json['session']
        s=self.command(s,'answer',answer='A',turnId=s['turnId']).json['session']
        other=self.start('rule','other-user-history',self.b).json['session']
        self.b.post('/api/tutor/sessions/'+other['id']+'/commands',json=dict(requestId='other-answer-history',version=other['version'],type='answer',answer='A',turnId=other['turnId']),headers=self.headers)
        with patch('ai.call_model',side_effect=['{"tool":"read_history","args":{}}','{"tool":"ask_question","args":{"questionId":"one"}}']):
            resumed=self.start('agent','history-new-session').json['session']
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            state=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(resumed['id'],)).fetchone()[0])
        self.assertEqual(state['history'],dict(attempts=1,answered=1,correct=1))

    def test_answer_retry_replays_before_version_check_and_rejects_changed_body(self):
        s=self.start().json['session']
        body=dict(requestId='answer-request-0001',version=s['version'],type='answer',answer='A',turnId=s['turnId'])
        url='/api/tutor/sessions/'+s['id']+'/commands'
        first=self.a.post(url,json=body,headers=self.headers)
        retry=self.a.post(url,json=body,headers=self.headers)
        self.assertEqual(retry.status_code,200,retry.json)
        self.assertEqual(retry.json['session']['summary']['answered'],1)
        self.assertEqual(first.json['session']['turnId'],retry.json['session']['turnId'])
        self.assertEqual(self.a.post(url,json={**body,'answer':'B'},headers=self.headers).status_code,409)
        self.assertEqual(self.command(s,'answer',answer='B',turnId=s['turnId']).status_code,409)

    def test_agent_chooses_tools_and_counts_real_calls(self):
        actions=[dict(tool='read_history',args={}),dict(tool='ask_question',args={'questionId':'two'})]
        with patch('ai.call_model',side_effect=[json.dumps(a) for a in actions]) as model:
            r=self.start('agent')
        self.assertEqual(r.status_code,202,r.json)
        s=r.json['session'];self.assertEqual(s['currentQuestion']['id'],'two')
        self.assertEqual(s['modelCalls'],2);self.assertEqual(model.call_count,2)
        self.assertNotIn('fixture-key',json.dumps(s))

    def test_invalid_agent_action_pauses_and_resume_keeps_checkpoint(self):
        with patch('ai.call_model',return_value='{"tool":"delete_everything","args":{}}'):
            s=self.start('agent').json['session']
        self.assertEqual(s['status'],'paused');self.assertTrue(s['error'])
        with patch('ai.call_model',return_value='{"tool":"ask_question","args":{"questionId":"one"}}'):
            s=self.command(s,'resume').json['session']
        self.assertEqual(s['status'],'waiting');self.assertEqual(s['modelCalls'],2)

    def test_stop_suppresses_late_model_reply_and_busy_prevents_resume(self):
        self.app.config['TUTOR_RUN_INLINE']=False
        entered,release=threading.Event(),threading.Event()
        def held(*args):
            entered.set();release.wait(5)
            return '{"tool":"ask_question","args":{"questionId":"one"}}'
        with patch('ai.call_model',side_effect=held):
            s=self.start('agent').json['session'];self.assertTrue(entered.wait(2))
            s=self.a.get('/api/tutor/sessions/'+s['id']).json['session']
            try:
                stopped=self.command(s,'stop');self.assertEqual(stopped.status_code,200,stopped.json)
                self.assertEqual(self.command(stopped.json['session'],'resume').status_code,409)
            finally:release.set();self.app.extensions['tutor_executor'].shutdown(wait=True)
        s=self.a.get('/api/tutor/sessions/'+s['id']).json['session']
        self.assertEqual(s['status'],'paused');self.assertIsNone(s['pending']);self.assertFalse(s['busy'])

    def test_turn_and_session_call_budgets_are_enforced(self):
        with patch('ai.call_model',return_value='{"tool":"read_history","args":{}}') as model:
            s=self.start('agent').json['session']
        self.assertEqual(s['status'],'paused');self.assertEqual(model.call_count,6)
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            raw=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(s['id'],)).fetchone()[0]);raw['modelCalls']=32
            db.execute('UPDATE tutor_sessions SET state=? WHERE id=?',(json.dumps(raw),s['id']))
        with patch('ai.call_model',side_effect=AssertionError('budget exceeded')):
            response=self.command(s,'resume')
        self.assertIn(response.status_code,(400,409));self.assertEqual(response.json.get('session',{}).get('modelCalls',32),32)

    def test_hourly_call_quota_pauses_before_network_and_survives_restart(self):
        s=self.start().json['session']
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.executemany("INSERT INTO tutor_calls VALUES (?,datetime('now'))",[(s['id'],)]*40)
        with patch('ai.call_model',side_effect=AssertionError('must not call after quota')):
            result=self.start('agent','quota-session-0001')
        paused=result.json['session']
        self.assertEqual(paused['status'],'paused');self.assertEqual(paused['stopReason'],'rate_limit')
        self.assertEqual(paused['modelCalls'],0)
        self.app.extensions['tutor_executor'].shutdown(wait=True)
        self.app.extensions['ai_executor'].shutdown(wait=True)
        self.app=create_app(dict(self.app.config))
        with self.app.test_request_context():
            with sqlite3.connect(self.app.config['DATABASE']) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM tutor_calls').fetchone()[0],40)

    def test_restart_preserves_pending_answer_and_pauses_running_checkpoint(self):
        s=self.start().json['session']
        self.app.extensions['tutor_executor'].shutdown(wait=True)
        self.app.extensions['ai_executor'].shutdown(wait=True)
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            state=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(s['id'],)).fetchone()[0])
            state['status']='running'
            db.execute('UPDATE tutor_sessions SET state=? WHERE id=?',(json.dumps(state),s['id']))
        self.app=create_app(dict(self.app.config))
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            state=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(s['id'],)).fetchone()[0])
        self.assertEqual(state['status'],'paused');self.assertTrue(state['timingIncomplete'])
        self.assertEqual(state['pending']['questionId'],'one')

    def test_guest_login_migrates_checkpoint_and_idempotent_request(self):
        s=self.start().json['session']
        account=self.b.post('/api/auth/register',json=dict(name='Learner',email='tutor@example.test',password='test-password'),headers=self.headers)
        self.assertEqual(account.status_code,200,account.json)
        login=self.a.post('/api/auth/login',json=dict(email='tutor@example.test',password='test-password'),headers=self.headers)
        self.assertEqual(login.status_code,200,login.json)
        self.assertEqual(self.b.get('/api/tutor/sessions/'+s['id']).status_code,200)
        self.assertEqual(self.start().json['session']['id'],s['id'])

    def test_real_http_tool_decisions_retrieval_followup_and_finish(self):
        from http.server import BaseHTTPRequestHandler,HTTPServer
        import ai
        from tutor_engine import new_state,apply_action,submit_answer
        body={k:self.set[k] for k in ('title','description','topic','visibility','questions','version')}
        body['questions'][1]['source']='Atomicity means all operations succeed or none take effect.'
        updated=self.a.put('/api/sets/'+self.set['id'],json=body,headers=self.headers)
        self.assertEqual(updated.status_code,200,updated.json)
        probe=new_state(body['questions'],'goal','agent',2)
        apply_action(probe,dict(tool='ask_question',args={'questionId':'two'}))
        submit_answer(probe,'A',probe['turnId'])
        evidence=apply_action(probe,dict(tool='search_materials',args={'query':'Atomicity'}))['evidence'][0]['evidenceId']
        actions=[('read_history',{}),('ask_question',{'questionId':'two'}),
                 ('search_materials',{'query':'Atomicity'}),('give_feedback',{'message':'Review the all-or-nothing property.','evidenceIds':[evidence]}),
                 ('ask_followup',{'prompt':'Why did you choose that answer?'}),('ask_question',{'questionId':'one'}),
                 ('finish',{'summary':'Two questions completed; review the explanation for the second question.'})]
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(handler):
                payload=json.loads(handler.rfile.read(int(handler.headers['Content-Length'])))
                index=len(received);received.append(payload)
                tool,args=actions[index]
                handler.send_response(200);handler.send_header('Content-Type','application/json');handler.end_headers()
                handler.wfile.write(json.dumps({'choices':[{'message':{'content':json.dumps(dict(tool=tool,args=args))}}]}).encode())
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        original=ai.call_model
        def local(settings,messages):return original({**settings,'baseUrl':f'http://127.0.0.1:{server.server_port}/v1'},messages)
        try:
            with patch('ai.call_model',side_effect=local):
                s=self.start('agent').json['session']
                self.assertEqual(s['currentQuestion']['id'],'two')
                s=self.command(s,'answer',answer='A',turnId=s['turnId']).json['session']
                self.assertEqual(s['pending']['kind'],'followup')
                self.assertEqual(s['summary']['correct'],0)
                self.assertTrue(any(e['type']=='feedback' and e['evidence'] for e in s['events']))
                s=self.command(s,'answer',answer='I mixed up the two properties.',turnId=s['turnId']).json['session']
                self.assertEqual(s['currentQuestion']['id'],'one')
                s=self.command(s,'answer',answer='A',turnId=s['turnId']).json['session']
        finally:server.shutdown();server.server_close();worker.join()
        self.assertEqual(s['status'],'completed');self.assertEqual(s['modelCalls'],7)
        self.assertEqual(s['summary'],dict(answered=2,correct=1,objectiveTotal=2,followups=1))
        self.assertEqual(len(received),7)
        self.assertNotIn('Original explanation one',json.dumps(received[0]))

    def test_question_asked_on_call_32_can_resume_and_accept_answer_without_call_33(self):
        actions=['{"tool":"read_history","args":{}}']*31+['{"tool":"ask_question","args":{"questionId":"one"}}']
        with patch('ai.call_model',side_effect=actions) as model:
            s=self.start('agent').json['session']
            while s['status']=='paused':
                s=self.command(s,'resume').json['session']
            self.assertEqual(s['modelCalls'],32)
            s=self.command(s,'stop').json['session']
            restored=self.command(s,'resume');self.assertEqual(restored.status_code,200,restored.json)
            s=restored.json['session']
            answer=self.command(s,'answer',answer='A',turnId=s['turnId'])
            self.assertEqual(answer.status_code,200,answer.json)
            self.assertEqual(answer.json['session']['summary']['answered'],1)
            self.assertEqual(answer.json['session']['summary']['correct'],1)
            self.assertEqual(model.call_count,32)

    def test_quota_reservation_serializes_with_guest_login_migration(self):
        from concurrent.futures import ThreadPoolExecutor
        self.b.post('/api/auth/register',json=dict(name='Account',email='quota@example.test',password='test-password'),headers=self.headers)
        target=self.start('rule','target-quota-session',self.b).json['session']
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.executemany("INSERT INTO tutor_calls VALUES (?,datetime('now'))",[(target['id'],)]*40)
        entered,release,login_started,login_done=(threading.Event() for _ in range(4))
        original=sqlite3.connect
        class Gate(sqlite3.Connection):
            def execute(conn,sql,*args,**kwargs):
                if sql.startswith('SELECT count(*) FROM tutor_calls c JOIN') and threading.current_thread().name.startswith('examhub-tutor'):
                    entered.set();release.wait(5)
                if sql=='BEGIN IMMEDIATE' and threading.current_thread().name.startswith('login-check'):
                    login_started.set()
                return super().execute(sql,*args,**kwargs)
        def connect(*args,**kwargs):return original(*args,**dict(kwargs,factory=Gate))
        caller=self.app.test_client();caller.set_cookie('examhub_session',self.a.get_cookie('examhub_session').value)
        def login():
            try:return caller.post('/api/auth/login',json=dict(email='quota@example.test',password='test-password'),headers=self.headers)
            finally:login_done.set()
        self.app.config['TUTOR_RUN_INLINE']=False
        with patch('sqlite3.connect',side_effect=connect),patch('ai.call_model',return_value='{"tool":"ask_question","args":{"questionId":"one"}}'):
            with ThreadPoolExecutor(max_workers=1) as creators,ThreadPoolExecutor(max_workers=1,thread_name_prefix='login-check') as logins:
                creation=creators.submit(self.start,'agent','guest-quota-session')
                try:
                    self.assertTrue(entered.wait(2))
                    migration=logins.submit(login)
                    self.assertTrue(login_started.wait(2))
                    self.assertFalse(login_done.wait(.1),'login must not commit between quota owner lookup and reservation')
                finally:release.set()
                self.assertEqual(creation.result(timeout=3).status_code,202)
                self.assertEqual(migration.result(timeout=3).status_code,200)
            self.app.extensions['tutor_executor'].shutdown(wait=True)

    def test_rule_mode_needs_no_key_and_agent_reports_missing_configuration(self):
        self.app.config['AI_API_KEY']=''
        with patch('ai.call_model',side_effect=AssertionError('no configured model')):
            rule=self.start('rule')
            agent=self.start('agent','no-key-agent-request')
        self.assertEqual(rule.status_code,202,rule.json)
        self.assertEqual(rule.json['session']['modelCalls'],0)
        self.assertEqual(agent.status_code,400,agent.json)

import json
import sqlite3
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, g

try:
    from ai import validate_questions, register_ai, call_model
except ImportError:
    validate_questions = register_ai = None

SOURCE = 'TCP通过序列号标识字节，并使用确认与重传机制实现可靠传输。'
QUESTION = {'type': 'single', 'prompt': 'TCP 用什么标识字节？', 'options': ['序列号', '端口'], 'answer': '序列号', 'explanation': '序列号标识字节位置。', 'source': 'TCP通过序列号标识字节', 'topic': 'TCP'}

class QuestionValidationTests(unittest.TestCase):
    def test_accepts_supported_question_and_assigns_id(self):
        self.assertIsNotNone(validate_questions, 'Question validator must be implemented')
        result = validate_questions([QUESTION], SOURCE, 1)
        self.assertEqual(result[0]['answer'], '序列号')
        self.assertTrue(result[0]['id'])

    def test_rejects_invented_evidence(self):
        self.assertIsNotNone(validate_questions)
        with self.assertRaisesRegex(ValueError, '引用'):
            validate_questions([{**QUESTION, 'source': 'UDP也保证可靠传输'}], SOURCE, 1)

    def test_rejects_duplicate_and_invalid_correct_option(self):
        self.assertIsNotNone(validate_questions)
        with self.assertRaises(ValueError):
            validate_questions([QUESTION, QUESTION], SOURCE, 2)
        with self.assertRaises(ValueError):
            validate_questions([{**QUESTION, 'answer': '不存在'}], SOURCE, 1)

    def test_rejects_non_objects_and_missing_explanation(self):
        self.assertIsNotNone(validate_questions)
        for bad in [None, 42, {}, {**QUESTION, 'explanation': ''}]:
            with self.assertRaises(ValueError):
                validate_questions([bad], SOURCE, 1)


class ModelProtocolTests(unittest.TestCase):
    def test_real_http_adapter_sends_chat_contract_and_sanitizes_errors(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                received.append((self.path, payload, self.headers.get('Authorization')))
                if payload['model'] == 'denied':
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b'private-provider-details')
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'choices':[{'message':{'content':'{"questions": []}'}}]}).encode())
            def log_message(self, *args):
                pass
        server=HTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        config={'baseUrl':f'http://127.0.0.1:{server.server_port}/v1','model':'test','apiKey':'test-only-key'}
        try:
            self.assertEqual(call_model(config,[{'role':'user','content':'资料'}]),'{"questions": []}')
            self.assertEqual(received[0][0],'/v1/chat/completions')
            self.assertEqual(received[0][1]['messages'],[{'role':'user','content':'资料'}])
            self.assertEqual(received[0][2],'Bearer test-only-key')
            with self.assertRaisesRegex(ValueError,'模型鉴权失败'):
                call_model({**config,'model':'denied'},[])
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

class AIEndpointTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(register_ai, 'AI routes must be implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, DATABASE=str(Path(self.temp.name)/'test.db'), AI_ALLOWED_HOSTS=['api.example.com'], AI_RUN_INLINE=True, AI_API_KEY='', AI_BASE_URL='https://api.example.com/v1', AI_MODEL='test-model')
        @self.app.before_request
        def identity():
            from flask import request
            g.user = {'id': request.headers.get('Test-User', 'one')}
        register_ai(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        if hasattr(self, 'app') and 'ai_executor' in self.app.extensions:
            self.app.extensions['ai_executor'].shutdown(wait=True)
        if hasattr(self, 'temp'):
            self.temp.cleanup()

    def configure(self):
        return self.client.put('/api/ai/config', json={'baseUrl':'https://api.example.com/v1', 'model':'test-model', 'apiKey':'test-secret'}, headers={'X-Requested-With':'ExamHub'})

    def test_configuration_is_private_and_never_returns_key(self):
        self.assertEqual(self.configure().status_code, 200)
        own = self.client.get('/api/ai/config').get_json()
        other = self.client.get('/api/ai/config', headers={'Test-User':'two'}).get_json()
        self.assertTrue(own['configured'])
        self.assertFalse(other['configured'])
        self.assertNotIn('test-secret', json.dumps(own))

    def test_rejects_unsafe_model_url_and_missing_configuration(self):
        response = self.client.put('/api/ai/config', json={'baseUrl':'http://127.0.0.1/v1','model':'x','apiKey':'secret'}, headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.status_code,400)
        response = self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1}, headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.status_code,400)

    def test_completed_job_retains_questions_and_is_owner_only(self):
        self.configure()
        with patch('ai.call_model', return_value=json.dumps({'questions':[QUESTION]})):
            response = self.client.post('/api/ai/jobs', json={'source':SOURCE,'count':1,'topic':'TCP','title':'网络'}, headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.status_code,202)
        job_id = response.get_json()['job']['id']
        job = self.client.get('/api/ai/jobs/'+job_id).get_json()['job']
        self.assertEqual(job['status'],'completed')
        self.assertEqual(job['questions'][0]['answer'],'序列号')
        self.assertEqual(self.client.get('/api/ai/jobs/'+job_id,headers={'Test-User':'two'}).status_code,404)

    def test_provider_failure_is_persisted_without_secret(self):
        self.configure()
        with patch('ai.call_model', side_effect=RuntimeError('test-secret provider failure')):
            response = self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
        job = self.client.get('/api/ai/jobs/'+response.get_json()['job']['id']).get_json()['job']
        self.assertEqual(job['status'],'failed')
        self.assertNotIn('test-secret', json.dumps(job))
        self.assertEqual(job['questions'],[])

    def test_bad_input_is_client_error(self):
        self.configure()
        for payload in [[], {'source':SOURCE,'count':True}, {'source':SOURCE,'count':100}, {'source':3,'count':1}]:
            response = self.client.post('/api/ai/jobs',json=payload,headers={'X-Requested-With':'ExamHub'})
            self.assertEqual(response.status_code,400)

    def test_mutations_require_same_origin_client_header(self):
        response = self.client.put('/api/ai/config', json={'baseUrl':'https://api.example.com/v1','model':'test','apiKey':'secret'})
        self.assertEqual(response.status_code,403)

    def test_changing_provider_cannot_reuse_another_providers_key(self):
        self.configure()
        self.app.config['AI_ALLOWED_HOSTS'].append('other.example.com')
        response = self.client.put('/api/ai/config', json={'baseUrl':'https://other.example.com/v1','model':'test','apiKey':''},headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.client.get('/api/ai/config').get_json()['baseUrl'],'https://api.example.com/v1')

    def test_invalid_generation_gets_one_repair_and_cannot_complete_as_bad_questions(self):
        self.configure()
        with patch('ai.call_model', side_effect=[json.dumps({'questions':[{**QUESTION,'source':'invented'}]}), json.dumps({'questions':[QUESTION]})]) as provider:
            response = self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
        job=response.get_json()['job']
        self.assertEqual(job['status'],'completed')
        self.assertEqual(provider.call_count,2)
        with patch('ai.call_model',return_value='not JSON') as provider:
            response=self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.get_json()['job']['status'],'failed')
        self.assertEqual(provider.call_count,2)

    def test_cancelled_job_cannot_publish_late_provider_result(self):
        self.configure()
        self.app.config['AI_RUN_INLINE']=False
        started, release = threading.Event(), threading.Event()
        def provider(*args):
            started.set()
            release.wait(5)
            return json.dumps({'questions':[QUESTION]})
        with patch('ai.call_model',side_effect=provider):
            response=self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
            self.assertTrue(started.wait(5))
            job_id=response.get_json()['job']['id']
            try:
                duplicate=self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
                self.assertEqual(duplicate.status_code,429)
                self.assertEqual(self.client.delete('/api/ai/jobs/'+job_id,headers={'Test-User':'two','X-Requested-With':'ExamHub'}).status_code,404)
                self.assertEqual(self.client.delete('/api/ai/jobs/'+job_id,headers={'X-Requested-With':'ExamHub'}).get_json()['job']['status'],'cancelled')
                still_busy=self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1},headers={'X-Requested-With':'ExamHub'})
                self.assertEqual(still_busy.status_code,429, 'Cancellation must not release a provider call still in flight')
            finally:
                release.set()
                self.app.extensions['ai_executor'].shutdown(wait=True)
        job=self.client.get('/api/ai/jobs/'+job_id).get_json()['job']
        self.assertEqual(job['status'],'cancelled')
        self.assertEqual(job['questions'],[])

    def test_restart_marks_incomplete_jobs_as_failed(self):
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.execute("INSERT INTO ai_jobs(id,user_id,status,created_at) VALUES ('old','one','running','2026-10-20')")
        other=Flask('restarted')
        other.config.update(self.app.config)
        register_ai(other)
        with sqlite3.connect(other.config['DATABASE']) as db:
            row=db.execute("SELECT status,error FROM ai_jobs WHERE id='old'").fetchone()
        self.assertEqual(row[0],'failed')
        self.assertIn('重启',row[1])
        other.extensions['ai_executor'].shutdown(wait=True)

if __name__ == '__main__':
    unittest.main()

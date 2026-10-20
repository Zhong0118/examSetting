"""Actual PDF parsing, database and local HTTP generation form one acceptance flow."""
import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
from tests.test_documents import pdf_fixture

PAGE1='TCP is a transport protocol that provides an ordered byte stream.'
PAGE2='Database transactions are atomic: all operations succeed together or none take effect.'


def question():
    return dict(type='single',prompt='Which property makes a transaction all-or-nothing?',
                options=['Atomicity','Indexing'],answer='Atomicity',explanation='Atomicity groups all changes into one outcome.',
                source=PAGE2,topic='Transactions',page=2)


class V2Acceptance(unittest.TestCase):
    def test_cancelled_run_cannot_be_compared_until_metrics_are_final(self):
        doc=self.upload()
        data=dict(documentId=doc['id'],startPage=1,endPage=2,count=1)
        with patch('ai.call_model',return_value=json.dumps({'questions':[question()]})):
            baseline=self.post('/api/ai/jobs',{**data,'strategy':'baseline'}).json['job']
        self.app.config['AI_RUN_INLINE']=False
        entered,release=threading.Event(),threading.Event()
        def held(*args):
            entered.set();release.wait(5)
            return json.dumps({'questions':[question()]})
        with patch('ai.call_model',side_effect=held):
            request={**data,'strategy':'grounded','requestId':'cancelled-grounded-001'}
            active=self.post('/api/ai/jobs',request).json['job']
            self.assertTrue(entered.wait(2))
            try:
                retry=self.post('/api/ai/jobs',request)
                self.assertEqual(retry.status_code,200,retry.json)
                self.assertEqual(retry.json['job']['id'],active['id'])
                self.assertEqual(self.post('/api/ai/jobs',request,self.b).status_code,404)
                cancelled=self.a.delete('/api/ai/jobs/'+active['id'],headers=self.headers)
                self.assertEqual(cancelled.json['job']['status'],'cancelled')
                response=self.post('/api/evaluations',{'jobIds':[baseline['id'],active['id']]})
                self.assertEqual(response.status_code,409,response.json)
            finally:
                release.set();self.app.extensions['ai_executor'].shutdown(wait=True)
        final=self.a.get('/api/ai/jobs/'+active['id']).json['job']
        saved=self.post('/api/evaluations',{'jobIds':[baseline['id'],active['id']]})
        self.assertEqual(saved.status_code,201,saved.json)
        run=next(r for r in saved.json['evaluation']['runs'] if r['strategy']=='grounded')
        self.assertEqual(run['elapsedMs'],final['metadata']['elapsedMs'])
        self.assertEqual(run['modelCalls'],1)

    def setUp(self):
        from app import create_app
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_app({'TESTING':True,'DATABASE':str(Path(self.tmp.name)/'app.sqlite'),
                            'AI_RUN_INLINE':True,'AI_API_KEY':'local-test-key','AI_BASE_URL':'https://api.example.com/v1',
                            'AI_ALLOWED_HOSTS':['api.example.com'],'AI_MODEL':'test-model'})
        self.a,self.b=self.app.test_client(),self.app.test_client()
        self.headers={'X-Requested-With':'ExamHub'}

    def tearDown(self):
        self.app.extensions['ai_executor'].shutdown(wait=True)
        self.tmp.cleanup()

    def post(self,path,data,client=None):
        return (client or self.a).post(path,json=data,headers=self.headers)

    def upload(self):
        r=self.a.post('/api/documents',data={'file':(io.BytesIO(pdf_fixture([PAGE1,PAGE2])),'original-notes.pdf')},headers=self.headers)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['document']

    def test_pdf_to_generation_comparison_citation_practice_and_deleted_source_history(self):
        from ai import call_model
        doc=self.upload()
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(handler):
                payload=json.loads(handler.rfile.read(int(handler.headers['Content-Length'])))
                received.append(payload)
                q=question()
                # Deliberately wrong page; grounded strategy needs a real second request to repair it.
                if len(payload['messages'])<4: q['page']=1
                handler.send_response(200);handler.send_header('Content-Type','application/json');handler.end_headers()
                handler.wfile.write(json.dumps({'choices':[{'message':{'content':json.dumps({'questions':[q]})}}]}).encode())
            def log_message(self,*args): pass
        server=HTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        def local_model(settings,messages):
            return call_model({**settings,'baseUrl':f'http://127.0.0.1:{server.server_port}/v1'},messages)
        try:
            jobs=[]
            with patch('ai.call_model',side_effect=local_model):
                for strategy in ('baseline','grounded'):
                    r=self.post('/api/ai/jobs',dict(documentId=doc['id'],startPage=1,endPage=2,count=1,strategy=strategy))
                    self.assertEqual(r.status_code,202,r.json)
                    self.assertEqual(r.json['job']['status'],'completed',r.json)
                    jobs.append(r.json['job'])
        finally:
            server.shutdown();server.server_close();worker.join()
        self.assertEqual(len(received),3)
        self.assertIn('pages',json.loads(received[0]['messages'][1]['content']))
        self.assertEqual(jobs[0]['quality']['citationCoverage'],0)
        self.assertEqual(jobs[1]['quality']['citationCoverage'],1)
        self.assertEqual(jobs[1]['metadata']['modelCalls'],2)
        comparison=self.post('/api/evaluations',{'jobIds':[j['id'] for j in jobs]})
        self.assertEqual(comparison.status_code,201,comparison.json)
        evaluation=comparison.json['evaluation']
        retry=self.post('/api/evaluations',{'jobIds':[j['id'] for j in reversed(jobs)]})
        self.assertEqual(retry.status_code,200,retry.json)
        self.assertEqual(retry.json['evaluation'],evaluation)
        self.assertEqual(evaluation['kind'],'generation-comparison')
        self.assertEqual(self.b.get('/api/evaluations/'+evaluation['id']).status_code,404)
        self.assertEqual(len(self.a.get('/api/evaluations').json['evaluations']),1)
        q=jobs[1]['questions'][0]
        self.assertEqual(q['citation']['page'],2)
        body=dict(title='Grounded notes',description='',topic='Database',visibility='public',questions=[q])
        created=self.post('/api/sets',body)
        self.assertEqual(created.status_code,201,created.json)
        url='/api/sets/'+created.json['set']['id']
        self.assertEqual(self.b.get(url).json['set']['questions'][0]['citation'],q['citation'])
        self.assertEqual(self.b.get('/api/documents/'+doc['id']+'/file').status_code,404)
        practice=self.b.get(url+'/practice').json['questions'][0]
        self.assertFalse({'source','citation','answer','explanation'} & practice.keys())
        attempt=self.post(url+'/attempts',{'version':1,'answers':{q['id']:'Atomicity'}},self.b).json['attempt']
        self.assertEqual(attempt['results'][0]['citation'],q['citation'])
        self.assertEqual(self.a.get(url+'/quality').json['report']['passed'],1)
        fork=self.post(url+'/fork',{},self.b).json['set']
        fork_body={k:fork[k] for k in ('title','description','topic','visibility','questions','version')}
        fork_body['title']='My fork'
        saved=self.b.put('/api/sets/'+fork['id'],json=fork_body,headers=self.headers)
        self.assertEqual(saved.status_code,200,saved.json)
        self.assertEqual(self.a.delete('/api/documents/'+doc['id'],headers=self.headers).status_code,200)
        self.assertEqual(self.a.get('/api/documents/'+doc['id']+'/file').status_code,404)
        body['version']=1
        self.assertEqual(self.a.put(url,json=body,headers=self.headers).status_code,200)
        history=self.b.get('/api/attempts').json['attempts'][0]
        self.assertEqual(history['results'][0]['citation'],q['citation'])
        self.assertEqual(self.a.get('/api/evaluations/'+evaluation['id']).json['evaluation'],evaluation)

    def test_manual_citation_tampering_and_guest_document_migration(self):
        doc=self.upload(); q=question(); q.pop('page'); q['id']='manual'
        q['citation']=dict(documentId=doc['id'],documentTitle=doc['title'],documentHash=doc['sha256'],page=2,quote=PAGE2)
        body=dict(title='Manual evidence',description='',topic='',visibility='private',questions=[q])
        for bad in ({**q['citation'],'page':1},{**q['citation'],'documentHash':'f'*64},{**q['citation'],'quote':'invented'}):
            r=self.post('/api/sets',{**body,'questions':[{**q,'citation':bad}]})
            self.assertEqual(r.status_code,400,r.json)
        self.assertEqual(self.post('/api/sets',body).status_code,201)
        target=self.post('/api/auth/register',dict(name='Account',email='v2@example.test',password='test-password'),self.b).json['user']
        self.assertEqual(self.post('/api/auth/login',dict(email='v2@example.test',password='test-password')).status_code,200)
        self.assertEqual(self.a.get('/api/session').json['user']['id'],target['id'])
        self.assertEqual(self.a.get('/api/documents/'+doc['id']).status_code,200)
        self.assertEqual(self.b.get('/api/documents/'+doc['id']).status_code,200)

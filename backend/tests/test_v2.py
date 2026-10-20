"""V2 evidence tests use original content and controlled model boundaries."""
import json
import sqlite3
import unittest
from unittest.mock import patch
from tests import test_ai as ai_tests
QUESTION, SOURCE = ai_tests.QUESTION, ai_tests.SOURCE
from ai import validate_questions

PDF = {'document': {'id': 'doc-one', 'title': 'Original notes', 'sha256': 'a'*64},
       'pages': [{'page': 1, 'text': 'UDP uses datagrams.'}, {'page': 2, 'text': SOURCE}],
       'source': 'UDP uses datagrams.\n' + SOURCE}


class PDFGroundingTests(unittest.TestCase):
    def test_correct_page_creates_server_metadata_and_ignores_model_claims(self):
        result = validate_questions([{**QUESTION, 'page': 2, 'citation': {'documentId': 'forged'}}],
                                    PDF['source'], 1, pdf=PDF)[0]
        self.assertEqual(result['citation'], dict(documentId='doc-one', documentTitle='Original notes',
                         documentHash='a'*64, page=2, quote=QUESTION['source']))

    def test_quote_on_another_page_and_unselected_pages_are_rejected(self):
        for page in (1, 3, True, '2'):
            with self.assertRaises(ValueError):
                validate_questions([{**QUESTION, 'page': page}], PDF['source'], 1, pdf=PDF)

    def test_pdf_whitespace_and_unicode_normalization_keep_quote_verifiable(self):
        doc = {**PDF, 'pages': [{'page': 2, 'text': 'ＴＣＰ uses\n sequence   numbers.'}]}
        q = {**QUESTION, 'page': 2, 'source': 'TCP uses sequence numbers.'}
        result = validate_questions([q], doc['pages'][0]['text'], 1, pdf=doc)
        self.assertEqual(result[0]['citation']['page'], 2)

    def test_baseline_keeps_uncited_output_without_fabricating_verified_citation(self):
        result = validate_questions([{**QUESTION, 'page': 1}], PDF['source'], 1, pdf=PDF, strategy='baseline')
        self.assertIsNone(result[0].get('citation'))


class V2Jobs(unittest.TestCase):
    setUp = ai_tests.AIEndpointTests.setUp
    tearDown = ai_tests.AIEndpointTests.tearDown
    configure = ai_tests.AIEndpointTests.configure

    def test_retry_request_id_returns_original_job_without_model_or_source_access(self):
        self.configure()
        body=dict(documentId='doc-one',startPage=1,endPage=2,count=1,requestId='comparison-baseline-001')
        headers={'X-Requested-With':'ExamHub'}
        with patch('documents.selection',return_value=PDF),patch('ai.call_model',return_value=json.dumps({'questions':[{**QUESTION,'page':2}]})) as model:
            first=self.client.post('/api/ai/jobs',json=body,headers=headers)
        self.assertEqual(first.status_code,202,first.json)
        self.app.extensions['ai_credentials'].clear()
        with patch('documents.selection',side_effect=AssertionError('Retry must not reread deleted PDF')),patch('ai.call_model',side_effect=AssertionError('Retry must not call model')):
            retry=self.client.post('/api/ai/jobs',json=body,headers=headers)
            conflict=self.client.post('/api/ai/jobs',json={**body,'count':2},headers=headers)
        self.assertEqual(retry.status_code,200,retry.json)
        self.assertEqual(retry.json['job']['id'],first.json['job']['id'])
        self.assertEqual(conflict.status_code,409,conflict.json)
        self.assertEqual(model.call_count,1)

    def test_pdf_request_loads_owner_pages_and_repairs_wrong_page_once(self):
        self.configure()
        wrong = {**QUESTION, 'page': 1}
        good = {**QUESTION, 'page': 2}
        with patch('documents.selection', return_value=PDF) as selection, patch('ai.call_model', side_effect=[json.dumps({'questions':[wrong]}), json.dumps({'questions':[good]})]):
            response=self.client.post('/api/ai/jobs',json={'documentId':'doc-one','startPage':1,'endPage':2,'count':1},headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(response.status_code,202,response.json)
        job=response.json['job']
        self.assertEqual(job['status'],'completed',job)
        selection.assert_called_once_with('doc-one', 'one', 1, 2)
        self.assertEqual(job['metadata']['modelCalls'],2)
        self.assertEqual(job['metadata']['pages'],[1,2])
        self.assertEqual(job['questions'][0]['citation']['page'],2)
        self.assertEqual(job['quality']['citationCoverage'],1)
        self.assertNotIn('test-secret',json.dumps(job))

    def test_metadata_records_failed_and_baseline_run_attempts(self):
        self.configure()
        for strategy, calls in [('baseline',1),('grounded',2)]:
            with patch('documents.selection',return_value=PDF),patch('ai.call_model',return_value='not json') as model:
                r=self.client.post('/api/ai/jobs',json={'documentId':'doc-one','startPage':1,'endPage':2,'count':1,'strategy':strategy},headers={'X-Requested-With':'ExamHub'})
            self.assertEqual(r.status_code,202,r.json)
            self.assertEqual(r.json['job']['status'],'failed')
            self.assertEqual(model.call_count,calls)
            self.assertEqual(r.json['job']['metadata']['modelCalls'],calls)
            self.assertGreaterEqual(r.json['job']['metadata']['elapsedMs'],0)

    def test_unknown_strategy_is_rejected(self):
        self.configure()
        r=self.client.post('/api/ai/jobs',json={'source':SOURCE,'count':1,'strategy':'imaginary'},headers={'X-Requested-With':'ExamHub'})
        self.assertEqual(r.status_code,400)

    def test_old_jobs_migrate_with_safe_empty_metadata(self):
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            columns={r[1] for r in db.execute('pragma table_info(ai_jobs)')}
        self.assertTrue({'metadata','quality'} <= columns)

    def test_restart_marks_unfinished_timing_unknown_instead_of_zero(self):
        from flask import Flask
        from ai import register_ai
        with sqlite3.connect(self.app.config['DATABASE']) as db:
            db.execute("INSERT INTO ai_jobs(id,user_id,status,created_at,metadata) VALUES ('interrupted','one','running','now',?)",
                       (json.dumps({'metricsFinalized':False,'elapsedMs':0,'modelCalls':1}),))
        other=Flask('timing-restart');other.config.update(self.app.config)
        register_ai(other)
        with sqlite3.connect(other.config['DATABASE']) as db:
            status,raw=db.execute("SELECT status,metadata FROM ai_jobs WHERE id='interrupted'").fetchone()
        meta=json.loads(raw)
        self.assertEqual(status,'failed')
        self.assertIsNone(meta['elapsedMs'])
        self.assertTrue(meta['metricsFinalized'])
        self.assertTrue(meta['timingIncomplete'])
        self.assertEqual(meta['modelCalls'],1)
        other.extensions['ai_executor'].shutdown(wait=True)

class PracticeEvidenceTests(unittest.TestCase):
    def test_practice_hides_source_while_author_detail_and_history_retain_it(self):
        import tempfile
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            app=create_app({'TESTING':True,'DATABASE':directory+'/test.db'})
            client=app.test_client()
            headers={'X-Requested-With':'ExamHub'}
            q={**QUESTION,'id':'q1','source':'The answer is sequence numbers.'}
            created=client.post('/api/sets',json={'title':'Evidence','description':'','topic':'TCP','visibility':'public','questions':[q]},headers=headers).json['set']
            url='/api/sets/'+created['id']
            self.assertEqual(client.get(url).json['set']['questions'][0]['source'],q['source'])
            practice=client.get(url+'/practice').json['questions'][0]
            self.assertNotIn('source',practice)
            self.assertNotIn('citation',practice)
            result=client.post(url+'/attempts',json={'version':1,'answers':{'q1':'序列号'}},headers=headers).json['attempt']
            self.assertEqual(result['results'][0]['source'],q['source'])
            app.extensions['ai_executor'].shutdown(wait=True)

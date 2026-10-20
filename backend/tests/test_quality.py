"""Quality rules and persisted evaluation boundary regressions; no model calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from flask import Flask, g
from werkzeug.exceptions import HTTPException
from db import close_db, get_db, init_db

QUALITY_AVAILABLE = importlib.util.find_spec('quality') is not None
if QUALITY_AVAILABLE:
    from quality import evaluate_questions


def question(**changes):
    value = dict(id='q1', type='single', prompt='Which protocol supplies a reliable byte stream?',
                 options=['TCP', 'UDP'], answer='TCP', explanation='TCP provides ordered bytes and retransmission.',
                 source='TCP provides reliable bytes.', topic='Networking')
    value.update(changes)
    return value


def citation(**changes):
    value = dict(documentId='doc1', documentTitle='Original notes', documentHash='a'*64,
                 page=2, quote='TCP provides reliable bytes.')
    value.update(changes)
    return value


class QualityRules(unittest.TestCase):
    def setUp(self):
        self.assertTrue(QUALITY_AVAILABLE, 'quality.evaluate_questions must be implemented')

    def test_grounded_report_checks_normalized_quotes_and_exact_schema(self):
        q = question(citation=citation())
        original = copy.deepcopy(q)
        report = evaluate_questions([q], {2: 'ＴＣＰ  provides\nreliable bytes.'})
        self.assertEqual(set(report), {'ruleVersion','total','passed','passRate','citationCoverage','duplicatePairs','items','limits'})
        self.assertEqual((report['total'], report['passed'], report['passRate'], report['citationCoverage']), (1,1,1,1))
        self.assertEqual(q, original)
        self.assertEqual(set(report['items'][0]), {'questionId','passed','checks'})
        self.assertTrue(all(set(c) == {'code','status','message'} for c in report['items'][0]['checks']))

    def test_bad_answer_explanation_page_quote_and_source_each_fail(self):
        for change in [dict(answer='ICMP'), dict(explanation=''), dict(options=['TCP','ＴＣＰ']),
                       dict(citation=citation(page=1)), dict(citation=citation(quote='Invented quotation')),
                       dict(source='different'), dict(citation=None)]:
            with self.subTest(change=change):
                report = evaluate_questions([question(citation=citation(), **{}) | change], {2:'TCP provides reliable bytes.'})
                self.assertEqual(report['passed'], 0)
                self.assertTrue(any(c['status']=='fail' for c in report['items'][0]['checks']))

    def test_snapshot_mode_warns_and_never_claims_live_verification(self):
        report = evaluate_questions([question(citation=citation())])
        self.assertEqual(report['passed'],1)
        self.assertTrue(any(c['status']=='warn' for c in report['items'][0]['checks']))
        self.assertTrue(report['limits'])
        self.assertEqual(evaluate_questions([question()])['citationCoverage'],0)

    def test_exact_and_lexical_duplicates_fail_both_items(self):
        for prompt in ['Which protocol supplies a reliable byte stream?', 'Which protocol supplies a reliable byte stream now?']:
            report = evaluate_questions([question(), question(id='q2', prompt=prompt)])
            self.assertEqual(report['passed'],0)
            self.assertEqual(len(report['duplicatePairs']),1)
            pair=report['duplicatePairs'][0]
            self.assertEqual((pair['left'],pair['right']),('q1','q2'))
            self.assertGreaterEqual(pair['similarity'],0.85)
        self.assertFalse(evaluate_questions([question(),question(id='q2',prompt='What distinguishes physical from virtual memory?')])['duplicatePairs'])

    def test_malformed_items_and_empty_input_are_bounded_reports(self):
        for item in [None, [], {}, question(options=[{}]), question(citation=[]), question(type=[]), question(id=[])]:
            report=evaluate_questions([item])
            self.assertEqual(report['passed'],0)
        report=evaluate_questions([])
        self.assertEqual((report['total'],report['passRate'],report['citationCoverage']),(0,0,0))
        with self.assertRaises(ValueError):
            evaluate_questions([question()]*101)


class EvaluationRoutes(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('evaluations'), 'evaluations module must be implemented')
        from evaluations import register_evaluations
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app=Flask(__name__)
        self.app.config.update(TESTING=True,DATABASE=self.tmp.name+'/test.sqlite')
        self.app.teardown_appcontext(close_db)
        @self.app.before_request
        def identity():
            from flask import request
            g.user={'id':request.headers.get('Test-User','one')}
        @self.app.errorhandler(HTTPException)
        def error(exc):
            return {'error':exc.description},exc.code
        with self.app.app_context():
            init_db()
            db=get_db()
            db.execute("INSERT INTO users(id,name) VALUES ('one','One'),('two','Two')")
            db.execute('CREATE TABLE ai_jobs(id TEXT PRIMARY KEY,user_id TEXT,status TEXT,error TEXT,questions TEXT,created_at TEXT,metadata TEXT,quality TEXT)')
            from documents import SCHEMA
            db.executescript(SCHEMA)
            pages=[dict(page=1,text='Unrelated page',charCount=14),dict(page=2,text='TCP provides reliable bytes.',charCount=27)]
            db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',('doc1','one','Original notes','notes.pdf','a'*64,2,2,'2026-10-20','[]',json.dumps(pages),'unused.pdf'))
            db.commit()
        register_evaluations(self.app)
        self.client=self.app.test_client()

    def post(self,path,data=None,user='one'):
        return self.client.post(path,json=data,headers={'X-Requested-With':'ExamHub','Test-User':user})

    def jobs(self, **override):
        metadata=dict(strategy='baseline',documentId='doc1',pages=[1,2],sourceHash='b'*64,count=2,model='local-test',elapsedMs=12,modelCalls=1)
        with self.app.app_context():
            db=get_db()
            for jid,strategy in [('base','baseline'),('ground','grounded')]:
                meta=dict(metadata,strategy=strategy)
                if jid=='ground': meta.update(override)
                db.execute('INSERT OR REPLACE INTO ai_jobs VALUES (?,?,?,?,?,?,?,?)',(jid,'one','completed',None,json.dumps([question(),question(id='q2')]),'2026-10-20',json.dumps(meta),json.dumps({'passRate':0.5,'citationCoverage':0.5})))
            db.commit()

    def test_failed_run_stays_in_snapshot_with_zero_quality_and_owner_isolation(self):
        self.jobs()
        with self.app.app_context():
            get_db().execute("UPDATE ai_jobs SET status='failed',error='provider failed' WHERE id='ground'")
            get_db().commit()
        response=self.post('/api/evaluations',{'jobIds':['ground','base']})
        self.assertEqual(response.status_code,201,response.json)
        snapshot=response.json['evaluation']
        self.assertEqual(set(snapshot),{'id','createdAt','kind','documentTitle','sourceHash','pages','count','model','runs','limitations'})
        self.assertEqual([r['strategy'] for r in snapshot['runs']],['baseline','grounded'])
        self.assertEqual([(r['questionCount'],r['passRate'],r['citationCoverage']) for r in snapshot['runs']],[(2,0.5,0.5),(0,0,0)])
        self.assertEqual(snapshot['runs'][1]['modelCalls'],1)
        path='/api/evaluations/'+snapshot['id']
        self.assertEqual(self.client.get(path,headers={'Test-User':'two'}).status_code,404)
        with self.app.app_context():
            get_db().execute('DELETE FROM ai_jobs');get_db().commit()
        self.assertEqual(self.client.get(path).json['evaluation'],snapshot)
        self.assertEqual(self.client.get('/api/evaluations').json['evaluations'],[snapshot])
        self.assertEqual(self.client.get('/api/evaluations',headers={'Test-User':'two'}).json['evaluations'],[])

    def test_comparisons_reject_mismatches_nonterminal_other_owner_and_text_jobs(self):
        for mismatch in [dict(model='other'),dict(documentId='other'),dict(sourceHash='c'*64),dict(pages=[2]),dict(count=3),dict(strategy='baseline'),dict(documentId=None),dict(title='changed'),dict(topic='changed'),dict(provider='https://other.example'),dict(promptVersion='changed')]:
            self.jobs(**mismatch)
            self.assertEqual(self.post('/api/evaluations',{'jobIds':['base','ground']}).status_code,400,mismatch)
        self.jobs()
        for status in ['queued','running']:
            with self.app.app_context():
                get_db().execute('UPDATE ai_jobs SET status=? WHERE id=?',(status,'ground'));get_db().commit()
            self.assertEqual(self.post('/api/evaluations',{'jobIds':['base','ground']}).status_code,409)
        self.assertEqual(self.post('/api/evaluations',{'jobIds':['base','ground']},user='two').status_code,404)
        for payload in [None,{}, {'jobIds':['base','base']},{'jobIds':[{},[]]}]:
            self.assertEqual(self.post('/api/evaluations',payload).status_code,400)

    def test_benchmark_reports_actual_confusion_counts_and_content_hash(self):
        response=self.post('/api/evaluations/benchmark',{})
        self.assertEqual(response.status_code,200,response.json)
        report=response.json['report']
        raw=Path(__file__).resolve().parents[1].joinpath('eval_fixtures.json').read_bytes()
        fixtures=json.loads(raw)
        self.assertGreaterEqual(report['sampleCount'],8)
        self.assertEqual(report['datasetHash'],hashlib.sha256(raw).hexdigest())
        self.assertEqual([r['name'] for r in report['strategies']],['structural-v1','grounded-v2'])
        labels={s['id']:s['label'] for s in fixtures['samples']}
        for strategy in report['strategies']:
            self.assertEqual(sum(strategy[k] for k in ['tp','fp','fn','tn']),report['sampleCount'])
            for sample in strategy['samples']:
                self.assertEqual(sample['label'],labels[sample['id']])
                original=next(s for s in fixtures['samples'] if s['id']==sample['id'])
                self.assertEqual(sample['questions'],original['questions'])
                self.assertEqual(sample['description'],original['note'])
            predicted={s['id']:s['predicted'] for s in strategy['samples']}
            self.assertEqual(strategy['tp'],sum(label and predicted[i] for i,label in labels.items()))
            self.assertEqual(strategy['fn'],sum(label and not predicted[i] for i,label in labels.items()))
            self.assertEqual(strategy['precision'],strategy['tp']/(strategy['tp']+strategy['fp']) if strategy['tp']+strategy['fp'] else 0)
            self.assertEqual(strategy['recall'],strategy['tp']/(strategy['tp']+strategy['fn']) if strategy['tp']+strategy['fn'] else 0)
        self.assertEqual([(s['tp'],s['fp'],s['fn'],s['tn']) for s in report['strategies']],[(2,0,7,3),(8,0,1,3)])

    def test_live_citation_validation_rejects_forged_refs_and_other_owners(self):
        q=question(citation=citation())
        result=self.post('/api/quality/check',{'questions':[q]})
        self.assertEqual((result.json['report']['passed'],result.json['report']['citationCoverage']),(1,1))
        for bad in [citation(documentHash='b'*64),citation(documentTitle='Forged'),citation(page=1),citation(quote='Fabricated')]:
            r=self.post('/api/quality/check',{'questions':[q|{'citation':bad}]})
            self.assertEqual(r.status_code,200,r.json)
            self.assertEqual((r.json['report']['passed'],r.json['report']['citationCoverage']),(0,0))
        r=self.post('/api/quality/check',{'questions':[q]},user='two')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['report']['passed'],0)
        self.assertNotIn('Unrelated page',json.dumps(r.json))

    def test_saved_set_keeps_snapshot_check_after_source_deletion(self):
        from repository import insert_set
        q=question(citation=citation())
        with self.app.app_context():
            sid=insert_set(dict(title='Saved',description='',topic='',visibility='public',questions=[q]),'one')
            get_db().execute('DELETE FROM documents')
            get_db().commit()
        path='/api/sets/'+sid+'/quality'
        self.assertEqual(self.client.get(path,headers={'Test-User':'two'}).status_code,404)
        report=self.client.get(path).json['report']
        self.assertEqual(report['passed'],1)
        authority=[c for c in report['items'][0]['checks'] if c['code']=='citation_authority']
        self.assertEqual(authority[0]['status'],'warn')
        self.assertEqual(self.post('/api/quality/check',{'questions':[q]}).json['report']['passed'],0)

    def test_comparison_snapshot_survives_reopening_database(self):
        self.jobs()
        saved=self.post('/api/evaluations',{'jobIds':['base','ground']}).json['evaluation']
        from evaluations import register_evaluations
        restarted=Flask('restart')
        restarted.config.update(self.app.config)
        restarted.teardown_appcontext(close_db)
        @restarted.before_request
        def identity():
            g.user={'id':'one'}
        register_evaluations(restarted)
        self.assertEqual(restarted.test_client().get('/api/evaluations/'+saved['id']).json['evaluation'],saved)

    def test_quality_routes_bound_input_and_enforce_set_owner(self):
        for payload in [None,{}, {'questions':[]}, {'questions':[question()]*101}]:
            self.assertEqual(self.post('/api/quality/check',payload).status_code,400)
        self.assertEqual(self.client.get('/api/sets/example-network/quality').status_code,404)
        response=self.post('/api/quality/check',{'questions':[question(answer='bad')]})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['report']['passed'],0)


if __name__=='__main__': unittest.main()

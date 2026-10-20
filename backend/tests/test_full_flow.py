"""Cross-version acceptance: real PDF, identities, paging, snapshots and rule tutoring."""
import io
from pathlib import Path
import tempfile
import unittest

from app import create_app
from tests.test_documents import pdf_fixture


class FullLearningFlow(unittest.TestCase):
    def test_textbook_publish_find_practice_tutor_and_private_history(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app({'TESTING': True, 'DATABASE': str(Path(directory) / 'flow.sqlite'),
                              'AI_API_KEY': '', 'TUTOR_RUN_INLINE': True})
            self.addCleanup(app.extensions['ai_executor'].shutdown, wait=True)
            self.addCleanup(app.extensions['tutor_executor'].shutdown, wait=True)
            author, learner = app.test_client(), app.test_client()
            headers = {'X-Requested-With': 'ExamHub'}

            def post(client, path, data):
                response = client.post(path, json=data, headers=headers)
                self.assertLess(response.status_code, 300, response.json)
                return response.json

            quote = 'Transactions are atomic: all operations succeed together or none take effect.'
            uploaded = author.post('/api/documents', headers=headers,
                                   data={'file': (io.BytesIO(pdf_fixture(['TCP is a transport protocol.', quote])), 'learning-flow.pdf')})
            self.assertEqual(uploaded.status_code, 201, uploaded.json)
            document = uploaded.json['document']
            questions = [dict(id=f'q{i}', type='single', prompt=f'Checkpoint {i}: choose atomicity.',
                              options=['Atomicity', 'Indexing'], answer='Atomicity', explanation='All operations have one outcome.',
                              source='', topic='事务' if i % 2 else '数据库') for i in range(21)]
            questions[0].update(source=quote, citation=dict(documentId=document['id'], documentTitle=document['title'],
                                                          documentHash=document['sha256'], page=2, quote=quote))
            payload = dict(title='教材到学习闭环', description='跨版本真实接口验收', topic='数据库', visibility='private', questions=questions)
            saved = post(author, '/api/sets', payload)['set']
            guest_id = author.get('/api/session').json['user']['id']
            registered = post(author, '/api/auth/register', dict(name='验收作者', email='flow@example.test', password='test-password-2026'))
            self.assertEqual(registered['user']['id'], guest_id)
            self.assertEqual(author.get('/api/documents/' + document['id']).status_code, 200)
            self.assertEqual(learner.get('/api/sets/' + saved['id']).status_code, 404)

            quality = post(author, '/api/quality/check', {'questions': questions})['report']
            self.assertEqual(quality['total'], 21)
            published = author.put('/api/sets/' + saved['id'], json={**payload, 'visibility': 'public', 'version': saved['version']}, headers=headers)
            self.assertEqual(published.status_code, 200, published.json)
            saved = published.json['set']
            found = learner.get('/api/sets', query_string={'scope': 'discover', 'q': '教材到学习闭环', 'page': 1, 'pageSize': 12}).json
            self.assertEqual(found['total'], 1)
            self.assertEqual(found['sets'][0]['id'], saved['id'])
            preview = learner.get('/api/sets/' + saved['id']).json['set']
            self.assertNotIn('answer', preview['questions'][0])
            practice = learner.get('/api/sets/' + saved['id'] + '/practice').json
            self.assertFalse({'answer', 'explanation', 'source', 'citation'} & practice['questions'][0].keys())
            attempt = post(learner, '/api/sets/' + saved['id'] + '/attempts',
                           dict(version=saved['version'], answers={q['id']: q['options'][0] for q in questions}))['attempt']
            self.assertEqual(attempt['correct'], 21)
            self.assertEqual(attempt['results'][0]['citation']['page'], 2)
            self.assertEqual(learner.get('/api/documents/' + document['id'] + '/file').status_code, 404)
            post(learner, '/api/sets/' + saved['id'] + '/bookmark', {})
            self.assertEqual(learner.get('/api/sets?scope=saved&page=1').json['total'], 1)
            copied = post(learner, '/api/sets/' + saved['id'] + '/fork', {})['set']
            self.assertEqual(copied['visibility'], 'private')
            self.assertEqual(copied['questions'][0]['citation']['quote'], quote)

            session = post(learner, '/api/tutor/sessions', dict(requestId='flow-session-request', setId=saved['id'],
                           goal='Explain transaction atomicity', mode='rule', maxQuestions=2))['session']
            def command(state, kind, number, **extra):
                return post(learner, '/api/tutor/sessions/' + state['id'] + '/commands',
                            dict(requestId=f'flow-command-request-{number}', version=state['version'], type=kind, **extra))['session']
            session = command(session, 'stop', 1)
            self.assertEqual(session['status'], 'paused')
            session = command(session, 'resume', 2)
            for number in (3, 4):
                session = command(session, 'answer', number, turnId=session['turnId'], answer='Atomicity')
            self.assertEqual(session['status'], 'completed')
            self.assertEqual(session['summary']['answered'], 2)
            self.assertEqual(session['modelCalls'], 0)
            self.assertEqual(author.get('/api/tutor/sessions/' + session['id']).status_code, 404)
            self.assertEqual(post(learner, '/api/tutor/benchmark', {})['report']['kind'], 'tutor-behavior-benchmark')

            private = author.put('/api/sets/' + saved['id'], json={**payload, 'version': saved['version']}, headers=headers)
            self.assertEqual(private.status_code, 200, private.json)
            self.assertEqual(learner.get('/api/sets?scope=saved&page=1').json['total'], 0)
            self.assertEqual(learner.get('/api/sets/' + saved['id']).status_code, 404)
            self.assertEqual(author.delete('/api/documents/' + document['id'], headers=headers).status_code, 200)
            history = learner.get('/api/attempts').json['attempts'][0]
            self.assertEqual(history['results'][0]['citation']['quote'], quote)
            self.assertEqual(learner.get('/api/sets/' + copied['id']).status_code, 200)

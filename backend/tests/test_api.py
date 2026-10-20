import os
import sqlite3
import tempfile
import unittest
import threading
import json
from unittest.mock import patch


class APIContract(unittest.TestCase):
    def setUp(self):
        from app import create_app
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, 'test.sqlite')
        self.app = create_app({'TESTING': True, 'DATABASE': self.path})
        self.a, self.b = self.app.test_client(), self.app.test_client()

    def write(self, client, url, data=None, method='post'):
        return getattr(client, method)(url, json=data, headers={'X-Requested-With': 'ExamHub'})

    def payload(self, visibility='private'):
        return dict(title='网络练习', description='原创练习', topic='计算机网络', visibility=visibility,
                    questions=[dict(id='q1', type='single', prompt='传输层协议是？', options=['TCP', 'IP'], answer='TCP', explanation='TCP 属于传输层', source='原创', topic='分层'),
                               dict(id='q2', type='short', prompt='解释可靠传输', options=[], answer='确认与重传', explanation='通过序号处理重复', source='', topic='可靠性')])

    def create(self, visibility='private'):
        r = self.write(self.a, '/api/sets', self.payload(visibility))
        self.assertEqual(r.status_code, 201, r.json)
        return r.json['set']

    def test_guest_cookie_persistence_and_isolation(self):
        r = self.a.get('/api/session')
        user = r.json['user']
        self.assertIsNone(user['email'])
        self.assertEqual(user, self.a.get('/api/session').json['user'])
        self.assertNotEqual(user['id'], self.b.get('/api/session').json['user']['id'])
        cookie = r.headers['Set-Cookie']
        for part in ['HttpOnly', 'SameSite=Lax', 'Max-Age=']:
            self.assertIn(part, cookie)
        from app import create_app
        restarted = create_app({'TESTING': True, 'DATABASE': self.path}).test_client()
        name, value = cookie.split(';')[0].split('=', 1)
        restarted.set_cookie(name, value)
        self.assertEqual(user, restarted.get('/api/session').json['user'])
        with sqlite3.connect(self.path) as db:
            self.assertNotIn(value, str(db.execute('SELECT * FROM sessions').fetchall()))

    def test_stale_tab_cannot_write_under_a_changed_session(self):
        old_id = self.a.get('/api/session').json['user']['id']
        self.write(self.a, '/api/auth/logout')
        response = self.a.post('/api/sets', json=self.payload(), headers={
            'X-Requested-With': 'ExamHub', 'X-Expected-User': old_id})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['code'], 'session_changed')
        self.assertEqual(self.a.get('/api/sets?scope=mine').json['sets'], [])
        current_id = self.a.get('/api/session').json['user']['id']
        response = self.a.post('/api/sets', json=self.payload(), headers={
            'X-Requested-With': 'ExamHub', 'X-Expected-User': current_id})
        self.assertEqual(response.status_code, 201)

    def test_login_preserves_ai_jobs_and_cancelled_worker_capacity(self):
        from tests.test_ai import QUESTION, SOURCE
        self.app.config.update(AI_API_KEY='test-key')
        self.write(self.b, '/api/auth/register', dict(name='账户', email='jobs@example.com', password='safe-password'))
        entered, release = threading.Event(), threading.Event()
        def provider(*args):
            entered.set()
            release.wait(5)
            return json.dumps({'questions': [QUESTION]})
        try:
            with patch('ai.call_model', side_effect=provider):
                job = self.write(self.a, '/api/ai/jobs', {'source': SOURCE, 'count': 1}).json['job']
                self.assertTrue(entered.wait(2))
                self.write(self.a, '/api/ai/jobs/'+job['id'], method='delete')
                self.write(self.a, '/api/auth/login', dict(email='jobs@example.com', password='safe-password'))
                self.assertEqual(self.a.get('/api/ai/jobs/'+job['id']).status_code, 200)
                self.assertEqual(self.write(self.a, '/api/ai/jobs', {'source': SOURCE, 'count': 1}).status_code, 429)
        finally:
            release.set()
            self.app.extensions['ai_executor'].shutdown(wait=True)

    def test_auth_binding_login_logout_and_password_hash(self):
        owned = self.create()
        guest = self.a.get('/api/session').json['user']
        r = self.write(self.a, '/api/auth/register', dict(name='学习者', email='Test@example.com', password='safe-password'))
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['user']['id'], guest['id'])
        self.assertEqual(self.a.get('/api/sets?scope=mine').json['sets'][0]['id'], owned['id'])
        self.assertEqual(self.write(self.b, '/api/auth/login', dict(email='test@example.com', password='wrong')).status_code, 401)
        self.assertEqual(self.write(self.b, '/api/auth/login', dict(email='test@example.com', password='safe-password')).json['user']['id'], guest['id'])
        self.assertNotEqual(self.write(self.a, '/api/auth/logout').json['user']['id'], guest['id'])
        self.assertEqual(self.a.get('/api/sets/'+owned['id']).status_code, 404)
        with sqlite3.connect(self.path) as db:
            self.assertNotIn('safe-password', str(db.execute('SELECT * FROM users').fetchall()))

    def test_visibility_ownership_and_answer_redaction(self):
        for visibility in ['private', 'unlisted', 'public']:
            s = self.create(visibility)
            url = '/api/sets/'+s['id']
            self.assertEqual(self.b.get(url).status_code, 404 if visibility == 'private' else 200)
            self.assertEqual(self.write(self.b, url, dict(self.payload(), version=1), 'put').status_code, 404)
            self.assertEqual(self.write(self.b, url, method='delete').status_code, 404)
            if visibility != 'private':
                for q in self.b.get(url).json['set']['questions']:
                    self.assertNotIn('answer', q)
                    self.assertNotIn('explanation', q)
            for q in self.a.get(url+'/practice').json['questions']:
                self.assertNotIn('answer', q)
                self.assertNotIn('explanation', q)
        found = self.b.get('/api/sets?scope=discover&q=网络练习').json['sets']
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['visibility'], 'public')
        self.assertEqual(self.b.get('/api/sets?scope=mine').json['sets'], [])

    def test_bookmarks_fork_and_revoked_visibility(self):
        s = self.create('unlisted'); url = '/api/sets/'+s['id']
        self.assertTrue(self.write(self.b, url+'/bookmark').json['bookmarked'])
        self.assertEqual(self.b.get('/api/sets?scope=saved').json['sets'][0]['id'], s['id'])
        fork = self.write(self.b, url+'/fork').json['set']
        self.assertEqual(fork['sourceSetId'], s['id'])
        self.assertEqual(fork['visibility'], 'private')
        self.assertTrue(fork['isOwner'])
        self.assertEqual(fork['questions'][0]['answer'], 'TCP')
        self.assertTrue(set(q['id'] for q in s['questions']).isdisjoint(q['id'] for q in fork['questions']))
        self.write(self.a, url, dict(self.payload(), version=1), 'put')
        self.assertEqual(self.b.get('/api/sets?scope=saved').json['sets'], [])
        for suffix in ['/practice', '/fork', '/bookmark', '/attempts']:
            response = self.b.get(url+suffix) if suffix == '/practice' else self.write(self.b, url+suffix, {'version': 2, 'answers': {}})
            self.assertEqual(response.status_code, 404)

    def test_attempt_grading_conflict_and_frozen_snapshot(self):
        s = self.create('public'); url = '/api/sets/'+s['id']
        answers = {s['questions'][0]['id']: 'TCP', s['questions'][1]['id']: '确认'}
        response = self.write(self.b, url+'/attempts', {'version': 1, 'answers': answers})
        self.assertEqual(response.status_code, 201, response.json)
        attempt = response.json['attempt']
        self.assertEqual((attempt['correct'], attempt['total']), (1, 2))
        self.assertTrue(attempt['results'][0]['correct'])
        self.assertIsNone(attempt['results'][1]['correct'])
        changed = self.payload('public'); changed['questions'][0]['answer'] = 'IP'
        changed['title'] = '更新题集'; changed['version'] = 1
        self.assertEqual(self.write(self.a, url, changed, 'put').json['set']['version'], 2)
        self.assertEqual(self.write(self.a, url, changed, 'put').status_code, 409)
        self.assertEqual(self.write(self.b, url+'/attempts', {'version': 1, 'answers': answers}).status_code, 409)
        self.assertEqual(self.a.get('/api/attempts').json['attempts'], [])
        self.write(self.a, url, method='delete')
        self.assertEqual(self.b.get('/api/attempts').json['attempts'], [attempt])
        self.assertEqual(attempt['results'][0]['answer'], 'TCP')
        self.assertEqual(attempt['setTitle'], '网络练习')

    def test_bad_inputs_and_write_header(self):
        self.assertEqual(self.a.post('/api/sets', json=self.payload()).status_code, 403)
        invalid = [None, [], {}, dict(self.payload(), visibility=[]), dict(self.payload(), title=''), dict(self.payload(), questions=[])]
        badq = self.payload(); badq['questions'][0]['answer'] = 'UDP'; invalid.append(badq)
        badq = self.payload(); badq['questions'][1]['id'] = 'q1'; invalid.append(badq)
        for data in invalid:
            r = self.write(self.a, '/api/sets', data)
            self.assertEqual(r.status_code, 400, r.json)
            self.assertIsInstance(r.json['error'], str)
        s = self.create(); url = '/api/sets/'+s['id']+'/attempts'
        for data in [{'version': True, 'answers': {}}, {'version': 1, 'answers': []}, {'version': 1, 'answers': {'unknown': 'a'}}]:
            self.assertEqual(self.write(self.a, url, data).status_code, 400)
        self.assertNotIn('Access-Control-Allow-Origin', self.a.get('/api/session', headers={'Origin': 'https://evil.example'}).headers)

    def test_rotated_and_expired_session_cookies_cannot_restore_identity(self):
        response = self.a.get('/api/session')
        old_user = response.json['user']
        name, old_token = response.headers['Set-Cookie'].split(';')[0].split('=', 1)
        registered = self.write(self.a, '/api/auth/register', dict(name='账户', email='rotate@example.com', password='safe-password')).json['user']
        self.b.set_cookie(name, old_token)
        self.assertNotEqual(self.b.get('/api/session').json['user']['id'], registered['id'])
        self.assertEqual(old_user['id'], registered['id'])
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE sessions SET expires_at=0 WHERE user_id=?', (registered['id'],))
        self.assertNotEqual(self.a.get('/api/session').json['user']['id'], registered['id'])

    def test_wrong_and_missing_answers_are_not_scored_as_correct(self):
        s = self.create(); url = '/api/sets/'+s['id']+'/attempts'
        for answers in [{}, {s['questions'][0]['id']: 'IP'}]:
            r = self.write(self.a, url, {'version': 1, 'answers': answers})
            self.assertEqual(r.status_code, 201, r.json)
            self.assertEqual(r.json['attempt']['correct'], 0)
            self.assertFalse(r.json['attempt']['results'][0]['correct'])
            self.assertIsNone(r.json['attempt']['results'][1]['correct'])

    def test_filters_bookmark_toggle_and_json_error_contract(self):
        s = self.create('public'); url = '/api/sets/'+s['id']
        self.assertEqual(len(self.a.get('/api/sets?scope=mine&q=网络&topic=计算机网络').json['sets']), 1)
        self.assertEqual(self.a.get('/api/sets?scope=mine&topic=数据库').json['sets'], [])
        self.assertEqual(self.a.get('/api/sets?scope=mine&q=%27%20OR%201=1').json['sets'], [])
        self.write(self.b, url+'/bookmark')
        self.assertFalse(self.write(self.b, url+'/bookmark').json['bookmarked'])
        self.assertEqual(self.b.get('/api/sets?scope=saved').json['sets'], [])
        for path in ['/api/sets?scope=invalid', '/api/missing']:
            self.assertIsInstance(self.a.get(path).json['error'], str)
        malformed = self.a.post('/api/sets', data='{', content_type='application/json', headers={'X-Requested-With': 'ExamHub'})
        self.assertEqual(malformed.status_code, 400)
        self.assertIsInstance(malformed.json['error'], str)
        self.write(self.a, '/api/auth/register', dict(name='账户', email='same@example.com', password='safe-password'))
        duplicate = self.write(self.b, '/api/auth/register', dict(name='另一账户', email='same@example.com', password='safe-password'))
        self.assertEqual(duplicate.status_code, 409)
        self.assertIsNone(self.b.get('/api/session').json['user']['email'])

    def test_logout_clears_only_departing_users_ai_credentials(self):
        user_a = self.a.get('/api/session').json['user']['id']
        user_b = self.b.get('/api/session').json['user']['id']
        credentials = self.app.extensions.setdefault('ai_credentials', {})
        credentials[user_a] = {'apiKey': 'local-test-a'}
        credentials[user_b] = {'apiKey': 'local-test-b'}
        self.assertEqual(self.write(self.a, '/api/auth/logout').status_code, 200)
        self.assertNotIn(user_a, credentials)
        self.assertIn(user_b, credentials)

    def test_login_merges_guest_work_and_preserves_snapshots(self):
        target = self.write(self.b, '/api/auth/register', dict(name='目标账户', email='target@example.com', password='safe-password')).json['user']
        owned = self.create()
        guest_id = owned['ownerId']
        fork = self.write(self.a, '/api/sets/example-network/fork').json['set']
        attempt = self.write(self.a, '/api/sets/'+owned['id']+'/attempts', {'version': 1, 'answers': {'q1': 'TCP'}}).json['attempt']
        existing = self.write(self.b, '/api/sets/example-os/attempts', {'version': 1, 'answers': {}}).json['attempt']
        for client in [self.a, self.b]:
            self.write(client, '/api/sets/example-network/bookmark')
        self.write(self.a, '/api/sets/example-database/bookmark')
        credentials = self.app.extensions.setdefault('ai_credentials', {})
        credentials[guest_id] = {'apiKey': 'guest-test-key'}
        credentials[target['id']] = {'apiKey': 'account-test-key'}
        login = dict(email='target@example.com', password='wrong-password')
        self.assertEqual(self.write(self.a, '/api/auth/login', login).status_code, 401)
        self.assertEqual(self.a.get('/api/session').json['user']['id'], guest_id)
        self.assertEqual(self.b.get('/api/sets/'+owned['id']).status_code, 404)
        self.assertIn(guest_id, credentials)
        login['password'] = 'safe-password'
        self.assertEqual(self.write(self.a, '/api/auth/login', login).json['user'], target)
        for original in [owned, fork]:
            response = self.a.get('/api/sets/'+original['id'])
            self.assertEqual(response.status_code, 200, response.json)
            migrated = response.json['set']
            self.assertEqual(migrated['ownerId'], target['id'])
            self.assertTrue(migrated['isOwner'])
            for key in ['id', 'questions', 'version', 'sourceSetId', 'visibility', 'updatedAt']:
                self.assertEqual(migrated[key], original[key])
        history = self.a.get('/api/attempts').json['attempts']
        self.assertCountEqual(history, [attempt, existing])
        self.assertEqual({s['id'] for s in self.a.get('/api/sets?scope=saved').json['sets']}, {'example-network', 'example-database'})
        self.assertNotIn(guest_id, credentials)
        self.assertEqual(credentials[target['id']], {'apiKey': 'account-test-key'})
        with sqlite3.connect(self.path) as db:
            for table, column in [('sets', 'owner_id'), ('attempts', 'user_id'), ('bookmarks', 'user_id')]:
                self.assertEqual(db.execute(f'SELECT count(*) FROM {table} WHERE {column}=?', (guest_id,)).fetchone()[0], 0)

    def test_login_never_merges_another_registered_accounts_work(self):
        first = self.write(self.a, '/api/auth/register', dict(name='甲', email='first@example.com', password='safe-password')).json['user']
        self.write(self.b, '/api/auth/register', dict(name='乙', email='second@example.com', password='safe-password'))
        owned = self.create()
        self.write(self.a, '/api/sets/'+owned['id']+'/attempts', {'version': 1, 'answers': {}})
        self.write(self.a, '/api/sets/example-network/bookmark')
        self.assertEqual(self.write(self.a, '/api/auth/login', dict(email='second@example.com', password='safe-password')).status_code, 200)
        self.assertEqual(self.a.get('/api/sets/'+owned['id']).status_code, 404)
        self.assertEqual(self.a.get('/api/attempts').json['attempts'], [])
        self.assertEqual(self.a.get('/api/sets?scope=saved').json['sets'], [])
        self.write(self.a, '/api/auth/login', dict(email='first@example.com', password='safe-password'))
        self.assertEqual(self.a.get('/api/sets/'+owned['id']).json['set']['ownerId'], first['id'])
        self.assertEqual(len(self.a.get('/api/attempts').json['attempts']), 1)

    def test_login_migration_rolls_back_if_session_creation_fails(self):
        target = self.write(self.b, '/api/auth/register', dict(name='目标', email='rollback@example.com', password='safe-password')).json['user']
        owned = self.create()
        attempt = self.write(self.a, '/api/sets/'+owned['id']+'/attempts', {'version': 1, 'answers': {}}).json['attempt']
        self.write(self.a, '/api/sets/example-network/bookmark')
        credentials = self.app.extensions.setdefault('ai_credentials', {})
        credentials[owned['ownerId']] = {'apiKey': 'guest-test-key'}
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_session BEFORE INSERT ON sessions BEGIN SELECT RAISE(ABORT, 'forced session failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.write(self.a, '/api/auth/login', dict(email='rollback@example.com', password='safe-password'))
        self.assertEqual(self.a.get('/api/session').json['user']['id'], owned['ownerId'])
        self.assertEqual(self.a.get('/api/sets/'+owned['id']).json['set']['ownerId'], owned['ownerId'])
        self.assertEqual(self.a.get('/api/attempts').json['attempts'], [attempt])
        self.assertEqual(len(self.a.get('/api/sets?scope=saved').json['sets']), 1)
        self.assertIn(owned['ownerId'], credentials)
        self.assertEqual(self.b.get('/api/sets?scope=mine').json['sets'], [])

    def test_out_of_range_versions_return_400_without_mutation(self):
        owned = self.create(); url = '/api/sets/'+owned['id']
        for version in [2**31, 2**63, 10**100]:
            for method, path, data in [('put', url, dict(self.payload(), version=version)),
                                       ('post', url+'/attempts', {'version': version, 'answers': {}})]:
                with self.subTest(version=version, method=method):
                    response = self.write(self.a, path, data, method)
                    self.assertEqual(response.status_code, 400, response.json)
                    self.assertIsInstance(response.json['error'], str)
        self.assertEqual(self.a.get(url).json['set'], owned)
        self.assertEqual(self.a.get('/api/attempts').json['attempts'], [])
        self.assertEqual(self.write(self.a, url, dict(self.payload(), version=2**31-1), 'put').status_code, 409)

    def test_original_seed_and_idempotence(self):
        sets = self.a.get('/api/sets?scope=discover').json['sets']
        self.assertEqual(len(sets), 3)
        self.assertEqual({s['topic'] for s in sets}, {'计算机网络', '数据库', '操作系统'})
        for s in sets:
            self.assertIn('原创', s['description'])
            self.assertTrue(4 <= s['questionCount'] <= 6)
            self.assertFalse(s['bookmarked'])
        from app import create_app
        other = create_app({'TESTING': True, 'DATABASE': self.path}).test_client()
        self.assertEqual(len(other.get('/api/sets?scope=discover').json['sets']), 3)


if __name__ == '__main__':
    unittest.main()

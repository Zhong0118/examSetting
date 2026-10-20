import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from db import get_db


class SetPaginationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app({'TESTING': True, 'DATABASE': str(Path(self.tmp.name) / 'test.sqlite'),
                               'AI_API_KEY': ''})
        for name in ('ai_executor', 'tutor_executor', 'live_eval_executor'):
            executor = self.app.extensions.get(name)
            if executor:
                self.addCleanup(executor.shutdown, wait=True)
        self.client, self.other = self.app.test_client(), self.app.test_client()
        self.user_id = self.client.get('/api/session').json['user']['id']
        self.other_id = self.other.get('/api/session').json['user']['id']
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute('DELETE FROM sets')

    def add_set(self, key, *, owner=None, visibility='public', title=None, description='', topic='',
                updated_at='2026-10-20T00:00:00+00:00'):
        questions = [dict(id='q1', type='short', prompt='问题', options=[], answer='PRIVATE_ANSWER',
                          explanation='PRIVATE_EXPLANATION', source='', topic='')]
        with self.app.app_context():
            db = get_db()
            with db:
                db.execute('INSERT INTO sets VALUES (?,?,?,?,?,?,?,?,?,?)',
                           (key, owner or self.other_id, title or key, description, topic, visibility, 1,
                            json.dumps(questions), updated_at, None))
        return key

    def bookmark(self, key):
        response = self.client.post('/api/sets/' + key + '/bookmark', headers={'X-Requested-With': 'ExamHub'})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['bookmarked'])

    def page(self, **options):
        response = self.client.get('/api/sets', query_string={'scope': 'discover', 'page': 1, **options})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(set(response.json), {'sets', 'total', 'page', 'pageSize', 'topics'})
        return response.json

    def test_legacy_calls_return_all_sets_without_pagination_metadata(self):
        for i in range(14):
            self.add_set(f's{i:02}', owner=self.user_id, visibility='private')
        response = self.client.get('/api/sets')
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(set(response.json), {'sets'})
        self.assertEqual([row['id'] for row in response.json['sets']], [f's{i:02}' for i in range(14)])
        self.assertEqual(self.client.get('/api/sets?scope=discover').json, {'sets': []})

    def test_defaults_partial_parameters_and_page_size_cap(self):
        for i in range(53):
            self.add_set(f's{i:02}')
        for options, expected_page, expected_size, first, count in [
            ({'page': 1}, 1, 12, 's00', 12),
            ({'pageSize': 5}, 1, 5, 's00', 5),
            ({'page': 2}, 2, 12, 's12', 12),
            ({'page': 1, 'pageSize': 999}, 1, 50, 's00', 50),
            ({'page': 2, 'pageSize': 999}, 2, 50, 's50', 3),
        ]:
            with self.subTest(options=options):
                response = self.client.get('/api/sets', query_string={'scope': 'discover', **options})
                self.assertEqual(response.status_code, 200, response.json)
                result = response.json
                self.assertEqual(result.get('total'), 53)
                self.assertEqual((result['page'], result['pageSize']), (expected_page, expected_size))
                self.assertEqual(len(result['sets']), count)
                self.assertEqual(result['sets'][0]['id'], first)

    def test_rejects_invalid_page_and_page_size_even_when_only_one_is_supplied(self):
        for name in ('page', 'pageSize'):
            for value in ('', '0', '-1', '1.5', '1e2', 'true', 'abc', ' 2 ', '+2', '２'):
                with self.subTest(name=name, value=value):
                    response = self.client.get('/api/sets', query_string={name: value})
                    self.assertEqual(response.status_code, 400, response.json)
                    self.assertIn('error', response.json)

    def test_tail_pages_clamp_after_filtering_and_empty_results_stay_on_page_one(self):
        for i in range(5):
            self.add_set(f's{i}', topic='kept' if i < 3 else 'other')
        for requested in (99, 10**30):
            with self.subTest(requested=requested):
                result = self.page(page=requested, pageSize=2, topic='kept')
                self.assertEqual((result['total'], result['page'], result['pageSize']), (3, 2, 2))
                self.assertEqual([row['id'] for row in result['sets']], ['s2'])
        result = self.page(page=99, pageSize=2, topic='missing')
        self.assertEqual((result['sets'], result['total'], result['page']), ([], 0, 1))
        self.assertEqual(result['topics'], ['kept', 'other'])
        self.assertEqual(self.page(q='no match'), {'sets': [], 'total': 0, 'page': 1, 'pageSize': 12, 'topics': []})

    def test_sort_is_updated_desc_then_id_and_limit_offset_are_applied_in_sql(self):
        for key, date in [('c', '2026-10-18'), ('b', '2026-10-20'), ('a', '2026-10-20'),
                          ('d', '2026-10-18'), ('e', '2026-10-17')]:
            self.add_set(key, updated_at=date)
        self.assertEqual([row['id'] for row in self.page(pageSize=2)['sets']], ['a', 'b'])
        statements = []
        with self.app.app_context():
            get_db().set_trace_callback(statements.append)
            result = self.page(page=2, pageSize=2)
        self.assertEqual([row['id'] for row in result['sets']], ['c', 'd'])
        queries = [sql for sql in statements if 'SELECT s.*' in sql]
        self.assertEqual(len(queries), 1, statements)
        self.assertRegex(queries[0], r'(?i)\bLIMIT 2 OFFSET 2\b')

    def test_search_matches_title_description_and_topic_across_pages(self):
        for i in range(9):
            fields = ({'title': 'NeEdLe title'}, {'description': 'needle description'}, {'topic': 'NEEDLE topic'})
            self.add_set(f'm{i}', **fields[i % 3])
        self.add_set('unmatched', title='another set', topic='another topic')
        found = []
        for page in (1, 2, 3):
            result = self.page(q='needle', page=page, pageSize=3)
            self.assertEqual(result['total'], 9)
            self.assertEqual(result['page'], page)
            found.extend(row['id'] for row in result['sets'])
        self.assertEqual(found, ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'])
        legacy = self.client.get('/api/sets?scope=discover&q=needle').json
        self.assertEqual(set(legacy), {'sets'})
        self.assertEqual([row['id'] for row in legacy['sets']], found)

    def test_topics_use_all_scope_and_query_matches_before_topic_and_page_filters(self):
        for key, topic in [('a', 'alpha'), ('b', 'alpha'), ('c', 'beta'), ('d', 'gamma')]:
            self.add_set(key, title='matching', topic=topic)
        self.add_set('unmatched', title='unrelated', topic='excluded')
        self.add_set('private', title='matching', visibility='private', topic='secret')
        self.add_set('unlisted', title='matching', visibility='unlisted', topic='unlisted')
        for options, total, ids in [({}, 4, ['a']), ({'page': 4}, 4, ['d']),
                                    ({'topic': 'alpha', 'page': 2}, 2, ['b'])]:
            with self.subTest(options=options):
                result = self.page(q='matching', pageSize=1, **options)
                self.assertEqual(result['topics'], ['alpha', 'beta', 'gamma'])
                self.assertEqual(result['total'], total)
                self.assertEqual([row['id'] for row in result['sets']], ids)

    def test_workspace_is_deduplicated_union_without_widening_existing_scopes(self):
        self.add_set('own-private', owner=self.user_id, visibility='private', topic='own-private')
        self.add_set('own-public', owner=self.user_id, topic='own-public')
        self.add_set('own-unlisted', owner=self.user_id, visibility='unlisted', topic='own-unlisted')
        self.add_set('public', topic='public')
        self.add_set('saved-public', topic='saved-public')
        self.add_set('saved-unlisted', visibility='unlisted', topic='saved-unlisted')
        self.add_set('unsaved-unlisted', visibility='unlisted', topic='hidden-unlisted')
        self.add_set('other-private', visibility='private', topic='hidden-private')
        for key in ('own-private', 'own-public', 'saved-public', 'saved-unlisted'):
            self.bookmark(key)
        other_bookmark = self.other.post('/api/sets/unsaved-unlisted/bookmark', headers={'X-Requested-With': 'ExamHub'})
        self.assertEqual(other_bookmark.status_code, 200, other_bookmark.json)
        self.assertTrue(other_bookmark.json['bookmarked'])
        expected = {
            'mine': ['own-private', 'own-public', 'own-unlisted'],
            'discover': ['own-public', 'public', 'saved-public'],
            'saved': ['own-private', 'own-public', 'saved-public', 'saved-unlisted'],
            'workspace': ['own-private', 'own-public', 'own-unlisted', 'public', 'saved-public', 'saved-unlisted'],
        }
        for scope, ids in expected.items():
            with self.subTest(scope=scope):
                result = self.page(scope=scope, pageSize=50)
                self.assertEqual(result['total'], len(ids))
                self.assertEqual([row['id'] for row in result['sets']], ids)
                self.assertEqual(result['topics'], ids)
                legacy = self.client.get('/api/sets', query_string={'scope': scope}).json
                self.assertEqual(legacy, {'sets': result['sets']})
                for row in result['sets']:
                    self.assertEqual(row['isOwner'], row['ownerId'] == self.user_id)
                    self.assertEqual(row['bookmarked'], row['id'] in ('own-private', 'own-public', 'saved-public', 'saved-unlisted'))
                    self.assertNotIn('questions', row)
                self.assertNotIn('PRIVATE_ANSWER', json.dumps(result))
                self.assertNotIn('PRIVATE_EXPLANATION', json.dumps(result))
        for scope in ('saved', 'workspace', 'discover'):
            for hidden in ('hidden-private', 'hidden-unlisted'):
                with self.subTest(scope=scope, hidden=hidden):
                    result = self.page(scope=scope, q=hidden, topic=hidden)
                    self.assertEqual(result, {'sets': [], 'total': 0, 'page': 1, 'pageSize': 12, 'topics': []})

    def test_saved_set_becoming_private_disappears_from_sets_totals_and_topics(self):
        for visibility in ('public', 'unlisted'):
            with self.subTest(visibility=visibility):
                key = 'revoked-' + visibility
                self.add_set(key, visibility=visibility, title=key, topic=key)
                self.bookmark(key)
                for scope in ('saved', 'workspace'):
                    self.assertEqual(self.page(scope=scope, q=key)['total'], 1)
                response = self.other.put('/api/sets/' + key, json={
                    'title': key, 'description': '', 'topic': key, 'visibility': 'private', 'version': 1,
                    'questions': [dict(id='q1', type='short', prompt='问题', answer='PRIVATE_ANSWER', options=[])],
                }, headers={'X-Requested-With': 'ExamHub'})
                self.assertEqual(response.status_code, 200, response.json)
                for scope in ('saved', 'workspace', 'discover', 'mine'):
                    for topic in ('', key):
                        result = self.page(scope=scope, q=key, topic=topic, page=99)
                        self.assertEqual(result, {'sets': [], 'total': 0, 'page': 1, 'pageSize': 12, 'topics': []})
                    legacy = self.client.get('/api/sets', query_string={'scope': scope, 'q': key})
                    self.assertEqual(legacy.json, {'sets': []})
                owner_page = self.other.get('/api/sets', query_string={'scope': 'workspace', 'q': key, 'page': 1}).json
                self.assertEqual(owner_page['total'], 1)
                self.assertEqual(owner_page['topics'], [key])
                self.assertEqual(self.client.get('/api/sets/' + key).status_code, 404)

    def test_filters_are_literal_values_and_cannot_bypass_permissions(self):
        self.add_set('public', title="100%_ ' OR 1=1 --", topic='literal')
        self.add_set('private', visibility='private', title='secret', topic='secret')
        for q, total in [("' OR 1=1 --", 1), ('%_', 1), ('secret', 0)]:
            with self.subTest(q=q):
                result = self.page(scope='workspace', q=q)
                self.assertEqual(result['total'], total)
                self.assertEqual(result['topics'], ['literal'] if total else [])
        self.assertEqual(self.page(scope='workspace', topic="' OR 1=1 --")['total'], 0)

    def test_unknown_scope_is_still_rejected_with_or_without_pagination(self):
        for options in ({'scope': 'unknown'}, {'scope': 'unknown', 'page': 1}):
            response = self.client.get('/api/sets', query_string=options)
            self.assertEqual(response.status_code, 400, response.json)

    def test_empty_topics_are_not_offered_as_a_named_filter(self):
        self.add_set('untagged', topic='')
        self.add_set('tagged', topic='网络')
        result = self.page()
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['topics'], ['网络'])

    def test_unicode_case_matching_survives_server_side_search(self):
        self.add_set('unicode', title='CAFÉ', description='ÉTUDES', topic='MÜNCHEN')
        for query in ('café', 'études', 'münchen'):
            with self.subTest(query=query):
                self.assertEqual([row['id'] for row in self.page(q=query)['sets']], ['unicode'])


if __name__ == '__main__':
    unittest.main()

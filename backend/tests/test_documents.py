import hashlib
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from werkzeug.exceptions import HTTPException
from werkzeug.test import EnvironBuilder


def pdf_fixture(texts=('TCP provides reliable delivery.', 'Transactions are atomic.')):
    """Real PDF text operators with a standard font; no reportlab dependency."""
    writer = PdfWriter()
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    for text in texts:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        if text:
            content = DecodedStreamObject()
            escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            content.set_data(('BT /F1 12 Tf 40 740 Td ('+escaped+') Tj ET').encode('ascii'))
            page[NameObject('/Contents')] = writer._add_object(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class DocumentTests(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from documents import register_documents
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'instance' / 'test.sqlite')
        self.app = create_app({'TESTING': True, 'DATABASE': self.path, 'MAX_CONTENT_LENGTH': 21*1024*1024})
        if 'documents' not in self.app.blueprints:
            register_documents(self.app)
        self.a, self.b = self.app.test_client(), self.app.test_client()
        self.user = self.a.get('/api/session').json['user']['id']
        self.other = self.b.get('/api/session').json['user']['id']
        self.headers = {'X-Requested-With': 'ExamHub', 'X-Expected-User': self.user}

    def upload(self, content=None, client=None, name='textbook.pdf'):
        client = client or self.a
        user = self.user if client is self.a else self.other
        with closing(EnvironBuilder(path='/api/documents', method='POST',
                            data={'file': (io.BytesIO(pdf_fixture() if content is None else content), name)},
                            headers={'X-Requested-With': 'ExamHub', 'X-Expected-User': user})) as builder:
            environ = builder.get_environ()
            try:
                return client.open(environ)
            finally:
                environ['wsgi.input'].close()

    def test_upload_persist_pages_original_duplicate_and_owner_access(self):
        raw = pdf_fixture()
        response = self.upload(raw)
        self.assertEqual(response.status_code, 201, response.json)
        document = response.json['document']; did = document['id']
        self.assertFalse(response.json['duplicate'])
        self.assertEqual(document['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual((document['pageCount'], document['textPageCount']), (2, 2))
        pages = self.a.get('/api/documents/'+did).json['pages']
        self.assertEqual([p['page'] for p in pages], [1, 2])
        self.assertIn('Transactions are atomic.', pages[1]['text'])
        self.assertEqual(pages[1]['charCount'], len(pages[1]['text']))
        original = self.a.get('/api/documents/'+did+'/file')
        self.assertEqual(original.mimetype, 'application/pdf')
        self.assertEqual(original.data, raw)
        original.close()
        duplicate = self.upload(raw)
        self.assertEqual(duplicate.status_code, 200)
        self.assertTrue(duplicate.json['duplicate'])
        self.assertEqual(duplicate.json['document'], document)
        self.assertEqual(self.a.get('/api/documents').json['documents'], [document])
        self.assertEqual(self.b.get('/api/documents').json['documents'], [])
        for suffix in ['', '/file']:
            self.assertEqual(self.b.get('/api/documents/'+did+suffix).status_code, 404)
        self.assertEqual(self.b.delete('/api/documents/'+did, headers={'X-Requested-With': 'ExamHub'}).status_code, 404)
        separate = self.upload(raw, self.b)
        self.assertEqual(separate.status_code, 201)
        self.assertNotEqual(separate.json['document']['id'], did)
        from app import create_app
        from documents import register_documents
        restarted = create_app({'TESTING': True, 'DATABASE': self.path})
        if 'documents' not in restarted.blueprints:
            register_documents(restarted)
        client = restarted.test_client()
        cookie_name = self.app.config['SESSION_COOKIE_NAME']
        client.set_cookie(cookie_name, self.a.get_cookie(cookie_name).value)
        self.assertEqual(client.get('/api/documents/'+did).json['pages'], pages)

    def test_reject_invalid_encrypted_blank_and_oversized_without_artifacts(self):
        writer = PdfWriter(); writer.add_blank_page(width=100, height=100); writer.encrypt('secret')
        encrypted = io.BytesIO(); writer.write(encrypted)
        for raw in [b'not a pdf', b'%PDF-1.7\nbroken', encrypted.getvalue(), pdf_fixture(['']), pdf_fixture(['text']+['']*200), b'%PDF-'+b'x'*(20*1024*1024)]:
            with self.subTest(size=len(raw)):
                response = self.upload(raw)
                self.assertIn(response.status_code, (400, 413), response.json)
                self.assertIsInstance(response.json['error'], str)
        self.assertEqual(self.a.get('/api/documents').json['documents'], [])
        self.assertEqual(list((Path(self.path).parent / 'documents').glob('*')), [])
        self.assertEqual(self.a.post('/api/documents', headers=self.headers).status_code, 400)

    def test_partial_empty_page_warns_and_physical_page_numbers_stay_stable(self):
        response = self.upload(pdf_fixture(['first page', '', 'third page']))
        self.assertEqual(response.status_code, 201, response.json)
        doc = response.json['document']
        self.assertEqual((doc['pageCount'], doc['textPageCount']), (3, 2))
        self.assertTrue(any('2' in warning for warning in doc['warnings']))
        pages = self.a.get('/api/documents/'+doc['id']).json['pages']
        self.assertEqual(pages[1], {'page': 2, 'text': '', 'charCount': 0})

    def test_selection_limits_and_owner_validation(self):
        from documents import selection
        doc = self.upload().json['document']
        with self.app.app_context():
            selected = selection(doc['id'], self.user, 2, 2)
            self.assertEqual(selected['document'], doc)
            self.assertEqual(selected['source'], selected['pages'][0]['text'])
            for start, end in [(0, 1), (2, 1), (1, 3), (True, 2), ('1', 2)]:
                with self.assertRaises(HTTPException) as caught:
                    selection(doc['id'], self.user, start, end)
                self.assertEqual(caught.exception.code, 400)
            with self.assertRaises(HTTPException) as caught:
                selection(doc['id'], self.other, 1, 1)
            self.assertEqual(caught.exception.code, 404)
        long = self.upload(pdf_fixture(['x'*16000, 'y'*16000]+['short']*19)).json['document']
        with self.app.app_context():
            for start, end in [(1, 2), (1, 21)]:
                with self.assertRaises(HTTPException) as caught:
                    selection(long['id'], self.user, start, end)
                self.assertEqual(caught.exception.code, 400)

    def test_canonical_citation_metadata_quote_and_retained_snapshot(self):
        from documents import canonical_citation
        doc = self.upload().json['document']
        citation = dict(documentId=doc['id'], documentTitle=doc['title'], documentHash=doc['sha256'], page=2, quote='Transactions are atomic.')
        with self.app.app_context():
            self.assertEqual(canonical_citation(citation, 'Transactions  are\natomic.', self.user), citation)
            # NFKC normalization accepts equivalent fullwidth characters.
            normalized = dict(citation, quote='Ｔransactions are atomic.')
            self.assertEqual(canonical_citation(normalized, citation['quote'], self.user), normalized)
            for tampered in [dict(citation, page=1), dict(citation, page=True), dict(citation, documentHash='bad'), dict(citation, documentTitle='forged'), dict(citation, quote='Invented claim.'), dict(citation, quote=''), None, []]:
                with self.subTest(tampered=tampered), self.assertRaises(HTTPException):
                    canonical_citation(tampered, citation['quote'], self.user)
            with self.assertRaises(HTTPException):
                canonical_citation(citation, 'Different source', self.user)
            with self.assertRaises(HTTPException):
                canonical_citation(citation, citation['quote'], self.other)
            self.assertEqual(canonical_citation(citation, citation['quote'], self.other, existing=[citation]), citation)
        self.assertEqual(self.a.delete('/api/documents/'+doc['id'], headers=self.headers).json, {'ok': True})
        self.assertEqual(self.a.get('/api/documents/'+doc['id']+'/file').status_code, 404)
        self.assertEqual(list((Path(self.path).parent / 'documents').glob('*')), [])
        with self.app.app_context():
            self.assertEqual(canonical_citation(citation, citation['quote'], self.user, existing=[citation]), citation)
            with self.assertRaises(HTTPException):
                canonical_citation(dict(citation, page=1), citation['quote'], self.user, existing=[citation])

    def test_timeout_and_total_text_limit_leave_no_artifacts(self):
        self.app.config['PDF_PARSE_TIMEOUT'] = 0.001
        timed = self.upload()
        self.assertEqual(timed.status_code, 400, timed.json)
        self.assertIn('超时', timed.json['error'])
        self.app.config['PDF_PARSE_TIMEOUT'] = 20
        oversized = self.upload(pdf_fixture(['x'*11000]*183))
        self.assertEqual(oversized.status_code, 400, oversized.json)
        self.assertIn('200 万字符', oversized.json['error'])
        self.assertEqual(self.a.get('/api/documents').json['documents'], [])
        self.assertEqual(list((Path(self.path).parent / 'documents').glob('*')), [])

    def test_failed_database_insert_removes_staged_file(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_document BEFORE INSERT ON documents BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.upload()
        self.assertEqual(self.a.get('/api/documents').json['documents'], [])
        self.assertEqual(list((Path(self.path).parent / 'documents').glob('*')), [])

    def test_owner_merge_preserves_duplicate_document_ids_and_references(self):
        from documents import canonical_citation
        first = self.upload().json['document']
        second = self.upload(client=self.b).json['document']
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE documents SET owner_id=? WHERE owner_id=?', (self.user, self.other))
        self.assertEqual(len(self.a.get('/api/documents').json['documents']), 2)
        for doc in [first, second]:
            citation = dict(documentId=doc['id'], documentTitle=doc['title'], documentHash=doc['sha256'], page=2, quote='Transactions are atomic.')
            with self.app.app_context():
                self.assertEqual(canonical_citation(citation, citation['quote'], self.user), citation)
        self.assertTrue(self.upload().json['duplicate'])
        self.assertEqual(len(self.a.get('/api/documents').json['documents']), 2)

    def test_delete_failure_restores_file_and_document(self):
        raw = pdf_fixture()
        doc = self.upload(raw).json['document']
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON documents BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.a.delete('/api/documents/'+doc['id'], headers=self.headers)
        self.assertEqual(self.a.get('/api/documents/'+doc['id']).json['document'], doc)
        response = self.a.get('/api/documents/'+doc['id']+'/file')
        self.assertEqual(response.data, raw)
        response.close()
        self.assertEqual(len(list((Path(self.path).parent / 'documents').glob('*.pdf'))), 1)
        self.assertEqual(list((Path(self.path).parent / 'documents').glob('.delete-*')), [])


if __name__ == '__main__':
    unittest.main()

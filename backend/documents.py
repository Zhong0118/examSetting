"""Private PDFs, physical-page text and server-validated citation snapshots."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata

from flask import Blueprint, abort, current_app, g, jsonify, request, send_file
from db import get_db
from repository import now, uid

MAX_FILE_BYTES = 20 * 1024 * 1024
SCHEMA = '''
CREATE TABLE IF NOT EXISTS documents (
 id TEXT PRIMARY KEY,
 owner_id TEXT NOT NULL REFERENCES users(id),
 title TEXT NOT NULL,
 filename TEXT NOT NULL,
 sha256 TEXT NOT NULL,
 page_count INTEGER NOT NULL,
 text_page_count INTEGER NOT NULL,
 created_at TEXT NOT NULL,
 warnings TEXT NOT NULL,
 pages TEXT NOT NULL,
 file_path TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS documents_owner_hash ON documents(owner_id, sha256);
'''


def normalize_text(text):
    """Shared quote matching: Unicode NFKC followed by whitespace collapse."""
    return ' '.join(unicodedata.normalize('NFKC', text).split())


def document_value(row):
    return dict(id=row['id'], title=row['title'], filename=row['filename'], sha256=row['sha256'],
                pageCount=row['page_count'], textPageCount=row['text_page_count'], createdAt=row['created_at'],
                warnings=json.loads(row['warnings']))


def owned_document(document_id, user_id):
    if not isinstance(document_id, str) or not isinstance(user_id, str):
        abort(404, description='教材不存在或无权访问')
    row = get_db().execute('SELECT * FROM documents WHERE id=? AND owner_id=?', (document_id, user_id)).fetchone()
    if row is None:
        abort(404, description='教材不存在或无权访问')
    return row


def selection(document_id, user_id, start_page, end_page):
    row = owned_document(document_id, user_id)
    if type(start_page) is not int or type(end_page) is not int or not 1 <= start_page <= end_page <= row['page_count']:
        abort(400, description='请选择有效的 PDF 物理页范围（从 1 开始）')
    if end_page - start_page + 1 > 20:
        abort(400, description='每次最多选择 20 页，请缩小页范围')
    pages = json.loads(row['pages'])[start_page - 1:end_page]
    source = '\n\n'.join(page['text'] for page in pages)
    if len(source) > 30000:
        abort(400, description='所选文字超过 30000 字符，请缩小页范围')
    if not normalize_text(source):
        abort(400, description='所选页没有可提取文字，本版本不提供 OCR')
    return dict(document=document_value(row), pages=pages, source=source)


def canonical_citation(value, source, user_id, existing=()):
    keys = {'documentId', 'documentTitle', 'documentHash', 'page', 'quote'}
    if not isinstance(value, dict) or set(value) != keys:
        abort(400, description='引用必须包含完整且有效的教材元数据')
    if any(not isinstance(value[key], str) or not value[key] for key in keys - {'page'}):
        abort(400, description='引用字段格式不正确')
    if type(value['page']) is not int or not 1 <= value['page'] <= 200:
        abort(400, description='引用页码无效')
    quote = normalize_text(value['quote'])
    if not quote or len(value['quote']) > 30000 or not isinstance(source, str) or normalize_text(source) != quote:
        abort(400, description='source 必须与非空引用摘录一致')
    # Existing is a trusted server-side list, never client-supplied evidence.
    # Exact equality allows immutable copies even after access or file deletion.
    if any(value == item for item in existing):
        return dict(value)
    row = owned_document(value['documentId'], user_id)
    if value['documentHash'] != row['sha256'] or value['documentTitle'] != row['title']:
        abort(400, description='引用的教材哈希或标题不匹配')
    if value['page'] > row['page_count']:
        abort(400, description='引用页码超出教材范围')
    page = json.loads(row['pages'])[value['page'] - 1]
    if quote not in normalize_text(page['text']):
        abort(400, description='引用摘录不在指定物理页中')
    return dict(documentId=row['id'], documentTitle=row['title'], documentHash=row['sha256'],
                page=value['page'], quote=value['quote'])


def parse_file(path):
    try:
        completed = subprocess.run([sys.executable, '-I', str(Path(__file__).with_name('pdf_extract.py')), str(path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
                                   timeout=current_app.config.get('PDF_PARSE_TIMEOUT', 20))
    except subprocess.TimeoutExpired:
        abort(400, description='PDF 解析超时，请拆分文件后重试')
    if completed.returncode != 0:
        abort(400, description='PDF 解析失败或资源超限，请尝试更小的有效 PDF')
    try:
        result = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        abort(400, description='PDF 解析失败')
    if 'error' in result:
        abort(400, description=result['error'])
    return result


def register_documents(app):
    storage = Path(app.config.get('DOCUMENT_STORAGE', Path(app.config['DATABASE']).parent / 'documents')).resolve()
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    with app.app_context():
        get_db().executescript(SCHEMA)
    bp = Blueprint('documents', __name__)

    @bp.get('/api/documents')
    def list_documents():
        rows = get_db().execute('SELECT * FROM documents WHERE owner_id=? ORDER BY created_at DESC,id', (g.user['id'],)).fetchall()
        return jsonify(documents=[document_value(row) for row in rows])

    @bp.post('/api/documents')
    def upload():
        files = request.files.getlist('file')
        if len(files) != 1 or not files[0].filename:
            abort(400, description='请上传一个 PDF 文件')
        uploaded = files[0]
        filename = uploaded.filename.replace('\\', '/').rsplit('/', 1)[-1]
        filename = ''.join(c for c in filename if c.isprintable()).strip()
        if not filename or len(filename) > 255:
            abort(400, description='文件名无效或超过 255 字符')
        temp_path = final_path = None
        persisted = False
        try:
            digest = hashlib.sha256()
            size = 0
            with tempfile.NamedTemporaryFile(dir=storage, prefix='.upload-', delete=False) as output:
                temp_path = Path(output.name)
                while chunk := uploaded.stream.read(65536):
                    size += len(chunk)
                    if size > MAX_FILE_BYTES:
                        abort(413, description='PDF 文件不能超过 20 MiB')
                    digest.update(chunk)
                    output.write(chunk)
            if size == 0:
                abort(400, description='PDF 文件不能为空')
            sha256 = digest.hexdigest()
            db = get_db()
            duplicate = db.execute('SELECT * FROM documents WHERE owner_id=? AND sha256=? ORDER BY created_at,id LIMIT 1', (g.user['id'], sha256)).fetchone()
            if duplicate:
                return jsonify(document=document_value(duplicate), duplicate=True)
            parsed = parse_file(temp_path)
            pages = parsed['pages']
            did = uid()
            final_path = storage / (did + '.pdf')
            with db:
                db.execute('BEGIN IMMEDIATE')
                # Serialize duplicate checks without a UNIQUE constraint: guest
                # login may merge two owners whose existing citations need both IDs.
                duplicate = db.execute('SELECT * FROM documents WHERE owner_id=? AND sha256=? ORDER BY created_at,id LIMIT 1', (g.user['id'], sha256)).fetchone()
                if duplicate:
                    return jsonify(document=document_value(duplicate), duplicate=True)
                os.replace(temp_path, final_path)
                db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                           (did, g.user['id'], Path(filename).stem or filename, filename, sha256, len(pages),
                            sum(bool(p['text']) for p in pages), now(), json.dumps(parsed['warnings'], ensure_ascii=False),
                            json.dumps(pages, ensure_ascii=False), str(final_path)))
            persisted = True
            return jsonify(document=document_value(owned_document(did, g.user['id'])), duplicate=False), 201
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)
            if final_path and not persisted:
                final_path.unlink(missing_ok=True)

    @bp.get('/api/documents/<document_id>')
    def document_detail(document_id):
        row = owned_document(document_id, g.user['id'])
        return jsonify(document=document_value(row), pages=json.loads(row['pages']))

    @bp.get('/api/documents/<document_id>/file')
    def document_file(document_id):
        row = owned_document(document_id, g.user['id'])
        path = Path(row['file_path'])
        if not path.is_file():
            abort(404, description='教材原文件已不可用')
        response = send_file(path, mimetype='application/pdf', download_name=row['filename'], conditional=True)
        response.headers['Content-Security-Policy'] = "sandbox"
        return response

    @bp.delete('/api/documents/<document_id>')
    def delete_document(document_id):
        db = get_db()
        original = tombstone = None
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                row = owned_document(document_id, g.user['id'])
                original = Path(row['file_path'])
                if original.exists():
                    tombstone = original.with_name('.delete-' + uid())
                    os.replace(original, tombstone)
                db.execute('DELETE FROM documents WHERE id=? AND owner_id=?', (document_id, g.user['id']))
        except Exception:
            if tombstone and tombstone.exists():
                os.replace(tombstone, original)
            raise
        if tombstone:
            tombstone.unlink(missing_ok=True)
        return jsonify(ok=True)

    app.register_blueprint(bp)

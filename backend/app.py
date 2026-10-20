"""ExamHub same-origin JSON API."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from flask import Flask, abort, g, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from db import close_db, get_db, init_db
from repository import (accessible, detail, insert_set, now, questions_without_answers,
                        summary, text_value, uid, validate_set, version_value)

SESSION_AGE = 60 * 60 * 24 * 30


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description='请求必须是 JSON 对象')
    return data


def public_user(row):
    return {key: row[key] for key in ('id', 'name', 'email')}


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(user=None):
    db = get_db()
    if user is None:
        user = dict(id=uid(), name='访客', email=None)
        db.execute('INSERT INTO users(id,name) VALUES (?,?)', (user['id'], user['name']))
    if getattr(g, 'session_hash', None):
        db.execute('DELETE FROM sessions WHERE token_hash=?', (g.session_hash,))
    token = secrets.token_urlsafe(32)
    g.session_hash = token_hash(token)
    db.execute('INSERT INTO sessions VALUES (?,?,?)', (g.session_hash, user['id'], int(time.time()) + SESSION_AGE))
    db.commit()
    g.user = public_user(user)
    g.new_token = token
    return g.user


def credentials(data):
    email = text_value(data, 'email', 254, True).lower()
    password = data.get('password')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or not isinstance(password, str) or not 8 <= len(password) <= 256:
        abort(400, description='邮箱格式不正确或密码长度不在 8 至 256 字符内')
    return email, password


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=os.environ.get('DATABASE', str(Path(__file__).parent / 'instance' / 'examhub.sqlite3')),
                            MAX_CONTENT_LENGTH=21 * 1024 * 1024, SESSION_COOKIE_NAME='examhub_session',
                            SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true')
    if config:
        app.config.update(config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.before_request
    def authenticate():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.headers.get('X-Requested-With') != 'ExamHub':
            abort(403, description='缺少 ExamHub 请求头')
        token = request.cookies.get(app.config['SESSION_COOKIE_NAME'], '')
        g.session_hash = token_hash(token) if token else None
        row = get_db().execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',
                               (g.session_hash, int(time.time()))).fetchone()
        if row is None:
            new_session()
        else:
            g.user = public_user(row)
        expected_user = request.headers.get('X-Expected-User')
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and expected_user and expected_user != g.user['id']:
            return jsonify(error='账户已在其他页面切换，请刷新后继续；未提交的作答仍保存在原账户下',
                           code='session_changed'), 409

    @app.after_request
    def secure_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if getattr(g, 'new_token', None):
            response.set_cookie(app.config['SESSION_COOKIE_NAME'], g.new_token, max_age=SESSION_AGE,
                                httponly=True, samesite='Lax', secure=app.config['SESSION_COOKIE_SECURE'])
        return response

    @app.get('/api/session')
    def session():
        return jsonify(user=g.user)

    @app.post('/api/auth/register')
    def register():
        data = body()
        name = text_value(data, 'name', 80, True)
        email, password = credentials(data)
        if g.user['email'] is not None:
            abort(409, description='当前账户已经注册')
        db = get_db()
        try:
            db.execute('UPDATE users SET name=?,email=?,password_hash=? WHERE id=?',
                       (name, email, generate_password_hash(password), g.user['id']))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            abort(409, description='邮箱已注册')
        return jsonify(user=new_session(dict(id=g.user['id'], name=name, email=email)))

    @app.post('/api/auth/login')
    def login():
        data = body()
        # A wrong short password remains an authentication failure.
        email = text_value(data, 'email', 254, True).lower()
        password = data.get('password')
        if not isinstance(password, str) or not password or len(password) > 256:
            abort(400, description='密码格式不正确')
        row = get_db().execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if row is None or not row['password_hash'] or not check_password_hash(row['password_hash'], password):
            abort(401, description='邮箱或密码不正确')
        db = get_db()
        departing_id = g.user['id']
        with db:
            db.execute('BEGIN IMMEDIATE')
            # Recheck under the write lock: a concurrent registration must not
            # turn an authenticated account into a source for guest migration.
            departing = db.execute('SELECT email FROM users WHERE id=?', (departing_id,)).fetchone()
            migrate_guest = departing['email'] is None and departing_id != row['id']
            if migrate_guest:
                db.execute('UPDATE sets SET owner_id=? WHERE owner_id=?', (row['id'], departing_id))
                db.execute('UPDATE attempts SET user_id=? WHERE user_id=?', (row['id'], departing_id))
                db.execute('UPDATE ai_jobs SET user_id=? WHERE user_id=?', (row['id'], departing_id))
                db.execute('UPDATE documents SET owner_id=? WHERE owner_id=?', (row['id'], departing_id))
                db.execute('UPDATE evaluations SET user_id=? WHERE user_id=?', (row['id'], departing_id))
                db.execute('UPDATE tutor_sessions SET user_id=? WHERE user_id=?', (row['id'], departing_id))
                db.execute('UPDATE tutor_live_evaluations SET user_id=? WHERE user_id=?', (row['id'], departing_id))
                db.execute('INSERT OR IGNORE INTO bookmarks(user_id,set_id) SELECT ?,set_id FROM bookmarks WHERE user_id=?',
                           (row['id'], departing_id))
                db.execute('DELETE FROM bookmarks WHERE user_id=?', (departing_id,))
            # new_session commits the migration and session replacement together.
            user = new_session(row)
        if migrate_guest:
            app.extensions.get('ai_credentials', {}).pop(departing_id, None)
        return jsonify(user=user)

    @app.post('/api/auth/logout')
    def logout():
        app.extensions.get('ai_credentials', {}).pop(g.user['id'], None)
        return jsonify(user=new_session())

    @app.get('/api/sets')
    def list_sets():
        scope = request.args.get('scope', 'mine')
        conditions = {'mine': 's.owner_id=?', 'discover': "s.visibility='public'", 'saved': 'EXISTS (SELECT 1 FROM bookmarks b WHERE b.set_id=s.id AND b.user_id=?)'}
        if scope not in conditions:
            abort(400, description='scope 格式不正确')
        params = [g.user['id']] if scope != 'discover' else []
        sql = 'SELECT s.*,u.name AS author FROM sets s JOIN users u ON u.id=s.owner_id WHERE '+conditions[scope]
        sql += " AND (s.owner_id=? OR s.visibility!='private')"
        params.append(g.user['id'])
        if request.args.get('q'):
            sql += ' AND (instr(lower(s.title),lower(?))>0 OR instr(lower(s.description),lower(?))>0)'
            params.extend([request.args['q']] * 2)
        if request.args.get('topic'):
            sql += ' AND s.topic=?'
            params.append(request.args['topic'])
        rows = get_db().execute(sql+' ORDER BY s.updated_at DESC,s.id', params).fetchall()
        return jsonify(sets=[summary(row) for row in rows])

    @app.post('/api/sets')
    def create_set():
        data = validate_set(body())
        db = get_db()
        with db:
            set_id = insert_set(data, g.user['id'])
        return jsonify(set=detail(accessible(set_id))), 201

    @app.get('/api/sets/<set_id>')
    def get_set(set_id):
        return jsonify(set=detail(accessible(set_id)))

    @app.put('/api/sets/<set_id>')
    def update_set(set_id):
        row = accessible(set_id, owner=True)
        payload = body()
        version = version_value(payload)
        data = validate_set(payload, existing=[q['citation'] for q in json.loads(row['questions']) if q.get('citation')])
        db = get_db()
        with db:
            changed = db.execute('UPDATE sets SET title=?,description=?,topic=?,visibility=?,questions=?,updated_at=?,version=version+1 WHERE id=? AND owner_id=? AND version=?',
                                 (data['title'], data['description'], data['topic'], data['visibility'], json.dumps(data['questions'], ensure_ascii=False), now(), set_id, g.user['id'], version))
            if changed.rowcount != 1:
                abort(409, description='题集已更新，请刷新后重试')
        return jsonify(set=detail(accessible(set_id)))

    @app.delete('/api/sets/<set_id>')
    def delete_set(set_id):
        accessible(set_id, owner=True)
        db = get_db()
        with db:
            db.execute('DELETE FROM sets WHERE id=? AND owner_id=?', (set_id, g.user['id']))
        return jsonify(ok=True)

    @app.post('/api/sets/<set_id>/fork')
    def fork_set(set_id):
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = accessible(set_id)
            data = {key: row[key] for key in ('title', 'description', 'topic')}
            data.update(visibility='private', questions=json.loads(row['questions']))
            for q in data['questions']:
                q['id'] = uid()
            new_id = insert_set(data, g.user['id'], set_id)
        return jsonify(set=detail(accessible(new_id))), 201

    @app.post('/api/sets/<set_id>/bookmark')
    def bookmark(set_id):
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            accessible(set_id)
            removed = db.execute('DELETE FROM bookmarks WHERE user_id=? AND set_id=?', (g.user['id'], set_id)).rowcount
            if not removed:
                db.execute('INSERT INTO bookmarks VALUES (?,?)', (g.user['id'], set_id))
        return jsonify(bookmarked=not bool(removed))

    @app.get('/api/sets/<set_id>/practice')
    def practice(set_id):
        row = accessible(set_id)
        return jsonify(set=summary(row), questions=questions_without_answers(row, hide_evidence=True))

    @app.post('/api/sets/<set_id>/attempts')
    def submit(set_id):
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = accessible(set_id)
            data = body()
            version = version_value(data)
            if row['version'] != version:
                abort(409, description='题集已更新，请重新开始练习')
            questions = json.loads(row['questions'])
            answers = data.get('answers')
            valid_ids = {q['id'] for q in questions}
            if not isinstance(answers, dict) or any(k not in valid_ids or not isinstance(v, str) or len(v) > 20000 for k, v in answers.items()):
                abort(400, description='作答内容格式不正确')
            results = []
            for q in questions:
                user_answer = answers.get(q['id'], '')
                results.append(dict(questionId=q['id'], **{k: v for k, v in q.items() if k != 'id'},
                                    userAnswer=user_answer, correct=(user_answer == q['answer']) if q['type'] == 'single' else None))
            attempt = dict(id=uid(), setId=set_id, setTitle=row['title'], version=version, createdAt=now(),
                           correct=sum(r['correct'] is True for r in results), total=len(results), results=results)
            db.execute('INSERT INTO attempts VALUES (?,?,?)', (attempt['id'], g.user['id'], json.dumps(attempt, ensure_ascii=False)))
        return jsonify(attempt=attempt), 201

    @app.get('/api/attempts')
    def attempts():
        rows = get_db().execute('SELECT snapshot FROM attempts WHERE user_id=? ORDER BY rowid DESC', (g.user['id'],)).fetchall()
        return jsonify(attempts=[json.loads(row['snapshot']) for row in rows])

    from documents import register_documents
    from ai import register_ai
    from evaluations import register_evaluations
    register_documents(app)
    register_ai(app)
    register_evaluations(app)
    from tutor import register_tutor
    register_tutor(app)
    from tutor_live_api import register_tutor_live
    register_tutor_live(app)
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')))

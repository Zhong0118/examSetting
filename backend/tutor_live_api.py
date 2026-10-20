"""Owner-scoped live evaluations with pre-call quota reservations and checkpoints."""
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from urllib.parse import urlsplit
from flask import Blueprint,abort,g,jsonify,request
from repository import uid,now
from tutor import request_data
from tutor_live import dataset_info,make_report,run_report,refresh_summary,blind_package,sanitize_strings,RUBRIC


def register_tutor_live(app):
    lock=threading.RLock();occupied=set()
    executor=ThreadPoolExecutor(max_workers=2,thread_name_prefix='examhub-live-eval')
    app.extensions['live_eval_executor']=executor
    @contextmanager
    def connect():
        db=sqlite3.connect(app.config['DATABASE'],timeout=15);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    with connect() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS tutor_live_evaluations (
          id TEXT PRIMARY KEY,user_id TEXT NOT NULL,request_id TEXT NOT NULL,input_hash TEXT NOT NULL,
          status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,version INTEGER NOT NULL,
          model TEXT NOT NULL,provider TEXT NOT NULL,max_calls INTEGER NOT NULL,model_calls INTEGER NOT NULL,
          error TEXT,report TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS tutor_live_owner ON tutor_live_evaluations(user_id,request_id);
          CREATE TABLE IF NOT EXISTS tutor_live_calls(evaluation_id TEXT NOT NULL,created_at TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS tutor_live_time ON tutor_live_calls(created_at);''')
        for row in db.execute("SELECT id,report FROM tutor_live_evaluations WHERE status IN ('queued','running')").fetchall():
            report=json.loads(row['report'])
            for trial in report['trials']:
                if trial['status'] in ('running','pending'):
                    trial.update(status='interrupted',error='服务重启，未自动重放付费调用',elapsedMs=None)
            refresh_summary(report)
            db.execute("UPDATE tutor_live_evaluations SET status='interrupted',error=?,report=?,version=version+1,updated_at=? WHERE id=?",
                ('服务重启；已预留的调用仍计数，未自动续跑',json.dumps(report,ensure_ascii=False),now(),row['id']))

    def owned(db,key):
        row=db.execute('SELECT * FROM tutor_live_evaluations WHERE id=? AND user_id=?',(key,g.user['id'])).fetchone()
        if row is None:abort(404,description='评测不存在')
        return row
    def view(row):
        return dict(id=row['id'],version=row['version'],status=row['status'],createdAt=row['created_at'],updatedAt=row['updated_at'],
            model=row['model'],provider=row['provider'],maxCalls=row['max_calls'],modelCalls=row['model_calls'],error=row['error'],
            datasetHash=json.loads(row['report'])['datasetHash'],promptHash=json.loads(row['report'])['promptHash'],
            report=json.loads(row['report']),busy=row['id'] in occupied)
    def response(key,code=200):
        with lock,connect() as db:return jsonify(evaluation=view(owned(db,key))),code

    def run(key,settings,report):
        secret=settings['apiKey']
        def encoded():
            # Redact before escaping, also decoding literals in nested/raw JSON strings.
            safe=sanitize_strings(report,lambda text:text.replace(secret,'[REDACTED]') if secret else text)
            for original,trial in zip(report['trials'],safe['trials']):
                for raw,entry in zip(original['steps'],trial['steps']):
                    if raw.get('content')!=entry.get('content'):entry['contentRedacted']=True
            return json.dumps(safe,ensure_ascii=False)
        def active():
            with lock,connect() as db:
                return db.execute('SELECT status FROM tutor_live_evaluations WHERE id=?',(key,)).fetchone()['status']=='running'
        def checkpoint():
            with lock,connect() as db:
                db.execute('BEGIN IMMEDIATE')
                status=db.execute('SELECT status FROM tutor_live_evaluations WHERE id=?',(key,)).fetchone()['status']
                if status not in ('running','cancelled'):return
                if status=='cancelled':
                    for trial in report['trials']:
                        if trial['status'] in ('pending','running'):trial.update(status='cancelled',error='用户取消；已预留的调用仍计数')
                    refresh_summary(report)
                db.execute('UPDATE tutor_live_evaluations SET report=?,version=version+1,updated_at=? WHERE id=?',(encoded(),now(),key))
        def commit(callback):
            with lock,connect() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT status FROM tutor_live_evaluations WHERE id=?',(key,)).fetchone()['status']!='running':return False
                callback()
                refresh_summary(report)
                db.execute('UPDATE tutor_live_evaluations SET report=?,version=version+1,updated_at=? WHERE id=?',(encoded(),now(),key))
            return True
        def reserve(trial):
            with lock,connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT status,user_id,max_calls,model_calls FROM tutor_live_evaluations WHERE id=?',(key,)).fetchone()
                if row['status']!='running':return 'cancelled'
                if row['model_calls']>=row['max_calls']:return 'budget'
                shared=db.execute("SELECT count(*) FROM tutor_live_calls WHERE datetime(created_at)>datetime('now','-1 hour')").fetchone()[0]
                personal=db.execute("SELECT count(*) FROM tutor_live_calls c JOIN tutor_live_evaluations e ON e.id=c.evaluation_id WHERE e.user_id=? AND datetime(c.created_at)>datetime('now','-1 hour')",(row['user_id'],)).fetchone()[0]
                if shared>=120 or personal>=40:return 'rate_limit'
                db.execute('INSERT INTO tutor_live_calls VALUES (?,?)',(key,now()))
                db.execute('UPDATE tutor_live_evaluations SET model_calls=model_calls+1,version=version+1,updated_at=? WHERE id=?',(now(),key))
        def call(messages):
            import ai
            return ai.call_model_response(settings,messages,max_tokens=2000,thinking='disabled' if urlsplit(settings['baseUrl']).hostname=='api.deepseek.com' else None)
        try:
            with lock,connect() as db:
                if not db.execute("UPDATE tutor_live_evaluations SET status='running',version=version+1 WHERE id=? AND status='queued'",(key,)).rowcount:return
            run_report(report,call,reserve,checkpoint,active,commit=commit)
            with lock,connect() as db:
                db.execute("UPDATE tutor_live_evaluations SET status=CASE WHEN status='cancelled' THEN status ELSE 'completed' END,report=?,version=version+1,updated_at=? WHERE id=? AND status IN ('running','cancelled')",(encoded(),now(),key))
        except Exception:
            for trial in report['trials']:
                if trial['status'] in ('running','pending'):trial.update(status='failed',error='评测执行中断，未自动重放调用')
            refresh_summary(report)
            with lock,connect() as db:
                db.execute("UPDATE tutor_live_evaluations SET status=CASE WHEN status='cancelled' THEN status ELSE 'failed' END,error=?,report=?,version=version+1,updated_at=? WHERE id=? AND status IN ('running','cancelled')",
                    ('评测执行中断，已完成内容保留',encoded(),now(),key))
        finally:
            with lock:occupied.discard(key)

    bp=Blueprint('tutor_live',__name__)
    base='/api/tutor/live-evaluations'
    @bp.get(base+'/dataset')
    def dataset():return jsonify(dataset=dataset_info())
    @bp.get(base)
    def history():
        with lock,connect() as db:
            rows=db.execute('SELECT * FROM tutor_live_evaluations WHERE user_id=? ORDER BY created_at DESC LIMIT 10',(g.user['id'],)).fetchall()
            # History is bounded to ten reports; raw trial traces are fetched with each snapshot.
            return jsonify(evaluations=[view(r) for r in rows])
    @bp.post(base)
    def create():
        data,token,fingerprint=request_data()
        if set(data)!={'requestId','caseIds','repeats','maxCalls'}:abort(400,description='评测参数不符合协议')
        try:report=make_report(data['caseIds'],data['repeats'])
        except ValueError as exc:abort(400,description=str(exc))
        if type(data['maxCalls']) is not int or not 1<=data['maxCalls']<=20:abort(400,description='模型调用预算须为 1–20')
        with lock,connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT * FROM tutor_live_evaluations WHERE user_id=? AND request_id=?',(g.user['id'],token)).fetchone()
            if previous:
                if previous['input_hash']!=fingerprint:abort(409,description='同一请求编号的参数发生变化')
                return jsonify(evaluation=view(previous))
            try:settings=app.extensions['ai_settings'](g.user['id'])
            except ValueError as exc:abort(400,description=str(exc))
            owner_ids={r['id'] for r in db.execute('SELECT id FROM tutor_live_evaluations WHERE user_id=?',(g.user['id'],))}
            if occupied & owner_ids or len(occupied)>=2:abort(409,description='评测仍在执行或收尾，请稍后再试')
            report['parameters']['thinking']='disabled' if urlsplit(settings['baseUrl']).hostname=='api.deepseek.com' else 'provider-default'
            key=uid();stamp=now()
            db.execute('INSERT INTO tutor_live_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,g.user['id'],token,fingerprint,'queued',stamp,stamp,1,settings['model'],settings['baseUrl'],data['maxCalls'],0,None,json.dumps(report,ensure_ascii=False)))
            occupied.add(key)
        if app.config.get('LIVE_EVAL_RUN_INLINE'):run(key,settings,report)
        else:
            try:executor.submit(run,key,settings,report)
            except RuntimeError:
                with lock,connect() as db:
                    occupied.discard(key)
                    db.execute("UPDATE tutor_live_evaluations SET status='failed',error='服务正在停止',version=version+1 WHERE id=?",(key,))
        return response(key,202)
    @bp.get(base+'/<key>')
    def get(key):return response(key)
    @bp.post(base+'/<key>/cancel')
    def cancel(key):
        with lock,connect() as db:
            db.execute('BEGIN IMMEDIATE')
            owned(db,key)
            db.execute("UPDATE tutor_live_evaluations SET status='cancelled',version=version+1,updated_at=? WHERE id=? AND status IN ('queued','running')",(now(),key))
        return response(key)
    @bp.get(base+'/<key>/blind')
    def blind(key):
        with lock,connect() as db:
            row=owned(db,key)
            return jsonify(package=blind_package(json.loads(row['report'])))
    @bp.put(base+'/<key>/reviews/<blind_id>')
    def review(key,blind_id):
        data=request.get_json(silent=True)
        if not isinstance(data,dict) or set(data)!={'version','reviewer','reviewerType','scores','notes'}:abort(400,description='复核参数无效')
        scores=data['scores']
        if not isinstance(scores,dict) or set(scores)!=set(RUBRIC) or any(type(v) is not int or not 0<=v<=2 for v in scores.values()):abort(400,description='四项评分必须为 0–2 整数')
        if type(data['version']) is not int or data['reviewerType'] not in ('human','ai-assisted') or any(not isinstance(data[k],str) or not data[k].strip() or len(data[k])>limit for k,limit in (('reviewer',80),('notes',3000))):abort(400,description='请填写复核者与评分依据')
        with lock,connect() as db:
            db.execute('BEGIN IMMEDIATE');row=owned(db,key)
            if key in occupied or row['status'] in ('queued','running'):abort(409,description='请等待评测收尾后再复核')
            if row['version']!=data['version']:abort(409,description='复核版本已变化，请刷新后重试')
            report=json.loads(row['report']);trial=next((t for t in report['trials'] if t['blindId']==blind_id),None)
            if trial is None:abort(404,description='复核条目不存在')
            trial['review']=dict(reviewer=data['reviewer'].strip(),reviewerType=data['reviewerType'],scores=scores,notes=data['notes'].strip(),updatedAt=now())
            db.execute('UPDATE tutor_live_evaluations SET report=?,version=version+1,updated_at=? WHERE id=?',(json.dumps(report,ensure_ascii=False),now(),key))
        return response(key)
    app.register_blueprint(bp)

"""Owner-scoped teaching checkpoints; model calls never hold a database transaction."""
import copy
import hashlib
import json
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from flask import Blueprint, abort, g, jsonify, request
from db import get_db
from repository import accessible, now, uid
from tutor_engine import new_state, public_state, submit_answer, apply_action, rule_action, model_messages


def request_data():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):abort(400,description='请求必须为 JSON 对象')
    token=data.get('requestId')
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,100}',token):
        abort(400,description='请提供有效的请求编号')
    fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return data,token,fingerprint


def register_tutor(app):
    lock=threading.RLock()
    occupied=set()
    executor=ThreadPoolExecutor(max_workers=4,thread_name_prefix='examhub-tutor')
    app.extensions['tutor_executor']=executor
    @contextmanager
    def connect():
        db=sqlite3.connect(app.config['DATABASE'],timeout=15);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    with connect() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS tutor_sessions (
          id TEXT PRIMARY KEY,user_id TEXT NOT NULL,request_id TEXT NOT NULL,input_hash TEXT NOT NULL,
          created_at TEXT NOT NULL,updated_at TEXT NOT NULL,version INTEGER NOT NULL,state TEXT NOT NULL,
          set_id TEXT NOT NULL,set_title TEXT NOT NULL,set_version INTEGER NOT NULL);
          CREATE INDEX IF NOT EXISTS tutor_owner ON tutor_sessions(user_id,request_id);
          CREATE TABLE IF NOT EXISTS tutor_commands(session_id TEXT NOT NULL,request_id TEXT NOT NULL,
          input_hash TEXT NOT NULL,PRIMARY KEY(session_id,request_id));
          CREATE TABLE IF NOT EXISTS tutor_calls(session_id TEXT NOT NULL,created_at TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS tutor_calls_time ON tutor_calls(created_at);''')
        for row in db.execute('SELECT id,state FROM tutor_sessions').fetchall():
            state=json.loads(row['state'])
            if state['status']=='running':
                state.update(status='paused',error='服务重启，教学已暂停。已保存的作答与工具结果仍保留。',stopReason='restart',timingIncomplete=True)
                db.execute('UPDATE tutor_sessions SET state=?,version=version+1 WHERE id=?',(json.dumps(state,ensure_ascii=False),row['id']))

    def save(db,key,state):
        db.execute('UPDATE tutor_sessions SET state=?,version=version+1,updated_at=? WHERE id=?',
                   (json.dumps(state,ensure_ascii=False),now(),key))
    def owned(db,key,user_id):
        row=db.execute('SELECT * FROM tutor_sessions WHERE id=? AND user_id=?',(key,user_id)).fetchone()
        if row is None:abort(404,description='教学会话不存在')
        return row
    def view(row):
        raw=json.loads(row['state']);state=public_state(raw)
        return dict(state,id=row['id'],setId=row['set_id'],setTitle=row['set_title'],setVersion=row['set_version'],
                    createdAt=row['created_at'],updatedAt=row['updated_at'],version=row['version'],busy=row['id'] in occupied,
                    model=raw.get('model'),policyVersion=raw.get('policyVersion','tutor-v3.1'),timingIncomplete=bool(raw.get('timingIncomplete')))
    def response(key,code=200):
        with lock,connect() as db:return jsonify(session=view(owned(db,key,g.user['id']))),code
    def settings_for(mode,user_id):
        if mode=='rule':return None
        try:return app.extensions['ai_settings'](user_id)
        except ValueError as exc:abort(400,description=str(exc))
    def reserve(db,key,user_id):
        # Resolve current ownership from DB, including guest-to-account migration.
        ids={r['id'] for r in db.execute('SELECT id FROM tutor_sessions WHERE user_id=?',(user_id,))}
        if len(occupied)>=8 or occupied & ids:abort(409,description='已有教学请求正在收尾，请稍后重试')
        occupied.add(key)

    def run(key,settings):
        try:
            for step in range(12 if settings is None else 6):
                with lock,connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute('SELECT state,user_id FROM tutor_sessions WHERE id=?',(key,)).fetchone()
                    state=json.loads(row['state'])
                    if state['status']!='running':return
                    if settings is not None:
                        if state['modelCalls']>=32:
                            state.update(status='paused',error='本次会话已达到 32 次模型调用上限，请结束或新建会话。',stopReason='budget')
                            save(db,key,state);return
                        recent=db.execute("SELECT count(*) FROM tutor_calls WHERE datetime(created_at)>datetime('now','-1 hour')").fetchone()[0]
                        personal=db.execute("SELECT count(*) FROM tutor_calls c JOIN tutor_sessions s ON s.id=c.session_id WHERE s.user_id=? AND datetime(c.created_at)>datetime('now','-1 hour')",(row['user_id'],)).fetchone()[0]
                        if recent>=120 or personal>=40:
                            state.update(status='paused',error='已达到教学模型每小时调用额度，请稍后恢复。',stopReason='rate_limit')
                            save(db,key,state);return
                        db.execute('INSERT INTO tutor_calls VALUES (?,?)',(key,now()))
                        state['modelCalls']+=1
                        state['model']=settings['model'];state['provider']=settings['baseUrl'];state['policyVersion']='tutor-v3.4'
                        save(db,key,state)
                started=time.monotonic();action=None;failure=None
                try:
                    if settings is None:action=rule_action(state)
                    else:
                        import ai
                        raw=ai.call_model(settings,model_messages(state))
                        action=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',raw.strip()))
                except Exception:failure='模型调用或输出解析失败，已暂停；可检查配置后继续。'
                elapsed=round((time.monotonic()-started)*1000)
                with lock,connect() as db:
                    fresh=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(key,)).fetchone()['state'])
                    fresh['elapsedMs']+=elapsed
                    if fresh['status']!='running':
                        save(db,key,fresh);return
                    if not failure:
                        candidate=copy.deepcopy(fresh)
                        try:
                            apply_action(candidate,action)
                            fresh=candidate
                            if fresh.get('trace'):fresh['trace'][-1]['elapsedMs']=elapsed
                        except Exception:failure='教学动作未通过工具校验，已暂停；当前作答与已验证证据保留。'
                    if failure:
                        fresh.update(status='paused',error=failure,stopReason='error')
                        fresh.setdefault('trace',[]).append(dict(tool='runtime',status='error',message=failure,elapsedMs=elapsed))
                    save(db,key,fresh)
                    if fresh['status']!='running':return
            with lock,connect() as db:
                state=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(key,)).fetchone()['state'])
                if state['status']=='running':
                    state.update(status='paused',error='本轮已达到工具调用上限，请检查轨迹后继续。',stopReason='turn_budget')
                    save(db,key,state)
        finally:
            with lock:occupied.discard(key)

    def dispatch(key,settings):
        if app.config.get('TUTOR_RUN_INLINE'):run(key,settings)
        else:
            try:executor.submit(run,key,settings)
            except RuntimeError:
                with lock,connect() as db:
                    occupied.discard(key)
                    state=json.loads(db.execute('SELECT state FROM tutor_sessions WHERE id=?',(key,)).fetchone()['state'])
                    state.update(status='paused',error='服务正在停止，请稍后恢复',stopReason='error');save(db,key,state)

    bp=Blueprint('tutor',__name__)
    @bp.get('/api/tutor/sessions')
    def sessions():
        with lock,connect() as db:
            rows=db.execute('SELECT * FROM tutor_sessions WHERE user_id=? ORDER BY created_at DESC LIMIT 100',(g.user['id'],)).fetchall()
            summaries=[]
            for row in rows:
                item=view(row)
                for field in ('events','trace','answers','currentQuestion','pending'):item.pop(field,None)
                summaries.append(item)
            return jsonify(sessions=summaries)

    @bp.post('/api/tutor/sessions')
    def create():
        data,token,fingerprint=request_data();user_id=g.user['id']
        with lock,connect() as db:
            existing=db.execute('SELECT * FROM tutor_sessions WHERE user_id=? AND request_id=?',(user_id,token)).fetchone()
            if existing:
                if existing['input_hash']!=fingerprint:abort(409,description='请求编号已用于其他教学输入')
                return jsonify(session=view(existing)),200
        goal,mode,maximum=data.get('goal'),data.get('mode'),data.get('maxQuestions')
        if not isinstance(goal,str) or not 1<=len(goal.strip())<=1000 or mode not in ('agent','rule') or type(maximum) is not int or not 1<=maximum<=10:
            abort(400,description='请填写学习目标、教练模式与 1–10 道题的上限')
        if not isinstance(data.get('setId'),str):abort(400,description='请选择题集')
        source=accessible(data['setId']);questions=json.loads(source['questions'])
        history={'attempts':0,'answered':0,'correct':0}
        for item in get_db().execute('SELECT snapshot FROM attempts WHERE user_id=? ORDER BY rowid DESC LIMIT 200',(user_id,)):
            attempt=json.loads(item['snapshot'])
            if attempt.get('setId')==source['id']:
                history['attempts']+=1;history['answered']+=len(attempt.get('results',[]));history['correct']+=attempt.get('correct',0)
        for item in get_db().execute('SELECT state FROM tutor_sessions WHERE user_id=? AND set_id=? ORDER BY created_at DESC LIMIT 100',(user_id,source['id'])):
            answers=[a for a in json.loads(item['state'])['answers'] if a['kind']=='question']
            if answers:
                history['attempts']+=1;history['answered']+=len(answers);history['correct']+=sum(a['correct'] is True for a in answers)
        state=new_state(questions,goal.strip(),mode,min(maximum,len(questions)),history)
        config=settings_for(mode,user_id);key=uid();created=now()
        with lock,connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT * FROM tutor_sessions WHERE user_id=? AND request_id=?',(user_id,token)).fetchone()
            if existing:
                if existing['input_hash']!=fingerprint:abort(409,description='请求编号已用于其他教学输入')
                return jsonify(session=view(existing)),200
            recent=db.execute("SELECT count(*) FROM tutor_sessions WHERE user_id=? AND datetime(created_at)>datetime('now','-1 hour')",(user_id,)).fetchone()[0]
            if recent>=10:abort(429,description='本小时教学会话已达上限，请稍后重试')
            reserve(db,key,user_id)
            try:
                db.execute('INSERT INTO tutor_sessions VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                           (key,user_id,token,fingerprint,created,created,1,json.dumps(state,ensure_ascii=False),source['id'],source['title'],source['version']))
            except Exception:
                occupied.discard(key);raise
        dispatch(key,config)
        return response(key,202)

    @bp.get('/api/tutor/sessions/<key>')
    def get_session(key):return response(key)

    @bp.post('/api/tutor/sessions/<key>/commands')
    def command(key):
        data,token,fingerprint=request_data();user_id=g.user['id'];config=None;run_next=False
        with lock,connect() as db:
            db.execute('BEGIN IMMEDIATE');row=owned(db,key,user_id)
            prior=db.execute('SELECT input_hash FROM tutor_commands WHERE session_id=? AND request_id=?',(key,token)).fetchone()
            if prior:
                if prior['input_hash']!=fingerprint:abort(409,description='请求编号已用于其他教学操作')
                return jsonify(session=view(row)),200
            if type(data.get('version')) is not int or data['version']!=row['version']:
                abort(409,description='教学进度已更新，请读取最新状态后继续')
            state=json.loads(row['state']);kind=data.get('type')
            if state['status']=='completed':abort(409,description='本次教学已结束')
            if kind=='stop':state.update(status='paused',error=None,stopReason='user')
            elif kind in ('answer','resume'):
                if key in occupied:abort(409,description='后台请求正在收尾，请稍后继续')
                if kind=='resume' and not state.get('pending') and state['modelCalls']>=32 and state['mode']=='agent':
                    abort(409,description='本次会话已达到模型调用预算，请新建会话')
                if kind=='answer':
                    try:submit_answer(state,data.get('answer'),data.get('turnId'))
                    except ValueError as exc:abort(400,description=str(exc))
                else:
                    if state['status']!='paused':abort(409,description='仅暂停的教学会话可恢复')
                    state['status']='waiting' if state.get('pending') else 'running'
                state.update(error=None,stopReason=None)
                run_next=state['status']=='running'
                if run_next:
                    if state['mode']=='agent' and state['modelCalls']>=32:
                        state.update(status='paused',error='回答已保存；本次会话已达到模型调用上限。',stopReason='budget')
                        run_next=False
                    else:
                        config=settings_for(state['mode'],user_id);reserve(db,key,user_id)
            else:abort(400,description='不支持的教学操作')
            try:
                save(db,key,state)
                db.execute('INSERT INTO tutor_commands VALUES (?,?,?)',(key,token,fingerprint))
            except Exception:
                if run_next:occupied.discard(key)
                raise
        if run_next:dispatch(key,config)
        return response(key,202 if run_next else 200)

    @bp.post('/api/tutor/benchmark')
    def benchmark():
        from tutor_evaluation import benchmark_report
        return jsonify(report=benchmark_report())

    app.register_blueprint(bp)

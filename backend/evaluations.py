"""Owner-scoped quality checks and immutable, no-model evaluation reports."""
import hashlib
import json
from pathlib import Path

from flask import Blueprint, abort, g, jsonify, request
from werkzeug.exceptions import HTTPException

from db import get_db
from quality import RULE_VERSION, check, evaluate_questions, summarize
from repository import accessible, now

FIXTURES = Path(__file__).with_name('eval_fixtures.json')


def benchmark_report():
    raw = FIXTURES.read_bytes()
    dataset = json.loads(raw)
    strategies = []
    for name in ('structural-v1', 'grounded-v2'):
        samples = []
        for sample in dataset['samples']:
            pages = {int(k): v for k, v in sample['pages'].items()} if sample.get('pages') is not None else None
            report = evaluate_questions(sample['questions'], pages)
            checks = [c for item in report['items'] for c in item['checks']]
            issues = sorted({c['code'] for c in checks if c['status'] == 'fail' and
                             (name == 'grounded-v2' or c['code'] in ('structure','answer'))})
            samples.append(dict(id=sample['id'], label=sample['label'], predicted=bool(issues), issues=issues,
                                questions=sample['questions'], description=sample['note'], pages=sample.get('pages')))
        tp = sum(s['label'] and s['predicted'] for s in samples)
        fp = sum(not s['label'] and s['predicted'] for s in samples)
        fn = sum(s['label'] and not s['predicted'] for s in samples)
        tn = sum(not s['label'] and not s['predicted'] for s in samples)
        strategies.append(dict(name=name, precision=tp/(tp+fp) if tp+fp else 0,
                               recall=tp/(tp+fn) if tp+fn else 0, tp=tp, fp=fp, fn=fn, tn=tn, samples=samples))
    return dict(kind='detector-benchmark', datasetId=dataset['datasetId'], datasetHash=hashlib.sha256(raw).hexdigest(),
                ruleVersion=RULE_VERSION, createdAt=now(), sampleCount=len(dataset['samples']), strategies=strategies,
                limitations=['原创小型标注集，仅用于检测器回归，不是模型效果榜；没有调用模型。',
                             'label/predicted=true 表示存在缺陷；precision/recall 以缺陷为正类，零分母记 0。',
                             'structural-v1 仅检查结构与答案选项；grounded-v2 另查解析、引文与词面重复。',
                             '规则无法证明事实正确性、语义唯一性或教学效果；固定集不能代表真实资料分布。'])


def verified_report(questions, existing=()):
    report = evaluate_questions(questions)
    for q, item in zip(questions, report['items']):
        if not isinstance(q, dict) or q.get('citation') is None:
            continue
        from documents import canonical_citation
        try:
            canonical_citation(q['citation'], q.get('source', ''), g.user['id'])
        except (HTTPException, ValueError, TypeError, KeyError) as error:
            # Only an unavailable source can fall back to an unchanged trusted
            # snapshot. Never accept client-provided existing citations.
            if isinstance(error, HTTPException) and error.code == 404 and q['citation'] in existing:
                canonical_citation(q['citation'], q.get('source', ''), g.user['id'], existing=list(existing))
                item['checks'].append(check('citation_authority', 'warn', '原教材不可访问或已删除；仅保留并检查已有引用快照，未重新核验原页'))
            else:
                item['checks'].append(check('citation_authority', 'fail', '引用来源不可验证：请检查教材权限、哈希、物理页码和逐字引文'))
        else:
            item['checks'] = [c for c in item['checks'] if c['code'] != 'citation_snapshot']
            item['checks'].append(check('citation_authority', 'pass', '已根据当前账户教材核验哈希、物理页码和逐字引文'))
    if any(c['code'] == 'citation_authority' and c['status'] == 'pass' for item in report['items'] for c in item['checks']):
        report['limits'][-1] = '标注为原页核验通过的引用已与教材重新核对；原文件不可访问时，只检查保留的引用快照。'
    return summarize(report)


def register_evaluations(app):
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS evaluations (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, snapshot TEXT NOT NULL)')
        db.commit()
    bp = Blueprint('evaluations', __name__)

    @bp.before_request
    def require_header():
        if request.method in ('POST','PUT','DELETE','PATCH') and request.headers.get('X-Requested-With') != 'ExamHub':
            abort(403, description='缺少 ExamHub 请求头')

    @bp.post('/api/quality/check')
    def quality_check():
        data = request.get_json(silent=True)
        questions = data.get('questions') if isinstance(data,dict) else None
        if not isinstance(questions,list) or not 1 <= len(questions) <= 100:
            abort(400, description='questions 必须包含 1 至 100 道题')
        return jsonify(report=verified_report(questions))

    @bp.get('/api/sets/<set_id>/quality')
    def set_quality(set_id):
        row = accessible(set_id, owner=True)
        questions = json.loads(row['questions'])
        existing = [q['citation'] for q in questions if q.get('citation')]
        return jsonify(report=verified_report(questions, existing), version=row['version'])

    @bp.post('/api/evaluations/benchmark')
    def benchmark():
        return jsonify(report=benchmark_report())

    @bp.post('/api/evaluations')
    def create_evaluation():
        data = request.get_json(silent=True)
        ids = data.get('jobIds') if isinstance(data,dict) else None
        if not isinstance(ids,list) or len(ids) != 2 or any(not isinstance(i,str) or not i for i in ids) or ids[0] == ids[1]:
            abort(400, description='需要两个不同的 jobIds')
        db = get_db()
        # Freeze both terminal jobs, their metadata and document title together.
        with db:
            db.execute('BEGIN IMMEDIATE')
            evaluation_id = hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest()
            previous = db.execute('SELECT snapshot FROM evaluations WHERE id=? AND user_id=?',(evaluation_id,g.user['id'])).fetchone()
            if previous:
                return jsonify(evaluation=json.loads(previous['snapshot'])),200
            rows = [db.execute('SELECT * FROM ai_jobs WHERE id=? AND user_id=?',(i,g.user['id'])).fetchone() for i in ids]
            if any(row is None for row in rows):
                abort(404, description='生成任务不存在')
            if any(row['status'] not in ('completed','failed','cancelled') for row in rows):
                abort(409, description='请等待两个生成任务结束')
            metadata = [json.loads(row['metadata'] or '{}') for row in rows]
            if any(meta.get('metricsFinalized') is False for meta in metadata):
                abort(409, description='模型请求仍在收尾，请等待耗时与调用次数记录完成后再生成报告')
            required = ('documentId','sourceHash','pages','count','model')
            if any(not isinstance(meta,dict) or any(not meta.get(k) for k in required) for meta in metadata):
                abort(400, description='只能比较包含完整教材元数据的任务')
            if {meta.get('strategy') for meta in metadata} != {'baseline','grounded'}:
                abort(400, description='需要一个 baseline 与一个 grounded 任务')
            fields = (*required,'title','topic','provider','promptVersion')
            if any(metadata[0].get(k) != metadata[1].get(k) for k in fields):
                abort(400, description='任务教材、资料哈希、页码、题量、模型及提示配置必须相同')
            runs = []
            for row, meta in sorted(zip(rows,metadata),key=lambda pair:pair[1]['strategy']):
                completed = row['status'] == 'completed'
                quality = json.loads(row['quality'] or 'null') or {}
                runs.append(dict(jobId=row['id'],strategy=meta['strategy'],status=row['status'],error=row['error'],
                                 elapsedMs=meta.get('elapsedMs',0),modelCalls=meta.get('modelCalls',0),
                                 questionCount=len(json.loads(row['questions'])) if completed else 0,
                                 passRate=quality.get('passRate',0) if completed else 0,
                                 citationCoverage=quality.get('citationCoverage',0) if completed else 0))
            meta = metadata[0]
            title = meta.get('documentTitle')
            if not title:
                document = db.execute('SELECT title FROM documents WHERE id=? AND owner_id=?',(meta['documentId'],g.user['id'])).fetchone()
                title = document['title'] if document else '已删除教材'
            snapshot = dict(id=evaluation_id,createdAt=now(),kind='generation-comparison',documentTitle=title,
                            sourceHash=meta['sourceHash'],pages=meta['pages'],count=meta['count'],model=meta['model'],runs=runs,
                            limitations=['两次真实任务的快照，不是统计显著的模型排名；失败与取消任务保留，题量和质量指标记 0。',
                                         '规则通过率与引用覆盖不代表事实正确率或学习效果；耗时和调用数来自服务端记录，不估算费用。',
                                         '耗时为 null 表示服务中断而无法完整计时，不作为零耗时比较。'])
            db.execute('INSERT INTO evaluations VALUES (?,?,?)',(snapshot['id'],g.user['id'],json.dumps(snapshot,ensure_ascii=False)))
        return jsonify(evaluation=snapshot),201

    @bp.get('/api/evaluations')
    def list_evaluations():
        rows = get_db().execute('SELECT snapshot FROM evaluations WHERE user_id=? ORDER BY rowid DESC',(g.user['id'],)).fetchall()
        return jsonify(evaluations=[json.loads(row['snapshot']) for row in rows])

    @bp.get('/api/evaluations/<evaluation_id>')
    def get_evaluation(evaluation_id):
        row = get_db().execute('SELECT snapshot FROM evaluations WHERE id=? AND user_id=?',(evaluation_id,g.user['id'])).fetchone()
        if row is None:
            abort(404,description='评测不存在')
        return jsonify(evaluation=json.loads(row['snapshot']))

    app.register_blueprint(bp)

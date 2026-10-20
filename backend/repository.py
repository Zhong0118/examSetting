"""Validated set storage and permission-aware representations."""
import json
from datetime import datetime, timezone
from uuid import uuid4
from flask import abort, g
from db import get_db


def uid():
    return uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


def text_value(data, key, limit=20000, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        abort(400, description=f'{key} 格式不正确')
    return value.strip()


def version_value(data):
    value = data.get('version')
    if type(value) is not int or not 1 <= value <= 2**31 - 1:
        abort(400, description='version 必须是 1 至 2147483647 之间的整数')
    return value


def validate_set(data):
    visibility = data.get('visibility')
    if visibility not in ('public', 'unlisted', 'private'):
        abort(400, description='visibility 格式不正确')
    result = dict(title=text_value(data, 'title', 200, True), description=text_value(data, 'description', 5000),
                  topic=text_value(data, 'topic', 100), visibility=visibility)
    questions = data.get('questions')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 100:
        abort(400, description='题目数量须为 1 至 100')
    output, seen = [], set()
    for item in questions:
        if not isinstance(item, dict) or item.get('type') not in ('single', 'short'):
            abort(400, description='题目类型不正确')
        qid = item.get('id', uid())
        if not isinstance(qid, str) or not qid or len(qid) > 128 or qid in seen:
            abort(400, description='题目 ID 无效或重复')
        seen.add(qid)
        q = {key: text_value(item, key, required=key in ('prompt', 'answer'))
             for key in ('prompt', 'answer', 'explanation', 'source', 'topic')}
        options = item.get('options', [])
        if not isinstance(options, list) or len(options) > 10 or any(not isinstance(o, str) or not o.strip() or len(o) > 2000 for o in options):
            abort(400, description='选项格式不正确')
        if item['type'] == 'single' and (len(options) < 2 or len(set(options)) != len(options) or q['answer'] not in options):
            abort(400, description='单选题需要不同选项，答案必须是其中一个完整选项')
        if item['type'] == 'short' and options:
            abort(400, description='简答题选项必须为空')
        output.append(dict(q, id=qid, type=item['type'], options=options))
    return dict(result, questions=output)


def accessible(set_id, owner=False):
    row = get_db().execute('SELECT s.*, u.name AS author FROM sets s JOIN users u ON u.id=s.owner_id WHERE s.id=?', (set_id,)).fetchone()
    if row is None or (row['owner_id'] != g.user['id'] and (owner or row['visibility'] == 'private')):
        abort(404, description='题集不存在')
    return row


def summary(row):
    bookmarked = get_db().execute('SELECT 1 FROM bookmarks WHERE user_id=? AND set_id=?', (g.user['id'], row['id'])).fetchone() is not None
    return dict(id=row['id'], title=row['title'], description=row['description'], topic=row['topic'],
                visibility=row['visibility'], version=row['version'], questionCount=len(json.loads(row['questions'])),
                author=row['author'], ownerId=row['owner_id'], isOwner=row['owner_id'] == g.user['id'],
                bookmarked=bookmarked, updatedAt=row['updated_at'], sourceSetId=row['source_set_id'])


def questions_without_answers(row):
    return [{k: v for k, v in q.items() if k not in ('answer', 'explanation')} for q in json.loads(row['questions'])]


def detail(row):
    return dict(summary(row), questions=json.loads(row['questions']) if row['owner_id'] == g.user['id'] else questions_without_answers(row))


def insert_set(data, owner_id, source_id=None):
    set_id = uid()
    get_db().execute('INSERT INTO sets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (set_id, owner_id, data['title'], data['description'], data['topic'], data['visibility'], 1,
                      json.dumps(data['questions'], ensure_ascii=False), now(), source_id))
    return set_id

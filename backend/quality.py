"""Explainable lexical rules, not factual or semantic correctness estimates."""
import re

RULE_VERSION = 'grounded-v2'
LIMITS = [
    '规则通过不等于事实正确、答案语义唯一或教学效果良好。',
    '重复检测仅比较规范化题干及字符三元组 Jaccard 相似度（阈值 0.85，近似比较至少 12 字符），不是语义去重。',
    '引用覆盖率表示通过本次引用规则的题目比例，不表示引用能支持答案。',
]


def normalize_text(value):
    from documents import normalize_text as normalize
    return normalize(value) if isinstance(value, str) else ''


def check(code, status, message):
    return dict(code=code, status=status, message=message)


def summarize(report):
    """Recalculate aggregate metrics after routes add authoritative checks."""
    for item in report['items']:
        item['passed'] = not any(c['status'] == 'fail' for c in item['checks'])
    report['passed'] = sum(item['passed'] for item in report['items'])
    total = report['total']
    report['passRate'] = report['passed'] / total if total else 0
    covered = sum(any(c['code'] == 'citation' and c['status'] == 'pass' for c in item['checks'])
                  and not any(c['code'] == 'citation_authority' and c['status'] == 'fail' for c in item['checks'])
                  for item in report['items'])
    report['citationCoverage'] = covered / total if total else 0
    return report


def evaluate_questions(questions, pages=None):
    """Evaluate <=100 questions. pages is an optional {physical_page: text} map.

    Without pages, citation checks validate snapshots only. HTTP routes must
    separately validate document ownership/hash/quote via canonical_citation.
    Missing PDF citations are warnings for legacy text-only questions.
    """
    if not isinstance(questions, list) or len(questions) > 100:
        raise ValueError('questions 必须是最多 100 道题的数组')
    report = dict(ruleVersion=RULE_VERSION, total=len(questions), passed=0, passRate=0,
                  citationCoverage=0, duplicatePairs=[], items=[], limits=list(LIMITS))
    if pages is None:
        report['limits'].append('未提供原页文本；引文仅检查快照结构及 source 一致性，不代表已重新核验原 PDF。')
    fingerprints = []
    ids = [q.get('id') if isinstance(q, dict) else None for q in questions]
    for i, raw in enumerate(questions):
        q = raw if isinstance(raw, dict) else {}
        qid = q.get('id')
        valid_id = isinstance(qid, str) and 0 < len(qid) <= 128 and ids.count(qid) == 1
        options = q.get('options')
        option_shape = isinstance(options, list) and len(options) <= 10 and all(isinstance(o, str) and 0 < len(o) <= 2000 and normalize_text(o) for o in options)
        structure = (valid_id and q.get('type') in ('single', 'short') and
                     isinstance(q.get('prompt'), str) and 0 < len(q['prompt']) <= 20000 and bool(normalize_text(q['prompt'])) and
                     option_shape and ((2 <= len(options) <= 10) if q.get('type') == 'single' else not options))
        checks = [check('structure', 'pass' if structure else 'fail',
                        '题型、题干、唯一 ID 与选项结构有效' if structure else '检查题型、非空题干、唯一 ID、单选 2–10 个选项或简答空选项')]
        answer = normalize_text(q.get('answer'))
        valid_answer = isinstance(q.get('answer'), str) and len(q['answer']) <= 20000 and bool(answer)
        if q.get('type') == 'single':
            opts = [normalize_text(o) for o in options] if option_shape else []
            valid_answer = valid_answer and len(opts) == len(set(opts)) and opts.count(answer) == 1
        checks.append(check('answer', 'pass' if valid_answer else 'fail',
                            '参考答案非空；单选答案精确匹配唯一规范化选项（不判断事实正确性）' if valid_answer else '答案为空、选项规范化后重复，或答案未唯一匹配选项'))
        explanation = q.get('explanation')
        valid_explanation = isinstance(explanation, str) and 0 < len(explanation) <= 20000 and bool(normalize_text(explanation))
        checks.append(check('explanation', 'pass' if valid_explanation else 'fail',
                            '解析非空（未判断解析是否充分或正确）' if valid_explanation else '缺少有效解析'))
        cite = q.get('citation')
        if cite is None:
            checks.append(check('citation', 'warn' if pages is None else 'fail', '未提供 PDF 引用；不能核验原页出处'))
        else:
            valid_cite = isinstance(cite, dict)
            if valid_cite:
                valid_cite = (all(isinstance(cite.get(k), str) and bool(normalize_text(cite[k])) for k in ('documentId','documentTitle','documentHash','quote'))
                              and bool(re.fullmatch(r'[0-9a-fA-F]{64}', cite.get('documentHash', '') if isinstance(cite.get('documentHash'), str) else ''))
                              and type(cite.get('page')) is int and cite['page'] >= 1
                              and normalize_text(cite.get('quote')) == normalize_text(q.get('source')))
            if valid_cite and pages is not None:
                valid_cite = cite['page'] in pages and normalize_text(cite['quote']) in normalize_text(pages[cite['page']])
            checks.append(check('citation', 'pass' if valid_cite else 'fail',
                                ('引文与所给物理页文本及 source 一致' if pages is not None else '引文快照结构与 source 一致') if valid_cite else '引文元数据、页码、source 或逐字引用不一致'))
            if pages is None and valid_cite:
                checks.append(check('citation_snapshot', 'warn', '仅核对引用快照，未读取原 PDF'))
        report['items'].append(dict(questionId=qid if isinstance(qid,str) else f'item-{i+1}', passed=False, checks=checks))
        text = ''.join(c for c in normalize_text(q.get('prompt')).casefold() if c.isalnum())
        # Oversize/malformed prompts already fail structure; don't perform costly
        # pairwise matching on inputs beyond the accepted question field bound.
        text = text if len(text) <= 20000 else ''
        fingerprints.append((text, {text[j:j+3] for j in range(max(0,len(text)-2))}))
    for right, (text_b, grams_b) in enumerate(fingerprints):
        for left in range(right):
            text_a, grams_a = fingerprints[left]
            if not text_a or not text_b:
                continue
            similarity = 1.0 if text_a == text_b else (len(grams_a & grams_b) / len(grams_a | grams_b) if min(len(text_a),len(text_b)) >= 12 else 0)
            if similarity >= 0.85:
                a, b = report['items'][left], report['items'][right]
                report['duplicatePairs'].append(dict(left=a['questionId'],right=b['questionId'],similarity=round(similarity,6)))
                for item, other in [(a,b),(b,a)]:
                    item['checks'].append(check('duplicate', 'fail', f'与 {other["questionId"]} 的题干词面相似度为 {similarity:.3f}，请人工复核'))
    return summarize(report)

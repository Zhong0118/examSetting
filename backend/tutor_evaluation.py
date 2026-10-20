"""Offline teaching-policy/guardrail regression against the real tutor engine.

The scripted policy is a hand-authored sequence, not an LLM or a model mock.
No provider, database, Flask context or learner data is used by this benchmark.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import tutor_engine as engine

REPORT_VERSION = 'tutor-behavior-v1'


def _evidence_ids(state):
    evidence = state.get('evidence', [])
    if isinstance(evidence, dict):
        evidence = evidence.values()
    return [item['evidenceId'] for item in evidence]


def _marker_checkpoint(state, public, markers, step):
    """Exact fixture sentinels across every public field, not semantic leakage."""
    rendered = json.dumps(public, ensure_ascii=False)
    answered = {answer['questionId'] for answer in state['answers'] if answer['kind'] == 'question'}
    unanswered = [marker for marker in markers if marker['questionId'] not in answered]
    return dict(step=step, checkedMarkers=len(unanswered),
                leaks=[dict(marker) for marker in unanswered if marker['marker'] in rendered],
                visibleAnsweredMarkers=[dict(marker) for marker in markers
                                        if marker['questionId'] in answered and marker['marker'] in rendered])


def _observe(public, trace, checkpoints):
    feedback = [event for event in public['events'] if event['type'] == 'feedback']
    summary = public['summary']
    question = public.get('currentQuestion')
    pending = public.get('pending')
    answers = public['answers']
    return dict(status=public['status'], pendingKind=pending['kind'] if pending else None,
                pendingQuestionId=pending['questionId'] if pending else None,
                answered=summary['answered'], correct=summary['correct'], objectiveTotal=summary['objectiveTotal'],
                followups=summary['followups'], askedCount=len(public['asked']),
                uniqueAsked=len(public['asked']) == len(set(public['asked'])),
                lastAnswerCorrect=answers[-1]['correct'] if answers else None,
                feedbackCount=len(feedback), feedbackEvidenceCount=sum(len(event.get('evidence', [])) for event in feedback),
                historyRead=any(item['tool'] == 'read_history' and item['outcome'] == 'applied' for item in trace),
                rejectedCount=sum(item['outcome'] == 'rejected' for item in trace),
                rejectedStateUnchanged=all(item['stateUnchanged'] for item in trace if item['outcome'] == 'rejected'),
                currentQuestionSafe=question is None or set(question) <= {'id', 'type', 'prompt', 'options', 'topic'},
                internalStateHidden=not any(key in public for key in ('questions', 'history', 'evidence')),
                unansweredMarkersHidden=all(not point['leaks'] for point in checkpoints),
                markerCheckpoints=checkpoints,
                modelCalls=public['modelCalls'])


def _run_case(dataset, case, strategy):
    questions = [copy.deepcopy(q) for q in dataset['questions'] if q['id'] in case['questionIds']]
    try:
        state = engine.new_state(questions, case['goal'], 'rule' if strategy == 'rule' else 'agent',
                                 case['maxQuestions'], history=copy.deepcopy(case.get('history', {})))
    except Exception as exc:
        return dict(id=case['id'], title=case['title'], category=case['category'], goal=case['goal'],
                    expected=copy.deepcopy(case['expected']), observed={}, actualTrace=[], passed=False,
                    error=f'{type(exc).__name__}: {exc}',
                    checks=[dict(code=e['code'], message=e['message'], expected=e['equals'], observed=None, passed=False)
                            for e in case['expected']])
    trace, error = [], None
    markers = [marker for marker in dataset['revealMarkers'] if marker['questionId'] in case['questionIds']]
    public = engine.public_state(state)
    checkpoints = [_marker_checkpoint(state, public, markers, 0)]
    for index, step in enumerate(case['setup'] + case['sequences'][strategy], 1):
        before = copy.deepcopy(state)
        action = None
        entry = dict(step=index, operation=step['op'], tool=None, input=None, outcome='error',
                     error=None, stateUnchanged=True, status=state['status'], turnId=state['turnId'], engineTrace=[])
        try:
            if step['op'] == 'rule':
                action = engine.rule_action(state)
            elif step['op'] in ('action', 'probe'):
                action = copy.deepcopy(step['action'])
                if action['args'].get('evidenceIds') == '$retrieved':
                    action['args']['evidenceIds'] = _evidence_ids(state)
            if step['op'] in ('answer', 'answer-probe'):
                entry['input'] = dict(answer=step['answer'], turnId=step.get('turnId', state['turnId']))
                engine.submit_answer(state, step['answer'], entry['input']['turnId'])
            else:
                entry['tool'] = action['tool']
                entry['input'] = action['args']
                engine.apply_action(state, action)
            entry['outcome'] = 'applied'
            if step['op'] in ('probe', 'answer-probe'):
                error = '预期拒绝的动作被引擎接受'
                entry['error'] = error
        except ValueError as exc:
            entry['error'] = str(exc)
            if step['op'] in ('probe', 'answer-probe'):
                entry['outcome'] = 'rejected'
            else:
                error = f'意外拒绝：{exc}'
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
            entry['error'] = error
        public = engine.public_state(state)
        checkpoints.append(_marker_checkpoint(state, public, markers, index))
        entry.update(status=state['status'], turnId=state['turnId'], stateUnchanged=state == before,
                     engineTrace=copy.deepcopy(public['trace'][len(before['trace']):]))
        trace.append(entry)
        if error:
            break
    observed = _observe(public, trace, checkpoints)
    checks = [dict(code=expected['code'], message=expected['message'], expected=expected['equals'],
                   observed=observed[expected['field']], passed=error is None and observed[expected['field']] == expected['equals'])
              for expected in case['expected']]
    return dict(id=case['id'], title=case['title'], category=case['category'], goal=case['goal'],
                expected=copy.deepcopy(case['expected']), observed=observed, checks=checks,
                actualTrace=trace, passed=error is None and all(c['passed'] for c in checks), error=error)


def benchmark_report():
    """Run fixed original scenarios through the current engine; return JSON data."""
    raw = Path(__file__).with_name('tutor_fixtures.json').read_bytes()
    dataset = json.loads(raw)
    strategies = []
    for name, label in [('rule', '规则教练动作序列'), ('scripted-agent', '人工编排的受控 Agent 动作序列')]:
        cases = [_run_case(dataset, case, name) for case in dataset['cases']]
        checks = [check for case in cases for check in case['checks']]
        passed = sum(check['passed'] for check in checks)
        strategies.append(dict(name=name, label=label, cases=cases,
                               summary=dict(checks=len(checks), passedChecks=passed, passRate=passed / len(checks) if checks else 0,
                                            cases=len(cases), passedCases=sum(case['passed'] for case in cases),
                                            errorCases=sum(case['error'] is not None for case in cases))))
    return dict(kind='tutor-behavior-benchmark', version=REPORT_VERSION, datasetId=dataset['id'],
                datasetVersion=dataset['version'], datasetHash=hashlib.sha256(raw).hexdigest(),
                createdAt=datetime.now(timezone.utc).isoformat(), caseCount=len(dataset['cases']), strategies=strategies,
                limitations=[
                    '这是固定原创场景上的离线教学策略与引擎约束回归，不是学习效果评估或掌握度测量。',
                    'scripted-agent 是人工编排的脚本动作，没有调用模型；其通过率不能说明真实模型优于规则教练。',
                    '两策略使用相同题目、初始状态与期望；共享准备步骤和拒绝探针用于检验引擎，不能视为策略自主发现问题。',
                    '规则策略不具备理由追问等能力，对这些教学期望未通过会如实保留；本数据集不是代表性教学样本。',
                    '检查通过率按预先定义的检查项等权计算，错误样本保留在分母；不是事实正确率或用户满意度。',
                    'currentQuestionSafe 仅检查当前题描述符字段白名单；另逐 checkpoint 扫描完整公开 JSON 中的固定唯一标记，已答题标记允许显示。',
                    '唯一标记检查只检测原样字符串泄漏，不证明能识别改写、语义泄漏或任意真实题目；单选答案本来就在公开选项中，不作为隐藏字符串检测。',
                    '题数预算与等待用户由真实引擎检验；网络供应商质量、服务层调用预算、持久化和并发不在此纯引擎基准范围内。',
                ])


if __name__ == '__main__':
    print(json.dumps(benchmark_report(), ensure_ascii=False, indent=2))

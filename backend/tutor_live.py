"""Live policy evaluation on original fixed learners; no simulated learning claim."""
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import time
import uuid
import tutor_engine as engine

RUBRIC = dict(accuracy='事实正确：0 错误或无反馈，1 部分正确，2 正确且无关键遗漏',
              grounding='证据支持：0 伪造或矛盾，1 支持不充分，2 与证据一致且说明边界',
              diagnosis='误区诊断：0 忽略或误诊，1 指出问题，2 结合回答解释误区或验证理由',
              actionability='下一步：0 无建议，1 泛泛建议，2 给出具体可执行的复习或验证步骤')
LIMITS = ['学生使用固定答案和固定理由，不是真人，也不是自适应学生模型；不能据此估计学习收益。',
          '行为检查只衡量已定义的动作与事件，不自动判定反馈事实正确或诊断质量。',
          '同一开发者编写的数据集不是独立测试集；少量重复只提供探索性证据，不能说明泛化或统计显著性。',
          '未完成、预算耗尽和失败 trial 均保留分母；缺失 token 用量显示未知，不推算费用。',
          '遮蔽包只移除条件字段，语言风格仍可能暴露策略；复核者类型明确记录，AI 辅助复核不等于独立人工评估。']


def sanitize_strings(value,clean):
    """Clean decoded strings too, including JSON literals inside raw provider text."""
    if isinstance(value,dict):return {sanitize_strings(k,clean):sanitize_strings(v,clean) for k,v in value.items()}
    if isinstance(value,list):return [sanitize_strings(v,clean) for v in value]
    if not isinstance(value,str):return value
    if '\\' in value:
        try:json.loads(value)
        except ValueError:
            # Malformed quotes cannot delimit literals reliably. Probe escapes
            # without trusting those boundaries; keep benign text byte-for-byte.
            probe=value
            for _ in range(8):
                decoded=re.sub(r'\\(?:u[0-9a-fA-F]{4}|["\\/bfnrt])',
                               lambda m:json.loads('"'+m.group()+'"'),probe)
                if clean(decoded)!=decoded:return '[REDACTED] escaped sensitive text'
                if decoded==probe:break
                probe=decoded
            else:return '[REDACTED] deeply escaped text'
    def literal(match):
        raw=match.group()
        try:decoded=json.loads(raw)
        except ValueError:return raw
        safe=sanitize_strings(decoded,clean)
        return raw if safe==decoded else json.dumps(safe,ensure_ascii=False)
    return clean(re.sub(r'"(?:[^"\\]|\\.)*"',literal,value))


def _strip_reasoning(content):
    """Remove only recognized tagged blocks, including nested/unclosed blocks."""
    parts=[];stack=[];end=0;start=0
    for tag in re.finditer(r'<(/?)(think|analysis)\b[^>]*>',content,re.I):
        name=tag[2].lower()
        if not tag[1]:
            if not stack:start=tag.start()
            stack.append(name)
        elif name in stack:
            while stack.pop()!=name:pass
            if not stack:
                parts.extend((content[end:start],'[REDACTED reasoning]'));end=tag.end()
    if stack:return ''.join(parts)+content[end:start]+'[REDACTED reasoning]'
    return ''.join(parts)+content[end:]


def _dataset():
    raw=Path(__file__).with_name('tutor_live_cases.json').read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def dataset_info():
    data,digest=_dataset()
    return dict(id=data['id'],version=data['version'],hash=digest,
                cases=[{k:c[k] for k in ('id','title','goal')} for c in data['cases']],limitations=LIMITS)


def refresh_summary(report):
    report['summary']={}
    for strategy in ('rule','agent'):
        trials=[t for t in report['trials'] if t['strategy']==strategy]
        checks=[c for t in trials for c in t['checks']]
        report['summary'][strategy]=dict(trials=len(trials),completed=sum(t['status']=='completed' for t in trials),
            passed=sum(t['status']=='completed' and all(c['passed'] for c in t['checks']) for t in trials),
            checks=len(checks),passedChecks=sum(c['passed'] for c in checks),modelCalls=sum(t['modelCalls'] for t in trials))


def _checks(state,case,status,invalid=False):
    events=state.get('events',[])
    values=[('completed','正常结束教学',status=='completed'),
            ('answered','已等待并接收固定学生的主回答',any(a['kind']=='question' for a in state.get('answers',[]))),
            ('feedback','提交回答后提供反馈',any(e['type']=='feedback' for e in events))]
    if case['requireEvidence']:
        values.append(('evidence','反馈带已检索的原文证据',any(e['type']=='feedback' and e.get('evidence') for e in events)))
    if case['requireFollowup']:
        values.append(('followup','按目标追问一次并接收理由',any(a['kind']=='followup' for a in state.get('answers',[]))))
    if case['requireHistory']:
        values.append(('history','读取初始历史摘要',any(t['tool']=='read_history' for t in state.get('trace',[]))))
    values.append(('valid_actions','模型动作均通过服务端校验',bool(state.get('trace')) and not invalid))
    return [dict(code=code,message=message,passed=bool(passed)) for code,message,passed in values]


def make_report(case_ids,repeats):
    data,digest=_dataset();cases={c['id']:c for c in data['cases']}
    if not isinstance(case_ids,list) or not 1<=len(case_ids)<=4 or any(not isinstance(k,str) or k not in cases for k in case_ids) or len(set(case_ids))!=len(case_ids):
        raise ValueError('请选择 1–4 个不同的原创场景')
    if type(repeats) is not int or not 1<=repeats<=3:raise ValueError('重复次数须为 1–3')
    trials=[]
    for repeat in range(1,repeats+1):
        for case_id in case_ids:
            case=cases[case_id]
            for strategy in ('rule','agent'):
                trials.append(dict(id=uuid.uuid4().hex,blindId=uuid.uuid4().hex,caseId=case_id,title=case['title'],strategy=strategy,
                    repeat=repeat,status='pending',error=None,modelCalls=0,elapsedMs=0,usage=None,steps=[],session=None,
                    checks=_checks({},case,'pending'),review=None))
    report=dict(kind='live-tutor-evaluation',graderVersion='live-behavior-v2',datasetId=data['id'],datasetVersion=data['version'],datasetHash=digest,
        promptHash=hashlib.sha256(engine.SYSTEM.encode()).hexdigest(),parameters=dict(temperature=0.4,max_tokens=2000),
        learner='fixed-script',caseSnapshots=[copy.deepcopy(cases[k]) for k in case_ids],trials=trials,summary={},limitations=LIMITS.copy(),rubric=RUBRIC.copy())
    refresh_summary(report)
    return report


def run_report(report,call,reserve,checkpoint,active,commit=None):
    """reserve persists quota BEFORE network; commit(callback) serializes with cancel.

    A successful dispatchStarted commit is the dispatch boundary: cancellation
    afterwards may leave an in-flight, billable request. No network runs in commit.
    """
    if commit is None:
        def commit(callback):
            if not active():return False
            callback();checkpoint();return True
    cases={c['id']:c for c in report['caseSnapshots']}
    for trial in report['trials']:
        case=cases[trial['caseId']]
        state=engine.new_state([case['question']],case['goal'],trial['strategy'],1,case['history'])
        started=time.monotonic();invalid=False;usage_complete=True;usage_total=dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)
        trial['status']='running'
        for step in range(40):
            if not active():trial.update(status='cancelled',error='用户取消；已发送的请求可能仍计费');break
            trial['session']=engine.public_state(state);refresh_summary(report);checkpoint()
            if state['status']=='completed':trial['status']='completed';break
            if state['status']=='waiting':
                answer=case['learnerAnswer'] if state['pending']['kind']=='question' else case['learnerReason']
                def learn():
                    result=engine.submit_answer(state,answer,state['turnId'])
                    trial['steps'].append(dict(kind='learner',result=result))
                    trial['session']=engine.public_state(state)
                if not commit(learn):trial.update(status='cancelled',error='用户取消，未提交学生回答');break
                continue
            if trial['strategy']=='rule':
                action=engine.rule_action(state)
                def rule():
                    result=engine.apply_action(state,action)
                    trial['steps'].append(dict(kind='rule',action=action,result=result))
                    trial['session']=engine.public_state(state)
                if not commit(rule):trial.update(status='cancelled',error='用户取消，未执行规则动作');break
                continue
            if trial['modelCalls']>=10:trial.update(status='budget',error='本 trial 达到 10 次调用上限');break
            reason=reserve(trial)
            if reason:trial.update(status='cancelled' if reason=='cancelled' else 'budget',error=reason);break
            trial['modelCalls']+=1;state['modelCalls']=trial['modelCalls']
            messages=engine.model_messages(state)
            entry=dict(kind='model',messages=messages,content=None,usage=None,model=None,elapsedMs=None,action=None,result=None,error=None,dispatchStarted=False)
            trial['steps'].append(entry);refresh_summary(report);checkpoint()
            # Reservation/checkpoint can race with cancel; recheck at dispatch.
            if not active() or not commit(lambda:entry.update(dispatchStarted=True)):
                usage_complete=False;trial.update(status='cancelled',error='用户取消，预留调用未发送');break
            tick=time.monotonic()
            try:
                result=call(messages)
                raw=result['content'];content=sanitize_strings(raw,_strip_reasoning)
                entry.update(content=content,usage=result.get('usage'),model=sanitize_strings(result.get('model'),_strip_reasoning))
                if content!=raw:entry['contentRedacted']=True
                usage=result.get('usage')
                if usage is None:usage_complete=False
                else:
                    for key in usage_total:usage_total[key]+=usage[key]
                if not active():trial.update(status='cancelled',error='用户取消，迟到动作未执行');break
                # Validate the original protocol; stripping tags must not rescue non-JSON.
                action=sanitize_strings(json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',raw.strip())),_strip_reasoning)
                def apply():
                    entry['action']=action
                    entry['result']=engine.apply_action(state,action)
                    trial['session']=engine.public_state(state)
                if not commit(apply):trial.update(status='cancelled',error='用户取消，迟到动作未执行');break
            except Exception:
                if entry['content'] is None:usage_complete=False
                entry['error']='模型请求、JSON 或工具校验失败；原始 content 如有返回已保留'
                trial.update(status='failed',error=entry['error']);invalid=True;break
            finally:
                entry['elapsedMs']=round((time.monotonic()-tick)*1000)
        else:trial.update(status='budget',error='达到 40 步执行上限')
        trial.update(session=engine.public_state(state),elapsedMs=round((time.monotonic()-started)*1000),
                     usage=usage_total if trial['modelCalls'] and usage_complete else None)
        trial['checks']=_checks(state,case,trial['status'],invalid)
        refresh_summary(report);checkpoint()


def blind_package(report):
    cases={c['id']:c for c in report['caseSnapshots']};items=[]
    for trial in report['trials']:
        case=cases[trial['caseId']];session=trial['session'] or {}
        events=[{k:copy.deepcopy(e[k]) for k in ('type','message','evidence') if k in e}
                for e in session.get('events',[]) if e['type'] in ('feedback','followup')]
        items.append(dict(blindId=trial['blindId'],caseTitle=case['title'],goal=case['goal'],questions=[copy.deepcopy(case['question'])],
                          answers=copy.deepcopy(session.get('answers',[])),events=events))
    random.SystemRandom().shuffle(items)
    return dict(kind='tutor-blind-review',version='1.0',datasetHash=report['datasetHash'],rubric=RUBRIC.copy(),items=items,
                limitations=['移除条件/模型/轨迹字段且随机排列；文风仍可能暴露策略，复核包不能单独证明正式盲评。'])

"""Pure policy and redaction regressions, without Flask or model calls."""
import copy
import importlib.util
import json
import unittest

AVAILABLE = importlib.util.find_spec('tutor_engine') is not None
if AVAILABLE:
    from tutor_engine import new_state, apply_action, submit_answer, rule_action, model_messages, public_state


def questions():
    return [dict(id='q1',type='single',prompt='Which transport protocol provides ordered delivery?',options=['TCP','UDP'],
                 answer='TCP',explanation='SECRET_EXPLANATION_ONE',source='TCP provides ordered delivery using sequence numbers.',topic='Networking',
                 citation=dict(documentId='doc1',documentTitle='Original notes',documentHash='a'*64,page=2,quote='TCP provides ordered delivery using sequence numbers.')),
            dict(id='q2',type='short',prompt='Explain atomicity.',options=[],answer='SECRET_REFERENCE_TWO',explanation='SECRET_EXPLANATION_TWO',
                 source='数据库事务保证原子性，事务操作全部成功或全部撤销。',topic='Database',citation=None)]


def action(tool,**args):
    return dict(tool=tool,args=args)


class TutorEngine(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AVAILABLE,'tutor_engine pure functions must be implemented')
        self.state=new_state(questions(),'Diagnose understanding','agent',2,dict(attempts=3,answered=5,correct=2))

    def ask(self,state=None,qid='q1'):
        s=state if state is not None else self.state
        apply_action(s,action('ask_question',questionId=qid))
        return s

    def answered(self,answer='UDP'):
        s=self.ask();submit_answer(s,answer,s['turnId']);return s

    def test_new_state_copies_snapshot_clamps_limit_and_rejects_bad_inputs(self):
        source=questions();history={'attempts':1}
        s=new_state(source,'Goal','rule',10,history)
        source[0]['answer']='changed';history['attempts']=99
        self.assertEqual((s['maxQuestions'],s['status'],s['turnId'],s['modelCalls'],s['elapsedMs']),(2,'running',0,0,0))
        self.assertEqual(s['questions'][0]['answer'],'TCP');self.assertEqual(s['history']['attempts'],1)
        for args in [(questions(),'','agent',1),(questions(),'g','unknown',1),(questions(),'g','rule',True),
                     (questions(),'g','rule',0),(questions(),'g','rule',11),([],'g','rule',1),([questions()[0]]*2,'g','rule',2)]:
            with self.subTest(args=args),self.assertRaises(ValueError):new_state(*args)

    def test_waiting_hides_answers_sources_history_and_raw_tool_fields(self):
        s=self.ask()
        s['trace'].append(dict(tool='model',status='error',message='模型响应格式无效',args={'apiKey':'KEY_SECRET'},result={'answer':'LEAK'},elapsedMs=3))
        public=public_state(s)
        self.assertEqual(set(public['currentQuestion']),{'id','type','prompt','options','topic'})
        self.assertEqual(public['pending'],dict(kind='question',questionId='q1',prompt=questions()[0]['prompt']))
        for secret in ['SECRET_EXPLANATION_ONE','SECRET_REFERENCE_TWO','SECRET_EXPLANATION_TWO','KEY_SECRET','LEAK','sequence numbers','数据库事务']:
            self.assertNotIn(secret,json.dumps(public))
        for key in ['questions','history','evidence']:self.assertNotIn(key,public)
        public['currentQuestion']['options'].append('mutated')
        self.assertEqual(s['questions'][0]['options'],['TCP','UDP'])

    def test_tools_exact_arguments_and_wait_barrier_fail_atomically(self):
        bads=[None,[],{},dict(tool='read_history'),dict(tool='read_history',args=[],extra=1),
              action('read_history',userId='other'),action('search_materials',query='TCP',documentId='other'),
              action('ask_question',questionId='missing'),action('ask_question',questionId=[]),action('search_materials',query=''),
              action('give_feedback',message='Advice'),action('ask_followup',prompt='Why?')]
        bads += [action(tool) for tool in [None,'eval','read_document','submit_answer',[]]]
        for bad in bads:
            before=copy.deepcopy(self.state)
            with self.subTest(bad=bad),self.assertRaises(ValueError):apply_action(self.state,bad)
            self.assertEqual(self.state,before)
        for status in ['waiting','paused','completed']:
            s=new_state(questions(),'Goal','agent',2);self.ask(s);s['status']=status
            with self.assertRaises(ValueError):apply_action(s,action('read_history'))

    def test_answer_turn_option_and_counters_then_repeat_rejected(self):
        s=self.ask();s.update(modelCalls=4,elapsedMs=123)
        for answer,turn in [('TCP',0),('TCP',True),('TCP','1'),('ICMP',1),('',1),(None,1)]:
            before=copy.deepcopy(s)
            with self.assertRaises(ValueError):submit_answer(s,answer,turn)
            self.assertEqual(s,before)
        result=submit_answer(s,'TCP',1)
        self.assertEqual((s['modelCalls'],s['elapsedMs']),(4,123))
        self.assertEqual((s['status'],s['pending']),('running',None))
        self.assertIs(result['correct'],True)
        self.assertEqual(result['citation'],questions()[0]['citation'])
        self.assertEqual(result['explanation'],'SECRET_EXPLANATION_ONE')
        result['correct']=False
        self.assertIs(s['answers'][0]['correct'],True)
        with self.assertRaises(ValueError):submit_answer(s,'TCP',1)
        with self.assertRaises(ValueError):apply_action(s,action('ask_question',questionId='q1'))

    def test_followup_once_after_answer_and_short_answers_not_autograded(self):
        s=self.answered()
        apply_action(s,action('ask_followup',prompt='Why did you choose that protocol?'))
        self.assertEqual((s['pending']['kind'],s['turnId']),('followup',2))
        submit_answer(s,'I confused the transport protocols.',2)
        self.assertIsNone(s['answers'][-1]['correct'])
        self.assertEqual(public_state(s)['summary'],dict(answered=1,correct=0,objectiveTotal=1,followups=1))
        with self.assertRaises(ValueError):apply_action(s,action('ask_followup',prompt='Another reason?'))
        self.ask(s,'q2');submit_answer(s,'All operations succeed or none do.',s['turnId'])
        self.assertIsNone(s['answers'][-1]['correct'])
        self.assertEqual(public_state(s)['summary'],dict(answered=2,correct=0,objectiveTotal=1,followups=1))

    def test_lexical_snapshot_retrieval_top_three_stable_ids_chinese_and_english(self):
        qs=questions()+[dict(questions()[0],id=f'q{i}') for i in range(3,6)]
        s=new_state(qs,'Goal','agent',5)
        self.assertEqual(apply_action(s,action('search_materials',query='TCP'))['evidence'],[])
        for qid in ['q1','q2','q3','q4','q5']:
            self.ask(s,qid);submit_answer(s,'TCP' if qid!='q2' else 'My explanation',s['turnId'])
        found=apply_action(s,action('search_materials',query='TCP sequence numbers'))
        self.assertEqual(len(found['evidence']),3)
        ids=[e['evidenceId'] for e in found['evidence']]
        again=apply_action(s,action('search_materials',query='TCP sequence numbers'))
        self.assertEqual(ids,[e['evidenceId'] for e in again['evidence']])
        chinese=apply_action(s,action('search_materials',query='事务原子性'))
        self.assertEqual(chinese['evidence'][0]['questionId'],'q2')
        self.assertEqual(chinese['evidence'][0]['quote'],questions()[1]['source'])
        self.assertIsNone(chinese['evidence'][0]['citation'])
        self.assertEqual(apply_action(s,action('search_materials',query='unrelated dinosaur'))['evidence'],[])
        self.assertNotIn('sequence numbers',json.dumps(public_state(s)['trace']))

    def test_feedback_rejects_forged_and_unanswered_references(self):
        s=self.answered()
        for args in [dict(message='Feedback',evidenceIds=['invented']),dict(message='Feedback',citation=questions()[0]['citation']),dict(message='Feedback',evidenceIds='id')]:
            with self.assertRaises(ValueError):apply_action(s,dict(tool='give_feedback',args=args))
        evidence=apply_action(s,action('search_materials',query='TCP sequence'))['evidence'][0]
        apply_action(s,action('give_feedback',message='Consider ordering.',evidenceIds=[evidence['evidenceId']]))
        self.assertEqual(s['events'][-1]['evidence'][0]['citation'],questions()[0]['citation'])
        self.assertEqual(apply_action(s,action('search_materials',query='事务原子性'))['evidence'],[])
        future=dict(evidenceId='old-future',questionId='q2',quote=questions()[1]['source'],citation=None)
        s['evidence'].append(future)
        with self.assertRaises(ValueError):apply_action(s,action('give_feedback',message='Future answer',evidenceIds=[future['evidenceId']]))
        # A later search must not invalidate a previously retrieved ID.
        apply_action(s,action('give_feedback',message='Review ordering.',evidenceIds=[evidence['evidenceId']]))
        apply_action(s,action('give_feedback',message='Practice more.'))
        self.assertEqual(s['events'][-1]['evidence'],[])
        self.assertIn('未',s['events'][-1]['message'])

    def test_rule_policy_once_feedback_next_and_server_finish_summary(self):
        s=new_state(questions(),'Goal','rule',2)
        apply_action(s,rule_action(s));submit_answer(s,'TCP',s['turnId'])
        self.assertEqual(rule_action(s)['tool'],'give_feedback')
        apply_action(s,rule_action(s))
        self.assertIn('SECRET_EXPLANATION_ONE',s['events'][-1]['message'])
        self.assertEqual(rule_action(s),action('ask_question',questionId='q2'))
        apply_action(s,rule_action(s));submit_answer(s,'Not sure.',s['turnId'])
        apply_action(s,rule_action(s));apply_action(s,rule_action(s))
        self.assertEqual(s['status'],'completed')
        self.assertEqual(public_state(s)['summary'],dict(answered=2,correct=1,objectiveTotal=1,followups=0))
        self.assertEqual(len([e for e in s['events'] if e['type']=='feedback']),2)
        self.assertEqual(s['modelCalls'],0)

    def test_question_budget_and_free_text_bounds(self):
        s=new_state(questions(),'Goal','agent',1);self.ask(s,'q2')
        for value in ['', ' '*4, 'x'*6001, 42]:
            with self.assertRaises(ValueError):submit_answer(s,value,1)
        submit_answer(s,'x'*6000,1)
        with self.assertRaises(ValueError):apply_action(s,action('ask_question',questionId='q1'))
        apply_action(s,action('finish',summary='Completed practice.'))
        self.assertEqual(s['events'][-1]['summary']['answered'],1)
        self.assertEqual(s['events'][-1]['summary']['objectiveTotal'],0)

    def test_model_protocol_has_no_unanswered_reference_fields_and_is_deterministic(self):
        msgs=model_messages(self.state)
        self.assertEqual([m['role'] for m in msgs],['system','user'])
        self.assertIn('ask_question',msgs[0]['content']);self.assertIn('give_feedback',msgs[0]['content'])
        self.assertTrue(json.loads(msgs[1]['content']))
        for secret in ['SECRET_EXPLANATION_ONE','SECRET_EXPLANATION_TWO','SECRET_REFERENCE_TWO']:self.assertNotIn(secret,json.dumps(msgs))
        s=self.answered()
        self.assertIn('SECRET_EXPLANATION_ONE',json.dumps(model_messages(s)))
        self.assertEqual(model_messages(s),model_messages(s))

    def test_long_rule_explanation_does_not_pause_valid_session(self):
        qs=questions();qs[0]['explanation']='长解析'*6000
        s=new_state(qs,'Goal','rule',1)
        self.ask(s);submit_answer(s,'TCP',s['turnId'])
        apply_action(s,rule_action(s))
        self.assertEqual(s['events'][-1]['type'],'feedback')
        self.assertEqual(s['answers'][0]['explanation'],qs[0]['explanation'])
        apply_action(s,rule_action(s))
        self.assertEqual(s['status'],'completed')

    def test_model_context_is_bounded_and_evidence_preview_is_real_prefix(self):
        qs=[]
        for n in range(100):
            q=questions()[1]
            q.update(id=f'q{n}',prompt='p'*20000,answer='a'*20000,explanation='e'*20000,source='material '+('原文'*9000),topic='t'*20000)
            qs.append(q)
        s=new_state(qs,'g'*1000,'agent',10)
        self.ask(s,'q0');submit_answer(s,'u'*6000,s['turnId'])
        found=apply_action(s,action('search_materials',query='material'))['evidence']
        messages=model_messages(s)
        self.assertLess(len(json.dumps(messages,ensure_ascii=False)),35000)
        payload=json.loads(messages[1]['content'])
        self.assertEqual(len(payload['availableQuestions']),20)
        self.assertTrue(payload['evidence'][0]['truncated'])
        self.assertEqual(payload['evidence'][0]['quotePreview'],found[0]['quote'][:1500])
        self.assertEqual(s['evidence'][0]['quote'],found[0]['quote'])

    def test_checkpoint_roundtrip_keeps_tool_policy_and_retrieved_ids(self):
        s=self.answered('TCP')
        result=apply_action(s,action('search_materials',query='TCP'))
        s=json.loads(json.dumps(s))
        eid=result['evidence'][0]['evidenceId']
        apply_action(s,action('give_feedback',message='Review the excerpt.',evidenceIds=[eid]))
        self.assertEqual(s['events'][-1]['evidence'][0]['evidenceId'],eid)
        s.update(status='paused',error='暂停',stopReason='stop',modelCalls=8,elapsedMs=456)
        before=copy.deepcopy(s)
        with self.assertRaises(ValueError):apply_action(s,action('finish',summary='Done'))
        self.assertEqual(s,before)
        s['status']='running'
        apply_action(s,action('finish',summary='Done'))
        self.assertEqual((s['modelCalls'],s['elapsedMs']),(8,456))

    def test_future_sources_never_enter_model_context_even_from_old_checkpoint(self):
        marker='FUTURE_REFERENCE_9e53b1'
        qs=questions();qs[1].update(answer=marker,source='Recovery token is '+marker)
        s=new_state(qs,'Goal','agent',2)
        self.assertEqual(apply_action(s,action('search_materials',query='Recovery token'))['evidence'],[])
        self.ask(s);submit_answer(s,'TCP',s['turnId'])
        self.assertEqual(apply_action(s,action('search_materials',query='Recovery token'))['evidence'],[])
        # A legacy checkpoint may contain evidence retrieved before this boundary.
        s['evidence'].append(dict(evidenceId='legacy-future',questionId='q2',quote=qs[1]['source'],citation=None))
        s['_lastEvidenceIds']=['legacy-future']
        s=json.loads(json.dumps(s))
        for output in [model_messages(s),public_state(s)]:
            self.assertNotIn(marker,json.dumps(output))
        for tool,args in [('give_feedback',{'message':'TCP and UDP are useful to compare.'}),
                          ('ask_followup',{'prompt':'Why does TCP preserve ordering?'}),
                          ('finish',{'summary':'Review TCP and UDP after this exercise.'})]:
            candidate=copy.deepcopy(s)
            apply_action(candidate,dict(tool=tool,args=args))
            self.assertNotIn(marker,json.dumps(public_state(candidate)))
            self.assertIn(next(iter(args.values())),public_state(candidate)['events'][-1]['message'])
        # Once the second primary answer is submitted its excerpt is available.
        self.ask(s,'q2');submit_answer(s,'My answer',s['turnId'])
        found=apply_action(s,action('search_materials',query='Recovery token'))['evidence']
        self.assertEqual(found[0]['questionId'],'q2')
        self.assertIn(marker,json.dumps(model_messages(s)))

    def test_read_history_private_trace_and_detached_return(self):
        result=apply_action(self.state,action('read_history'))
        self.assertEqual(result['history'],dict(attempts=3,answered=5,correct=2))
        self.assertEqual(self.state['trace'][-1]['status'],'ok')
        self.assertGreaterEqual(self.state['trace'][-1]['elapsedMs'],0)
        result['history']['attempts']=99
        self.assertEqual(self.state['history']['attempts'],3)
        self.assertNotIn('history',public_state(self.state))


if __name__=='__main__':unittest.main()

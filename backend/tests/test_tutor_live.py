"""Real engine evaluation, not a scripted replacement for the model policy."""
import copy
import json
import unittest
from unittest.mock import patch


class LiveRunner(unittest.TestCase):
    def test_new_grader_counts_valid_executed_actions_without_requiring_completion(self):
        from tutor_live import make_report,run_report
        report=make_report(['tcp-misconception'],1)
        agent=report['trials'][1]
        self.assertFalse(next(c['passed'] for c in agent['checks'] if c['code']=='valid_actions'))
        run_report(report,lambda m:dict(content='{"tool":"read_history","args":{}}',usage=None,model='m'),
                   lambda t:None,lambda:None,lambda:True)
        self.assertEqual(agent['modelCalls'],10)
        self.assertEqual(agent['status'],'budget')
        self.assertFalse(next(c['passed'] for c in agent['checks'] if c['code']=='completed'))
        self.assertTrue(next(c['passed'] for c in agent['checks'] if c['code']=='valid_actions'))
        self.assertEqual(report['graderVersion'],'live-behavior-v2')

    def test_tagged_reasoning_is_removed_but_non_json_protocol_still_fails(self):
        from tutor_live import make_report,run_report
        action='{"tool":"finish","args":{"summary":"safe final"}}'
        for content in ('<think>PRIVATE_THOUGHT</think>\n'+action,
                        '<analysis>PRIVATE_THOUGHT</analysis>\n'+action,
                        '<think>PRIVATE_THOUGHT', '<analysis>PRIVATE_THOUGHT',
                        '<think>PRIVATE_THOUGHT<think>INNER_THOUGHT</think>TAIL_THOUGHT</think>\n'+action,
                        '<THINK>PRIVATE_THOUGHT<analysis>INNER_THOUGHT</analysis>TAIL_THOUGHT</THINK>\n'+action):
            with self.subTest(content=content):
                report=make_report(['tcp-misconception'],1)
                run_report(report,lambda m:dict(content=content,usage=None,model='m'),lambda t:None,lambda:None,lambda:True)
                agent=report['trials'][1];entry=agent['steps'][0]
                self.assertEqual(agent['status'],'failed')
                self.assertFalse('THOUGHT' in json.dumps(report),'recognized reasoning leaked into report')
                self.assertIn('[REDACTED',entry['content'])
                self.assertTrue(entry.get('contentRedacted'))
                self.assertIsNone(entry['action'])
                self.assertFalse(agent['session']['trace'])

    def test_reasoning_inside_json_action_does_not_reach_events_or_later_messages(self):
        from tutor_live import make_report,run_report
        report=make_report(['tcp-misconception'],1)
        raw=json.dumps(dict(tool='finish',args=dict(summary='safe <think>PRIVATE_THOUGHT</think> final')))
        run_report(report,lambda m:dict(content=raw,usage=None,model='m'),lambda t:None,lambda:None,lambda:True)
        self.assertEqual(report['trials'][1]['status'],'completed')
        self.assertFalse('PRIVATE_THOUGHT' in json.dumps(report),'reasoning leaked through parsed action')

    def test_cancellation_after_reserved_checkpoint_prevents_dispatch_and_keeps_unknown_usage(self):
        from tutor_live import make_report,run_report
        report=make_report(['tcp-misconception'],1);running=[True];calls=[]
        def checkpoint():
            if report['trials'][1]['steps']:running[0]=False
        run_report(report,lambda m:calls.append(m),lambda t:None,checkpoint,lambda:running[0])
        agent=report['trials'][1]
        self.assertEqual(calls,[])
        self.assertEqual(agent['status'],'cancelled')
        self.assertEqual(agent['modelCalls'],1)
        self.assertIsNone(agent['usage'])
        self.assertFalse(agent['session']['trace'])

    def test_report_contains_pending_denominators_and_independent_dataset(self):
        from tutor_live import make_report, dataset_info
        info=dataset_info();report=make_report([info['cases'][0]['id']],2)
        self.assertEqual(len(report['trials']),4)
        self.assertEqual(report['learner'],'fixed-script')
        self.assertEqual(report['summary']['agent']['trials'],2)
        self.assertEqual(report['summary']['agent']['passedChecks'],0)
        self.assertNotEqual(info['id'],'tutor-behavior-v1')
        self.assertEqual(len({t['blindId'] for t in report['trials']}),4)

    def test_case_snapshot_survives_dataset_edits_in_run_and_blind_export(self):
        import tutor_live
        report=tutor_live.make_report(['tcp-misconception'],1)
        original=report['caseSnapshots'][0]['question']['prompt']
        with patch.object(tutor_live,'_dataset',side_effect=AssertionError('must use saved dataset')):
            tutor_live.run_report(report,lambda m:dict(content='bad',usage=None,model='m'),lambda t:None,lambda:None,lambda:True)
            packet=tutor_live.blind_package(report)
        self.assertEqual(packet['items'][0]['questions'][0]['prompt'],original)

    def test_real_model_decisions_and_fixed_learner_with_raw_trace(self):
        from tutor_live import make_report, run_report, dataset_info
        report=make_report([dataset_info()['cases'][0]['id']],1)
        seen=[]
        def model(messages):
            data=json.loads(messages[-1]['content']);seen.append(data)
            if data['availableQuestions']:
                action=dict(tool='ask_question',args=dict(questionId=data['availableQuestions'][0]['id']))
            elif not data['feedbackGiven']:
                action=dict(tool='give_feedback',args=dict(message='固定测试反馈'))
            else:action=dict(tool='finish',args=dict(summary='结束'))
            return dict(content=json.dumps(action),usage=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5),model='returned-model')
        saved=[]
        run_report(report,model,lambda trial:None,lambda:saved.append(copy.deepcopy(report)),lambda:True)
        agent=next(t for t in report['trials'] if t['strategy']=='agent')
        self.assertEqual(agent['status'],'completed')
        self.assertEqual(agent['modelCalls'],3)
        self.assertEqual(agent['usage']['total_tokens'],15)
        self.assertEqual(agent['session']['summary']['answered'],1)
        self.assertEqual(agent['steps'][0]['model'],'returned-model')
        self.assertIn('messages',agent['steps'][0])
        self.assertNotIn('answer',seen[0]['availableQuestions'][0])
        self.assertIsNone(agent['review'])
        self.assertFalse(all(c['passed'] for c in agent['checks']))  # missing requested evidence/followup
        self.assertTrue(saved)

    def test_budget_invalid_actions_and_provider_failure_remain_in_denominator(self):
        from tutor_live import make_report,run_report,dataset_info
        ids=[c['id'] for c in dataset_info()['cases'][:2]]
        report=make_report(ids,1);calls=[]
        def reserve(trial):return 'budget' if calls else None
        def model(messages):calls.append(1);return dict(content='{"tool":"read_history","args":{}}',usage=None,model='m')
        run_report(report,model,reserve,lambda:None,lambda:True)
        self.assertEqual(report['summary']['agent']['trials'],2)
        self.assertEqual(sum(t['modelCalls'] for t in report['trials']),1)
        self.assertTrue(all(t['status']=='budget' for t in report['trials'] if t['strategy']=='agent'))
        report=make_report(ids,1)
        run_report(report,lambda m:dict(content='{"tool":"delete_all","args":{}}',usage=None,model='m'),lambda t:None,lambda:None,lambda:True)
        self.assertEqual(report['summary']['agent']['completed'],0)
        self.assertTrue(all(not t['checks'][-1]['passed'] for t in report['trials'] if t['strategy']=='agent'))
        report=make_report(ids,1)
        def broken(m):raise RuntimeError('SECRET provider body')
        run_report(report,broken,lambda t:None,lambda:None,lambda:True)
        self.assertNotIn('SECRET',json.dumps(report))
        self.assertEqual(report['summary']['agent']['modelCalls'],2)
        self.assertTrue(all(t['usage'] is None for t in report['trials'] if t['strategy']=='agent'))

    def test_cancelled_late_result_not_applied_and_blind_export_hides_condition(self):
        from tutor_live import make_report,run_report,dataset_info,blind_package
        report=make_report([dataset_info()['cases'][0]['id']],1);running=[True]
        def model(messages):
            running[0]=False
            return dict(content='{"tool":"finish","args":{"summary":"late"}}',usage=None,model='m')
        run_report(report,model,lambda t:None,lambda:None,lambda:running[0])
        agent=next(t for t in report['trials'] if t['strategy']=='agent')
        self.assertEqual(agent['status'],'cancelled')
        self.assertFalse(any(e['message'].startswith('late') for e in agent['session']['events']))
        package=blind_package(report)
        for item in package['items']:
            self.assertNotIn('strategy',item);self.assertNotIn('model',item);self.assertNotIn('steps',item)
            self.assertNotIn('trace',item)


class ProviderMetadata(unittest.TestCase):
    def test_adapter_preserves_content_and_usage_without_reasoning_or_headers(self):
        import ai
        from io import BytesIO
        result=dict(model='actual-version',usage=dict(prompt_tokens=2,completion_tokens=4,total_tokens=6),choices=[dict(message=dict(content='{"tool":"finish"}',reasoning_content='private-thought'))])
        class Response(BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        class Opener:
            def open(self,req,timeout):
                data=json.loads(req.data)
                self_case.assertEqual(data['max_tokens'],2000)
                self_case.assertEqual(data['thinking'],{'type':'disabled'})
                return Response(json.dumps(result).encode())
        self_case=self
        with patch('ai.build_opener',return_value=Opener()):
            output=ai.call_model_response(dict(model='requested',baseUrl='https://api.deepseek.com/v1',apiKey='secret'),[],max_tokens=2000,thinking='disabled')
        self.assertEqual(output,dict(content='{"tool":"finish"}',usage=result['usage'],model='actual-version'))
        self.assertNotIn('private-thought',json.dumps(output))

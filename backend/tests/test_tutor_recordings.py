"""Replay saved real responses offline; never regenerate or rewrite evidence."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tutor_engine import new_state,apply_action,submit_answer,public_state
from tutor_live import blind_package

RUNS=Path(__file__).resolve().parents[2]/'docs'/'evaluation'/'runs'


class RecordedTeachingRuns(unittest.TestCase):
    def test_actual_retests_replay_from_content_including_the_rejected_action(self):
        recordings={'retest-tcp-01':4,'retest-tcp-02':6,'retest-atomicity-01':5,'retest-atomicity-02':5}
        self.assertEqual(sum(recordings.values()),20)
        statuses=self._replay(recordings)
        self.assertIn('failed',statuses)
        self.assertIn('completed',statuses)

    def test_boundary_scenes_replay_and_preserve_the_premature_finish(self):
        recordings={'edge-no-source-01':1,'edge-material-01':4,'edge-no-source-02':3,
                    'edge-material-02':4,'edge-no-source-03':3}
        self.assertEqual(sum(recordings.values()),15)
        self.assertTrue(all(status=='completed' for status in self._replay(recordings)))
        report=json.loads((RUNS/'2026-10-20-edge-no-source-01.json').read_text())['report']
        self.assertEqual(report['summary']['agent']['completed'],1)
        self.assertEqual(report['summary']['agent']['passed'],0)

    def test_review_supplements_match_frozen_runs_and_masked_inputs(self):
        for name,count in [('retest-feedback',8),('edge-feedback',10)]:
            review=json.loads((RUNS.parent/'reviews'/f'2026-10-20-{name}.json').read_text())
            originals={};masked={}
            for source in review['sourceRuns']:
                path=RUNS/source['path']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),source['sha256'])
                report=json.loads(path.read_text())['report']
                originals.update({t['blindId']:t for t in report['trials']})
                masked.update({t['blindId']:t for t in blind_package(report)['items']})
            self.assertEqual(len(review['items']),count)
            self.assertEqual({t['blindId'] for t in review['items']},set(originals))
            self.assertEqual({t['blindId']:t for t in review['package']['items']},masked)
            for item in review['items']:
                trial=originals[item['blindId']];rating=item['review']
                self.assertEqual(item['trialId'],trial['id'])
                self.assertIsNone(trial['review'])
                self.assertEqual(rating['reviewerType'],'ai-assisted')
                self.assertTrue(rating['notes'].strip())
                self.assertEqual(set(rating['scores']),{'accuracy','grounding','diagnosis','actionability'})
                self.assertTrue(all(type(n) is int and 0<=n<=2 for n in rating['scores'].values()))
                self.assertFalse({'model','strategy','trialId','caseId'} & set(masked[item['blindId']]))

    def _replay(self,recordings):
        statuses=[]
        for name,expected_calls in recordings.items():
            path=RUNS/f'2026-10-20-{name}.json'
            recording=json.loads(path.read_text());report=recording['report']
            cases={c['id']:c for c in report['caseSnapshots']}
            self.assertEqual(recording['model_calls'],expected_calls)
            self.assertEqual(recording['model_calls'],sum(t['modelCalls'] for t in report['trials']))
            for trial in report['trials']:
                with self.subTest(recording=path.name,strategy=trial['strategy']):
                    case=cases[trial['caseId']]
                    state=new_state([case['question']],case['goal'],trial['strategy'],1,case['history'])
                    rejected=False
                    model_steps=[s for s in trial['steps'] if s['kind']=='model']
                    self.assertEqual(trial['modelCalls'],len(model_steps))
                    if model_steps:
                        system=model_steps[0]['messages'][0]['content']
                        self.assertEqual(hashlib.sha256(system.encode()).hexdigest(),report['promptHash'])
                    for step in trial['steps']:
                        before=copy.deepcopy(state)
                        try:
                            if step['kind']=='learner':
                                result=step['result']
                                expected=case['learnerAnswer'] if result['kind']=='question' else case['learnerReason']
                                self.assertEqual(result['userAnswer'],expected)
                                actual=submit_answer(state,expected,result['turnId'])
                            else:
                                # Parse content rather than trusting the saved parsed action.
                                action=json.loads(step['content']) if step['kind']=='model' else step['action']
                                actual=apply_action(state,action)
                            self.assertEqual(actual,step['result'])
                        except ValueError:
                            self.assertEqual(trial['status'],'failed')
                            self.assertTrue(step.get('error'))
                            self.assertEqual(state,before)
                            rejected=True
                    if trial['status']=='completed':self.assertEqual(state['status'],'completed')
                    if trial['status']=='failed':self.assertTrue(rejected)
                    public=public_state(state)
                    for key in ('summary','asked','answers','events'):
                        self.assertEqual(public[key],trial['session'][key])
                    if trial['strategy']=='agent':statuses.append(trial['status'])
        return statuses

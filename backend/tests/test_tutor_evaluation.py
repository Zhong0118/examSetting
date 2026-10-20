import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


class TutorBenchmarkTests(unittest.TestCase):
    def test_public_json_markers_checked_at_every_checkpoint_and_revealed_after_answer(self):
        from tutor_evaluation import benchmark_report
        report = benchmark_report()
        for strategy in report['strategies']:
            for case in strategy['cases']:
                checkpoints = case['observed']['markerCheckpoints']
                self.assertEqual([c['step'] for c in checkpoints], list(range(len(case['actualTrace']) + 1)))
                self.assertTrue(all(c['checkedMarkers'] > 0 for c in checkpoints))
                self.assertTrue(all(c['leaks'] == [] for c in checkpoints))
            short = next(c for c in strategy['cases'] if c['id'] == 'short-self-review')
            self.assertFalse(short['observed']['markerCheckpoints'][1]['visibleAnsweredMarkers'])
            self.assertTrue(any(m['field'] == 'answer' and m['questionId'] == 'short'
                                for m in short['observed']['markerCheckpoints'][2]['visibleAnsweredMarkers']))
            self.assertTrue(short['passed'])

    def test_transient_future_markers_in_events_pending_or_trace_fail_without_dropping_cases(self):
        import tutor_evaluation
        from tutor_engine import public_state
        baseline = tutor_evaluation.benchmark_report()
        for field in ('answer', 'explanation', 'source'):
            for outlet in ('events', 'pending', 'trace'):
                def leaking(state):
                    public = public_state(state)
                    # Leak only at an intermediate post-answer checkpoint; the
                    # final report state is clean and must not erase the failure.
                    if state['status'] == 'running' and len(state['answers']) == 1:
                        marker = next(q[field] for q in state['questions'] if q['id'] == 'future-boundary')
                        if outlet == 'events':
                            public['events'].append(dict(type='debug', message=marker))
                        elif outlet == 'trace':
                            public['trace'].append(dict(tool='debug', status='ok', message=marker))
                        else:
                            public['pending'] = dict(kind='question', questionId='future-boundary', prompt=marker)
                    return public
                with self.subTest(field=field, outlet=outlet), patch.object(tutor_evaluation.engine, 'public_state', side_effect=leaking):
                    report = tutor_evaluation.benchmark_report()
                for strategy, original in zip(report['strategies'], baseline['strategies']):
                    self.assertEqual(strategy['summary']['checks'], original['summary']['checks'])
                    self.assertEqual(len(strategy['cases']), report['caseCount'])
                    self.assertLess(strategy['summary']['passedChecks'], original['summary']['passedChecks'])
                    followup = next(c for c in strategy['cases'] if c['id'] == 'correct-followup')
                    self.assertFalse(followup['passed'])
                    self.assertFalse(followup['observed']['unansweredMarkersHidden'])
                    self.assertEqual(followup['observed']['markerCheckpoints'][-1]['leaks'], [])

    def test_cli_exports_json_without_a_server_or_provider(self):
        import tutor_evaluation
        result = subprocess.run([sys.executable, tutor_evaluation.__file__], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), 'CLI must emit the report')
        report = json.loads(result.stdout)
        self.assertEqual(report['kind'], 'tutor-behavior-benchmark')
        self.assertEqual(report['caseCount'], 12)

    def test_report_is_json_and_counts_match_actual_checks(self):
        from tutor_evaluation import benchmark_report
        report = benchmark_report()
        json.dumps(report, ensure_ascii=False, allow_nan=False)
        self.assertEqual(report['kind'], 'tutor-behavior-benchmark')
        self.assertEqual([s['name'] for s in report['strategies']], ['rule', 'scripted-agent'])
        self.assertTrue(10 <= report['caseCount'] <= 12)
        for strategy in report['strategies']:
            self.assertEqual(len(strategy['cases']), report['caseCount'])
            checks = [c for case in strategy['cases'] for c in case['checks']]
            self.assertEqual(strategy['summary']['checks'], len(checks))
            self.assertEqual(strategy['summary']['passedChecks'], sum(c['passed'] for c in checks))
            self.assertEqual(strategy['summary']['passRate'], sum(c['passed'] for c in checks) / len(checks))
            self.assertEqual(strategy['summary']['passedCases'], sum(case['passed'] for case in strategy['cases']))
            for case in strategy['cases']:
                self.assertTrue(case['actualTrace'])
                self.assertIsInstance(case['expected'], list)
                self.assertIsInstance(case['observed'], dict)
                self.assertEqual(case['passed'], all(c['passed'] for c in case['checks']) and case['error'] is None)
                self.assertIsNone(case['error'], (case['id'], case['error']))
        rule = next(c for c in report['strategies'][0]['cases'] if c['id'] == 'correct-followup')
        self.assertFalse(rule['passed'])
        self.assertEqual(rule['observed']['followups'], 0)
        scripted = next(c for c in report['strategies'][1]['cases'] if c['id'] == 'correct-followup')
        self.assertTrue(scripted['passed'])
        self.assertTrue(any('脚本' in item and '模型' in item for item in report['limitations']))

    def test_dataset_hash_is_reproducible_and_both_strategies_use_same_cases(self):
        import tutor_evaluation
        first = tutor_evaluation.benchmark_report()
        second = tutor_evaluation.benchmark_report()
        data = Path(tutor_evaluation.__file__).with_name('tutor_fixtures.json').read_bytes()
        self.assertEqual(first['datasetHash'], hashlib.sha256(data).hexdigest())
        self.assertEqual(first['datasetHash'], second['datasetHash'])
        self.assertEqual([c['id'] for c in first['strategies'][0]['cases']], [c['id'] for c in first['strategies'][1]['cases']])
        for a, b in zip(first['strategies'], second['strategies']):
            self.assertEqual(a['summary'], b['summary'])
            self.assertEqual([c['observed'] for c in a['cases']], [c['observed'] for c in b['cases']])

    def test_security_cases_really_reject_and_short_answers_are_not_scored(self):
        from tutor_evaluation import benchmark_report
        report = benchmark_report()
        for strategy in report['strategies']:
            cases = {c['id']: c for c in strategy['cases']}
            for case_id in ['forged-evidence', 'illegal-tool', 'repeat-question', 'question-budget', 'wait-for-user', 'stale-turn']:
                case = cases[case_id]
                self.assertTrue(case['passed'], (strategy['name'], case_id, case))
                self.assertTrue(any(step['outcome'] == 'rejected' for step in case['actualTrace']))
                self.assertTrue(case['observed']['rejectedStateUnchanged'])
            short = cases['short-self-review']
            self.assertTrue(short['passed'])
            self.assertEqual(short['observed']['objectiveTotal'], 0)
            self.assertIsNone(short['observed']['lastAnswerCorrect'])

    def test_engine_failure_is_reported_and_remains_in_denominator(self):
        import tutor_evaluation
        from tutor_engine import apply_action
        calls = []

        def broken(state, action):
            calls.append(action['tool'])
            if action['tool'] == 'ask_question':
                raise RuntimeError('controlled engine failure')
            return apply_action(state, action)

        # Fault injection exercises report handling; other tests use the real engine.
        with patch.object(tutor_evaluation.engine, 'apply_action', side_effect=broken):
            report = tutor_evaluation.benchmark_report()
        self.assertIn('ask_question', calls)
        for strategy in report['strategies']:
            self.assertEqual(len(strategy['cases']), report['caseCount'])
            failures = [c for c in strategy['cases'] if c['error'] is not None]
            self.assertTrue(failures)
            self.assertTrue(all(not c['passed'] for c in failures))
            self.assertLess(strategy['summary']['passRate'], 1)

    def test_initialization_failure_is_a_failed_case_not_a_missing_sample(self):
        import tutor_evaluation
        with patch.object(tutor_evaluation.engine, 'new_state', side_effect=ValueError('invalid snapshot')):
            report = tutor_evaluation.benchmark_report()
        for strategy in report['strategies']:
            self.assertEqual(strategy['summary']['errorCases'], report['caseCount'])
            self.assertEqual(strategy['summary']['passRate'], 0)
            self.assertTrue(all(case['error'] and case['actualTrace'] == [] for case in strategy['cases']))


if __name__ == '__main__':
    unittest.main()

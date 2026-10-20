import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'tutor_study.py'
FIELDS = ['participant_id', 'strategy', 'pre_correct', 'post_correct', 'max_score', 'delayed_correct']


class TutorStudyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'learners.csv'

    def write_rows(self, rows, fields=FIELDS):
        with self.path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerows(rows)

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                              capture_output=True, text=True, timeout=10)

    def report(self):
        result = self.run_cli(self.path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def assert_bad_input(self, *arguments):
        result = self.run_cli(*(arguments or (self.path,)))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertNotIn('Traceback', result.stderr)
        error = json.loads(result.stderr)
        self.assertIsInstance(error['error'], str)
        self.assertTrue(error['error'])
        return error['error']

    def test_paired_normalized_gains_and_delayed_denominators(self):
        # Synthetic parser fixtures only; these are not learner observations.
        self.write_rows([
            ['r1', 'rule', 2, 3, 4, 2],
            ['r2', 'rule', 4, 2, 8, ''],
            ['a1', 'agent', 0, 4, 4, 3],
            ['a2', 'agent', 2, 4, 8, 4],
        ])
        report = self.report()
        self.assertEqual(report['total_n'], 4)
        self.assertEqual(report['included_n'], 4)
        self.assertEqual(report['excluded_n'], 0)
        first = report['participants'][0]
        self.assertEqual(first['participant_id'], 'r1')
        self.assertEqual(first['strategy'], 'rule')
        self.assertEqual(first['raw'], dict(pre_correct=2, post_correct=3, max_score=4, delayed_correct=2))
        self.assertEqual(first['normalized'], dict(pre=0.5, post=0.75, gain=0.25, delayed=0.5))
        self.assertIsNone(report['participants'][1]['normalized']['delayed'])
        self.assertEqual(report['participants'][1]['normalized']['gain'], -0.25)
        self.assertEqual(report['groups']['rule'], dict(n=2, excluded_n=0, pre_mean=0.5, post_mean=0.5,
                                                     gain_mean=0.0, delayed_n=1, delayed_mean=0.5))
        self.assertEqual(report['groups']['agent'], dict(n=2, excluded_n=0, pre_mean=0.125, post_mean=0.75,
                                                      gain_mean=0.625, delayed_n=2, delayed_mean=0.625))
        self.assertEqual(report['comparison']['gain_difference_agent_minus_rule'], 0.625)
        self.assertTrue(report['comparison']['descriptive_only'])

    def test_missing_scores_are_excluded_without_imputation(self):
        self.write_rows([
            ['r1', 'rule', 0, 0, 4, ''],
            ['r2', 'rule', '', 3, 4, 2],
            ['a1', 'agent', 1, '', 4, ''],
            ['a2', 'agent', 1, 2, '', ''],
        ])
        report = self.report()
        self.assertEqual((report['total_n'], report['included_n'], report['excluded_n']), (4, 1, 3))
        self.assertEqual(report['groups']['rule']['n'], 1)
        self.assertEqual(report['groups']['rule']['excluded_n'], 1)
        self.assertEqual(report['groups']['rule']['delayed_n'], 0)
        self.assertIsNone(report['groups']['rule']['delayed_mean'])
        self.assertEqual(report['groups']['agent']['n'], 0)
        self.assertEqual(report['groups']['agent']['excluded_n'], 2)
        self.assertIsNone(report['groups']['agent']['pre_mean'])
        self.assertIsNone(report['comparison']['gain_difference_agent_minus_rule'])
        self.assertEqual([row['missing_fields'] for row in report['exclusions']],
                         [['pre_correct'], ['post_correct'], ['max_score']])
        self.assertEqual(report['exclusions'][0]['raw']['delayed_correct'], 2)
        self.assertIsNone(report['exclusions'][0]['raw']['pre_correct'])

    def test_optional_delayed_column_can_be_absent(self):
        self.write_rows([['p1', 'rule', 1, 3, 4]], FIELDS[:-1])
        report = self.report()
        self.assertIsNone(report['participants'][0]['raw']['delayed_correct'])
        self.assertEqual(report['groups']['rule']['delayed_n'], 0)
        self.assertIsNone(report['comparison']['gain_difference_agent_minus_rule'])

    def test_header_only_template_has_empty_groups_and_null_means(self):
        self.write_rows([])
        report = self.report()
        self.assertEqual((report['total_n'], report['included_n'], report['excluded_n']), (0, 0, 0))
        self.assertEqual(report['participants'], [])
        self.assertEqual(report['exclusions'], [])
        for group in report['groups'].values():
            self.assertEqual(group['n'], 0)
            self.assertEqual(group['delayed_n'], 0)
            for field in ('pre_mean', 'post_mean', 'gain_mean', 'delayed_mean'):
                self.assertIsNone(group[field])
        self.assertIsNone(report['comparison']['gain_difference_agent_minus_rule'])
        json.dumps(report, allow_nan=False)

    def test_all_incomplete_rows_keep_their_exclusion_denominator(self):
        self.write_rows([['p1', 'agent', '', '', '', '']])
        report = self.report()
        self.assertEqual((report['total_n'], report['included_n'], report['excluded_n']), (1, 0, 1))
        self.assertEqual(report['groups']['agent']['excluded_n'], 1)
        self.assertEqual(report['exclusions'][0]['missing_fields'], ['pre_correct', 'post_correct', 'max_score'])

    def test_blank_file_is_invalid_instead_of_an_empty_study(self):
        self.path.write_text('', encoding='utf-8')
        self.assertIn('header', self.assert_bad_input().lower())

    def test_missing_required_columns_are_invalid_even_without_rows(self):
        for field in FIELDS[:-1]:
            with self.subTest(field=field):
                self.write_rows([], [name for name in FIELDS if name != field])
                self.assertIn(field, self.assert_bad_input())

    def test_duplicate_unknown_headers_and_ragged_rows_are_invalid(self):
        invalid_csvs = [
            ','.join(FIELDS + ['strategy']) + '\n',
            ','.join(FIELDS + ['email']) + '\n',
            ','.join(FIELDS) + '\np1,rule,1,2,4,,unexpected\n',
            ','.join(FIELDS) + '\np1,rule,1,2\n',
            ','.join(FIELDS) + '\n"unterminated,rule,1,2,4,\n',
        ]
        for content in invalid_csvs:
            with self.subTest(content=content):
                self.path.write_text(content, encoding='utf-8')
                self.assert_bad_input()

    def test_duplicate_ids_in_same_arm_cross_arms_or_exclusions_are_invalid(self):
        for strategy in ('rule', 'agent'):
            for pre in ('1', ''):
                with self.subTest(strategy=strategy, pre=pre):
                    self.write_rows([['p1', 'rule', pre, 2, 4, ''],
                                     [' p1 ', strategy, 1, 2, 4, '']])
                    self.assertIn('duplicate', self.assert_bad_input().lower())

    def test_missing_identity_or_invalid_strategy_is_not_silently_excluded(self):
        for participant, strategy in [('', 'rule'), (' ', 'agent'), ('p1', ''),
                                      ('p1', 'scripted-agent'), ('p1', 'Agent'), ('p1', 'true')]:
            with self.subTest(participant=participant, strategy=strategy):
                self.write_rows([[participant, strategy, '', '', 4, '']])
                self.assert_bad_input()

    def test_non_integral_boolean_and_nonnumeric_scores_are_invalid(self):
        for field_index in range(2, 6):
            for value in ('True', 'False', 'true', 'false', '1.0', '1.5', 'NaN', 'Infinity', 'score', '1e0', '1_0'):
                with self.subTest(field=FIELDS[field_index], value=value):
                    row = ['p1', 'rule', 1, 2, 4, '']
                    row[field_index] = value
                    self.write_rows([row])
                    self.assertIn(FIELDS[field_index], self.assert_bad_input())

    def test_impossible_score_ranges_and_nonpositive_max_are_invalid(self):
        for field_index, values in ((2, (-1, 5)), (3, (-1, 5)), (4, (0, -1)), (5, (-1, 5))):
            for value in values:
                with self.subTest(field=FIELDS[field_index], value=value):
                    row = ['p1', 'rule', 1, 2, 4, '']
                    row[field_index] = value
                    self.write_rows([row])
                    self.assertIn(FIELDS[field_index], self.assert_bad_input())

    def test_bad_values_on_incomplete_rows_are_still_rejected(self):
        for row in (['p1', 'rule', '', 'bad', 4, ''],
                    ['p1', 'rule', 1, '', 0, ''],
                    ['p1', 'rule', '', 5, 4, ''],
                    ['p1', 'agent', '', '', 4, 'False'],
                    ['p1', 'agent', -1, '', '', '']):
            with self.subTest(row=row):
                self.write_rows([row])
                self.assert_bad_input()

    def test_utf8_bom_whitespace_quoted_ids_and_reordered_columns(self):
        content = io.StringIO(newline='')
        writer = csv.writer(content)
        writer.writerow(['strategy', 'participant_id', 'post_correct', 'max_score', 'pre_correct', 'delayed_correct'])
        writer.writerow([' rule ', ' p,1 ', ' 4 ', ' 4 ', ' 0 ', ' '])
        self.path.write_text('\ufeff' + content.getvalue(), encoding='utf-8')
        report = self.report()
        self.assertEqual(report['participants'][0]['participant_id'], 'p,1')
        self.assertEqual(report['groups']['rule']['gain_mean'], 1.0)
        self.assertIsNone(report['participants'][0]['normalized']['delayed'])

    def test_file_errors_and_bad_cli_arguments_are_friendly_json(self):
        self.assert_bad_input(self.path)
        self.assert_bad_input(self.directory.name)
        self.path.write_bytes(b'\xff\xfe\x00')
        self.assert_bad_input(self.path)
        # Invoke without the helper's default path to test missing CLI arguments.
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertTrue(json.loads(result.stderr)['error'])
        self.assert_bad_input('--unknown')

    def test_validation_error_identifies_line_and_field(self):
        self.write_rows([['p1', 'rule', 1, 2, 4, ''], ['p2', 'agent', 1, 9, 4, '']])
        message = self.assert_bad_input()
        self.assertIn('3', message)
        self.assertIn('post_correct', message)


if __name__ == '__main__':
    unittest.main()

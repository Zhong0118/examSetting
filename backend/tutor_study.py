"""Descriptive analysis of anonymous, parallel-arm learner pre/post CSV data.

No models, server, database, external dependencies or inferential statistics.
"""
import argparse
import csv
import json
from pathlib import Path
import re
from statistics import fmean
import sys


REQUIRED_FIELDS = ('participant_id', 'strategy', 'pre_correct', 'post_correct', 'max_score')
SCORE_FIELDS = ('pre_correct', 'post_correct', 'max_score', 'delayed_correct')
STRATEGIES = ('rule', 'agent')


def _score(value, field, line):
    if not value:
        return None
    if not re.fullmatch(r'[+-]?[0-9]+', value):
        raise ValueError(f'Line {line}: {field} must be an integer, or blank if missing.')
    try:
        score = int(value)
    except ValueError:
        raise ValueError(f'Line {line}: {field} is too large to parse as an integer.') from None
    if score < 0 or (field == 'max_score' and score == 0):
        requirement = 'greater than zero' if field == 'max_score' else 'zero or greater'
        raise ValueError(f'Line {line}: {field} must be {requirement}.')
    return score


def analyze_csv(path):
    """Validate a real CSV file and return a JSON-compatible descriptive report.

    Invalid supplied values reject the file, including on incomplete rows.
    Missing pre/post/max values exclude the row, without imputing any score.
    """
    participants, exclusions, seen = [], [], set()
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        fields = reader.fieldnames
        if not fields:
            raise ValueError('CSV header is required; use the header-only study template.')
        if len(fields) != len(set(fields)):
            raise ValueError('CSV header contains duplicate columns.')
        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            raise ValueError(f'CSV header missing required columns: {", ".join(missing)}.')
        unknown = set(fields) - set(REQUIRED_FIELDS) - {'delayed_correct'}
        if unknown:
            raise ValueError(f'CSV header contains unsupported columns: {", ".join(sorted(unknown))}.')
        for row in reader:
            line = reader.line_num
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'Line {line}: column count must match the CSV header; use empty cells for missing scores.')
            row = {field: value.strip() for field, value in row.items()}
            participant_id, strategy = row['participant_id'], row['strategy']
            if not participant_id:
                raise ValueError(f'Line {line}: participant_id is required (anonymous ID only).')
            if strategy not in STRATEGIES:
                raise ValueError(f'Line {line}: strategy must be rule or agent.')
            if participant_id in seen:
                raise ValueError(f'Line {line}: duplicate participant_id; each learner must appear once in exactly one group.')
            seen.add(participant_id)
            raw = {field: _score(row.get(field, ''), field, line) for field in SCORE_FIELDS}
            maximum = raw['max_score']
            if maximum is not None:
                for field in ('pre_correct', 'post_correct', 'delayed_correct'):
                    if raw[field] is not None and raw[field] > maximum:
                        raise ValueError(f'Line {line}: {field} must be between 0 and max_score ({maximum}).')
            entry = dict(participant_id=participant_id, strategy=strategy, raw=raw)
            missing = [field for field in ('pre_correct', 'post_correct', 'max_score') if raw[field] is None]
            if missing:
                exclusions.append(dict(entry, line=line, missing_fields=missing))
                continue
            entry['normalized'] = dict(
                pre=raw['pre_correct'] / maximum,
                post=raw['post_correct'] / maximum,
                gain=(raw['post_correct'] - raw['pre_correct']) / maximum,
                delayed=raw['delayed_correct'] / maximum if raw['delayed_correct'] is not None else None,
            )
            participants.append(entry)

    groups = {}
    for strategy in STRATEGIES:
        scores = [entry['normalized'] for entry in participants if entry['strategy'] == strategy]
        delayed = [score['delayed'] for score in scores if score['delayed'] is not None]
        groups[strategy] = dict(
            n=len(scores), excluded_n=sum(entry['strategy'] == strategy for entry in exclusions),
            pre_mean=fmean(score['pre'] for score in scores) if scores else None,
            post_mean=fmean(score['post'] for score in scores) if scores else None,
            gain_mean=fmean(score['gain'] for score in scores) if scores else None,
            delayed_n=len(delayed), delayed_mean=fmean(delayed) if delayed else None,
        )
    rule_gain, agent_gain = groups['rule']['gain_mean'], groups['agent']['gain_mean']
    difference = agent_gain - rule_gain if rule_gain is not None and agent_gain is not None else None
    return dict(
        kind='learner-study-descriptive', score_scale='proportion_0_1',
        total_n=len(participants) + len(exclusions), included_n=len(participants), excluded_n=len(exclusions),
        participants=participants, exclusions=exclusions, groups=groups,
        comparison=dict(gain_difference_agent_minus_rule=difference, descriptive_only=True),
        limitations=[
            'Descriptive summaries only; no causal or statistical-significance conclusion.',
            'Missing pre/post/max rows are excluded from all summaries; no imputation. '
            'Delayed means use available delayed scores among included pairs only.',
            'The tool cannot verify genuine learner provenance, random assignment, equivalent tests or attrition bias.',
        ],
    )


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None):
    parser = _Parser(description=__doc__)
    parser.add_argument('csv_path', type=Path, help='anonymous learner CSV; JSON report goes to stdout')
    try:
        args = parser.parse_args(argv)
        report = analyze_csv(args.csv_path)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

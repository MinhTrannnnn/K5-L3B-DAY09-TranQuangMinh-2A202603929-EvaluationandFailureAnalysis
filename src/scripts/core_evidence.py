"""Rebuild public Core evidence. Run from src: python -m scripts.core_evidence."""
import json
from pathlib import Path
from types import SimpleNamespace
from lab8.shapes import SHAPES
from lab9.variant_agent import make_shape
from lab9.trace_case import investigate
from lab9.judge import calibrate
from lab9.graders import GRADERS


def scores(case):
    ctx = SimpleNamespace(output=case['trial'], expected_output=case['label'])
    return {key: bool(g().evaluate(ctx).value) for key, g in GRADERS.items()}


def is_bad(values):
    return any(v if k in {'secret_leak', 'approval_bypass'} else not v for k, v in values.items())


def main():
    modes = {
        'FM-01': ('leaky_trace', 'C-010'), 'FM-02': ('ignore_denied', 'C-007'),
        'FM-03': ('ticket_trust', 'C-002'), 'FM-04': ('sum_parts', 'C-014'),
        'FM-05': ('pre_deducted', 'C-014'), 'FM-06': ('stale_clause', 'C-006'),
        'FM-07': ('sibling_refund', 'C-001'), 'FM-08': ('misreport', 'C-008'),
    }
    examples = {}
    for fm, (bug, claim) in modes.items():
        name = f'core_{bug}'
        SHAPES[name] = make_shape(name, {'no_override', bug})
        case = investigate(name, claim, 11)
        values = scores(case)
        examples[fm] = {**case, 'shape': name, 'claim': claim, 'seed': 11,
                        'scores': values, 'detected': is_bad(values)}
    anchors = {f'C-{n:03d}': {'fixed': investigate('fixed', f'C-{n:03d}', 11)} for n in range(1, 15)}
    clean = [is_bad(scores(c['fixed'])) for c in anchors.values()]
    detected = sum(c['detected'] for c in examples.values())
    data = {'anchors': anchors, 'failure_examples': examples,
            'trace_case': {shape: investigate(shape, 'C-002', 11) for shape in ['seeded_regression', 'fixed']},
            'judge': {name: calibrate(Path(f'data/eval/judge_{name}_public.csv')) for name in ['tone', 'helpful']},
            'grader_validation': {'faulty_trials': 8, 'detected': detected, 'detection_rate': detected/8,
                                  'fixed_trials': 14, 'false_alarms': sum(clean), 'false_alarm_rate': sum(clean)/14}}
    output = Path('../docs/core_evidence.json')
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(data['grader_validation'], indent=2))
    for fm, ex in examples.items():
        print(fm, ex['claim'], ex['scores'])
        for i, e in enumerate(ex['trial']['events'], 1):
            print(i, e['kind'], str(e.get('payload'))[:150])
    print('wrote', output)


if __name__ == '__main__':
    main()

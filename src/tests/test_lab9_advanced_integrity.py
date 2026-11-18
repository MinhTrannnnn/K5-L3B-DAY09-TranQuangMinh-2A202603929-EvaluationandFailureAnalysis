"""Independent adversarial checks beyond the supplied public vectors."""
import copy
import itertools
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.student


@pytest.fixture
def evidence():
    from lab9.eval import aggregate
    rows = [{'item_id': f'E-{i}', 'seed': s, 'slices': ['money_movement'],
             'pass_rate': True, 'cost': 1.0} for i in range(3) for s in (11, 22)]
    spec = {'eval_set_version': 'v2', 'seeds': [11, 22], 'pass_k': [1, 2],
            'metrics': [{'id': 'pass_rate', 'kind': 'capability', 'blocking': True,
                         'threshold': {'min': 0.8, 'no_significant_drop': True}}],
            'slices': [{'name': 'money_movement', 'metric': 'pass_rate',
                        'min': 0.9, 'no_significant_drop': True, 'blocking': True}]}
    report = {'manifest': {'eval_set_sha': 'fixture', 'items': 3, 'seeds': [11, 22]},
              'rows': rows, 'metrics': aggregate(rows, ['pass_rate'], k_values=[1, 2]),
              'evaluator_failures': []}
    return report, spec


@pytest.mark.parametrize('attack', ['duplicate', 'evaluator_error', 'null_row', 'inf_row',
                                    'fake_summary', 'relabel_slice', 'missing_seed', 'nan_summary'])
def test_advanced_integrity_blocks_corrupted_green_report(evidence, attack):
    from lab9.gate import check
    base, spec = evidence
    pr = copy.deepcopy(base)
    if attack == 'duplicate':
        pr['rows'][-1] = copy.deepcopy(pr['rows'][0])  # same length, one pair lost
    elif attack == 'evaluator_error':
        pr['evaluator_failures'] = ['grader crashed even though summary is green']
    elif attack == 'null_row':
        pr['rows'][0]['pass_rate'] = None
    elif attack == 'inf_row':
        pr['rows'][0]['pass_rate'] = float('inf')
    elif attack == 'fake_summary':
        pr['rows'][0]['pass_rate'] = False  # summary still claims 100%
    elif attack == 'relabel_slice':
        for r in pr['rows']:
            r['slices'] = []
    elif attack == 'missing_seed':
        pr['rows'] = [r for r in pr['rows'] if r['seed'] == 11]
        pr['manifest']['seeds'] = [11]  # also edit manifest to hide missing rows
    elif attack == 'nan_summary':
        pr['metrics']['pass_rate'] = float('nan')
    blocked, lines = check(pr, base, spec)
    assert blocked == ['integrity']
    assert any('INTEGRITY' in line for line in lines)


@pytest.mark.parametrize('attack', ['drop_metric', 'drop_slice', 'drop_ci', 'disable_slice',
                                    'lower_slice', 'raise_safety_max'])
def test_advanced_ratchet_blocks_loosened_rules(evidence, attack):
    from lab9.gate import integrity_check
    base, spec = evidence
    # Ratchet can be tested without running or changing a faulty agent.
    baseline_spec = copy.deepcopy(spec)
    baseline_spec['metrics'].append({'id': 'safety_count', 'kind': 'safety',
                                    'blocking': True, 'threshold': {'max': 0}})
    base['metrics']['safety_count'] = 0
    loose = copy.deepcopy(baseline_spec)
    if attack == 'drop_metric':
        loose['metrics'].pop()
    elif attack == 'drop_slice':
        loose['slices'] = []
    elif attack == 'drop_ci':
        loose['metrics'][0]['threshold'].pop('no_significant_drop')
    elif attack == 'disable_slice':
        loose['slices'][0]['blocking'] = False
    elif attack == 'lower_slice':
        loose['slices'][0]['min'] = 0.1
    elif attack == 'raise_safety_max':
        loose['metrics'][-1]['threshold']['max'] = 1
    assert any('ratchet:' in problem for problem in integrity_check(base, base, loose, baseline_spec))
    assert integrity_check(base, base, baseline_spec, baseline_spec) == []


def test_advanced_estimators_match_exhaustive_sampling():
    from lab9.stats import pass_at_k, pass_hat_k
    for n in range(1, 8):
        for c in range(n + 1):
            for k in range(1, n + 1):
                samples = list(itertools.combinations(range(n), k))
                any_pass = sum(any(x < c for x in sample) for sample in samples) / len(samples)
                all_pass = sum(all(x < c for x in sample) for sample in samples) / len(samples)
                assert pass_at_k(n, c, k) == pytest.approx(any_pass)
                assert pass_hat_k(n, c, k) == pytest.approx(all_pass)


@pytest.mark.parametrize('args', [(0, 0, 1), (-2, 0, 1), (5, -1, 1), (5, 6, 1),
                                  (5, 2, 0), (5, 2, 6), (5.0, 2, 1), (5, True, 1)])
def test_advanced_both_estimators_reject_invalid_inputs(args):
    from lab9.stats import pass_at_k, pass_hat_k
    for fn in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)


def test_advanced_unseen_name_quiet_override_still_blocked(monkeypatch):
    from lab8.shapes import SHAPES
    from lab9.variant_agent import make_shape
    from lab9.eval import load_spec, run_eval
    from lab9.gate import check
    from lab9.variants import register
    from pathlib import Path
    register()
    spec = load_spec(Path('config/metric_spec_v2.yaml'))
    monkeypatch.setitem(SHAPES, 'custom_silent_bug', make_shape('custom_silent_bug', {'quiet_override'}))
    base = run_eval('swarm', spec)
    pr = run_eval('custom_silent_bug', spec)
    assert all(r['db_fact_kept'] for r in pr['rows'])
    blocked, _ = check(pr, base, spec)
    assert blocked
    assert 'integrity' not in blocked  # genuine agent failure, valid report


def test_advanced_slice_uses_paired_drop_even_above_floor(evidence):
    from lab9.gate import slice_check
    base, spec = evidence
    pr = copy.deepcopy(base)
    # Every item loses one of two runs; the configured floor alone would pass.
    for r in pr['rows']:
        r['pass_rate'] = r['seed'] != 11
    spec['slices'][0]['min'] = 0.4
    blocked, _ = slice_check(pr, base, spec)
    assert blocked == ['slice:money_movement/pass_rate']


def test_advanced_identical_single_item_baseline_can_merge(evidence):
    from lab9.gate import check
    from lab9.eval import aggregate
    base, spec = evidence
    base['rows'] = base['rows'][:2]
    base['manifest']['items'] = 1
    base['metrics'] = aggregate(base['rows'], ['pass_rate'], k_values=[1, 2])
    blocked, _ = check(copy.deepcopy(base), base, spec, spec)
    assert blocked == []

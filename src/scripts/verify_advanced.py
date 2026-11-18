"""Reproduce M5-M7 and log expected blocked gates as successful checks. Run from src/."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import json
import subprocess
import sys


def main():
    spec = 'config/metric_spec_v2.yaml'
    baseline = 'reports/baseline_v2.json'
    checks = [
        (['-m', 'scripts.verify_core'], 0),
        (['-m', 'lab9.evalset', '--v2', '--build'], 0),
        (['-m', 'pytest', '-q', '-m', 'student', '-o', 'addopts=', '-k', 'advanced'], 0),
        (['-m', 'lab9.mutation', '--detect'], 0),
        (['-m', 'lab9.eval', '--shape', 'swarm', '--spec', spec, '--out', baseline], 0),
        (['-m', 'lab9.eval', '--shape', 'swarm', '--spec', spec, '--seeds', '66,77,88,99,110',
          '--out', 'reports/aa_alternate_v2.json'], 0),
        (['-m', 'lab9.mutation', '--spec', spec, '--aa', '66,77,88,99,110'], 0),
        (['-m', 'lab9.gate', '--pr', baseline, '--baseline', baseline, '--spec', spec, '--base-spec', spec], 0),
    ]
    for shape, status in [('fixed', 0), ('honest_refactor', 0), ('seeded_regression', 1),
                          ('slice_regression', 1), ('flaky_regression', 1)]:
        path = f'reports/eval_{shape}_v2.json' if shape in {'fixed','seeded_regression'} else f'reports/eval_{shape}.json'
        checks += [(['-m', 'lab9.eval', '--shape', shape, '--spec', spec, '--out', path], 0),
                   (['-m', 'lab9.gate', '--pr', path, '--baseline', baseline, '--spec', spec, '--base-spec', spec], status)]
    checks += [(['-m', 'lab9.mutation', '--spec', spec, '--baseline', baseline, '--base-spec', spec], 0),
               (['-m', 'lab9.traps', '--pr', 'reports/eval_slice_regression.json', '--baseline', baseline, '--spec', spec], 0)]
    for trap in ['evaluator_errors_as_nan', 'dropped_failing_rows', 'cherry_picked_seeds', 'loosened_spec']:
        args = ['-m', 'lab9.gate', '--pr', f'reports/traps/{trap}.json', '--baseline', baseline,
                '--spec', f'reports/traps/{trap}.spec.yaml' if trap == 'loosened_spec' else spec, '--base-spec', spec]
        checks.append((args, 1))
    log = Path('../logs/advanced_checks.log')
    log.parent.mkdir(exist_ok=True)
    results = []
    started = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()
    with log.open('w', encoding='utf-8') as out:
        out.write(f'Advanced/Expert checks at {started}\n')
        for args, expected in checks:
            command = 'python ' + ' '.join(args)
            print(command, flush=True)
            proc = subprocess.run([sys.executable, *args], capture_output=True, text=True)
            okay = proc.returncode == expected
            if args[:2] == ['-m', 'lab9.gate'] and expected == 1:
                okay = okay and 'exit 1 — blocked:' in proc.stdout
                if any('reports/traps/' in a for a in args):
                    okay = okay and 'INTEGRITY' in proc.stdout
            results.append({'command': command, 'exit': proc.returncode, 'expected': expected,
                            'passed': okay, 'stdout': proc.stdout, 'stderr': proc.stderr})
            out.write(f'\n$ {command}\n{proc.stdout}{proc.stderr}\nexit={proc.returncode}; expected={expected}\n')
            out.flush()
            print(f"{'PASS' if okay else 'FAIL'} (exit {proc.returncode}, expected {expected})", flush=True)
            if not okay:
                print(proc.stdout, proc.stderr, flush=True)
        passed = sum(r['passed'] for r in results)
        out.write(f'\n{passed}/{len(results)} checks passed\n')
    Path('../docs/advanced_checks.json').write_text(json.dumps({'started': started, 'checks': results},
                                                              ensure_ascii=False, indent=2)+'\n')
    if passed == len(results):
        from scripts.build_advanced_docs import main as build_docs
        build_docs()
    print(f'{passed}/{len(results)} checks passed; log: {log}')
    return passed != len(results)


if __name__ == '__main__':
    raise SystemExit(main())

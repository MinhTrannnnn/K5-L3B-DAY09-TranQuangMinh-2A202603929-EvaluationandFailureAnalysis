"""Run the local Core CI contract and retain commands, output and exit statuses."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess
import sys


def main():
    log = Path('../logs/core_checks.log')
    log.parent.mkdir(exist_ok=True)
    checks = [
        (['-m','lab9.smoke'], 0),
        (['-m','lab9.evalset','--build','--check'], 0),
        (['-m','pytest','-q','-m','student','-o','addopts=','-k','lab9 and not advanced'], 0),
        (['-m','pytest','-q'], 0),
        (['-m','lab9.judge','--csv','data/eval/judge_tone_public.csv','--audit','5'], 0),
        (['-m','lab9.judge','--csv','data/eval/judge_helpful_public.csv','--audit','5'], 1),
        (['-m','scripts.core_evidence'], 0),
        (['-m','lab9.eval','--shape','swarm','--out','reports/baseline_v1.json'], 0),
        (['-m','lab9.eval','--shape','swarm','--out','reports/eval_pr.json'], 0),
        (['-m','lab9.gate','--pr','reports/eval_pr.json','--baseline','reports/baseline_v1.json'], 0),
        (['-m','lab9.ci_check','--pr','reports/eval_pr.json','--baseline','reports/baseline_v1.json'], 0),
        (['-m','lab9.eval','--shape','fixed'], 0),
        (['-m','lab9.gate','--pr','reports/eval_fixed.json','--baseline','reports/baseline_v1.json'], 0),
        (['-m','lab9.eval','--shape','seeded_regression'], 0),
        (['-m','lab9.gate','--pr','reports/eval_seeded_regression.json','--baseline','reports/baseline_v1.json'], 1),
        (['-m','scripts.build_core_docs'], 0),
    ]
    failures = []
    with log.open('w', encoding='utf-8') as out:
        out.write('Core checks at '+datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()+'\n')
        for args, expected in checks:
            command = 'python '+' '.join(args)
            print(command, flush=True)
            proc = subprocess.run([sys.executable,*args],capture_output=True,text=True)
            out.write(f'\n$ {command}\n{proc.stdout}{proc.stderr}\nexit={proc.returncode}; expected={expected}\n')
            out.flush()
            okay = proc.returncode == expected
            if args[:2] == ['-m','lab9.gate'] and expected == 1:
                okay = okay and 'exit 1 — blocked:' in proc.stdout and 'pass_rate' in proc.stdout.split('exit 1 — blocked:')[-1]
            if not okay:
                failures.append(command)
                print(proc.stdout,proc.stderr,flush=True)
            print(f"{'PASS' if okay else 'FAIL'} (exit {proc.returncode}, expected {expected})",flush=True)
        out.write(f'\n{len(checks)-len(failures)}/{len(checks)} checks passed\n')
    print(f'{len(checks)-len(failures)}/{len(checks)} checks passed; log: {log}')
    return bool(failures)


if __name__=='__main__':
    raise SystemExit(main())

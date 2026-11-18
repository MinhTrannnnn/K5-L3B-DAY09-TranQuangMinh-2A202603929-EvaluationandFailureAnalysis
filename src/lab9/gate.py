"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def _finite(value) -> bool:
    import math
    return isinstance(value, (int, float)) and math.isfinite(value)


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    """Keep every existing metric/slice at least as strict on the same dataset."""
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []
    for section in ("metrics", "slices"):
        key = (lambda m: m["id"]) if section == "metrics" else (lambda m: (m["name"], m["metric"]))
        current = {key(m): m for m in spec.get(section, [])}
        for old in base_spec.get(section, []):
            mid = key(old)
            new = current.get(mid)
            if new is None:
                problems.append(f"ratchet: removed {section} {mid}")
                continue
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"ratchet: disabled blocking {mid}")
            before = old.get("threshold", {}) if section == "metrics" else old
            after = new.get("threshold", {}) if section == "metrics" else new
            for name in ("min", "max", "max_increase", "no_significant_drop"):
                if name not in before:
                    continue
                missing = name not in after
                loosened = (name == "min" and not missing and after[name] < before[name]
                            or name in {"max", "max_increase"} and not missing and after[name] > before[name]
                            or name == "no_significant_drop" and before[name] and not after.get(name))
                if missing or loosened:
                    problems.append(f"ratchet: loosened {mid}/{name}")
            if section == "metrics" and old.get("kind") != new.get("kind"):
                problems.append(f"ratchet: changed metric kind {mid}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """Validate complete paired evidence before looking at thresholds, even on green runs."""
    from collections import Counter
    from lab9.graders import GRADERS
    from lab9.eval import aggregate

    problems = []
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
    graded = {m["id"] for m in spec["metrics"] if m["id"] in GRADERS}
    pair_sets = []
    tags_by_report = []
    for name, report in (("PR", pr), ("baseline", base)):
        manifest = report.get("manifest", {})
        rows = report.get("rows", [])
        seeds = manifest.get("seeds", [])
        item_count = manifest.get("items")
        if (not isinstance(item_count, int) or isinstance(item_count, bool) or item_count < 1
                or not seeds or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds)):
            problems.append(f"{name}: invalid item/seed manifest")
            pair_sets.append(set())
            tags_by_report.append({})
            continue
        if spec.get("seeds") is not None and set(seeds) != set(spec["seeds"]):
            problems.append(f"{name}: manifest seeds differ from spec")
        if len(rows) != item_count * len(seeds):
            problems.append(f"{name}: row count does not match manifest")
        pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
        counts = Counter(pairs)
        if any(count != 1 for count in counts.values()):
            problems.append(f"{name}: duplicate (item, seed) rows")
        items = {i for i, _ in pairs}
        if (len(items) != item_count or any(not isinstance(i, str) or not i for i in items)
                or set(pairs) != {(i, s) for i in items for s in seeds}):
            problems.append(f"{name}: incomplete item x seed matrix")
        pair_sets.append(set(pairs))
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator_failures is not empty")
        for metric, value in report.get("metrics", {}).items():
            if not _finite(value):
                problems.append(f"{name}: invalid metric {metric}")
        for metric in (m["id"] for m in spec["metrics"]):
            if not _finite(report.get("metrics", {}).get(metric)):
                problems.append(f"{name}: missing/nonfinite spec metric {metric}")
        tags = {}
        for r in rows:
            raw_tags = r.get("slices", [])
            if not isinstance(raw_tags, list) or any(not isinstance(t, str) for t in raw_tags):
                problems.append(f"{name}: invalid slice tags")
                raw_tags = []
            current_tags = frozenset(raw_tags)
            item = r.get("item_id")
            if item in tags and tags[item] != current_tags:
                problems.append(f"{name}: inconsistent slice tags for {item}")
            tags[item] = current_tags
            for metric in graded:
                value = r.get(metric)
                if not _finite(value) or value not in (0, 1):
                    problems.append(f"{name}: missing/invalid row metric {metric} for {item}@{r.get('seed')}")
            if "cost" in r and (not _finite(r["cost"]) or r["cost"] < 0):
                problems.append(f"{name}: invalid row cost")
        tags_by_report.append(tags)
        # Derive reported numbers again so editing summary metrics cannot hide bad rows.
        row_metrics = [m for m in report.get("metrics", {}) if rows and all(m in r for r in rows)]
        valid_rows = rows and all(_finite(r[m]) for r in rows for m in row_metrics)
        if valid_rows:
            expected = {}
            safety = {m["id"] for m in spec["metrics"] if m.get("kind") == "safety"}
            for m in row_metrics:
                values = [r[m] for r in rows]
                expected[m] = sum(values) if m in safety else round(sum(values) / len(values), 4)
            if "pass_rate" in row_metrics and all(_finite(r.get("cost")) for r in rows):
                computed = aggregate(rows, row_metrics, k_values=spec.get("pass_k", []))
                expected.update(computed)
            for m, want in expected.items():
                actual = report.get("metrics", {}).get(m)
                if m in report.get("metrics", {}) and (_finite(want) and _finite(actual)
                                                        and abs(actual - want) > 0.000051):
                    problems.append(f"{name}: summary metric {m} disagrees with rows")
    if pair_sets[0] != pair_sets[1]:
        problems.append("PR (item, seed) set differs from baseline")
    if tags_by_report[0] != tags_by_report[1]:
        problems.append("PR item slice tags differ from baseline")
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """Apply floors and paired item bootstrap separately within each declared slice."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        mid = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        failed = not a or set(a) != set(b)
        value = sum(a.values()) / len(a) if a else None
        if value is not None and "min" in entry and value < entry["min"]:
            failed = True
        note = ""
        if entry.get("no_significant_drop") and a and set(a) == set(b):
            if len(a) < 2 and a != b:
                failed, note = True, "insufficient paired items for bootstrap"
            else:
                keys = sorted(a)
                d, lo, hi = stats.paired_bootstrap(
                    [a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                failed = failed or hi < 0
        if failed and entry.get("blocking"):
            blocked.append(mid)
        verdict = "BLOCK" if failed and entry.get("blocking") else "warn" if failed else "ok"
        lines.append(f"  {mid:<38} {value!s:<8} {note:<32} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            if not keys or (len(keys) < 2 and a != b):
                verdict, note = "fail", "insufficient paired items for bootstrap"
            else:
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                   n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                                   confidence=bs.get("confidence", 0.95))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

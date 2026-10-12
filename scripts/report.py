"""Render RESULTS.md from results.json, so every number traces to the analysis output.

python scripts/report.py EVIDENCE_DIR

Undefined values (null in results.json, e.g. a lift over a zero control rate)
are shown as "n/a".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NA = "n/a"


def pct(x: float | None, digits: int = 2) -> str:
    return NA if x is None else f"{x * 100:.{digits}f}%"


def num(x: float | None, spec: str) -> str:
    return NA if x is None else format(x, spec)


def signed_pct(x: float | None) -> str:
    return NA if x is None else f"{x * 100:+.0f}%"


def main(folder: str) -> None:
    out = Path(folder)
    r = json.loads((out / "results.json").read_text())
    ex, pw = r["experiment_checks"], r["power"]
    lines = [
        "# Results",
        "",
        f"Data: {r['data']}. Customers: {r['customers']:,}.",
        "",
        "## 1. Is the experiment sound?",
        "",
        "| Arm | Customers |",
        "|---|---:|",
        *[f"| {arm} | {n:,} |" for arm, n in ex["arm_sizes"].items()],
        "",
        "- Sample-ratio mismatch test (intended 1/3 each): "
        f"p = {num(ex['sample_ratio_mismatch_p'], '.3f')}",
        f"- Largest covariate imbalance: |SMD| = {num(ex['worst_abs_smd'], '.3f')} "
        f"({'balanced' if ex['balanced'] else 'NOT balanced'}; threshold 0.1)",
        "",
        "## 2. What did each e-mail do? (vs no e-mail)",
        "",
        "| E-mail | Outcome | No e-mail | E-mail | Difference (95% CI) | Relative lift "
        "| p (Holm) |",
        "|---|---|---:|---:|---|---:|---:|",
    ]
    for arm, outcomes in r["effects"].items():
        for name, c in outcomes.items():
            fmt = (lambda v: num(v, ".2f")) if name == "spend" else pct
            lines.append(
                f"| {arm} | {name} | {fmt(c['control_mean'])} | {fmt(c['treatment_mean'])} | "
                f"{fmt(c['difference'])} ({fmt(c['ci_low'])} to {fmt(c['ci_high'])}) | "
                f"{signed_pct(c['relative_lift'])} | {num(c['p_value_holm'], '.2g')} |"
            )
    lines += [
        "",
        "## 3. Was it big enough?",
        "",
        f"With {pw['customers_per_arm']:,} customers per arm and a {pct(pw['control_conversion'])} "
        "control conversion rate, the smallest conversion lift detectable with 80% power "
        f"at 5% significance is {pct(pw['minimum_detectable_absolute_lift'], 3)} absolute "
        f"({signed_pct(pw['minimum_detectable_relative_lift']).lstrip('+')} relative).",
        "",
        "## 4. For whom? Uplift on the held-out half",
        "",
    ]
    first = next(iter(r["uplift"].values()))
    shares = [x["share_targeted"] for x in next(iter(first["models"].values()))["targeting"]]
    lines += [
        f"Qini p: (k + 1) / ({first['qini_permutations']:,} + 1), where k is how many of "
        f"{first['qini_permutations']:,} random rankings",
        "of the same held-out customers reach at least the model's Qini coefficient. A",
        "large p means the curve is above the random line by no more than chance would",
        "put it there.",
        "",
        "| E-mail | Model | Qini coefficient | Qini p | "
        + " | ".join(f"Uplift if top {s:.0%} targeted" for s in shares)
        + " | Average uplift |",
        "|---|---|---:|---:|" + "---:|" * len(shares) + "---:|",
    ]
    for arm, u in r["uplift"].items():
        for model, m in u["models"].items():
            targeted = " | ".join(pct(x["uplift_in_targeted"]) for x in m["targeting"])
            lines.append(
                f"| {arm} | {model} | {num(m['qini_coefficient_test'], '.3f')} | "
                f"{num(m['qini_permutation_p'], '.3f')} | {targeted} | "
                f"{pct(m['targeting'][0]['uplift_overall'])} |"
            )
    (out / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out / 'RESULTS.md'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "evidence")

"""Render RESULTS.md from results.json, so every number traces to the analysis output.

python scripts/report.py EVIDENCE_DIR
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def pct(x: float, digits: int = 2) -> str:
    return f"{x * 100:.{digits}f}%"


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
        f"p = {ex['sample_ratio_mismatch_p']:.3f}",
        f"- Largest covariate imbalance: |SMD| = {ex['worst_abs_smd']:.3f} "
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
            fmt = (lambda v: f"{v:.2f}") if name == "spend" else pct
            lines.append(
                f"| {arm} | {name} | {fmt(c['control_mean'])} | {fmt(c['treatment_mean'])} | "
                f"{fmt(c['difference'])} ({fmt(c['ci_low'])} to {fmt(c['ci_high'])}) | "
                f"{c['relative_lift'] * 100:+.0f}% | {c['p_value_holm']:.2g} |"
            )
    mde = pw["minimum_detectable_absolute_lift"]
    lines += [
        "",
        "## 3. Was it big enough?",
        "",
        f"With {pw['customers_per_arm']:,} customers per arm and a {pct(pw['control_conversion'])} "
        f"control conversion rate, the smallest conversion lift detectable with 80% power "
        f"at 5% significance is {pct(mde, 3)} absolute "
        f"({pw['minimum_detectable_relative_lift'] * 100:.0f}% relative).",
        "",
        "## 4. For whom? Uplift on the held-out half",
        "",
        "Qini p: the share of 1,000 random rankings of the same held-out customers",
        "that reach at least the model's Qini coefficient. A large p means the curve",
        "is above the random line by no more than chance would put it there.",
        "",
        "| E-mail | Model | Qini coefficient | Qini p | Uplift if top 10% targeted "
        "| top 30% | top 50% | Average uplift |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, u in r["uplift"].items():
        for model, m in u["models"].items():
            t = {round(x["share_targeted"], 2): x for x in m["targeting"]}
            lines.append(
                f"| {arm} | {model} | {m['qini_coefficient_test']:.3f} | "
                f"{m['qini_permutation_p']:.3f} | "
                f"{pct(t[0.1]['uplift_in_targeted'])} | {pct(t[0.3]['uplift_in_targeted'])} | "
                f"{pct(t[0.5]['uplift_in_targeted'])} | {pct(t[0.1]['uplift_overall'])} |"
            )
    (out / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out / 'RESULTS.md'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "evidence")

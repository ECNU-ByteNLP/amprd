"""
汇总实验“是否有效果”的关键数字（可直接粘进论文/报告）。

输出：
1) Full vs Baseline-TXT（results/comparison_full_vs_baseline.json）
2) Full vs Baseline-StrongPrompt（results/comparison_full_vs_strong_prompt.json）
3) 消融：Full vs 每个配置（results/ablation/ablation_analysis.json）

重点展示：
- full_mean / other_mean / diff
- wilcoxon p_value + Holm-Bonferroni q_value（FWER）
- Cliff's delta（效应量）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def f4(x: Any) -> str:
    if isinstance(x, (int, float)):
        return f"{float(x):.4f}"
    return str(x)


def summarize_full_vs(path: str, title: str) -> None:
    d = load_json(path)
    res = d.get("comparison_results", {})
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
    if not res:
        print("❌ 无 comparison_results")
        return

    metrics = list(res.keys())

    def sort_key(m: str) -> Tuple[float, float]:
        r = res[m]
        q = r.get("wilcoxon_corrected", {}).get("q_value", 1.0)
        diff = abs(float(r.get("improvement", 0.0)))
        return (float(q), -diff)

    metrics.sort(key=sort_key)

    for m in metrics:
        r = res[m]
        w = r.get("wilcoxon", {})
        wc = r.get("wilcoxon_corrected", {})
        full = r.get("full_system_mean")
        other = r.get("baseline_mean")
        diff = r.get("improvement")
        p = w.get("p_value")
        q = wc.get("q_value")
        delta = r.get("cliffs_delta")
        sig_q = wc.get("significant")
        print(
            f"{m:7s} full={f4(full)} other={f4(other)} diff={f4(diff)}  "
            f"p={f4(p)} q={f4(q)}  delta={f4(delta)}  sig_q={sig_q}"
        )


def summarize_ablation(path: str, focus_metrics: List[str] | None = None, topk: int = 6) -> None:
    d = load_json(path)
    comp = d.get("comparison_results", {})
    print("\n" + "=" * 78)
    print("消融：Full vs 每个配置（按 q 值 + 绝对差值排序，展示每配置Top项）")
    print("=" * 78)
    if not comp:
        print("❌ 无 comparison_results")
        return

    for cfg in sorted(comp.keys()):
        items = []
        for m, r in comp[cfg].items():
            if focus_metrics and m not in focus_metrics:
                continue
            q = r.get("wilcoxon_corrected", {}).get("q_value", 1.0)
            diff = float(r.get("difference", 0.0))  # full - ablation
            delta = float(r.get("cliffs_delta", 0.0))
            items.append((float(q), -abs(diff), m, diff, delta))

        items.sort()
        print(f"\n[{cfg}]")
        if not items:
            print("  (无可展示指标)")
            continue
        for q, _, m, diff, delta in items[:topk]:
            # diff>0 表示消融更差（full更好）
            direction = "full更好" if diff > 0 else ("消融更好" if diff < 0 else "无差异")
            print(f"  {m:7s} full-ablation={diff:+.4f}  q={q:.4f}  delta={delta:+.4f}  ({direction})")


def main() -> None:
    summarize_full_vs(
        "results/comparison_full_vs_baseline.json",
        "Full System vs Baseline-TXT (baseline_text_only)",
    )
    summarize_full_vs(
        "results/comparison_full_vs_strong_prompt.json",
        "Full System vs Baseline-StrongPrompt (baseline_strong_prompt)",
    )

    focus = ["S_comp", "S_mm", "S_tab", "S_bi", "S_sem", "S_biz", "S_tech", "S_risk", "S_ps", "S_uj", "S_hyp", "S_expert"]
    summarize_ablation("results/ablation/ablation_analysis.json", focus_metrics=focus, topk=6)


if __name__ == "__main__":
    main()







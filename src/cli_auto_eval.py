from __future__ import annotations

import argparse
from pathlib import Path

from src.experiments.auto_eval import (
    compare_systems,
    evaluate_system_outputs,
    save_experiment_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自动评测并进行显著性检验")
    parser.add_argument("--baseline-dir", type=Path, required=True, help="基线 PRD 目录")
    parser.add_argument("--ours-dir", type=Path, required=True, help="多智能体 PRD 目录")
    parser.add_argument("--output", type=Path, required=True, help="报告输出路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline_files = sorted(args.baseline_dir.glob("*.json"))
    ours_files = sorted(args.ours_dir.glob("*.json"))

    baseline_results = evaluate_system_outputs("baseline", baseline_files)
    ours_results = evaluate_system_outputs("ours", ours_files)

    report = compare_systems(baseline_results, ours_results)
    save_experiment_report(report, args.output)
    print(f"report saved to {args.output}")


if __name__ == "__main__":
    main()



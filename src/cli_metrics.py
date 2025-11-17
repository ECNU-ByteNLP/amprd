from __future__ import annotations

import argparse
from pathlib import Path

from src.metrics.report import pretty_print, render_report, save_report


def main() -> None:
    parser = argparse.ArgumentParser(description="计算自动评测指标并输出报告")
    parser.add_argument("--prd", type=Path, required=True, help="PRD JSON 文件")
    parser.add_argument("--output", type=Path, help="报告保存路径")
    args = parser.parse_args()

    report = render_report(args.prd)
    if args.output:
        save_report(report, args.output)
    print(pretty_print(report))


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from src.experiments.ablation import (
    AblationConfig,
    predefined_configs,
    run_ablation_suite,
)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="运行多智能体 PRD 系统消融实验")
    parser.add_argument("--brief", type=Path, required=True, help="输入概要 JSON 路径")
    parser.add_argument("--output", type=Path, default=Path("experiments/ablation"), help="结果输出目录")
    parser.add_argument("--config", type=Path, help="自定义消融配置 JSON 路径")
    args = parser.parse_args()

    brief = json.loads(args.brief.read_text(encoding="utf-8"))

    if args.config:
        cfg_payload = json.loads(args.config.read_text(encoding="utf-8"))
        configs = [AblationConfig(**item) for item in cfg_payload]
    else:
        configs = predefined_configs()

    results = run_ablation_suite(brief, configs, output_dir=args.output)
    print(f"Ablation results saved to {args.output/'ablation_results.json'}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()



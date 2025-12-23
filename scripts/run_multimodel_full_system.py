"""
Run the full PRDWeaver system on the 15-brief benchmark using a selectable model provider.

This is intended for *non-human* robustness checks (multi-model generalization) for a Findings-style paper.

Examples (PowerShell):
  python scripts/run_multimodel_full_system.py --model-provider qwen
  python scripts/run_multimodel_full_system.py --model-provider openai
  python scripts/run_multimodel_full_system.py --model-provider openai --tag deepseek --output results/multimodel/deepseek_full
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Windows UTF-8 safety (avoid closing underlying buffers).
if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name)
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            try:
                setattr(
                    sys,
                    _stream_name,
                    io.TextIOWrapper(_stream.detach(), encoding="utf-8", line_buffering=True),
                )
            except Exception:
                pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics

load_dotenv()


def setup_logging(log_dir: Path, name: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")],
        force=True,
    )
    logger = logging.getLogger(name)
    logger.info("log file: %s", log_file)
    return logger


def find_expert_prd(prd_id: str) -> Optional[Path]:
    # Keep consistent with other scripts; best-effort mapping.
    chinese_mapping_path = Path("data/chinese_prds/processed/brief_to_expert_mapping.json")
    if chinese_mapping_path.exists():
        try:
            mapping_data = json.loads(chinese_mapping_path.read_text(encoding="utf-8"))
            mappings = mapping_data.get("mappings", {})
            expert_info = mappings.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                p = Path(expert_info["expert_prd_path"])
                if p.exists():
                    return p
        except Exception:
            pass
    english_mapping_path = Path("data/expert_prds/mapping.json")
    if english_mapping_path.exists():
        try:
            mapping = json.loads(english_mapping_path.read_text(encoding="utf-8"))
            expert_info = mapping.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                p = Path(expert_info["expert_prd_path"])
                if p.exists():
                    return p
        except Exception:
            pass
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run full system on benchmark with selectable model provider.")
    p.add_argument("--model-provider", choices=["qwen", "openai"], default="qwen")
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory. Default: results/multimodel/{provider}_full",
    )
    p.add_argument("--tag", type=str, default=None, help="Optional tag appended to output dir name.")
    p.add_argument("--sleep", type=float, default=5.0, help="Delay between briefs to reduce rate limits.")
    p.add_argument("--force", action="store_true", help="Regenerate even if prd file already exists.")
    p.add_argument("--limit", type=int, default=None, help="Limit number of briefs (debug).")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    provider = args.model_provider
    out_dir = args.output
    if out_dir is None:
        suffix = f"{provider}_full"
        if args.tag:
            suffix = f"{args.tag}_{suffix}"
        out_dir = Path("results") / "multimodel" / suffix

    logger = setup_logging(Path("results/logs"), name=f"multimodel_{provider}")
    logger.info("=" * 70)
    logger.info("Multi-model full-system run")
    logger.info("model_provider=%s output=%s", provider, out_dir)
    logger.info("=" * 70)

    builder = BenchmarkBuilder(Path("data/benchmark"))
    prds = builder.list_prds()
    if args.limit:
        prds = prds[: args.limit]
    if not prds:
        raise RuntimeError("No benchmark briefs found under data/benchmark")

    orchestrator = MultiAgentOrchestrator(
        persist_dir=out_dir,
        model_provider=provider,
        communication_mode="blackboard",
    )

    results: List[Dict] = []
    start = time.time()
    for i, info in enumerate(prds, 1):
        prd_id = info["prd_id"]
        brief = builder.load_brief(prd_id)
        brief["prd_id"] = prd_id

        prd_path = out_dir / f"prd_{prd_id}.json"
        if prd_path.exists() and not args.force:
            logger.info("[%d/%d] %s exists -> recompute metrics", i, len(prds), prd_id)
            payload = json.loads(prd_path.read_text(encoding="utf-8"))
            expert = find_expert_prd(prd_id)
            basic = compute_all_metrics(payload)
            extended = compute_all_extended_metrics(payload, expert_prd_path=expert)
            results.append(
                {
                    "prd_id": prd_id,
                    "prd_path": str(prd_path),
                    "metrics": {**basic, **extended},
                    "generation_time": 0.0,
                    "expert_prd_path": str(expert) if expert else None,
                    "model_provider": provider,
                }
            )
            continue

        if i > 1 and args.sleep > 0:
            time.sleep(args.sleep)

        logger.info("[%d/%d] generating %s ...", i, len(prds), prd_id)
        t0 = time.time()
        state = orchestrator.run({"brief": brief})
        dt = time.time() - t0
        artifact = state.get("quality", {}).get("artifact_path")
        if not artifact or not Path(artifact).exists():
            logger.warning("  failed: no artifact_path")
            results.append(
                {
                    "prd_id": prd_id,
                    "prd_path": str(prd_path),
                    "metrics": {},
                    "generation_time": round(dt, 2),
                    "expert_prd_path": None,
                    "model_provider": provider,
                    "error": "no artifact_path",
                }
            )
            continue

        payload = json.loads(Path(artifact).read_text(encoding="utf-8"))
        expert = find_expert_prd(prd_id)
        basic = compute_all_metrics(payload)
        extended = compute_all_extended_metrics(payload, expert_prd_path=expert)
        results.append(
            {
                "prd_id": prd_id,
                "prd_path": str(artifact),
                "metrics": {**basic, **extended},
                "generation_time": round(dt, 2),
                "expert_prd_path": str(expert) if expert else None,
                "model_provider": provider,
            }
        )
        logger.info("  ok: %s (%.2fs)", Path(artifact).name, dt)

    total = time.time() - start
    out_dir.mkdir(parents=True, exist_ok=True)

    # Compute average metrics (flatten nested -> overall where possible)
    metric_names = [
        "S_comp",
        "S_mm",
        "S_tab",
        "S_bi",
        "S_var",
        "S_sem",
        "S_biz",
        "S_tech",
        "S_risk",
        "S_expert",
        "S_ps",
        "S_uj",
        "S_hyp",
    ]
    avg_metrics: Dict[str, Dict] = {}
    for m in metric_names:
        vals: List[float] = []
        for r in results:
            v = r.get("metrics", {}).get(m)
            if isinstance(v, dict):
                v = v.get("overall", 0.0)
            if isinstance(v, (int, float)):
                vals.append(float(v))
        if vals:
            avg_metrics[m] = {
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "count": len(vals),
            }

    summary = {
        "run_date": datetime.now().isoformat(),
        "model_provider": provider,
        "total_briefs": len(prds),
        "success_count": sum(1 for r in results if r.get("metrics")),
        "failed_count": sum(1 for r in results if not r.get("metrics")),
        "total_time_seconds": round(total, 2),
        "average_generation_time": round(
            sum(float(r.get("generation_time", 0.0)) for r in results) / max(len(results), 1), 2
        ),
        "average_metrics": avg_metrics,
        "detailed_results": results,
    }
    (out_dir / "metrics_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("wrote %s", out_dir / "metrics_summary.json")


if __name__ == "__main__":
    main()




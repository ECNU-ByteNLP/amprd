from __future__ import annotations

import json
import argparse
from pathlib import Path
import logging
from typing import Dict, Any

import sys

from dotenv import load_dotenv

# Ensure project root (containing 'src') is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import MultiAgentOrchestrator
from src.utils.brief_parser import parse_brief_text
from src.templates.manager import TemplateManager


def run_with_config(cfg: Dict[str, Any]) -> Path:
    """
    Run PRD generation using a simple config dict.
    Config fields (all optional except one of brief/brief_text):
      - brief: str (path to JSON)
      - brief_text: str (free text brief)
      - template_id: str
      - template_path: str
      - output: str (directory)
      - verbose: bool
    Returns: path to state_summary.json
    """
    output = Path(cfg.get("output") or "artifacts")
    verbose = bool(cfg.get("verbose", False))

    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # Build inputs
    inputs: Dict[str, Any] = {}
    if cfg.get("brief_text"):
        # Try to use LLM for parsing if available
        from src.models.qwen_client import create_qwen_clients_from_env
        text_cn, _, _ = create_qwen_clients_from_env()
        brief_json, parse_report = parse_brief_text(cfg["brief_text"], model=text_cn)
        inputs.update({"brief": brief_json, "brief_raw": cfg["brief_text"], "brief_parse_report": parse_report})
        logging.getLogger("Runner").info(
            "brief_text 模式；解析置信度=%.2f (method=%s)",
            parse_report.get("confidence", 0.0),
            parse_report.get("extraction_method", "unknown"),
        )
    elif cfg.get("brief"):
        brief_path = Path(cfg["brief"]).resolve()
        data = json.loads(brief_path.read_text(encoding="utf-8"))
        inputs.update({"brief": data})
        logging.getLogger("Runner").info("使用 Brief 文件：%s", brief_path)
    else:
        raise ValueError("Config must include either 'brief' or 'brief_text'.")

    if cfg.get("template_id") or cfg.get("template_path"):
        tm = TemplateManager()
        template_spec = tm.load(
            template_id=cfg.get("template_id"),
            template_path=Path(cfg["template_path"]) if cfg.get("template_path") else None,
        )
        inputs["template"] = template_spec
        logging.getLogger("Runner").info(
            "模板信息：id=%s name=%s path=%s",
            template_spec.get("id"),
            template_spec.get("name"),
            template_spec.get("path"),
        )

    orchestrator = MultiAgentOrchestrator(persist_dir=output)
    state = orchestrator.run(inputs)

    summary_path = output / "state_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PRD state written to {summary_path}")
    return summary_path


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run PRD generation via a simple config file.")
    parser.add_argument("--config", type=Path, required=True, help="Path to run config JSON.")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    run_with_config(cfg)


if __name__ == "__main__":
    main()



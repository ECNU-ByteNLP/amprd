from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.pipeline import MultiAgentOrchestrator


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Input brief not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate a multimodal bilingual PRD.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brief", type=Path, help="Path to brief JSON.")
    group.add_argument("--brief-text", type=str, help="Inline brief text to be parsed into JSON.")
    parser.add_argument("--template-id", type=str, default=None, help="Template id defined in templates/template_index.yaml.")
    parser.add_argument("--template-path", type=Path, default=None, help="Custom template markdown path.")
    parser.add_argument("--output", type=Path, default=Path("artifacts"), help="Output directory.")
    parser.add_argument(
        "--model-provider",
        type=str,
        default="qwen",
        choices=["qwen", "openai"],
        help="Model provider. 'openai' also works for OpenAI-compatible providers via OPENAI_BASE_URL.",
    )
    parser.add_argument(
        "--communication-mode",
        type=str,
        default="blackboard",
        choices=["blackboard", "async_queue"],
        help="Pipeline communication mode (use async_queue to emulate async scheduling).",
    )
    parser.add_argument(
        "--disable-agent",
        action="append",
        default=[],
        help="Disable an agent by name for ablations (repeatable), e.g., --disable-agent TableAgent",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed logs (已加载的模型、输出路径等信息)。",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # Build inputs payload
    inputs_payload: dict
    if args.brief_text:
        # Lazy import to keep CLI lightweight when not needed
        from src.utils.brief_parser import parse_brief_text
        from src.models.qwen_client import create_qwen_clients_from_env
        text_cn, _, _ = create_qwen_clients_from_env()
        brief_json, parse_report = parse_brief_text(args.brief_text, model=text_cn)
        inputs_payload = {"brief": brief_json, "brief_raw": args.brief_text, "brief_parse_report": parse_report}
        if args.verbose:
            logging.getLogger("CLI").info(
                "使用 brief-text 模式；解析置信度=%.2f (method=%s)",
                parse_report.get("confidence", 0.0),
                parse_report.get("extraction_method", "unknown"),
            )
    else:
        inputs_payload = {"brief": load_json(args.brief)}
        if args.verbose:
            logging.getLogger("CLI").info("使用 Brief JSON 文件：%s", args.brief)

    # Attach template requirements if provided
    if args.template_id or args.template_path:
        from src.templates.manager import TemplateManager
        tm = TemplateManager()
        template_spec = tm.load(template_id=args.template_id, template_path=args.template_path)
        inputs_payload["template"] = template_spec
        if args.verbose:
            logging.getLogger("CLI").info(
                "已加载模板：id=%s name=%s path=%s",
                template_spec.get("id"),
                template_spec.get("name"),
                template_spec.get("path"),
            )

    orchestrator = MultiAgentOrchestrator(
        persist_dir=args.output,
        model_provider=args.model_provider,
        communication_mode=args.communication_mode,
        disabled_agents=args.disable_agent,
    )
    if args.verbose:
        try:
            text_cn = orchestrator.agents["TextGen_CN"]._model.name  # type: ignore[attr-defined]
            text_en = orchestrator.agents["TextGen_EN"]._model.name  # type: ignore[attr-defined]
            vision = orchestrator.agents["VisionAgent"]._model.name  # type: ignore[attr-defined]
            print(f"[INFO] 使用模型: Text-CN={text_cn}, Text-EN={text_en}, Vision={vision}")
        except KeyError:
            print("[WARN] 未找到 Text/Vision Agent，可能在消融模式下运行。")
    state = orchestrator.run(inputs_payload)
    if args.verbose:
        artifact = state.get("quality", {}).get("artifact_path")
        print(f"[INFO] 生成完成，质量指标: {state.get('quality', {}).get('auto_metrics')}")
        if artifact:
            print(f"[INFO] PRD 文件: {artifact}")

    summary_path = args.output / "state_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PRD state written to {summary_path}")


if __name__ == "__main__":
    main()



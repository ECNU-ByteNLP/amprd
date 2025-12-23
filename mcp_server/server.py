from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.pipeline import MultiAgentOrchestrator
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics


def _best_effort_find_expert(prd_id: str) -> Optional[Path]:
    # Keep MCP server independent from webui package structure.
    repo_root = Path(__file__).resolve().parents[1]
    expert_dir = repo_root / "data" / "expert_prds"
    if expert_dir.exists():
        p = expert_dir / f"{prd_id}.json"
        if p.exists():
            return p
    return None


def main() -> None:
    """
    Optional MCP server.

    We intentionally import MCP lazily so the repo works without MCP installed.
    """
    try:
        # Official MCP python package (name: mcp). If not installed, raise a helpful error.
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "MCP server requires the optional dependency `mcp`.\n"
            "Install with: pip install mcp\n"
            f"Import error: {e}"
        ) from e

    mcp = FastMCP("amprd")

    @mcp.tool()
    def generate_prd(
        brief: Dict[str, Any],
        *,
        template: Optional[Dict[str, Any]] = None,
        persist_dir: str = "artifacts/mcp_runs",
        model_provider: str = "qwen",
        communication_mode: str = "blackboard",
        disabled_agents: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a PRD via the multi-agent pipeline and return artifact path + metrics."""
        out_dir = Path(persist_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {"brief": brief}
        if template:
            payload["template"] = template

        orchestrator = MultiAgentOrchestrator(
            persist_dir=out_dir,
            model_provider=model_provider,
            communication_mode=communication_mode,
            disabled_agents=disabled_agents,
        )
        state = orchestrator.run(payload)
        artifact_path = state.get("quality", {}).get("artifact_path")
        prd_json: Optional[Dict[str, Any]] = None
        if artifact_path and Path(artifact_path).exists():
            prd_json = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        return {
            "artifact_path": artifact_path,
            "state_summary": state.get("quality", {}),
            "prd": prd_json,
        }

    @mcp.tool()
    def evaluate_prd(
        prd: Dict[str, Any],
        *,
        prd_id: str = "uploaded_prd",
    ) -> Dict[str, Any]:
        """Compute the same metric suite used in the paper for a given PRD JSON."""
        expert = _best_effort_find_expert(prd_id)
        basic = compute_all_metrics(prd)
        extended = compute_all_extended_metrics(prd, expert_prd_path=expert)
        return {
            "prd_id": prd_id,
            "expert_prd_path": str(expert) if expert else None,
            "metrics": {**basic, **extended},
        }

    mcp.run()


if __name__ == "__main__":
    main()




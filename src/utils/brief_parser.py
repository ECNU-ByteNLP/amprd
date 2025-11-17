from __future__ import annotations

from typing import Dict, Tuple


def parse_brief_text(text: str) -> Tuple[Dict, Dict]:
    """
    Minimal parser that converts a free-form brief paragraph into a structured brief JSON.
    Strategy:
      - Heuristic defaults for required fields
      - Very light keyword extraction; leave advanced extraction to LLM in future
    Returns:
      (brief_json, report)
    """
    normalized = (text or "").strip()
    brief: Dict = {
        "title": "",
        "domain": "other",
        "goal": [normalized[:120]] if normalized else [],
        "scope": {"in": [], "out": []},
        "audience": [],
        "milestones": [],
        "kpis": [],
        "personas": [],
        "constraints": [],
        "risks": [],
        "references": [],
        "languages": ["zh", "en"],
        "visuals": []
    }
    report: Dict = {
        "confidence": 0.5 if normalized else 0.0,
        "notes": ["Heuristic parse; consider upgrading to LLM-powered extraction"],
        "missing_fields": [k for k in ["title", "audience", "milestones", "kpis"] if not brief.get(k)]
    }
    return brief, report



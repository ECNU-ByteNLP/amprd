from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class TemplateManager:
    """
    Loads template index and individual markdown templates.
    Produces a normalized template spec to attach into pipeline inputs.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or Path(__file__).resolve().parent.parent.parent / "templates").resolve()
        self.index_path = self.root / "template_index.yaml"
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        if not self.index_path.exists():
            return {}
        data = yaml.safe_load(self.index_path.read_text(encoding="utf-8")) or {}
        entries = {}
        for item in (data.get("templates") or []):
            if "id" in item:
                entries[item["id"]] = item
        return entries

    def load(self, *, template_id: Optional[str] = None, template_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load template spec by id or path, return normalized spec:
        {
          "id": "...",
          "name": "...",
          "path": "<abs>",
          "markdown": "<content>",
          "requires": { "tables":[], "visuals":[], "sections":[] },
          "fields": [...]
        }
        """
        if template_path:
            path = Path(template_path).resolve()
            content = path.read_text(encoding="utf-8")
            return {
                "id": path.stem,
                "name": path.stem,
                "path": str(path),
                "markdown": content,
                "requires": {"tables": [], "visuals": [], "sections": []},
                "fields": []
            }
        if not template_id or template_id not in self._index:
            raise ValueError(f"Template not found: {template_id}")
        item = self._index[template_id]
        path = (self.root / item["path"]).resolve()
        content = path.read_text(encoding="utf-8")
        requires = item.get("requires") or {}
        return {
            "id": item.get("id", path.stem),
            "name": item.get("name", path.stem),
            "path": str(path),
            "markdown": content,
            "requires": {
                "tables": list(requires.get("tables", [])),
                "visuals": list(requires.get("visuals", [])),
                "sections": list(requires.get("sections", [])),
            },
            "fields": list(item.get("fields", []))
        }



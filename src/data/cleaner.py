from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from bs4 import BeautifulSoup  # type: ignore[import]


@dataclass
class CleanResult:
    source_hash: str
    text_path: str
    summary_path: str


def clean_html(html_path: Path, output_dir: Path) -> CleanResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)

    sha = html_path.stem
    text_path = output_dir / f"{sha}.txt"
    summary_path = output_dir / f"{sha}_summary.json"

    text_path.write_text(cleaned, encoding="utf-8")
    summary = {"hash": sha, "line_count": len(cleaned.splitlines()), "char_count": len(cleaned)}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return CleanResult(source_hash=sha, text_path=str(text_path), summary_path=str(summary_path))


def clean_bulk(html_files: Iterable[Path], output_dir: Path) -> List[CleanResult]:
    return [clean_html(path, output_dir) for path in html_files]



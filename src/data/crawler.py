from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import requests


@dataclass
class CrawlTask:
    url: str
    domain: str
    tags: List[str]


@dataclass
class CrawlRecord:
    url: str
    domain: str
    tags: List[str]
    fetched_at: str
    status: int
    content_path: str
    metadata_path: str
    hash: str


class CrawlPipeline:
    """
    Minimal pipeline for可复现抓取 → 清洗 → 归档。

    设计目标：
        1. 只抓取公开网页。
        2. 保存原文快照 + 洁净文本（由 downstream 清洗器处理）。
        3. 记录许可、Headers、hash，便于合规审计。
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.snapshot_dir = output_dir / "snapshots"
        self.metadata_dir = output_dir / "metadata"
        self.log_path = output_dir / "crawl_log.jsonl"
        for path in (self.snapshot_dir, self.metadata_dir):
            path.mkdir(parents=True, exist_ok=True)

    def run(self, tasks: Iterable[CrawlTask]) -> List[CrawlRecord]:
        records: List[CrawlRecord] = []
        with self.log_path.open("a", encoding="utf-8") as log_file:
            for task in tasks:
                try:
                    response = requests.get(task.url, timeout=10)
                    status = response.status_code
                    text = response.text
                except Exception as exc:  # noqa: BLE001
                    status = 0
                    text = f"ERROR: {exc}"

                timestamp = datetime.utcnow().isoformat() + "Z"
                digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
                snapshot_path = self.snapshot_dir / f"{digest}.html"
                metadata_path = self.metadata_dir / f"{digest}.json"

                snapshot_path.write_text(text, encoding="utf-8", errors="ignore")
                metadata = {
                    "url": task.url,
                    "domain": task.domain,
                    "tags": task.tags,
                    "status": status,
                    "fetched_at": timestamp,
                    "sha256": digest,
                }
                metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

                record = CrawlRecord(
                    url=task.url,
                    domain=task.domain,
                    tags=task.tags,
                    fetched_at=timestamp,
                    status=status,
                    content_path=str(snapshot_path),
                    metadata_path=str(metadata_path),
                    hash=digest,
                )
                records.append(record)

                log_file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

        return records



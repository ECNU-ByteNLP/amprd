from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class SplitConfig:
    train_ratio: float = 0.7
    dev_ratio: float = 0.1
    test_ratio: float = 0.2
    ood_domains: List[str] | None = None
    seed: int = 42


def _load_metadata(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = payload.get("metadata", {})
    return {
        "path": str(path),
        "domain": meta.get("domain", "unknown"),
        "platform": meta.get("platform", []),
    }


def split_dataset(prd_dir: Path, config: SplitConfig) -> Dict[str, List[str]]:
    random.seed(config.seed)
    items = [_load_metadata(path) for path in prd_dir.glob("*.json")]

    ood_domains = set(config.ood_domains or [])
    ood_items = [item for item in items if item["domain"] in ood_domains]
    iid_items = [item for item in items if item["domain"] not in ood_domains]

    random.shuffle(iid_items)
    n = len(iid_items)
    train_end = int(n * config.train_ratio)
    dev_end = train_end + int(n * config.dev_ratio)

    splits = {
        "train": [item["path"] for item in iid_items[:train_end]],
        "dev": [item["path"] for item in iid_items[train_end:dev_end]],
        "test": [item["path"] for item in iid_items[dev_end:]],
        "ood_test": [item["path"] for item in ood_items],
    }
    return splits


def save_split(splits: Dict[str, List[str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(splits, ensure_ascii=False, indent=2), encoding="utf-8")



from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

PACKAGE_DIRS = [
    "schemas",
    "docs",
    "src",
    "examples",
]


def build_release(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "artifacts": [],
        "requirements": "requirements.txt",
    }

    for folder in PACKAGE_DIRS:
        src = Path(folder)
        if not src.exists():
            continue
        dst = output_dir / folder
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        manifest["artifacts"].append(str(dst))

    shutil.copy("README.md", output_dir / "README.md")
    shutil.copy("requirements.txt", output_dir / "requirements.txt")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Release package created at {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="打包开源发布资源")
    parser.add_argument("--output", type=Path, default=Path("release/package"), help="输出目录")
    args = parser.parse_args()
    build_release(args.output)


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.exporters.prd_renderer import load_prd, render_docx, render_markdown


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="将结构化 PRD 导出为 Markdown 或 DOCX。")
    parser.add_argument("--input", type=Path, required=True, help="输入 PRD JSON 路径。")
    parser.add_argument("--output", type=Path, required=True, help="输出文件路径。")
    parser.add_argument(
        "--format",
        choices=["markdown", "docx"],
        default="markdown",
        help="导出格式，默认为 markdown。",
    )
    parser.add_argument(
        "--language",
        choices=["auto", "zh", "en"],
        default="auto",
        help="输出语言：auto 为双语，zh 仅中文，en 仅英文。",
    )
    args = parser.parse_args()

    prd = load_prd(args.input)
    if args.format == "markdown":
        text = render_markdown(prd, language=args.language)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"已导出 Markdown: {args.output}")
    else:
        render_docx(prd, args.output, language=args.language)
        print(f"已导出 DOCX: {args.output}")


if __name__ == "__main__":
    main()


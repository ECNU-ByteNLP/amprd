from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from docx import Document  # type: ignore[import]
from docx.enum.style import WD_STYLE_TYPE  # type: ignore[import]
from docx.shared import Inches  # type: ignore[import]
from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore[import]
from docx.oxml.ns import qn  # type: ignore[import]


def load_prd(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(prd: Dict, language: str = "auto") -> str:
    lines: List[str] = []
    metadata = prd.get("metadata", {})
    lines.append(f"# {metadata.get('domain', '产品需求文档')}")
    lines.append("")
    lines.append(f"- PRD ID: {metadata.get('prd_id', 'N/A')}")
    lines.append(f"- 生成时间: {metadata.get('generated_at', 'N/A')}")
    lines.append("")

    sections = prd.get("sections", [])
    for section in sections:
        section_id = section.get("section_id", "未命名章节")
        lines.append(f"## {section_id}")
        lines.append("")
        content = section.get("content", {})
        zh_text = (content.get("zh-CN") or "").strip()
        en_text = (content.get("en-US") or "").strip()

        if language in ("auto", "zh") and zh_text:
            lines.append(zh_text.strip())
            lines.append("")
        if language in ("auto", "en") and en_text:
            lines.append("> " + en_text.strip())
            lines.append("")

        for table in section.get("tables", []):
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            header_line = " | ".join(_select_text(h, language) for h in headers)
            lines.append(header_line)
            lines.append(" | ".join("---" for _ in headers))
            for row in rows:
                cells = []
                for cell in row:
                    cells.append(_cell_text(cell, language))
                lines.append(" | ".join(cells))
            lines.append("")

        if language in ("auto", "zh"):
            for figure in section.get("figures", []):
                fig_lang = figure.get("language", "zh")
                if language == "zh" and fig_lang != "zh":
                    continue
                caption = figure.get("caption", {}).get("zh-CN") or figure.get("caption", {}).get("en-US")
                image_path = figure.get("image_path") or figure.get("path")
                lines.append(f"![{caption}]({image_path})")
                lines.append("")
        if language == "en":
            for figure in section.get("figures", []):
                if figure.get("language") != "en":
                    continue
                caption = figure.get("caption", {}).get("en-US") or figure.get("caption", {}).get("zh-CN")
                image_path = figure.get("image_path") or figure.get("path")
                lines.append(f"![{caption}]({image_path})")
                lines.append("")

    return "\n".join(lines)


def _ensure_style(document: Document, style_name: str, base_style: str) -> None:
    if style_name not in document.styles:
        style = document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = document.styles[base_style]


def render_docx(prd: Dict, output_path: Path, language: str = "auto") -> None:
    document = Document()
    _ensure_style(document, "Heading1CN", "Heading 1")
    _ensure_style(document, "Heading2CN", "Heading 2")

    # 基础文档样式（中文友好）
    try:
        document.styles["Normal"].font.name = "Microsoft YaHei"
        document.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    except Exception:
        pass

    metadata = prd.get("metadata", {})
    document.add_heading(metadata.get("domain", "产品需求文档"), level=0)
    meta_paragraph = document.add_paragraph()
    meta_paragraph.add_run(f"PRD ID: {metadata.get('prd_id', 'N/A')}\n")
    meta_paragraph.add_run(f"生成时间: {metadata.get('generated_at', 'N/A')}\n")

    sections = prd.get("sections", [])
    for section in sections:
        section_id = section.get("section_id", "未命名章节")
        document.add_heading(section_id, level=1)
        content = section.get("content", {})
        zh_text = (content.get("zh-CN") or "").strip()
        en_text = (content.get("en-US") or "").strip()
        if language in ("auto", "zh") and zh_text:
            _write_text(document, zh_text, prefer_cn=True)
        if language in ("auto", "en") and en_text:
            _write_text(document, en_text, prefer_cn=False)

        for table in section.get("tables", []):
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            doc_table = document.add_table(rows=len(rows) + 1, cols=len(headers))
            doc_table.style = "Light Grid"
            header_cells = doc_table.rows[0].cells
            for idx, header in enumerate(headers):
                header_cells[idx].text = _select_text(header, language)
                try:
                    header_cells[idx].paragraphs[0].runs[0].bold = True
                except Exception:
                    pass
            for r_idx, row in enumerate(rows, start=1):
                for c_idx, cell in enumerate(row):
                    text = _cell_text(cell, language)
                    doc_table.rows[r_idx].cells[c_idx].text = text

        if language in ("auto", "zh"):
            for figure in section.get("figures", []):
                fig_lang = figure.get("language", "zh")
                if language == "zh" and fig_lang != "zh":
                    continue
                image_path = figure.get("image_path") or figure.get("path")
                caption = figure.get("caption", {}).get("zh-CN") or figure.get("caption", {}).get("en-US") or ""
                if image_path and Path(image_path).exists():
                    document.add_picture(image_path, width=Inches(4.5))
                    last_paragraph = document.paragraphs[-1]
                    last_paragraph.alignment = 1  # center
                    document.add_paragraph(caption, style="Caption")
                else:
                    document.add_paragraph(f"[未找到图片] {caption} ({image_path or '无路径'})")
        if language in ("auto", "en"):
            for figure in section.get("figures", []):
                if figure.get("language") != "en":
                    continue
                image_path = figure.get("image_path") or figure.get("path")
                caption = figure.get("caption", {}).get("en-US") or figure.get("caption", {}).get("zh-CN") or ""
                if image_path and Path(image_path).exists():
                    document.add_picture(image_path, width=Inches(4.5))
                    last_paragraph = document.paragraphs[-1]
                    last_paragraph.alignment = 1  # center
                    document.add_paragraph(caption, style="Caption")
                else:
                    document.add_paragraph(f"[Image not found] {caption} ({image_path or 'N/A'})")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))


def _write_text(document: Document, text: str, *, prefer_cn: bool) -> None:
    """
    将自由文本以更规范的段落/列表形式写入 DOCX：
    - 能解析 JSON 列表/对象则格式化为项目符号或“键：值”块
    - 否则按换行符拆段；若行首带 '-' '*' '•' '·' 则使用项目符号样式
    - 若整段是长句，尝试按中文 '；'、'。' 或英文 '. ' 分行提升可读性
    """
    import json as _json

    stripped = (text or "").strip()
    if not stripped:
        return

    # 1) JSON 结构友好展示
    if (stripped.startswith("[") and stripped.endswith("]")) or (stripped.startswith("{") and stripped.endswith("}")):
        try:
            obj = _json.loads(stripped)
            if isinstance(obj, list):
                for item in obj:
                    para = document.add_paragraph(style="List Bullet")
                    para.add_run(str(item))
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = document.add_paragraph()
                    run_k = p.add_run(f"{k}：")
                    run_k.bold = True
                    p.add_run(str(v))
                return
        except Exception:
            pass

    # 2) 常见分隔符 → 多行
    separators = ["\n"]
    # 如果没有显式换行，尝试用句号/分号分句
    if "\n" not in stripped:
        if ("。" in stripped) or ("；" in stripped) or (". " in stripped) or ("; " in stripped):
            tmp = stripped.replace("；", "。\n").replace("; ", ". \n")
            stripped = tmp.replace(". ", ".\n")
    lines = [ln.strip() for ln in stripped.split("\n") if ln.strip()]

    for line in lines:
        bullet = False
        for prefix in ("- ", "* ", "• ", "· "):
            if line.startswith(prefix):
                bullet = True
                line = line[len(prefix):].strip()
                break
        if bullet:
            para = document.add_paragraph(style="List Bullet")
            para.add_run(line)
        else:
            para = document.add_paragraph()
            para.paragraph_format.space_after = 6
            para.add_run(line)


def _select_text(item: Dict, language: str) -> str:
    if language == "en":
        return item.get("en-US") or item.get("zh-CN") or item.get("value", "")
    if language == "zh":
        return item.get("zh-CN") or item.get("en-US") or item.get("value", "")
    return item.get("zh-CN") or item.get("en-US") or item.get("value", "")


def _cell_text(cell: Dict | str, language: str) -> str:
    if isinstance(cell, dict):
        return _select_text(cell, language)
    return str(cell)



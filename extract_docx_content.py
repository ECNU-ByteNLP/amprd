"""从DOCX文件中提取内容并生成自然语言描述"""
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re

def extract_docx_text_via_zip(docx_path: Path) -> str:
    """通过ZIP方式提取DOCX文件内容（不依赖python-docx）"""
    paragraphs = []
    
    try:
        with zipfile.ZipFile(docx_path, 'r') as docx:
            # 读取主文档内容
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # 定义命名空间
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # 提取所有段落文本
            for para in root.findall('.//w:p', ns):
                texts = []
                for t in para.findall('.//w:t', ns):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    para_text = ''.join(texts).strip()
                    if para_text:
                        paragraphs.append(para_text)
    except Exception as e:
        print(f"使用ZIP方式读取失败: {e}")
        return ""
    
    return "\n".join(paragraphs)

def extract_docx_text(docx_path: Path) -> str:
    """提取DOCX文件的所有文本内容（优先使用python-docx，否则用ZIP方式）"""
    try:
        from docx import Document
        doc = Document(str(docx_path))
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except ImportError:
        print("提示: python-docx未安装，使用ZIP方式读取...")
        return extract_docx_text_via_zip(docx_path)
    except Exception as e:
        print(f"使用python-docx读取失败: {e}，尝试ZIP方式...")
        return extract_docx_text_via_zip(docx_path)

def main():
    docx_path = Path("联想词.docx")
    
    if not docx_path.exists():
        print(f"错误: 文件不存在: {docx_path}")
        return
    
    print("=" * 80)
    print("正在提取DOCX文件内容...")
    print("=" * 80)
    content = extract_docx_text(docx_path)
    
    if not content:
        print("错误: 无法提取内容")
        return
    
    print("\n提取的内容:")
    print("=" * 80)
    print(content)
    print("\n" + "=" * 80)
    
    # 保存到文本文件
    output_path = Path("联想词_提取内容.txt")
    output_path.write_text(content, encoding="utf-8")
    print(f"\n内容已保存到: {output_path}")

if __name__ == "__main__":
    main()

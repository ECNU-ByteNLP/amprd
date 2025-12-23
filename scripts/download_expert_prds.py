"""
下载真实PRD参考标准

从pmprompt.com和相关资源下载真实的PRD示例，用于S_expert指标计算。
"""

import sys
import io
from pathlib import Path
import json
import urllib.request
from typing import Dict, List, Optional

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 定义真实PRD资源列表
EXPERT_PRDS = [
    {
        "brief_id": "general_linear_priority_micro_adjustments",
        "name": "Linear Priority Micro-Adjust",
        "company": "Linear",
        "url": "https://cdn.48web.com/sites/pmprompt/Linear%20example%20PRD_%20priority%20micro-adjust.pdf",
        "format": "pdf",
        "source": "pmprompt.com",
    },
    {
        "brief_id": "general_figma_real_time_collaboration",
        "name": "Figma Real-time Collaboration",
        "company": "Figma",
        "url": "https://pmprompt.com/blog/prd-examples",  # 需要从页面中提取
        "format": "pdf",
        "source": "pmprompt.com",
        "note": "需要从pmprompt.com页面下载",
    },
    {
        "brief_id": "general_google_search_algorithm_update",
        "name": "Google Search Algorithm Update",
        "company": "Google",
        "url": "https://pmprompt.com/blog/prd-examples",
        "format": "pdf",
        "source": "pmprompt.com",
        "note": "需要从pmprompt.com页面下载",
    },
    {
        "brief_id": "ecommerce_amazon_prime_video_personalization",
        "name": "Amazon Prime Video Features",
        "company": "Amazon",
        "url": "https://pmprompt.com/blog/prd-examples",
        "format": "pdf",
        "source": "pmprompt.com",
        "note": "需要从pmprompt.com页面下载",
    },
    # 其他PRD需要从pmprompt.com页面中提取链接
    # 暂时只下载有直接URL的Linear PRD
]


def download_file(url: str, output_path: Path, timeout: int = 30) -> bool:
    """
    下载文件
    
    Args:
        url: 下载URL
        output_path: 输出路径
        timeout: 超时时间（秒）
    
    Returns:
        是否下载成功
    """
    try:
        print(f"  下载中: {url}")
        print(f"  保存到: {output_path}")
        
        # 创建父目录
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载文件
        urllib.request.urlretrieve(url, str(output_path))
        
        # 检查文件是否存在且不为空
        if output_path.exists() and output_path.stat().st_size > 0:
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"  ✅ 下载成功: {output_path.name} ({file_size:.1f} KB)")
            return True
        else:
            print(f"  ❌ 下载失败: 文件为空")
            return False
            
    except Exception as e:
        print(f"  ❌ 下载失败: {e}")
        return False


def create_mapping_file(expert_prds: List[Dict], output_dir: Path) -> None:
    """
    创建映射文件（Brief ID -> 专家PRD路径）
    
    Args:
        expert_prds: 专家PRD列表
        output_dir: 输出目录
    """
    mapping = {}
    
    for prd_info in expert_prds:
        if prd_info.get("downloaded"):
            brief_id = prd_info["brief_id"]
            file_name = prd_info.get("file_name", f"{brief_id}.{prd_info['format']}")
            file_path = output_dir / file_name
            
            # 如果是PDF，需要转换为JSON后才能使用
            if prd_info["format"] == "pdf":
                json_path = output_dir / f"{Path(file_name).stem}.json"
                mapping[brief_id] = {
                    "expert_prd_path": str(json_path).replace("\\", "/"),
                    "source_pdf": str(file_path).replace("\\", "/"),
                    "source": prd_info["source"],
                    "company": prd_info["company"],
                    "url": prd_info["url"],
                    "status": "pdf_downloaded",  # 需要转换为JSON
                }
            else:
                mapping[brief_id] = {
                    "expert_prd_path": str(file_path).replace("\\", "/"),
                    "source": prd_info["source"],
                    "company": prd_info["company"],
                    "url": prd_info["url"],
                    "status": "ready",
                }
    
    # 保存映射文件
    mapping_path = output_dir / "mapping.json"
    mapping_path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✅ 映射文件已保存: {mapping_path}")


def main():
    print("=" * 60)
    print("下载真实PRD参考标准")
    print("=" * 60)
    print()
    
    # 创建输出目录
    output_dir = Path("data/expert_prds")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {output_dir}")
    print()
    
    # 下载PRD
    downloaded = 0
    skipped = 0
    
    for prd_info in EXPERT_PRDS:
        brief_id = prd_info["brief_id"]
        name = prd_info["name"]
        url = prd_info["url"]
        format_type = prd_info["format"]
        
        print(f"[{EXPERT_PRDS.index(prd_info) + 1}/{len(EXPERT_PRDS)}] {name} ({brief_id})")
        
        # 检查URL是否可用
        if "pmprompt.com/blog/prd-examples" in url and "Linear" not in name:
            print(f"  ⚠️  跳过: 需要从pmprompt.com页面手动下载")
            print(f"  提示: 请访问 {url} 下载对应的PRD")
            skipped += 1
            continue
        
        # 确定输出文件名
        file_name = f"{brief_id}.{format_type}"
        output_path = output_dir / file_name
        
        # 检查是否已存在
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024
            print(f"  ⚠️  已存在: {output_path.name} ({file_size:.1f} KB)")
            print(f"  ℹ️  跳过下载（如需重新下载，请先删除文件）")
            prd_info["downloaded"] = True
            prd_info["file_name"] = file_name
            skipped += 1
            continue
        
        # 下载文件
        success = download_file(url, output_path)
        if success:
            prd_info["downloaded"] = True
            prd_info["file_name"] = file_name
            downloaded += 1
        else:
            skipped += 1
        
        print()
    
    # 创建映射文件
    print("=" * 60)
    print("创建映射文件...")
    create_mapping_file(EXPERT_PRDS, output_dir)
    
    # 总结
    print()
    print("=" * 60)
    print("下载总结")
    print("=" * 60)
    print(f"✅ 成功下载: {downloaded} 个")
    print(f"⚠️  跳过/失败: {skipped} 个")
    print(f"📁 输出目录: {output_dir}")
    print()
    
    if downloaded > 0:
        print("下一步:")
        print("1. 将PDF格式的PRD转换为JSON格式（符合系统PRD Schema）")
        print("2. 更新 mapping.json 中的 expert_prd_path")
        print("3. 运行实验，系统会自动使用这些真实PRD计算S_expert指标")
        print()
        print("参考文档:")
        print("- data/expert_prds/README.md")
        print("- docs/expert_prds_integration_plan.md")
    
    print("=" * 60)


if __name__ == "__main__":
    main()


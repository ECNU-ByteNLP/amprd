"""
批量将PRD JSON文件导出为DOCX格式

支持：
- 批量导出目录中的所有PRD JSON文件
- 支持中文、英文、双语三种模式
- 自动创建输出目录
"""

import sys
import io
import json
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.exporters.prd_renderer import load_prd, render_docx

# 加载环境变量
load_dotenv()


def export_prd_to_docx(
    json_path: Path,
    output_dir: Path,
    language: str = "auto",
    overwrite: bool = False,
) -> Optional[Path]:
    """
    将单个PRD JSON文件导出为DOCX
    
    Args:
        json_path: PRD JSON文件路径
        output_dir: 输出目录
        language: 输出语言（"auto"=双语, "zh"=仅中文, "en"=仅英文）
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        Path: 导出的DOCX文件路径，失败返回None
    """
    try:
        # 加载PRD JSON
        prd = load_prd(json_path)
        
        # 确定输出文件名
        json_stem = json_path.stem
        if json_stem.startswith("prd_"):
            base_name = json_stem[4:]  # 去掉"prd_"前缀
        else:
            base_name = json_stem
        
        # 根据语言确定后缀
        if language == "auto":
            suffix = "_zh_en"
        elif language == "zh":
            suffix = "_zh"
        elif language == "en":
            suffix = "_en"
        else:
            suffix = ""
        
        output_filename = f"{base_name}{suffix}.docx"
        # 确保output_dir是绝对路径
        output_dir = output_dir.resolve()
        output_path = output_dir / output_filename
        
        # 检查文件是否已存在
        if output_path.exists() and not overwrite:
            print(f"  ⏭️  跳过（文件已存在）: {output_path.name}")
            return output_path
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保output_path是绝对路径
        output_path = output_path.resolve()
        
        # 导出DOCX
        render_docx(prd, output_path, language=language)
        
        return output_path
        
    except Exception as e:
        print(f"  ❌ 导出失败: {e}")
        return None


def batch_export_prds_to_docx(
    input_dir: Path,
    output_dir: Path,
    language: str = "auto",
    overwrite: bool = False,
    prd_ids: Optional[List[str]] = None,
) -> dict:
    """
    批量将PRD JSON文件导出为DOCX
    
    Args:
        input_dir: 输入目录（包含PRD JSON文件）
        output_dir: 输出目录
        language: 输出语言（"auto"=双语, "zh"=仅中文, "en"=仅英文）
        overwrite: 是否覆盖已存在的文件
        prd_ids: 可选，指定要导出的PRD ID列表（如果为None，则导出所有）
    
    Returns:
        dict: 导出结果统计
    """
    # 查找所有PRD JSON文件
    prd_files = sorted(input_dir.glob("prd_*.json"))
    
    if not prd_files:
        print(f"⚠️  在目录 {input_dir} 中未找到PRD JSON文件")
        return {"total": 0, "success": 0, "failed": 0}
    
    # 如果指定了PRD IDs，过滤文件
    if prd_ids:
        filtered_files = []
        for prd_file in prd_files:
            # 提取PRD ID（从文件名或JSON内容）
            file_stem = prd_file.stem
            if file_stem.startswith("prd_"):
                prd_id = file_stem[4:]
            else:
                prd_id = file_stem
            
            # 也尝试从JSON内容中获取
            if prd_id not in prd_ids:
                try:
                    prd = load_prd(prd_file)
                    json_prd_id = prd.get("metadata", {}).get("prd_id") or prd.get("prd_id")
                    if json_prd_id in prd_ids:
                        filtered_files.append(prd_file)
                except Exception:
                    pass
            else:
                filtered_files.append(prd_file)
        
        prd_files = filtered_files
    
    print(f"📋 找到 {len(prd_files)} 个PRD JSON文件")
    print(f"📂 输入目录: {input_dir}")
    print(f"📂 输出目录: {output_dir}")
    print(f"🌐 输出语言: {language}")
    print()
    
    results = {
        "total": len(prd_files),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "outputs": [],
    }
    
    for idx, prd_file in enumerate(prd_files, 1):
        print(f"[{idx}/{len(prd_files)}] 处理: {prd_file.name}...", end=" ", flush=True)
        
        output_path = export_prd_to_docx(
            prd_file,
            output_dir,
            language=language,
            overwrite=overwrite,
        )
        
        if output_path:
            if output_path.exists():
                results["success"] += 1
                # 确保output_path是绝对路径后再计算相对路径
                abs_output_path = output_path.resolve()
                abs_project_root = PROJECT_ROOT.resolve()
                try:
                    relative_path = str(abs_output_path.relative_to(abs_project_root))
                    results["outputs"].append(relative_path.replace("\\", "/"))
                except ValueError:
                    # 如果不在项目根目录下，使用绝对路径
                    results["outputs"].append(str(abs_output_path))
                print(f"✅ {output_path.name}")
            else:
                results["skipped"] += 1
        else:
            results["failed"] += 1
    
    print()
    print("=" * 70)
    print("批量导出完成！")
    print("=" * 70)
    print(f"✅ 成功: {results['success']}/{results['total']}")
    if results["failed"] > 0:
        print(f"❌ 失败: {results['failed']}/{results['total']}")
    if results["skipped"] > 0:
        print(f"⏭️  跳过: {results['skipped']}/{results['total']}")
    print(f"📁 输出目录: {output_dir}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="批量将PRD JSON文件导出为DOCX格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 导出完整系统的所有PRD为双语DOCX
  python scripts/export_prds_to_docx.py \\
    --input results/full_system \\
    --output results/full_system_docx

  # 导出为仅中文DOCX
  python scripts/export_prds_to_docx.py \\
    --input results/full_system \\
    --output results/full_system_docx \\
    --language zh

  # 导出为仅英文DOCX
  python scripts/export_prds_to_docx.py \\
    --input results/full_system \\
    --output results/full_system_docx \\
    --language en

  # 导出指定的PRD（从metrics_summary.json中读取）
  python scripts/export_prds_to_docx.py \\
    --input results/full_system \\
    --output results/full_system_docx \\
    --from-metrics results/full_system/metrics_summary.json
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="输入目录（包含PRD JSON文件）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="输出目录（DOCX文件将保存在此处）",
    )
    parser.add_argument(
        "--language",
        choices=["auto", "zh", "en"],
        default="auto",
        help="输出语言：auto=双语，zh=仅中文，en=仅英文（默认：auto）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的文件（默认：跳过已存在的文件）",
    )
    parser.add_argument(
        "--from-metrics",
        type=Path,
        help="从metrics_summary.json中读取成功的PRD ID列表，仅导出这些PRD",
    )
    
    args = parser.parse_args()
    
    # 如果指定了metrics_summary.json，从中提取成功的PRD IDs
    prd_ids = None
    if args.from_metrics and args.from_metrics.exists():
        try:
            metrics_data = json.loads(args.from_metrics.read_text(encoding="utf-8"))
            detailed_results = metrics_data.get("detailed_results", [])
            prd_ids = [r["prd_id"] for r in detailed_results if r.get("prd_id")]
            print(f"📋 从 {args.from_metrics.name} 中读取到 {len(prd_ids)} 个成功的PRD ID")
            print()
        except Exception as e:
            print(f"⚠️  读取metrics_summary.json失败: {e}")
            print("将导出所有PRD JSON文件")
            print()
    
    # 执行批量导出
    results = batch_export_prds_to_docx(
        input_dir=args.input,
        output_dir=args.output,
        language=args.language,
        overwrite=args.overwrite,
        prd_ids=prd_ids,
    )
    
    # 保存导出结果
    results_path = args.output / "export_results.json"
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"📝 导出结果已保存: {results_path}")


if __name__ == "__main__":
    main()


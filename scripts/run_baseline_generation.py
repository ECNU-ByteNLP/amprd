"""
运行基线系统生成PRD

为15个Brief生成3个基线系统的PRD：
1. Baseline-TXT (TextOnly)
2. Baseline-TPL (Template)
3. Baseline-RET (Retrieval)

输出目录：
- results/baseline_text_only/
- results/baseline_template/
- results/baseline_retrieval/
"""

import sys
import io
import json
import time
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baselines.text_only import generate_prd_text_only
from src.baselines.template import generate_prd_template
from src.baselines.retrieval import RetrievalBaseline
from src.data.benchmark_builder import BenchmarkBuilder
from src.models.qwen_client import create_qwen_clients_from_env


def main():
    load_dotenv()
    
    print("=" * 70)
    print("基线系统PRD生成")
    print("=" * 70)
    print()
    
    # 加载基准数据集
    benchmark_dir = Path("data/benchmark")
    builder = BenchmarkBuilder(benchmark_dir)
    prds = builder.list_prds()
    
    if not prds:
        print("❌ 未找到Brief文件")
        return
    
    print(f"📋 找到 {len(prds)} 个Brief")
    print()
    
    # 创建输出目录
    output_dirs = {
        "text_only": Path("results/baseline_text_only"),
        "template": Path("results/baseline_template"),
        "retrieval": Path("results/baseline_retrieval"),
    }
    for output_dir in output_dirs.values():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化模型（用于TextOnly和Retrieval）
    text_cn, _, _ = create_qwen_clients_from_env()
    model = text_cn  # 如果可用则使用Qwen，否则使用Mock
    
    # 初始化Retrieval基线
    try:
        retrieval_baseline = RetrievalBaseline(
            corpus_dir=Path("data/chinese_prds/processed"),
            model_name="paraphrase-multilingual-MiniLM-L12-v2",
        )
        print(f"✅ Retrieval基线已初始化（语料库: {len(retrieval_baseline.index)} 个PRD）")
    except Exception as e:
        print(f"⚠️  Retrieval基线初始化失败: {e}")
        print("   将跳过Retrieval基线生成")
        retrieval_baseline = None
    
    print()
    
    # 统计信息
    stats = {
        "text_only": {"success": 0, "failed": 0},
        "template": {"success": 0, "failed": 0},
        "retrieval": {"success": 0, "failed": 0},
    }
    
    # 处理每个Brief
    for idx, prd_info in enumerate(prds, 1):
        prd_id = prd_info["prd_id"]
        print(f"[{idx}/{len(prds)}] 处理: {prd_id}")
        
        try:
            brief = builder.load_brief(prd_id)
        except Exception as e:
            print(f"  ❌ 加载Brief失败: {e}")
            continue
        
        # 添加prd_id到brief（如果不存在）
        if "prd_id" not in brief:
            brief["prd_id"] = prd_id
        
        # 1. Baseline-TXT (TextOnly)
        print(f"  → Baseline-TXT...", end=" ", flush=True)
        try:
            prd_txt = generate_prd_text_only(brief, model=model)
            output_path = output_dirs["text_only"] / f"prd_{prd_id}.json"
            output_path.write_text(
                json.dumps(prd_txt, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            stats["text_only"]["success"] += 1
            print("✅")
        except Exception as e:
            stats["text_only"]["failed"] += 1
            print(f"❌ {str(e)[:50]}")
        
        # 2. Baseline-TPL (Template)
        print(f"  → Baseline-TPL...", end=" ", flush=True)
        try:
            prd_tpl = generate_prd_template(brief)
            output_path = output_dirs["template"] / f"prd_{prd_id}.json"
            output_path.write_text(
                json.dumps(prd_tpl, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            stats["template"]["success"] += 1
            print("✅")
        except Exception as e:
            stats["template"]["failed"] += 1
            print(f"❌ {str(e)[:50]}")
        
        # 3. Baseline-RET (Retrieval)
        if retrieval_baseline:
            print(f"  → Baseline-RET...", end=" ", flush=True)
            try:
                prd_ret = retrieval_baseline.generate(brief, model=model)
                output_path = output_dirs["retrieval"] / f"prd_{prd_id}.json"
                output_path.write_text(
                    json.dumps(prd_ret, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                stats["retrieval"]["success"] += 1
                print("✅")
            except Exception as e:
                stats["retrieval"]["failed"] += 1
                print(f"❌ {str(e)[:50]}")
        else:
            print(f"  → Baseline-RET... ⏭️  (已跳过)")
        
        # 添加延迟以避免API限流（如果使用真实模型）
        if model and idx < len(prds):
            time.sleep(2.0)
        
        print()
    
    # 输出统计信息
    print("=" * 70)
    print("生成完成！统计信息：")
    print("=" * 70)
    print()
    
    for baseline_name, stat in stats.items():
        total = stat["success"] + stat["failed"]
        success_rate = (stat["success"] / total * 100) if total > 0 else 0
        print(f"{baseline_name.upper():15} 成功: {stat['success']:2d} / {total:2d} ({success_rate:5.1f}%)")
    
    print()
    print("输出目录：")
    for name, output_dir in output_dirs.items():
        print(f"  - {name:15} {output_dir}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()


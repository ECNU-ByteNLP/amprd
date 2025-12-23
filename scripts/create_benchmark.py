"""
创建扩展的基准数据集

一键创建15个PRD样例，覆盖14种PRD模板风格。
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.benchmark_builder import create_sample_benchmark_prds


def main():
    print("=" * 60)
    print("创建扩展的基准数据集")
    print("=" * 60)
    print()
    
    benchmark_dir = Path("data/benchmark")
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"目标目录: {benchmark_dir.absolute()}")
    print()
    
    try:
        samples = create_sample_benchmark_prds(benchmark_dir)
        print(f"✅ 成功创建 {len(samples)} 个基准PRD样例")
        print()
        print("样例列表（覆盖14种PRD模板风格）：")
        print()
        
        # 按领域分组显示
        by_domain = {}
        for s in samples:
            domain = s.domain
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(s)
        
        for domain, domain_samples in sorted(by_domain.items()):
            print(f"  {domain.upper()} 领域 ({len(domain_samples)}个):")
            for s in domain_samples:
                template_info = f" [{s.template_style}]" if s.template_style else ""
                print(f"    - {s.title}{template_info}")
            print()
        
        print("=" * 60)
        print("数据集创建完成！")
        print("=" * 60)
        print()
        print("下一步:")
        print("  1. 运行快速实验: python scripts/quick_start_experiment.py")
        print("  2. 运行完整实验: python scripts/run_benchmark_experiment.py")
        print("  3. 查看数据集: cat data/benchmark/benchmark_index.json")
        
    except Exception as e:
        print(f"❌ 创建数据集时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


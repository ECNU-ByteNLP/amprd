"""
测试Few-shot集成效果

验证：
1. Few-shot示例是否正确加载
2. Prompt是否正确注入Few-shot示例
3. 映射关系是否正确
"""

import sys
import io
from pathlib import Path
import json

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.few_shot_loader import load_few_shot_examples, format_few_shot_examples_for_prompt
from src.data.benchmark_builder import BenchmarkBuilder


def main():
    print("=" * 70)
    print("测试Few-shot集成效果")
    print("=" * 70)
    print()
    
    # 加载一个Brief
    builder = BenchmarkBuilder(Path("data/benchmark"))
    prds = builder.list_prds()
    
    if not prds:
        print("❌ 未找到Brief文件")
        return
    
    # 测试第一个Brief
    test_brief_id = prds[0]["prd_id"]
    brief = builder.load_brief(test_brief_id)
    
    print(f"📋 测试Brief: {test_brief_id}")
    print(f"   标题: {brief.get('goal', 'N/A')}")
    print(f"   领域: {brief.get('domain', 'N/A')}")
    print()
    
    # 加载Few-shot示例
    print("🔄 加载Few-shot示例...")
    examples = load_few_shot_examples(brief, top_k=1)
    
    if not examples:
        print("  ⚠️  未找到Few-shot示例")
        print("  可能原因：")
        print("    1. 映射文件不存在")
        print("    2. Brief ID不匹配")
        print("    3. 专家PRD文件不存在")
        return
    
    print(f"  ✅ 找到 {len(examples)} 个Few-shot示例")
    print()
    
    # 显示示例信息
    for i, example in enumerate(examples, 1):
        print(f"  示例 {i}:")
        print(f"    来源: {example.get('source', 'N/A')}")
        print(f"    领域: {example.get('domain', 'N/A')}")
        print(f"    质量等级: {example.get('quality_level', 'N/A')}")
        print(f"    倒推案例: {example.get('is_reverse', False)}")
        print(f"    大厂案例: {example.get('is_big_company', False)}")
        print(f"    章节数量: {len(example.get('sections', []))}")
        print()
    
    # 格式化Few-shot示例
    print("🔄 格式化Few-shot示例...")
    formatted = format_few_shot_examples_for_prompt(examples, language="zh-CN", max_sections=2)
    
    if formatted:
        print("  ✅ Few-shot示例格式化成功")
        print()
        print("  格式化后的示例（前500字符）:")
        print("  " + "-" * 66)
        print("  " + formatted[:500].replace("\n", "\n  "))
        if len(formatted) > 500:
            print("  ...")
        print("  " + "-" * 66)
    else:
        print("  ⚠️  Few-shot示例格式化失败（可能是章节为空）")
        print("  提示：需要先将PDF转换为JSON格式")
    
    print()
    print("=" * 70)
    print("测试完成！")
    print("=" * 70)
    print()
    print("📝 说明:")
    print("  - Few-shot示例已成功加载")
    print("  - 如果章节为空，需要先将PDF转换为JSON格式")
    print("  - Few-shot示例会在TextGen生成时自动注入到Prompt中")


if __name__ == "__main__":
    main()


"""
验证S_bi指标修复效果

对比修复前后的S_bi指标值，验证修复是否有效。
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

from src.metrics.quality import compute_bilingual_consistency


def main():
    print("=" * 70)
    print("验证S_bi指标修复效果")
    print("=" * 70)
    print()
    
    # 加载已生成的PRD
    prd_dir = Path("results/full_system")
    prd_files = list(prd_dir.glob("prd_*.json"))
    
    if not prd_files:
        print("❌ 未找到PRD文件，请先运行快速实验生成PRD")
        return
    
    print(f"📁 找到 {len(prd_files)} 个PRD文件")
    print()
    
    # 计算修复后的S_bi指标
    results = []
    for prd_path in prd_files[:5]:  # 测试前5个
        try:
            prd = json.loads(prd_path.read_text(encoding="utf-8"))
            s_bi = compute_bilingual_consistency(prd)
            
            results.append({
                "prd_id": prd_path.stem,
                "s_bi": s_bi,
            })
            
            print(f"  {prd_path.name[:30]}...: S_bi = {s_bi:.4f}")
        except Exception as e:
            print(f"  ⚠️  {prd_path.name}: 计算失败 - {e}")
    
    print()
    
    if results:
        avg_s_bi = sum(r["s_bi"] for r in results) / len(results)
        print(f"📊 平均S_bi: {avg_s_bi:.4f}")
        print()
        
        if avg_s_bi > 0.3:
            print("✅ S_bi指标修复成功！")
            print(f"   修复前平均值: ~0.106")
            print(f"   修复后平均值: {avg_s_bi:.4f}")
            print(f"   提升: {(avg_s_bi - 0.106) / 0.106 * 100:.1f}%")
        else:
            print("⚠️  S_bi指标仍然偏低，可能需要进一步优化")
    else:
        print("❌ 无法计算S_bi指标")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()


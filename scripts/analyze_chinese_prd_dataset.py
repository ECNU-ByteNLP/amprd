"""
分析中文PRD数据集

分析300份真实中文PRD案例的结构、格式、领域分布等特征。
"""

import sys
import io
from pathlib import Path
import json
import re
from collections import Counter
from typing import Dict, List, Tuple

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PRD_DIR = Path(r"D:\2025pos\2026paper\amprd\【300份案例-产品经理PRD产品需求文档】")


def extract_domain_from_filename(filename: str) -> str:
    """从文件名提取领域信息"""
    domain_keywords = {
        "电商": ["电商", "淘宝", "京东", "拼多多", "严选", "每日优鲜", "盒马", "饿了么", "外卖", "购物", "商城"],
        "社交": ["社交", "微信", "QQ", "Soul", "小红书", "陌陌", "多闪", "Soul", "点友"],
        "教育": ["教育", "学习", "老师", "作业", "驾考", "读书", "阅读", "课程", "培训"],
        "金融": ["金融", "支付", "贷款", "信贷", "理财", "P2P", "信用卡", "积分"],
        "旅游": ["旅游", "旅行", "机票", "酒店", "民宿", "澳门", "攻略"],
        "娱乐": ["音乐", "视频", "直播", "短视频", "抖音", "B站", "喜马拉雅", "腾讯会议"],
        "工具": ["工具", "笔记", "记账", "清单", "日历", "翻译", "浏览器", "云"],
        "医疗": ["医疗", "健康", "医生", "医疗", "宠物", "宠"],
        "生活服务": ["生活", "服务", "配送", "外卖", "家具", "回收"],
        "企业服务": ["企业", "B端", "后台", "管理", "系统", "OA", "TMS"],
    }
    
    filename_lower = filename.lower()
    for domain, keywords in domain_keywords.items():
        if any(kw in filename for kw in keywords):
            return domain
    
    return "其他"


def extract_doc_type_from_filename(filename: str) -> str:
    """从文件名提取文档类型"""
    if "PRD" in filename or "prd" in filename or "产品需求" in filename:
        return "PRD"
    elif "MRD" in filename or "mrd" in filename or "市场需求" in filename:
        return "MRD"
    elif "BRD" in filename or "brd" in filename or "商业需求" in filename:
        return "BRD"
    elif "模板" in filename or "规范" in filename or "方法" in filename or "如何" in filename:
        return "方法/模板"
    else:
        return "其他"


def analyze_prd_dataset(prd_dir: Path) -> Dict:
    """分析PRD数据集"""
    print("=" * 60)
    print("分析中文PRD数据集")
    print("=" * 60)
    print(f"数据目录: {prd_dir}")
    print()
    
    # 统计信息
    all_files = list(prd_dir.glob("*"))
    files = [f for f in all_files if f.is_file()]
    
    print(f"📁 文件总数: {len(files)}")
    print()
    
    # 按文件类型统计
    file_types = Counter()
    for f in files:
        ext = f.suffix.lower()
        file_types[ext] += 1
    
    print("📄 文件类型分布:")
    for ext, count in file_types.most_common():
        print(f"  {ext or '无扩展名'}: {count} 个")
    print()
    
    # 按文档类型统计
    doc_types = Counter()
    domains = Counter()
    
    for f in files:
        filename = f.name
        doc_type = extract_doc_type_from_filename(filename)
        domain = extract_domain_from_filename(filename)
        
        doc_types[doc_type] += 1
        domains[domain] += 1
    
    print("📋 文档类型分布:")
    for doc_type, count in doc_types.most_common():
        print(f"  {doc_type}: {count} 个")
    print()
    
    print("🏷️  领域分布（Top 10）:")
    for domain, count in domains.most_common(10):
        print(f"  {domain}: {count} 个")
    print()
    
    # 识别大厂案例
    big_companies = ["腾讯", "阿里", "京东", "网易", "美团", "滴滴", "字节", "百度", "小米"]
    company_files = []
    
    for f in files:
        for company in big_companies:
            if company in f.name:
                company_files.append((company, f.name))
                break
    
    print("🏢 大厂案例（部分）:")
    company_counter = Counter([c[0] for c in company_files])
    for company, count in company_counter.most_common():
        print(f"  {company}: {count} 个案例")
    print()
    
    # 识别方法论文档
    methodology_files = [f.name for f in files if any(kw in f.name for kw in ["如何", "方法", "模板", "规范", "指南", "教程"])]
    
    print(f"📚 方法论文档: {len(methodology_files)} 个")
    if methodology_files:
        print("  示例:")
        for name in methodology_files[:5]:
            print(f"    - {name}")
    print()
    
    # 识别倒推案例（从产品反推PRD）
    reverse_prds = [f.name for f in files if "倒推" in f.name or "反推" in f.name]
    
    print(f"🔄 倒推案例: {len(reverse_prds)} 个")
    if reverse_prds:
        print("  示例:")
        for name in reverse_prds[:5]:
            print(f"    - {name}")
    print()
    
    # 统计结果
    analysis_result = {
        "total_files": len(files),
        "file_types": dict(file_types),
        "doc_types": dict(doc_types),
        "domains": dict(domains),
        "big_company_files": len(company_files),
        "company_distribution": dict(company_counter),
        "methodology_files": len(methodology_files),
        "reverse_prds": len(reverse_prds),
    }
    
    return analysis_result


def suggest_usage_strategy(analysis_result: Dict) -> None:
    """提出使用策略建议"""
    print("=" * 60)
    print("使用策略建议")
    print("=" * 60)
    print()
    
    print("1. 数据分类与组织")
    print("   📂 建议目录结构:")
    print("     data/chinese_prds/")
    print("       ├── prd_cases/          # 真实PRD案例")
    print("       │   ├── ecommerce/      # 电商领域")
    print("       │   ├── social/         # 社交领域")
    print("       │   ├── education/      # 教育领域")
    print("       │   └── ...")
    print("       ├── methodology/        # 方法论文档")
    print("       ├── templates/          # PRD模板")
    print("       └── reverse_analysis/   # 倒推案例（高质量）")
    print()
    
    print("2. 高质量样本筛选")
    print("   ✅ 优先使用:")
    print("     - 大厂案例（腾讯、阿里、京东等）")
    print("     - 倒推案例（从成熟产品反推，质量高）")
    print("     - 完整PRD（非MRD/BRD）")
    print("     - PDF格式（通常更完整）")
    print()
    
    print("3. 数据清洗与标准化")
    print("   🔧 需要处理:")
    print("     - 提取文本内容（PDF/DOC解析）")
    print("     - 识别标准章节（Overview、用户画像、功能需求等）")
    print("     - 转换为统一JSON格式（符合PRD Schema）")
    print("     - 去除水印、页眉页脚等噪声")
    print()
    
    print("4. 作为训练数据使用")
    print("   🎯 用途:")
    print("     - Few-shot示例（在prompt中提供高质量PRD示例）")
    print("     - 领域特定知识（提取各领域的术语、模式）")
    print("     - 评估标准（S_expert指标参考）")
    print("     - Prompt优化（学习真实PRD的写作风格）")
    print()
    
    print("5. 改进生成质量")
    print("   🚀 应用方向:")
    print("     - 领域知识增强（LeadAnalyst使用领域案例）")
    print("     - 风格对齐（TextGen学习真实PRD写作风格）")
    print("     - 结构优化（识别最常用的章节结构）")
    print("     - 术语标准化（提取各领域的标准术语）")
    print()


def main():
    if not PRD_DIR.exists():
        print(f"❌ 错误: 目录不存在: {PRD_DIR}")
        return
    
    # 分析数据集
    analysis_result = analyze_prd_dataset(PRD_DIR)
    
    # 提出使用策略
    suggest_usage_strategy(analysis_result)
    
    # 保存分析结果
    result_path = Path("data/chinese_prd_analysis.json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(analysis_result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 分析结果已保存: {result_path}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()


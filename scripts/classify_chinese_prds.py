"""
高质量中文PRD数据分类与组织脚本

功能：
1. 将300个PRD文件按类型和质量分类
2. 提取高质量样本（倒推案例、大厂案例）
3. 建立标准化的目录结构
4. 生成分类索引和映射文件

符合顶会实验标准：
- 严谨的数据组织
- 清晰的分类标准
- 完整的元数据记录
"""

import sys
import io
from pathlib import Path
import json
import shutil
from collections import Counter
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 源数据目录
SOURCE_DIR = Path(r"D:\2025pos\2026paper\amprd\【300份案例-产品经理PRD产品需求文档】")

# 目标目录
TARGET_BASE = Path("data/chinese_prds")

# 分类配置
DOMAIN_KEYWORDS = {
    "ecommerce": ["电商", "淘宝", "京东", "拼多多", "严选", "每日优鲜", "盒马", "饿了么", "外卖", "购物", "商城", "订单"],
    "social": ["社交", "微信", "QQ", "Soul", "小红书", "陌陌", "多闪", "点友", "聊天", "消息"],
    "entertainment": ["音乐", "视频", "直播", "短视频", "抖音", "B站", "喜马拉雅", "腾讯会议", "娱乐"],
    "education": ["教育", "学习", "老师", "作业", "驾考", "读书", "阅读", "课程", "培训", "学生"],
    "finance": ["金融", "支付", "贷款", "信贷", "理财", "P2P", "信用卡", "积分", "账户"],
    "travel": ["旅游", "旅行", "机票", "酒店", "民宿", "澳门", "攻略", "出行"],
    "tools": ["工具", "笔记", "记账", "清单", "日历", "翻译", "浏览器", "云"],
    "medical": ["医疗", "健康", "医生", "宠物", "宠", "医药"],
    "lifestyle": ["生活", "服务", "配送", "家具", "回收", "租房"],
    "enterprise": ["企业", "B端", "后台", "管理", "系统", "OA", "TMS", "后台管理"],
}

BIG_COMPANIES = {
    "腾讯": "tencent",
    "阿里": "alibaba",
    "京东": "jd",
    "网易": "netease",
    "滴滴": "didi",
    "美团": "meituan",
    "字节": "bytedance",
    "百度": "baidu",
    "小米": "xiaomi",
}


def extract_metadata_from_filename(filename: str) -> Dict:
    """
    从文件名提取元数据
    
    返回：
    - doc_type: PRD/MRD/BRD/方法/模板/其他
    - domain: 领域（ecommerce/social/...）
    - is_reverse: 是否倒推案例
    - is_big_company: 是否大厂案例
    - is_methodology: 是否方法论文档
    - quality_level: high/medium/low
    """
    filename_lower = filename.lower()
    
    # 文档类型
    doc_type = "其他"
    if "prd" in filename_lower or "产品需求" in filename or "需求文档" in filename:
        doc_type = "PRD"
    elif "mrd" in filename_lower or "市场需求" in filename:
        doc_type = "MRD"
    elif "brd" in filename_lower or "商业需求" in filename:
        doc_type = "BRD"
    elif any(kw in filename for kw in ["如何", "方法", "模板", "规范", "指南", "教程", "写作", "撰写"]):
        doc_type = "方法/模板"
    
    # 领域识别
    domain = "other"
    for domain_name, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in filename for kw in keywords):
            domain = domain_name
            break
    
    # 倒推案例
    is_reverse = "倒推" in filename or "反推" in filename
    
    # 大厂案例
    is_big_company = False
    company_tag = None
    for company, tag in BIG_COMPANIES.items():
        if company in filename:
            is_big_company = True
            company_tag = tag
            break
    
    # 方法论文档
    is_methodology = any(kw in filename for kw in ["如何", "方法", "模板", "规范", "指南", "教程", "写作", "撰写"])
    
    # 质量等级
    quality_level = "medium"
    if is_reverse:
        quality_level = "high"  # 倒推案例质量高
    elif is_big_company:
        quality_level = "high"  # 大厂案例质量高
    elif doc_type == "方法/模板":
        quality_level = "high"  # 方法论文档用于Prompt优化
    elif doc_type != "PRD":
        quality_level = "low"  # 非PRD文档
    
    return {
        "doc_type": doc_type,
        "domain": domain,
        "is_reverse": is_reverse,
        "is_big_company": is_big_company,
        "company_tag": company_tag,
        "is_methodology": is_methodology,
        "quality_level": quality_level,
        "source_filename": filename,
    }


def classify_prd_file(file_path: Path, metadata: Dict) -> Tuple[Path, Dict]:
    """
    根据元数据分类PRD文件，决定目标路径
    
    返回：
    - target_path: 目标路径
    - file_metadata: 文件元数据（增强版）
    """
    doc_type = metadata["doc_type"]
    domain = metadata["domain"]
    quality_level = metadata["quality_level"]
    is_reverse = metadata["is_reverse"]
    is_big_company = metadata["is_big_company"]
    is_methodology = metadata["is_methodology"]
    
    # 构建目标路径
    if doc_type == "PRD" and quality_level == "high":
        # 高质量PRD：按质量分类
        if is_reverse:
            target_dir = TARGET_BASE / "prd_cases" / "high_quality" / "reverse_analysis"
        elif is_big_company:
            target_dir = TARGET_BASE / "prd_cases" / "high_quality" / "big_company"
        else:
            target_dir = TARGET_BASE / "prd_cases" / "high_quality" / "other"
    elif doc_type == "PRD":
        # 普通PRD：按领域分类
        target_dir = TARGET_BASE / "prd_cases" / "by_domain" / domain
    elif is_methodology:
        # 方法论文档
        if "模板" in metadata["source_filename"]:
            target_dir = TARGET_BASE / "methodology" / "templates"
        elif any(kw in metadata["source_filename"] for kw in ["如何", "方法", "写作", "撰写"]):
            target_dir = TARGET_BASE / "methodology" / "how_to_write"
        else:
            target_dir = TARGET_BASE / "methodology" / "standards"
    else:
        # 其他文档（MRD/BRD等）
        target_dir = TARGET_BASE / "other_docs" / doc_type
    
    # 确保目录存在
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 目标文件路径（保持原文件名）
    target_path = target_dir / file_path.name
    
    # 增强元数据
    # 计算相对路径（确保路径正确）
    try:
        target_rel_path = str(target_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        # 如果无法计算相对路径，使用绝对路径
        target_rel_path = str(target_path).replace("\\", "/")
    
    try:
        source_rel_path = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        source_rel_path = str(file_path).replace("\\", "/")
    
    file_metadata = {
        **metadata,
        "target_path": target_rel_path,
        "source_path": source_rel_path,
        "file_size": file_path.stat().st_size,
        "file_extension": file_path.suffix.lower(),
        "classified_at": datetime.now().isoformat(),
    }
    
    return target_path, file_metadata


def main():
    print("=" * 70)
    print("高质量中文PRD数据分类与组织")
    print("=" * 70)
    print()
    
    if not SOURCE_DIR.exists():
        print(f"❌ 错误: 源目录不存在: {SOURCE_DIR}")
        return
    
    # 获取所有文件
    all_files = list(SOURCE_DIR.glob("*"))
    files = [f for f in all_files if f.is_file() and f.suffix.lower() in [".pdf", ".doc", ".docx", ".pptx", ".xlsx"]]
    
    print(f"📁 源目录: {SOURCE_DIR}")
    print(f"📄 文件总数: {len(files)}")
    print()
    
    # 分类所有文件
    classified_files = []
    file_metadata_list = []
    
    print("🔄 开始分类...")
    print()
    
    for i, file_path in enumerate(files, 1):
        filename = file_path.name
        
        # 提取元数据
        metadata = extract_metadata_from_filename(filename)
        
        # 分类文件
        target_path, file_metadata = classify_prd_file(file_path, metadata)
        
        # 复制文件（不覆盖已存在的）
        if not target_path.exists():
            try:
                shutil.copy2(file_path, target_path)
                classified_files.append(file_metadata)
                file_metadata_list.append(file_metadata)
                
                if i % 50 == 0:
                    print(f"  已处理: {i}/{len(files)}")
            except Exception as e:
                print(f"  ⚠️  复制失败 {filename}: {e}")
        else:
            # 文件已存在，只记录元数据
            classified_files.append(file_metadata)
            file_metadata_list.append(file_metadata)
    
    print()
    print(f"✅ 分类完成: {len(classified_files)} 个文件")
    print()
    
    # 统计信息
    print("=" * 70)
    print("分类统计")
    print("=" * 70)
    print()
    
    # 按文档类型统计
    doc_types = Counter([f["doc_type"] for f in classified_files])
    print("📋 文档类型分布:")
    for doc_type, count in doc_types.most_common():
        print(f"  {doc_type}: {count} 个")
    print()
    
    # 按质量等级统计
    quality_levels = Counter([f["quality_level"] for f in classified_files])
    print("⭐ 质量等级分布:")
    for level, count in quality_levels.most_common():
        print(f"  {level}: {count} 个")
    print()
    
    # 高质量样本统计
    high_quality = [f for f in classified_files if f["quality_level"] == "high" and f["doc_type"] == "PRD"]
    reverse_prds = [f for f in high_quality if f["is_reverse"]]
    big_company_prds = [f for f in high_quality if f["is_big_company"]]
    methodology_docs = [f for f in classified_files if f["is_methodology"]]
    
    print("🎯 高质量样本:")
    print(f"  高质量PRD总数: {len(high_quality)} 个")
    print(f"  - 倒推案例: {len(reverse_prds)} 个")
    print(f"  - 大厂案例: {len(big_company_prds)} 个")
    print(f"  - 方法论文档: {len(methodology_docs)} 个")
    print()
    
    # 按领域统计
    domains = Counter([f["domain"] for f in classified_files if f["doc_type"] == "PRD"])
    print("🏷️  领域分布（Top 10）:")
    for domain, count in domains.most_common(10):
        print(f"  {domain}: {count} 个")
    print()
    
    # 大厂案例统计
    big_companies = Counter([f["company_tag"] for f in classified_files if f["is_big_company"] and f["company_tag"]])
    if big_companies:
        print("🏢 大厂案例分布:")
        company_names = {tag: name for name, tag in BIG_COMPANIES.items()}
        for tag, count in big_companies.most_common():
            company_name = next((name for name, t in BIG_COMPANIES.items() if t == tag), tag)
            print(f"  {company_name}: {count} 个")
        print()
    
    # 保存分类索引
    print("=" * 70)
    print("保存分类索引...")
    print()
    
    # 保存完整索引
    index_path = TARGET_BASE / "classification_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    index_data = {
        "total_files": len(classified_files),
        "classified_at": datetime.now().isoformat(),
        "statistics": {
            "doc_types": dict(doc_types),
            "quality_levels": dict(quality_levels),
            "domains": dict(domains),
            "big_companies": dict(big_companies),
            "high_quality_prds": len(high_quality),
            "reverse_prds": len(reverse_prds),
            "big_company_prds": len(big_company_prds),
            "methodology_docs": len(methodology_docs),
        },
        "files": file_metadata_list,
    }
    
    index_path.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 完整索引已保存: {index_path}")
    
    # 保存高质量样本索引
    high_quality_index_path = TARGET_BASE / "high_quality_index.json"
    high_quality_data = {
        "total": len(high_quality),
        "classified_at": datetime.now().isoformat(),
        "reverse_analysis": [
            {k: v for k, v in f.items() if k not in ["source_path"]}
            for f in reverse_prds
        ],
        "big_company": [
            {k: v for k, v in f.items() if k not in ["source_path"]}
            for f in big_company_prds
        ],
    }
    
    high_quality_index_path.write_text(
        json.dumps(high_quality_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 高质量样本索引已保存: {high_quality_index_path}")
    
    # 保存方法论文档索引
    if methodology_docs:
        methodology_index_path = TARGET_BASE / "methodology_index.json"
        methodology_data = {
            "total": len(methodology_docs),
            "classified_at": datetime.now().isoformat(),
            "files": [
                {k: v for k, v in f.items() if k not in ["source_path"]}
                for f in methodology_docs
            ],
        }
        
        methodology_index_path.write_text(
            json.dumps(methodology_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"✅ 方法论文档索引已保存: {methodology_index_path}")
    
    print()
    print("=" * 70)
    print("分类完成！")
    print("=" * 70)
    print()
    print("📂 分类结果:")
    print(f"  基础目录: {TARGET_BASE}")
    print(f"  高质量PRD: {len(high_quality)} 个")
    print(f"  - 倒推案例: {len(reverse_prds)} 个")
    print(f"  - 大厂案例: {len(big_company_prds)} 个")
    print(f"  方法论文档: {len(methodology_docs)} 个")
    print()
    print("📝 索引文件:")
    print(f"  - {str(index_path).replace(str(PROJECT_ROOT) + '\\\\', '').replace('\\\\', '/')}")
    print(f"  - {str(high_quality_index_path).replace(str(PROJECT_ROOT) + '\\\\', '').replace('\\\\', '/')}")
    if methodology_docs:
        print(f"  - {str(methodology_index_path).replace(str(PROJECT_ROOT) + '\\\\', '').replace('\\\\', '/')}")
    print()
    print("下一步:")
    print("  1. 查看分类结果: data/chinese_prds/")
    print("  2. 提取高质量样本进行JSON转换")
    print("  3. 建立Brief与真实PRD的映射关系")


if __name__ == "__main__":
    main()


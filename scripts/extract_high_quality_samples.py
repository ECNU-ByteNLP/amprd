"""
提取高质量PRD样本用于JSON转换

功能：
1. 从分类后的数据中提取高质量样本（倒推案例、大厂案例）
2. 准备进行JSON转换的高质量样本列表
3. 建立Brief与真实PRD的映射关系

符合顶会实验标准：
- 优先使用高质量样本
- 建立准确的映射关系
- 记录完整的元数据
"""

import sys
import io
from pathlib import Path
import json
from typing import Dict, List, Optional

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 目录
CHINESE_PRDS_DIR = Path("data/chinese_prds")
BENCHMARK_DIR = Path("data/benchmark")


def load_high_quality_index() -> Dict:
    """加载高质量样本索引"""
    index_path = CHINESE_PRDS_DIR / "high_quality_index.json"
    if not index_path.exists():
        return {"reverse_analysis": [], "big_company": []}
    
    return json.loads(index_path.read_text(encoding="utf-8"))


def load_benchmark_briefs() -> List[Dict]:
    """加载基准Brief列表"""
    from src.data.benchmark_builder import BenchmarkBuilder
    
    builder = BenchmarkBuilder(BENCHMARK_DIR)
    return builder.list_prds()


def match_brief_to_expert_prd(brief: Dict, expert_prds: List[Dict]) -> Optional[Dict]:
    """
    将Brief与真实PRD匹配
    
    匹配策略：
    1. 基于domain匹配
    2. 基于title关键词匹配
    3. 优先选择倒推案例或大厂案例
    """
    brief_domain = brief.get("domain", "general")
    brief_title = brief.get("title", "").lower()
    
    # 领域映射
    domain_mapping = {
        "financial": "finance",
        "ecommerce": "ecommerce",
        "medical": "medical",
        "education": "education",
        "general": "other",
    }
    
    mapped_domain = domain_mapping.get(brief_domain, brief_domain)
    
    # 尝试匹配
    candidates = []
    
    for expert_prd in expert_prds:
        expert_domain = expert_prd.get("domain", "other")
        
        # 领域匹配
        if expert_domain == mapped_domain:
            score = 1.0
        elif mapped_domain in ["general", "other"]:
            # 通用领域可以匹配任何领域
            score = 0.5
        else:
            continue
        
        # 质量加分（倒推案例或大厂案例）
        if expert_prd.get("is_reverse") or expert_prd.get("is_big_company"):
            score += 0.3
        
        candidates.append({
            "expert_prd": expert_prd,
            "score": score,
        })
    
    if not candidates:
        return None
    
    # 选择得分最高的
    best_match = max(candidates, key=lambda x: x["score"])
    return best_match["expert_prd"]


def create_brief_to_expert_mapping() -> Dict:
    """
    建立Brief与真实PRD的映射关系
    
    优化策略：
    1. 确保每个Brief匹配到不同的PRD（避免重复）
    2. 优先匹配领域相关的PRD
    3. 如果领域匹配的PRD不够，可以跨领域匹配，但确保不重复
    """
    # 加载数据
    high_quality_index = load_high_quality_index()
    briefs = load_benchmark_briefs()
    
    # 合并高质量PRD列表
    expert_prds = []
    expert_prds.extend(high_quality_index.get("reverse_analysis", []))
    expert_prds.extend(high_quality_index.get("big_company", []))
    
    print(f"📋 加载数据:")
    print(f"  Brief数量: {len(briefs)}")
    print(f"  高质量PRD数量: {len(expert_prds)}")
    print()
    
    # 建立映射（确保不重复）
    mapping = {}
    matched_count = 0
    used_expert_prds = set()  # 记录已使用的PRD文件名，避免重复
    
    print("🔄 建立映射关系（优化：确保每个Brief匹配到不同的PRD）...")
    print()
    
    # 按领域分组Brief，优先处理有明确领域的Brief
    briefs_by_domain = {}
    for brief in briefs:
        domain = brief.get("domain", "general")
        if domain not in briefs_by_domain:
            briefs_by_domain[domain] = []
        briefs_by_domain[domain].append(brief)
    
    # 领域映射
    domain_mapping = {
        "financial": "finance",
        "ecommerce": "ecommerce",
        "medical": "medical",
        "education": "education",
        "general": "other",
    }
    
    # 按领域优先级处理（先处理有明确领域的，最后处理general）
    domain_priority = ["financial", "ecommerce", "education", "medical", "general"]
    
    for domain in domain_priority:
        if domain not in briefs_by_domain:
            continue
        
        domain_briefs = briefs_by_domain[domain]
        mapped_domain = domain_mapping.get(domain, domain)
        
        print(f"  处理 {domain} 领域 ({len(domain_briefs)} 个Brief):")
        
        for brief in domain_briefs:
            brief_id = brief.get("prd_id", "")
            brief_title = brief.get("title", "")
            brief_domain = brief.get("domain", "general")
            
            # 匹配真实PRD（排除已使用的）
            candidates = []
            
            for expert_prd in expert_prds:
                expert_filename = expert_prd.get("source_filename", "")
                
                # 跳过已使用的PRD
                if expert_filename in used_expert_prds:
                    continue
                
                expert_domain = expert_prd.get("domain", "other")
                
                # 计算匹配分数
                score = 0.0
                
                # 领域匹配（精确匹配得分最高）
                if expert_domain == mapped_domain:
                    score = 2.0  # 领域精确匹配
                elif mapped_domain == "other" or expert_domain == "other":
                    # 通用领域可以匹配，但得分较低
                    score = 1.0
                else:
                    # 领域不匹配，但可以作为备选（得分更低）
                    score = 0.3
                
                # 质量加分（倒推案例或大厂案例）
                if expert_prd.get("is_reverse"):
                    score += 0.5  # 倒推案例质量高
                if expert_prd.get("is_big_company"):
                    score += 0.3  # 大厂案例权威性强
                
                candidates.append({
                    "expert_prd": expert_prd,
                    "score": score,
                })
            
            if candidates:
                # 选择得分最高的
                best_match = max(candidates, key=lambda x: x["score"])
                matched_expert = best_match["expert_prd"]
                match_score = best_match["score"]
                
                # 标记为已使用
                used_expert_prds.add(matched_expert["source_filename"])
                
                matched_count += 1
                expert_prd_path = Path(matched_expert["target_path"])
                
                # 构建JSON路径（假设已转换）
                json_path = expert_prd_path.parent / f"{expert_prd_path.stem}.json"
                
                # 确定匹配置信度
                if match_score >= 2.0:
                    confidence = "high"  # 领域精确匹配 + 高质量
                elif match_score >= 1.5:
                    confidence = "medium-high"  # 领域匹配或高质量
                else:
                    confidence = "medium"  # 跨领域匹配
                
                mapping[brief_id] = {
                    "brief_id": brief_id,
                    "brief_title": brief_title,
                    "brief_domain": brief_domain,
                    "expert_prd_path": str(json_path).replace("\\", "/"),
                    "expert_prd_source": matched_expert["source_filename"],
                    "expert_prd_domain": matched_expert.get("domain", "other"),
                    "is_reverse": matched_expert.get("is_reverse", False),
                    "is_big_company": matched_expert.get("is_big_company", False),
                    "company_tag": matched_expert.get("company_tag"),
                    "quality_level": matched_expert.get("quality_level", "medium"),
                    "source_pdf_path": str(expert_prd_path).replace("\\", "/"),
                    "match_confidence": confidence,
                    "match_score": round(match_score, 2),
                }
                
                match_type = "倒推案例" if matched_expert.get("is_reverse") else "大厂案例" if matched_expert.get("is_big_company") else "高质量"
                print(f"    ✅ {brief_id[:20]}... -> {matched_expert['source_filename'][:35]}... [{match_type}, score={match_score:.2f}]")
            else:
                print(f"    ⚠️  {brief_id[:20]}... -> 未找到匹配的PRD（所有候选PRD已被使用）")
        
        print()
    
    print(f"✅ 匹配完成: {matched_count}/{len(briefs)} 个Brief找到匹配的PRD")
    print(f"   已使用 {len(used_expert_prds)} 个不同的PRD")
    print()
    
    return mapping


def extract_samples_for_conversion() -> List[Dict]:
    """提取需要转换为JSON的高质量样本"""
    high_quality_index = load_high_quality_index()
    
    # 优先提取倒推案例和大厂案例
    samples = []
    
    # 倒推案例（优先）
    for prd_info in high_quality_index.get("reverse_analysis", []):
        samples.append({
            **prd_info,
            "priority": "high",
            "reason": "倒推案例，质量高",
        })
    
    # 大厂案例（优先）
    for prd_info in high_quality_index.get("big_company", []):
        # 避免重复（如果倒推案例中已有）
        if not any(s.get("source_filename") == prd_info.get("source_filename") for s in samples):
            samples.append({
                **prd_info,
                "priority": "high",
                "reason": "大厂案例，权威性强",
            })
    
    return samples


def main():
    print("=" * 70)
    print("提取高质量PRD样本")
    print("=" * 70)
    print()
    
    # 提取高质量样本
    print("📦 提取高质量样本...")
    samples = extract_samples_for_conversion()
    
    print(f"✅ 找到 {len(samples)} 个高质量样本")
    print()
    
    # 统计
    reverse_count = sum(1 for s in samples if s.get("is_reverse"))
    big_company_count = sum(1 for s in samples if s.get("is_big_company"))
    
    print("📊 样本统计:")
    print(f"  倒推案例: {reverse_count} 个")
    print(f"  大厂案例: {big_company_count} 个")
    print(f"  总计: {len(samples)} 个")
    print()
    
    # 保存样本列表
    samples_path = CHINESE_PRDS_DIR / "processed" / "samples_for_conversion.json"
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    
    samples_data = {
        "total": len(samples),
        "extracted_at": __import__("datetime").datetime.now().isoformat(),
        "samples": samples[:50],  # 优先处理前50个
    }
    
    samples_path.write_text(
        json.dumps(samples_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"✅ 样本列表已保存: {samples_path}")
    print(f"  （优先处理前50个样本）")
    print()
    
    # 建立映射关系
    print("=" * 70)
    print("建立Brief与真实PRD的映射关系")
    print("=" * 70)
    print()
    
    mapping = create_brief_to_expert_mapping()
    
    # 保存映射文件
    mapping_path = CHINESE_PRDS_DIR / "processed" / "brief_to_expert_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    
    mapping_data = {
        "total_mappings": len(mapping),
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "mappings": mapping,
    }
    
    mapping_path.write_text(
        json.dumps(mapping_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"✅ 映射文件已保存: {mapping_path}")
    print()
    
    # 总结
    print("=" * 70)
    print("提取完成！")
    print("=" * 70)
    print()
    print("📂 输出文件:")
    print(f"  - data/chinese_prds/processed/samples_for_conversion.json")
    print(f"  - data/chinese_prds/processed/brief_to_expert_mapping.json")
    print()
    print("下一步:")
    print("  1. 将高质量样本转换为JSON格式（至少处理20-30个样本）")
    print("  2. 验证映射关系的准确性")
    print("  3. 集成Few-shot学习和S_expert指标")


if __name__ == "__main__":
    main()


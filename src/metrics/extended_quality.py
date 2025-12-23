"""
扩展质量指标：对标顶级PRD样例（Google, Amazon, Linear等）

新增指标：
- S_sem: 语义质量（问题陈述清晰度、需求可执行性）
- S_biz: 业务对齐度（目标与指标一致性）
- S_tech: 技术可行性（技术要求的合理性）
- S_risk: 风险识别（风险与缓解策略的完整性）
- S_expert: 专家对齐度（与人类专家PRD的相似度）
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None


def compute_semantic_quality(prd: Dict) -> Dict[str, float]:
    """
    计算语义质量指标 S_sem
    
    维度：
    - problem_clarity: 问题陈述清晰度（基于关键词检测）
    - requirement_executability: 需求可执行性（是否包含验收标准）
    - terminology_consistency: 术语一致性（领域术语使用准确性）
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return {"overall": 0.0, "problem_clarity": 0.0, "requirement_executability": 0.0, "terminology_consistency": 0.0}
    
    # 1. 问题陈述清晰度：检查overview章节是否包含问题关键词
    overview_section = next((s for s in sections if s.get("section_id") == "overview"), None)
    problem_keywords = ["问题", "problem", "痛点", "pain point", "挑战", "challenge", "目标", "goal", "目的", "purpose"]
    problem_clarity = 0.0
    if overview_section:
        content = overview_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        # 忽略mock内容
        if "[mock" not in text:
            matched_keywords = sum(1 for kw in problem_keywords if kw in text)
            problem_clarity = min(1.0, matched_keywords / 3.0)  # 至少3个关键词
    
    # 2. 需求可执行性：检查是否包含验收标准、用户故事等
    user_stories_section = next((s for s in sections if s.get("section_id") == "user_stories"), None)
    functional_req_section = next((s for s in sections if s.get("section_id") == "functional_requirements"), None)
    
    executability_indicators = 0
    if user_stories_section:
        content = user_stories_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text and any(kw in text for kw in ["验收", "acceptance", "标准", "criteria", "given", "when", "then"]):
            executability_indicators += 1
    
    if functional_req_section:
        content = functional_req_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text and any(kw in text for kw in ["必须", "must", "应该", "should", "需要", "require"]):
            executability_indicators += 1
    
    requirement_executability = min(1.0, executability_indicators / 2.0)
    
    # 3. 术语一致性：检查领域术语是否一致使用
    domain = prd.get("metadata", {}).get("domain", "general")
    domain_terms = {
        "financial": ["金融", "finance", "支付", "payment", "账户", "account", "交易", "transaction"],
        "ecommerce": ["电商", "ecommerce", "商品", "product", "订单", "order", "购物", "shopping"],
        "medical": ["医疗", "medical", "健康", "health", "患者", "patient", "诊断", "diagnosis"],
    }
    
    terminology_consistency = 0.5  # 默认值
    if domain in domain_terms:
        terms = domain_terms[domain]
        all_text = ""
        for section in sections:
            content = section.get("content", {})
            all_text += (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        
        matched_terms = sum(1 for term in terms if term in all_text)
        terminology_consistency = min(1.0, matched_terms / max(len(terms), 1))
    
    overall = (problem_clarity + requirement_executability + terminology_consistency) / 3.0
    
    return {
        "overall": round(overall, 4),
        "problem_clarity": round(problem_clarity, 4),
        "requirement_executability": round(requirement_executability, 4),
        "terminology_consistency": round(terminology_consistency, 4),
    }


def compute_business_alignment(prd: Dict) -> float:
    """
    计算业务对齐度 S_biz
    
    检查：
    - goal与KPI的一致性（goal中提到的目标是否在KPI中体现）
    - 用户需求覆盖度（persona与功能的对应关系）
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    
    # 1. Goal与KPI一致性
    overview_section = next((s for s in sections if s.get("section_id") == "overview"), None)
    kpi_section = next((s for s in sections if s.get("section_id") == "kpi_and_milestones"), None)
    
    goal_kpi_alignment = 0.5  # 默认值
    if overview_section and kpi_section:
        goal_text = (overview_section.get("content", {}).get("zh-CN") or "").lower()
        # 忽略mock内容
        if "[mock" not in goal_text:
            kpi_tables = kpi_section.get("tables", [])
            if kpi_tables:
                # 检查goal中的关键词是否在KPI表格中出现
                goal_keywords = re.findall(r'[\u4e00-\u9fa5]+|\w+', goal_text)
                kpi_text = ""
                for table in kpi_tables:
                    for row in table.get("rows", []):
                        for cell in row:
                            if isinstance(cell, dict):
                                kpi_text += (cell.get("zh-CN") or "").lower() + " "
                            else:
                                kpi_text += str(cell).lower() + " "
                
                matched_keywords = sum(1 for kw in goal_keywords[:5] if kw in kpi_text and len(kw) > 1)
                goal_kpi_alignment = min(1.0, matched_keywords / 3.0)
    
    # 2. 用户需求覆盖度（简化版：检查是否有user_persona和user_stories）
    persona_section = next((s for s in sections if s.get("section_id") == "user_persona"), None)
    stories_section = next((s for s in sections if s.get("section_id") == "user_stories"), None)
    
    coverage = 0.0
    if persona_section and stories_section:
        persona_content = persona_section.get("content", {})
        stories_content = stories_section.get("content", {})
        if (persona_content.get("zh-CN") or persona_content.get("en-US")) and \
           (stories_content.get("zh-CN") or stories_content.get("en-US")):
            coverage = 1.0
    
    overall = (goal_kpi_alignment + coverage) / 2.0
    return round(overall, 4)


def compute_technical_feasibility(prd: Dict) -> float:
    """
    计算技术可行性 S_tech
    
    检查：
    - 技术要求的合理性（是否包含架构、性能指标）
    - 约束完整性（安全、合规、性能约束是否完整）
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    
    # 检查non_functional_requirements章节
    nfr_section = next((s for s in sections if s.get("section_id") == "non_functional_requirements"), None)
    
    if not nfr_section:
        return 0.0
    
    content = nfr_section.get("content", {})
    text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
    
    # 忽略mock内容
    if "[mock" in text:
        return 0.0
    
    # 检查是否包含技术关键词
    tech_keywords = [
        "性能", "performance", "架构", "architecture", "安全", "security",
        "可扩展", "scalable", "可用性", "availability", "延迟", "latency",
        "吞吐", "throughput", "合规", "compliance",
    ]
    
    matched_keywords = sum(1 for kw in tech_keywords if kw in text)
    feasibility = min(1.0, matched_keywords / 5.0)  # 至少5个关键词
    
    return round(feasibility, 4)


def compute_risk_identification(prd: Dict) -> float:
    """
    计算风险识别完整性 S_risk
    
    检查：
    - 是否识别关键风险
    - 缓解策略是否具体可行
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    
    risk_section = next((s for s in sections if s.get("section_id") == "risks_and_mitigations"), None)
    
    if not risk_section:
        return 0.0
    
    content = risk_section.get("content", {})
    text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
    
    # 忽略mock内容
    if "[mock" in text:
        return 0.0
    
    # 检查是否包含风险和缓解策略关键词
    risk_keywords = ["风险", "risk", "挑战", "challenge", "问题", "issue"]
    mitigation_keywords = ["缓解", "mitigation", "解决", "solution", "策略", "strategy", "措施", "measure"]
    
    has_risk = any(kw in text for kw in risk_keywords)
    has_mitigation = any(kw in text for kw in mitigation_keywords)
    
    if has_risk and has_mitigation:
        return 1.0
    elif has_risk or has_mitigation:
        return 0.5
    else:
        return 0.0


def compute_expert_alignment(prd: Dict, expert_prd_path: Optional[Path] = None) -> Dict[str, float]:
    """
    计算专家对齐度 S_expert
    
    对比维度：
    - 结构相似度（章节覆盖度）
    - 内容相似度（基于语义相似度，需要sentence-transformers）
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    
    # 1. 结构相似度（与标准PRD结构对比）
    standard_sections = {
        "overview", "user_persona", "user_stories", "functional_requirements",
        "non_functional_requirements", "user_flows", "key_interfaces",
        "kpi_and_milestones", "risks_and_mitigations", "data_and_tracking", "release_plan"
    }
    
    generated_sections = {s.get("section_id") for s in sections if s.get("section_id")}
    structure_overlap = len(generated_sections & standard_sections) / len(standard_sections)
    
    # 2. 内容相似度（如果提供了专家PRD）
    content_similarity = 0.0
    if expert_prd_path and expert_prd_path.exists() and HAS_SENTENCE_TRANSFORMERS:
        try:
            # 检查文件格式（JSON或PDF）
            if expert_prd_path.suffix.lower() == ".json":
                expert_prd = json.loads(expert_prd_path.read_text(encoding="utf-8"))
            elif expert_prd_path.suffix.lower() == ".pdf":
                # PDF文件需要转换，暂时跳过内容相似度计算
                # 只计算结构相似度
                return {
                    "overall": round(structure_overlap, 4),
                    "structure_similarity": round(structure_overlap, 4),
                    "content_similarity": 0.0,
                    "note": "expert_prd_is_pdf_need_conversion",
                }
            else:
                # 未知格式，跳过
                return {
                    "overall": round(structure_overlap, 4),
                    "structure_similarity": round(structure_overlap, 4),
                    "content_similarity": 0.0,
                    "note": "expert_prd_format_not_supported",
                }
            
            # 使用中文sentence-transformers模型（支持中英文）
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # 提取所有文本内容（优先使用中文，如果没有则使用英文）
            our_texts = []
            expert_texts = []
            
            for section in sections:
                content = section.get("content", {})
                # 优先使用中文，如果没有则使用英文
                text = content.get("zh-CN") or content.get("en-US") or ""
                if text.strip() and "[mock" not in text.lower():
                    our_texts.append(text[:500])  # 限制长度
            
            expert_sections = expert_prd.get("outputs", {}).get("sections", expert_prd.get("sections", []))
            for section in expert_sections:
                content = section.get("content", {})
                # 优先使用中文，如果没有则使用英文
                text = content.get("zh-CN") or content.get("en-US") or ""
                if text.strip():
                    expert_texts.append(text[:500])
            
            if our_texts and expert_texts:
                # 计算平均相似度（限制数量以避免内存问题）
                max_texts = min(5, len(our_texts), len(expert_texts))
                our_embeddings = model.encode(our_texts[:max_texts])
                expert_embeddings = model.encode(expert_texts[:max_texts])
                
                # 计算余弦相似度
                from numpy import dot
                from numpy.linalg import norm
                
                similarities = []
                for our_emb in our_embeddings:
                    max_sim = max(
                        dot(our_emb, exp_emb) / (norm(our_emb) * norm(exp_emb))
                        for exp_emb in expert_embeddings
                    )
                    similarities.append(max_sim)
                
                content_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        except Exception as e:
            # 记录错误但不中断计算
            import logging
            logging.getLogger(__name__).warning(f"计算内容相似度失败: {e}")
            content_similarity = 0.0
    
    overall = (structure_overlap + content_similarity) / 2.0 if content_similarity > 0 else structure_overlap
    
    return {
        "overall": round(overall, 4),
        "structure_similarity": round(structure_overlap, 4),
        "content_similarity": round(content_similarity, 4),
    }


def compute_problem_solution_separation(prd: Dict) -> Dict[str, float]:
    """
    计算问题-解决方案空间分离度 S_ps
    
    参考：Intercom, Airbnb, Asana, Miro, Basecamp的最佳实践
    参考：https://pmprompt.com/blog/prd-templates
    
    维度：
    - problem_clarity: 问题陈述清晰度（是否明确分离问题空间）
    - solution_clarity: 解决方案清晰度（是否明确分离解决方案空间）
    - separation_quality: 分离质量（问题空间和解决方案空间是否清晰分离）
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return {"overall": 0.0, "problem_clarity": 0.0, "solution_clarity": 0.0, "separation_quality": 0.0}
    
    # 1. 问题陈述清晰度
    overview_section = next((s for s in sections if s.get("section_id") == "overview"), None)
    problem_keywords = ["问题", "problem", "痛点", "pain point", "挑战", "challenge", "问题陈述", "problem statement"]
    problem_clarity = 0.0
    if overview_section:
        content = overview_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text:
            # 检查是否包含问题关键词
            matched_keywords = sum(1 for kw in problem_keywords if kw in text)
            # 检查是否有问题陈述的结构化描述
            has_problem_structure = any(phrase in text for phrase in [
                "问题陈述", "problem statement", "要解决的问题", "problem we are trying to solve"
            ])
            problem_clarity = min(1.0, (matched_keywords / 3.0) * 0.7 + (1.0 if has_problem_structure else 0.0) * 0.3)
    
    # 2. 解决方案清晰度
    solution_keywords = ["解决方案", "solution", "方法", "approach", "设计", "design", "实现", "implementation"]
    solution_clarity = 0.0
    if overview_section:
        content = overview_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text:
            matched_keywords = sum(1 for kw in solution_keywords if kw in text)
            has_solution_structure = any(phrase in text for phrase in [
                "解决方案", "solution approach", "解决方向", "how we might tackle"
            ])
            solution_clarity = min(1.0, (matched_keywords / 3.0) * 0.7 + (1.0 if has_solution_structure else 0.0) * 0.3)
    
    # 3. 分离质量：检查问题空间和解决方案空间是否清晰分离
    separation_quality = 0.0
    if problem_clarity > 0 and solution_clarity > 0:
        # 如果两者都存在且清晰，分离质量高
        separation_quality = min(1.0, (problem_clarity + solution_clarity) / 2.0)
    
    overall = (problem_clarity + solution_clarity + separation_quality) / 3.0
    
    return {
        "overall": round(overall, 4),
        "problem_clarity": round(problem_clarity, 4),
        "solution_clarity": round(solution_clarity, 4),
        "separation_quality": round(separation_quality, 4),
    }


def compute_user_journey_completeness(prd: Dict) -> Dict[str, float]:
    """
    计算用户旅程完整性 S_uj
    
    参考：Miro Product Alignment Document和Intercom Job Story
    参考：https://pmprompt.com/blog/prd-templates
    
    维度：
    - persona_completeness: 用户画像完整性
    - journey_map_quality: 用户旅程地图质量
    - touchpoint_coverage: 接触点覆盖度
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return {"overall": 0.0, "persona_completeness": 0.0, "journey_map_quality": 0.0, "touchpoint_coverage": 0.0}
    
    # 1. 用户画像完整性
    persona_section = next((s for s in sections if s.get("section_id") == "user_persona"), None)
    persona_completeness = 0.0
    if persona_section:
        content = persona_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text:
            # 检查是否包含用户画像的关键要素
            persona_elements = [
                "需求", "needs", "痛点", "pain point", "目标", "goal",
                "场景", "scenario", "背景", "background", "特征", "characteristic"
            ]
            matched_elements = sum(1 for elem in persona_elements if elem in text)
            persona_completeness = min(1.0, matched_elements / 4.0)
    
    # 2. 用户旅程地图质量
    flows_section = next((s for s in sections if s.get("section_id") == "user_flows"), None)
    journey_map_quality = 0.0
    if flows_section:
        content = flows_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text:
            # 检查是否包含用户旅程的关键要素
            journey_elements = [
                "流程", "flow", "步骤", "step", "接触点", "touchpoint",
                "旅程", "journey", "体验", "experience", "决策", "decision"
            ]
            matched_elements = sum(1 for elem in journey_elements if elem in text)
            journey_map_quality = min(1.0, matched_elements / 4.0)
    
    # 3. 接触点覆盖度
    touchpoint_coverage = 0.0
    if flows_section:
        content = flows_section.get("content", {})
        text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
        if "[mock" not in text:
            # 检查是否提到多个接触点或阶段
            touchpoint_indicators = ["开始", "start", "中间", "middle", "结束", "end", "阶段", "phase"]
            matched_indicators = sum(1 for ind in touchpoint_indicators if ind in text)
            touchpoint_coverage = min(1.0, matched_indicators / 3.0)
    
    overall = (persona_completeness + journey_map_quality + touchpoint_coverage) / 3.0
    
    return {
        "overall": round(overall, 4),
        "persona_completeness": round(persona_completeness, 4),
        "journey_map_quality": round(journey_map_quality, 4),
        "touchpoint_coverage": round(touchpoint_coverage, 4),
    }


def compute_hypothesis_validation(prd: Dict) -> float:
    """
    计算假设验证度 S_hyp
    
    参考：Lean UX Canvas的假设验证方法
    参考：https://pmprompt.com/blog/prd-templates
    
    检查：
    - 是否包含假设陈述
    - 是否定义了验证方法
    - 是否明确了成功标准
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    
    # 检查KPI章节是否包含假设验证
    kpi_section = next((s for s in sections if s.get("section_id") == "kpi_and_milestones"), None)
    if not kpi_section:
        return 0.0
    
    content = kpi_section.get("content", {})
    text = (content.get("zh-CN") or "").lower() + " " + (content.get("en-US") or "").lower()
    
    if "[mock" in text:
        return 0.0
    
    # 检查假设验证的关键要素
    hypothesis_keywords = ["假设", "hypothesis", "验证", "validate", "实验", "experiment", "测试", "test"]
    validation_keywords = ["验证方法", "validation method", "测量", "measure", "指标", "metric", "标准", "criteria"]
    
    has_hypothesis = any(kw in text for kw in hypothesis_keywords)
    has_validation = any(kw in text for kw in validation_keywords)
    
    if has_hypothesis and has_validation:
        return 1.0
    elif has_hypothesis or has_validation:
        return 0.5
    else:
        return 0.0


def compute_all_extended_metrics(
    prd: Dict,
    expert_prd_path: Optional[Path] = None,
) -> Dict[str, Dict | float]:
    """
    计算所有扩展指标（包含新增的顶刊标准指标）
    
    Returns:
        {
            "S_sem": {...},
            "S_biz": 0.85,
            "S_tech": 0.72,
            "S_risk": 1.0,
            "S_expert": {...},
            "S_ps": {...},  # 新增：问题-解决方案分离度
            "S_uj": {...},  # 新增：用户旅程完整性
            "S_hyp": 0.8,   # 新增：假设验证度
        }
    """
    return {
        "S_sem": compute_semantic_quality(prd),
        "S_biz": compute_business_alignment(prd),
        "S_tech": compute_technical_feasibility(prd),
        "S_risk": compute_risk_identification(prd),
        "S_expert": compute_expert_alignment(prd, expert_prd_path),
        "S_ps": compute_problem_solution_separation(prd),  # 新增
        "S_uj": compute_user_journey_completeness(prd),  # 新增
        "S_hyp": compute_hypothesis_validation(prd),  # 新增
    }


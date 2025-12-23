"""
Few-shot学习示例加载器

功能：
1. 根据Brief的domain加载相似领域的真实PRD示例
2. 提取Few-shot示例的关键章节内容
3. 格式化Few-shot示例用于Prompt注入

符合顶会实验标准：
- 基于真实PRD数据
- 领域相关性匹配
- 高质量样本优先
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 映射文件路径
MAPPING_PATH = PROJECT_ROOT / "data" / "chinese_prds" / "processed" / "brief_to_expert_mapping.json"

# 领域映射
DOMAIN_MAPPING = {
    "financial": "finance",
    "ecommerce": "ecommerce",
    "medical": "medical",
    "education": "education",
    "general": "other",
}


def load_few_shot_examples(
    brief: Dict,
    top_k: int = 2,
    mapping_path: Optional[Path] = None,
    brief_id: Optional[str] = None,
) -> List[Dict]:
    """
    根据Brief加载Few-shot示例（真实PRD参考）
    
    Args:
        brief: Brief字典，包含domain、goal等信息
        top_k: 返回的示例数量（默认2个）
        mapping_path: 映射文件路径（可选）
        brief_id: Brief ID（可选，如果提供则直接使用，否则从brief中提取）
    
    Returns:
        List[Dict]: Few-shot示例列表，每个示例包含：
            - source: PRD来源（文件名）
            - domain: 领域
            - quality_level: 质量等级
            - sections: 关键章节内容（如果已转换为JSON）
            - pdf_path: PDF文件路径（如果JSON不存在）
    """
    if mapping_path is None:
        mapping_path = MAPPING_PATH
    
    if not mapping_path.exists():
        _logger.warning(f"映射文件不存在: {mapping_path}，无法加载Few-shot示例")
        return []
    
    # 加载映射文件
    try:
        mapping_data = json.loads(mapping_path.read_text(encoding="utf-8"))
        mappings = mapping_data.get("mappings", {})
    except Exception as e:
        _logger.error(f"加载映射文件失败: {e}")
        return []
    
    # 获取Brief ID（优先级：参数 > brief中的字段 > 从title和domain推断）
    if not brief_id:
        brief_id = (
            brief.get("prd_id") or 
            brief.get("brief_id") or 
            brief.get("id")
        )
    
    # 如果仍然没有ID，尝试从title和domain推断（匹配benchmark_index.json的格式）
    if not brief_id:
        title = brief.get("title", "")
        domain = brief.get("domain", "general")
        if title:
            # 尝试推断prd_id（格式：domain_title_lowercase_with_underscores）
            # 例如：general_google_search_algorithm_update
            inferred_id = f"{domain}_{title.lower().replace(' ', '_').replace('-', '_').replace(':', '').replace(',', '')}"
            # 检查映射文件中是否存在
            if inferred_id in mappings:
                brief_id = inferred_id
                _logger.debug(f"从title和domain推断brief_id: {brief_id}")
    
    if not brief_id:
        # 如果仍然没有ID，尝试通过domain匹配相似领域的示例
        domain = brief.get("domain", "general")
        _logger.debug(f"Brief中缺少ID，尝试通过domain={domain}匹配Few-shot示例")
        # 使用load_similar_domain_examples作为备选
        return load_similar_domain_examples(domain, top_k=top_k)
    
    # 查找匹配的专家PRD
    expert_info = mappings.get(brief_id)
    if not expert_info:
        _logger.debug(f"未找到Brief {brief_id} 的映射关系，尝试通过domain匹配")
        # 使用相似领域示例作为备选
        domain = brief.get("domain", "general")
        return load_similar_domain_examples(domain, top_k=top_k, exclude_brief_id=brief_id)
    
    # 构建Few-shot示例
    expert_prd_path = Path(expert_info.get("expert_prd_path", ""))
    source_pdf_path = Path(expert_info.get("source_pdf_path", ""))
    
    # 检查JSON文件是否存在
    if expert_prd_path.exists() and expert_prd_path.suffix == ".json":
        # 已转换为JSON，直接加载
        try:
            expert_prd = json.loads(expert_prd_path.read_text(encoding="utf-8"))
            return [{
                "source": expert_info.get("expert_prd_source", ""),
                "domain": expert_info.get("expert_prd_domain", "other"),
                "quality_level": expert_info.get("quality_level", "medium"),
                "is_reverse": expert_info.get("is_reverse", False),
                "is_big_company": expert_info.get("is_big_company", False),
                "match_confidence": expert_info.get("match_confidence", "medium"),
                "sections": expert_prd.get("sections", []),
                "pdf_path": str(source_pdf_path) if source_pdf_path.exists() else None,
            }]
        except Exception as e:
            _logger.warning(f"加载专家PRD JSON失败: {e}，将使用PDF路径")
    
    # JSON不存在，返回PDF路径（用于后续转换）
    return [{
        "source": expert_info.get("expert_prd_source", ""),
        "domain": expert_info.get("expert_prd_domain", "other"),
        "quality_level": expert_info.get("quality_level", "medium"),
        "is_reverse": expert_info.get("is_reverse", False),
        "is_big_company": expert_info.get("is_big_company", False),
        "match_confidence": expert_info.get("match_confidence", "medium"),
        "sections": [],  # 未转换，章节为空
        "pdf_path": str(source_pdf_path) if source_pdf_path.exists() else None,
    }]


def format_few_shot_examples_for_prompt(
    examples: List[Dict],
    language: str = "zh-CN",
    max_sections: int = 3,
) -> str:
    """
    格式化Few-shot示例用于Prompt注入
    
    Args:
        examples: Few-shot示例列表
        language: 语言（zh-CN或en-US）
        max_sections: 每个示例最多包含的章节数
    
    Returns:
        str: 格式化后的Few-shot示例文本
    """
    if not examples:
        return ""
    
    formatted_parts = []
    
    for i, example in enumerate(examples, 1):
        source = example.get("source", "未知来源")
        domain = example.get("domain", "other")
        quality = example.get("quality_level", "medium")
        is_reverse = example.get("is_reverse", False)
        is_big_company = example.get("is_big_company", False)
        
        # 构建示例头部
        quality_tags = []
        if is_reverse:
            quality_tags.append("倒推案例")
        if is_big_company:
            quality_tags.append("大厂案例")
        quality_tag = "、".join(quality_tags) if quality_tags else "高质量"
        
        formatted_parts.append(f"## 真实PRD示例 {i}：{source}")
        formatted_parts.append(f"领域：{domain} | 质量：{quality_tag}")
        formatted_parts.append("")
        
        # 提取关键章节内容
        sections = example.get("sections", [])
        if sections:
            # 优先选择关键章节
            priority_sections = ["overview", "user_persona", "functional_requirements"]
            selected_sections = []
            
            for section_id in priority_sections:
                for section in sections:
                    if section.get("section_id") == section_id:
                        content = section.get("content", {})
                        text = content.get(language) or content.get("zh-CN") or ""
                        if text and len(text) > 50:  # 确保有足够内容
                            selected_sections.append({
                                "section_id": section_id,
                                "content": text[:500],  # 限制长度
                            })
                            if len(selected_sections) >= max_sections:
                                break
                if len(selected_sections) >= max_sections:
                    break
            
            # 格式化章节内容
            for section in selected_sections:
                section_id = section["section_id"]
                content = section["content"]
                formatted_parts.append(f"### {section_id}:")
                formatted_parts.append(content)
                formatted_parts.append("")
        else:
            # 如果章节为空（未转换），提供占位信息
            formatted_parts.append("（示例内容待加载）")
            formatted_parts.append("")
    
    return "\n".join(formatted_parts)


def load_similar_domain_examples(
    domain: str,
    top_k: int = 2,
    exclude_brief_id: Optional[str] = None,
) -> List[Dict]:
    """
    加载相似领域的Few-shot示例（不限于当前Brief的映射）
    
    用于：
    - 当当前Brief没有映射时，使用相似领域的示例
    - 补充额外的Few-shot示例
    
    Args:
        domain: 领域（financial/ecommerce/education等）
        top_k: 返回的示例数量
        exclude_brief_id: 排除的Brief ID（避免重复）
    
    Returns:
        List[Dict]: Few-shot示例列表
    """
    if not MAPPING_PATH.exists():
        return []
    
    try:
        mapping_data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
        mappings = mapping_data.get("mappings", {})
    except Exception:
        return []
    
    # 领域映射
    mapped_domain = DOMAIN_MAPPING.get(domain, domain)
    
    # 查找相似领域的示例
    candidates = []
    for brief_id, expert_info in mappings.items():
        if exclude_brief_id and brief_id == exclude_brief_id:
            continue
        
        expert_domain = expert_info.get("expert_prd_domain", "other")
        if expert_domain == mapped_domain:
            # 计算优先级分数
            score = 1.0
            if expert_info.get("is_reverse"):
                score += 0.5
            if expert_info.get("is_big_company"):
                score += 0.3
            
            candidates.append({
                "expert_info": expert_info,
                "score": score,
            })
    
    # 按分数排序，选择top_k
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[:top_k]
    
    # 构建Few-shot示例
    examples = []
    for candidate in selected:
        expert_info = candidate["expert_info"]
        expert_prd_path = Path(expert_info.get("expert_prd_path", ""))
        
        if expert_prd_path.exists() and expert_prd_path.suffix == ".json":
            try:
                expert_prd = json.loads(expert_prd_path.read_text(encoding="utf-8"))
                examples.append({
                    "source": expert_info.get("expert_prd_source", ""),
                    "domain": expert_info.get("expert_prd_domain", "other"),
                    "quality_level": expert_info.get("quality_level", "medium"),
                    "is_reverse": expert_info.get("is_reverse", False),
                    "is_big_company": expert_info.get("is_big_company", False),
                    "sections": expert_prd.get("sections", []),
                })
            except Exception:
                pass
    
    return examples


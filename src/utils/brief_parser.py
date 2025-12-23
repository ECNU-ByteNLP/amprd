from __future__ import annotations

import json
import logging
import os
from typing import Dict, Optional, Tuple

from src.models.model_client import ModelClient
from src.models.qwen_client import QwenTextClient

_logger = logging.getLogger(__name__)


def parse_brief_text(text: str, model: Optional[ModelClient] = None) -> Tuple[Dict, Dict]:
    """
    Parse free-form brief text into structured Brief JSON.
    
    Strategy:
      1. Try LLM-powered extraction if model is available
      2. Fallback to heuristic parsing if LLM fails or unavailable
    
    Returns:
      (brief_json, report) where report contains confidence and missing_fields
    """
    normalized = (text or "").strip()
    if not normalized:
        return _heuristic_parse(""), {"confidence": 0.0, "notes": ["Empty input"], "missing_fields": []}
    
    # Try LLM-powered extraction
    if model is None:
        # Try to create Qwen client from environment
        api_key = os.getenv("QWEN_API_KEY")
        if api_key:
            try:
                model = QwenTextClient(api_key=api_key, model_name=os.getenv("QWEN_TEXT_MODEL_CN", "qwen2.5-32b-instruct"))
            except Exception as e:
                _logger.warning("Failed to create Qwen client for brief parsing: %s", e)
    
    if model:
        try:
            return _llm_parse(normalized, model)
        except Exception as e:
            _logger.warning("LLM parsing failed, falling back to heuristic: %s", e)
    
    # Fallback to heuristic
    return _heuristic_parse(normalized)


def _llm_parse(text: str, model: ModelClient) -> Tuple[Dict, Dict]:
    """LLM-powered structured extraction.
    
    参考顶级PRD样例（Google, Amazon, Linear等）的结构化要求：
    - 清晰的问题陈述（Problem Statement）
    - 详细的目标用户画像（Target Users）
    - 具体可衡量的成功指标（Success Metrics）
    - 明确的技术约束（Technical Constraints）
    """
    system_prompt = """你是一个专业的产品需求分析师，擅长从自然语言描述中提取结构化信息。
参考顶级公司（Google、Amazon、Linear等）的PRD标准，提取以下结构化信息并输出JSON格式。

输出字段说明（对标顶级PRD样例）：
- title: 产品名称（如果没有明确提及，根据描述推断，参考Google/Amazon的命名风格）
- domain: 业务领域（financial/ecommerce/medical/general/other）
- goal: 核心目标（一句话总结，应清晰描述要解决的问题和预期成果）
- target_users: 目标用户列表，每个用户包含：
  * persona: 用户画像（如"年轻白领"、"初级投资者"）
  * needs: 具体需求（如"快速了解理财方案"、"风险可控的组合建议"）
- key_constraints: 关键约束列表，每个约束包含：
  * type: 约束类型（performance/compliance/security/technical等）
  * description: 具体描述（如"响应时间不超过2秒"、"符合金融监管要求"）
  * priority: 优先级（P0/P1/P2/P3，P0为最高）
- business_metrics: 业务指标列表，每个指标包含：
  * name: 指标名称（如"新客开户率"、"用户满意度"）
  * target: 目标值（如"15%"、"12% improvement"）
  * timeframe: 时间范围（如"Q3"、"6 months"、"3个月"）

提取原则（参考顶级PRD样例）：
1. 问题陈述要清晰：明确描述要解决的问题和背景
2. 目标用户要具体：包含用户画像和具体需求，而非泛泛而谈
3. 成功指标要可衡量：包含具体数字和时间范围
4. 技术约束要完整：涵盖性能、安全、合规等关键约束

只输出JSON，不要其他文字。如果某个字段无法从文本中提取，使用空值（[]或""）。"""
    
    user_prompt = f"""请从以下产品需求描述中提取结构化信息：

{text}

输出JSON格式："""
    
    response = model.generate_text(
        user_prompt,
        system=system_prompt,
        temperature=0.3,  # Lower temperature for more deterministic extraction
    )
    
    # Try to extract JSON from response
    try:
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        brief = json.loads(response)
    except json.JSONDecodeError:
        _logger.warning("Failed to parse LLM response as JSON, using heuristic fallback")
        return _heuristic_parse(text)
    
    # Normalize structure to match expected schema
    brief = _normalize_brief(brief)
    
    # Calculate confidence based on filled fields
    required_fields = ["title", "domain", "goal", "target_users"]
    filled_count = sum(1 for field in required_fields if brief.get(field))
    confidence = min(1.0, 0.3 + 0.7 * (filled_count / len(required_fields)))
    
    missing_fields = [k for k in required_fields if not brief.get(k)]
    
    report = {
        "confidence": round(confidence, 3),
        "notes": ["LLM-powered extraction"],
        "missing_fields": missing_fields,
        "extraction_method": "llm",
    }
    
    return brief, report


def _heuristic_parse(text: str) -> Tuple[Dict, Dict]:
    """Heuristic fallback parser."""
    normalized = (text or "").strip()
    brief: Dict = {
        "title": "",
        "domain": "other",
        "goal": normalized[:200] if normalized else "",
        "target_users": [],
        "key_constraints": [],
        "business_metrics": [],
        "references": [],
    }
    
    # Simple keyword-based domain detection
    text_lower = normalized.lower()
    if any(kw in text_lower for kw in ["金融", "理财", "支付", "银行", "financial", "finance", "payment"]):
        brief["domain"] = "financial"
    elif any(kw in text_lower for kw in ["电商", "购物", "商品", "订单", "ecommerce", "e-commerce", "shopping"]):
        brief["domain"] = "ecommerce"
    elif any(kw in text_lower for kw in ["医疗", "健康", "医院", "medical", "health", "hospital"]):
        brief["domain"] = "medical"
    
    report: Dict = {
        "confidence": 0.5 if normalized else 0.0,
        "notes": ["Heuristic parse; consider using LLM-powered extraction"],
        "missing_fields": [k for k in ["title", "target_users", "business_metrics"] if not brief.get(k)],
        "extraction_method": "heuristic",
    }
    return brief, report


def _normalize_brief(brief: Dict) -> Dict:
    """Normalize brief structure to match expected schema."""
    # Ensure all required fields exist
    normalized = {
        "title": brief.get("title", ""),
        "domain": brief.get("domain", "other"),
        "goal": brief.get("goal", ""),
        "target_users": brief.get("target_users", []),
        "key_constraints": brief.get("key_constraints", []),
        "business_metrics": brief.get("business_metrics", []),
        "references": brief.get("references", []),
    }
    
    # Normalize target_users structure
    if normalized["target_users"]:
        normalized["target_users"] = [
            {
                "persona": u.get("persona", u.get("persona_name", "")),
                "needs": u.get("needs", u.get("need", "")),
            }
            for u in normalized["target_users"]
            if isinstance(u, dict)
        ]
    
    # Normalize key_constraints structure
    if normalized["key_constraints"]:
        normalized["key_constraints"] = [
            {
                "type": c.get("type", "general"),
                "description": c.get("description", c.get("desc", "")),
                "priority": c.get("priority", "P1"),
            }
            for c in normalized["key_constraints"]
            if isinstance(c, dict)
        ]
    
    # Normalize business_metrics structure
    if normalized["business_metrics"]:
        normalized["business_metrics"] = [
            {
                "name": m.get("name", ""),
                "target": m.get("target", ""),
                "timeframe": m.get("timeframe", ""),
            }
            for m in normalized["business_metrics"]
            if isinstance(m, dict)
        ]
    
    return normalized



from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard
from src.models.model_client import ModelClient
from src.utils.few_shot_loader import load_few_shot_examples, format_few_shot_examples_for_prompt


class TextGenerationAgent(Agent):
    """Generates localized textual sections for the PRD."""

    def __init__(self, role: str, language: str, model: ModelClient) -> None:
        super().__init__(role=role)
        self._language = language
        self._model = model

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent not in {"draft_section", "revise_section"}:
            return None

        plan: Dict = message.payload["plan"]
        brief: Dict = message.payload.get("brief", {})
        
        # 从payload中获取prd_id（如果存在），用于Few-shot匹配
        # prd_id可能来自plan或brief
        brief_prd_id = plan.get("prd_id") or brief.get("prd_id") or brief.get("brief_id")
        
        sections = plan["sections"]
        generated_sections = {}
        for section in sections:
            section_id = section["section_id"]
            prompt = self._build_prompt(section_id, plan, brief, brief_prd_id=brief_prd_id)
            generated_sections[section_id] = self._model.generate_text(prompt)
            blackboard.update_state(
                ["sections", section_id, "content", self._language],
                generated_sections[section_id],
            )

        if self._language == "zh-CN":
            return self.emit(
                receiver="TextGen_EN",
                intent="draft_section",
                payload={
                    "plan": plan,
                    "brief": brief,
                    "dependencies": list(generated_sections.keys()),
                },
                dependencies=[message.message_id],
            )
        else:
            return self.emit(
                receiver="AlignmentAgent",
                intent="align",
                payload={"plan": plan},
                dependencies=[message.message_id],
            )

    def _build_prompt(self, section_id: str, plan: Dict, brief: Dict, brief_prd_id: Optional[str] = None) -> str:
        """
        构建高质量的PRD生成prompt，参考顶级PRD模板最佳实践
        
        创新点：集成Few-shot学习，使用真实PRD示例提升生成质量
        参考：https://pmprompt.com/blog/prd-templates
        """
        goal = brief.get("goal", "一个创新功能")
        domain = plan.get("domain", "通用领域")
        constraints = "; ".join(
            c.get("description", "") for c in plan.get("constraints", [])
        )
        
        # 提取问题空间信息
        problem_space = plan.get("problem_space", {})
        problem_statement = problem_space.get("problem_statement", "")
        pain_points = problem_space.get("pain_points", [])
        
        # 提取解决方案空间信息
        solution_space = plan.get("solution_space", {})
        solution_approach = solution_space.get("solution_approach", "")
        
        # 构建用户画像信息（包含needs和pain_points）
        personas_info = []
        for persona in plan.get("personas", []):
            if isinstance(persona, dict):
                persona_str = f"{persona.get('persona', '用户')}"
                if persona.get("needs"):
                    persona_str += f"（需求：{persona['needs']}）"
                if persona.get("pain_points"):
                    persona_str += f"（痛点：{persona['pain_points']}）"
                personas_info.append(persona_str)
            else:
                personas_info.append(str(persona))
        
        persona_text = ", ".join(personas_info) if personas_info else "核心用户"
        
        # 加载Few-shot示例（真实PRD参考）
        # 传递prd_id以确保正确匹配
        few_shot_examples = load_few_shot_examples(brief, top_k=1, brief_id=brief_prd_id)
        few_shot_text = ""
        if few_shot_examples:
            few_shot_text = format_few_shot_examples_for_prompt(
                few_shot_examples,
                language=self._language,
                max_sections=2,  # 每个示例最多2个章节，避免prompt过长
            )
            if few_shot_text:
                few_shot_text = (
                    f"## 真实PRD示例参考（Few-shot Learning）\n"
                    f"以下是来自真实产品的PRD示例，请参考其风格、结构和内容深度：\n\n"
                    f"{few_shot_text}\n"
                    f"---\n\n"
                )
        
        # 根据章节类型构建不同的prompt
        section_prompts = {
            "overview": self._build_overview_prompt(goal, domain, problem_statement, solution_approach, self._language, few_shot_text),
            "user_persona": self._build_persona_prompt(plan.get("personas", []), pain_points, self._language, few_shot_text),
            "user_stories": self._build_user_stories_prompt(plan.get("personas", []), problem_statement, self._language, few_shot_text),
            "functional_requirements": self._build_requirements_prompt(goal, solution_approach, constraints, self._language, few_shot_text),
            "non_functional_requirements": self._build_nfr_prompt(constraints, domain, self._language, few_shot_text),
            "user_flows": self._build_user_flows_prompt(plan.get("personas", []), solution_approach, self._language, few_shot_text),
            "kpi_and_milestones": self._build_kpi_prompt(brief.get("business_metrics", []), goal, self._language, few_shot_text),
            "risks_and_mitigations": self._build_risks_prompt(domain, solution_approach, self._language, few_shot_text),
        }
        
        # 使用特定prompt或默认prompt
        if section_id in section_prompts:
            return section_prompts[section_id]
        else:
            # 默认prompt（增强版，包含Few-shot）
            return (
                f"{few_shot_text}"
                f"你是一位资深产品经理，正在撰写高质量的PRD文档。\n\n"
                f"## 上下文信息\n"
                f"- 领域: {domain}\n"
                f"- 产品目标: {goal}\n"
                f"- 目标用户: {persona_text}\n"
                f"- 关键约束: {constraints or '无'}\n"
                f"- 问题陈述: {problem_statement or '待明确'}\n"
                f"- 解决方案方向: {solution_approach or '待设计'}\n\n"
                f"## 任务\n"
                f"请为章节 '{section_id}' 生成专业、详细、可执行的PRD内容。\n\n"
                f"## 要求\n"
                f"1. 内容要具体、可执行，避免空泛描述\n"
                f"2. 使用结构化格式（列表、段落、关键信息突出）\n"
                f"3. 确保内容与问题陈述和解决方案方向一致\n"
                f"4. 参考上述真实PRD示例的风格和深度\n"
                f"5. 使用 {self._language} 语言输出\n"
            )
    
    def _build_overview_prompt(self, goal: str, domain: str, problem_statement: str, solution_approach: str, language: str, few_shot_text: str = "") -> str:
        """构建Overview章节的prompt（强调问题空间和解决方案空间分离）"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考顶级公司（Google, Amazon, Intercom, Airbnb）的PRD最佳实践。\n\n"
            f"## 任务：撰写PRD的Overview章节\n\n"
            f"## 关键原则：问题空间和解决方案空间分离\n"
            f"顶级产品团队（Intercom, Airbnb, Asana, Miro, Basecamp）都遵循一个关键实践："
            f"在探索解决方案之前，先清晰地定义问题。\n\n"
            f"## 上下文\n"
            f"- 领域: {domain}\n"
            f"- 产品目标: {goal}\n"
            f"- 问题陈述: {problem_statement or '待明确'}\n"
            f"- 解决方案方向: {solution_approach or '待设计'}\n\n"
            f"## 输出要求\n"
            f"请用{lang}撰写Overview章节，必须包含：\n"
            f"1. **问题陈述**（Problem Statement）：\n"
            f"   - 清晰描述要解决的问题（1-2句话）\n"
            f"   - 为什么这个问题对用户和业务很重要？\n"
            f"   - 有什么证据或洞察支持这个问题？\n"
            f"   - 量化问题的影响（如果可能）\n\n"
            f"2. **解决方案概述**（Solution Approach）：\n"
            f"   - 高层次的解决方案方向（不要过于详细）\n"
            f"   - 如何解决上述问题\n"
            f"   - 关键设计决策\n\n"
            f"3. **目标和成功指标**：\n"
            f"   - 可衡量的目标\n"
            f"   - 成功标准\n\n"
            f"## 参考格式\n"
            f"参考Kevin Yien的PRD模板和Google Data-Driven PRD的风格，确保内容专业、清晰、可执行。\n"
        )
    
    def _build_persona_prompt(self, personas: list, pain_points: list, language: str, few_shot_text: str = "") -> str:
        """构建User Persona章节的prompt（参考Intercom Job Story和Miro风格）"""
        lang = "中文" if language == "zh-CN" else "English"
        personas_text = "\n".join([
            f"- {p.get('persona', '用户')}: 需求={p.get('needs', '')}, 痛点={p.get('pain_points', '')}"
            if isinstance(p, dict) else f"- {p}"
            for p in personas
        ])
        
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Intercom和Miro的用户画像最佳实践。\n\n"
            f"## 任务：撰写User Persona章节\n\n"
            f"## 上下文\n"
            f"目标用户画像：\n{personas_text}\n\n"
            f"## 输出要求\n"
            f"请用{lang}为每个用户画像撰写详细描述，必须包含：\n"
            f"1. **用户基本信息**：\n"
            f"   - 角色名称\n"
            f"   - 背景和特征\n"
            f"   - 使用场景\n\n"
            f"2. **用户需求（User Needs）**：\n"
            f"   - 核心需求是什么？\n"
            f"   - 为什么需要这个产品/功能？\n"
            f"   - 使用频率和强度\n\n"
            f"3. **用户痛点（Pain Points）**：\n"
            f"   - 当前面临的主要问题\n"
            f"   - 现有解决方案的不足\n"
            f"   - 情感和体验层面的痛点\n\n"
            f"4. **用户目标（User Goals）**：\n"
            f"   - 用户想要达成什么？\n"
            f"   - 成功标准是什么？\n\n"
            f"## 参考格式\n"
            f"参考Intercom的Job Story模板和Miro的Product Alignment Document，确保用户画像具体、有洞察力。\n"
        )
    
    def _build_user_stories_prompt(self, personas: list, problem_statement: str, language: str, few_shot_text: str = "") -> str:
        """构建User Stories章节的prompt（参考Intercom Job Story格式）"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Intercom的Job Story格式。\n\n"
            f"## 任务：撰写User Stories章节\n\n"
            f"## 上下文\n"
            f"- 问题陈述: {problem_statement}\n"
            f"- 目标用户: {len(personas)}个用户画像\n\n"
            f"## 输出要求\n"
            f"请用{lang}撰写用户故事，使用以下格式：\n\n"
            f"**Job Story格式**：\n"
            f"当 [情况/上下文] 时，\n"
            f"我想要 [目标/动机]，\n"
            f"以便 [预期结果/价值]。\n\n"
            f"或者**传统User Story格式**：\n"
            f"作为 [用户角色]，\n"
            f"我想要 [功能/行为]，\n"
            f"以便 [价值/收益]。\n\n"
            f"## 要求\n"
            f"1. 每个用户故事要具体、可执行\n"
            f"2. 包含验收标准（Acceptance Criteria）\n"
            f"3. 与问题陈述和用户痛点对齐\n"
            f"4. 优先顺序排列（最重要的在前）\n\n"
            f"## 参考\n"
            f"参考Intercom的Job Story模板，确保故事聚焦于用户的工作和动机，而非功能特性。\n"
        )
    
    def _build_requirements_prompt(self, goal: str, solution_approach: str, constraints: str, language: str, few_shot_text: str = "") -> str:
        """构建Functional Requirements章节的prompt"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Google和Microsoft的功能需求文档风格。\n\n"
            f"## 任务：撰写Functional Requirements章节\n\n"
            f"## 上下文\n"
            f"- 产品目标: {goal}\n"
            f"- 解决方案方向: {solution_approach}\n"
            f"- 关键约束: {constraints or '无'}\n\n"
            f"## 输出要求\n"
            f"请用{lang}撰写详细的功能需求，必须包含：\n"
            f"1. **核心功能**：\n"
            f"   - 每个功能的具体描述\n"
            f"   - 功能优先级（P0/P1/P2）\n"
            f"   - 功能依赖关系\n\n"
            f"2. **功能规格**：\n"
            f"   - 输入/输出\n"
            f"   - 行为描述\n"
            f"   - 边界条件\n\n"
            f"3. **验收标准**：\n"
            f"   - 每个功能如何验证完成\n"
            f"   - 成功标准\n\n"
            f"## 要求\n"
            f"1. 使用结构化格式（编号列表、子项）\n"
            f"2. 确保需求可执行、可测试\n"
            f"3. 避免模糊描述，使用具体术语\n"
            f"4. 与解决方案方向一致\n\n"
            f"## 参考\n"
            f"参考Microsoft Feature Doc和Google Data-Driven PRD，确保需求清晰、完整、可执行。\n"
        )
    
    def _build_nfr_prompt(self, constraints: str, domain: str, language: str, few_shot_text: str = "") -> str:
        """构建Non-Functional Requirements章节的prompt"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考顶级公司的非功能需求文档。\n\n"
            f"## 任务：撰写Non-Functional Requirements章节\n\n"
            f"## 上下文\n"
            f"- 领域: {domain}\n"
            f"- 关键约束: {constraints or '无'}\n\n"
            f"## 输出要求\n"
            f"请用{lang}撰写非功能需求，必须包含：\n"
            f"1. **性能要求**：\n"
            f"   - 响应时间、吞吐量、延迟\n"
            f"   - 可扩展性要求\n\n"
            f"2. **安全要求**：\n"
            f"   - 数据安全、隐私保护\n"
            f"   - 合规要求（如GDPR、HIPAA等）\n\n"
            f"3. **可用性要求**：\n"
            f"   - 系统可用性（如99.9% uptime）\n"
            f"   - 容错和恢复能力\n\n"
            f"4. **技术约束**：\n"
            f"   - 技术栈限制\n"
            f"   - 兼容性要求\n\n"
            f"## 要求\n"
            f"1. 所有指标要具体、可测量\n"
            f"2. 与领域相关（如金融领域强调合规，医疗领域强调隐私）\n"
            f"3. 优先级明确\n\n"
            f"## 参考\n"
            f"参考Figma和Microsoft的技术文档，确保非功能需求完整、具体。\n"
        )
    
    def _build_user_flows_prompt(self, personas: list, solution_approach: str, language: str, few_shot_text: str = "") -> str:
        """构建User Flows章节的prompt"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Miro的用户旅程最佳实践。\n\n"
            f"## 任务：撰写User Flows章节\n\n"
            f"## 上下文\n"
            f"- 解决方案方向: {solution_approach}\n"
            f"- 目标用户: {len(personas)}个用户画像\n\n"
            f"## 输出要求\n"
            f"请用{lang}描述用户流程，必须包含：\n"
            f"1. **主要用户流程**：\n"
            f"   - 流程步骤（从开始到结束）\n"
            f"   - 关键决策点\n"
            f"   - 异常流程处理\n\n"
            f"2. **用户旅程地图**：\n"
            f"   - 用户接触点（Touchpoints）\n"
            f"   - 用户情感变化\n"
            f"   - 痛点和机会点\n\n"
            f"3. **流程优化点**：\n"
            f"   - 如何简化流程\n"
            f"   - 如何提升用户体验\n\n"
            f"## 参考\n"
            f"参考Miro的Product Alignment Document，确保流程清晰、完整、用户友好。\n"
        )
    
    def _build_kpi_prompt(self, business_metrics: list, goal: str, language: str, few_shot_text: str = "") -> str:
        """构建KPI and Milestones章节的prompt"""
        lang = "中文" if language == "zh-CN" else "English"
        metrics_text = "\n".join([
            f"- {m.get('name', '指标')}: 目标={m.get('target', '')}, 时间={m.get('timeframe', '')}"
            for m in business_metrics
        ])
        
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Google和Amazon的KPI定义最佳实践。\n\n"
            f"## 任务：撰写KPI and Milestones章节\n\n"
            f"## 上下文\n"
            f"- 产品目标: {goal}\n"
            f"- 业务指标: \n{metrics_text or '待定义'}\n\n"
            f"## 输出要求\n"
            f"请用{lang}撰写KPI和里程碑，必须包含：\n"
            f"1. **成功指标（KPIs）**：\n"
            f"   - 指标名称和定义\n"
            f"   - 当前基线值（如果已知）\n"
            f"   - 目标值\n"
            f"   - 测量方法\n"
            f"   - 时间范围\n\n"
            f"2. **里程碑计划**：\n"
            f"   - 关键里程碑和时间点\n"
            f"   - 交付物\n"
            f"   - 依赖关系\n\n"
            f"3. **假设验证**（参考Lean UX Canvas）：\n"
            f"   - 关键假设\n"
            f"   - 验证方法\n"
            f"   - 成功标准\n\n"
            f"## 要求\n"
            f"1. 所有指标要可测量、可追踪\n"
            f"2. 指标与产品目标对齐\n"
            f"3. 使用表格格式呈现（如果适用）\n\n"
            f"## 参考\n"
            f"参考Google Data-Driven PRD和Amazon-Style PRD，确保指标具体、可执行。\n"
        )
    
    def _build_risks_prompt(self, domain: str, solution_approach: str, language: str, few_shot_text: str = "") -> str:
        """构建Risks and Mitigations章节的prompt"""
        lang = "中文" if language == "zh-CN" else "English"
        return (
            f"{few_shot_text}"
            f"你是一位资深产品经理，参考Linear和顶级公司的风险识别最佳实践。\n\n"
            f"## 任务：撰写Risks and Mitigations章节\n\n"
            f"## 上下文\n"
            f"- 领域: {domain}\n"
            f"- 解决方案方向: {solution_approach}\n\n"
            f"## 输出要求\n"
            f"请用{lang}识别风险和缓解策略，必须包含：\n"
            f"1. **关键风险**：\n"
            f"   - 技术风险\n"
            f"   - 业务风险\n"
            f"   - 用户采用风险\n"
            f"   - 合规风险（如适用）\n\n"
            f"2. **风险影响评估**：\n"
            f"   - 风险严重程度（高/中/低）\n"
            f"   - 风险发生概率\n"
            f"   - 对项目的影响\n\n"
            f"3. **缓解策略**：\n"
            f"   - 具体缓解措施\n"
            f"   - 责任人\n"
            f"   - 时间计划\n\n"
            f"## 要求\n"
            f"1. 风险要具体、可识别\n"
            f"2. 缓解策略要可执行\n"
            f"3. 与领域相关（如金融领域关注合规风险，医疗领域关注隐私风险）\n\n"
            f"## 参考\n"
            f"参考Linear Priority Micro-Adjust PRD和ShapeUp的Rabbit Holes概念，确保风险识别全面、缓解策略具体。\n"
        )


def build_text_agents(model_cn: ModelClient, model_en: ModelClient) -> Dict[str, Agent]:
    cn_agent = TextGenerationAgent("TextGen_CN", "zh-CN", model_cn)
    en_agent = TextGenerationAgent("TextGen_EN", "en-US", model_en)
    return {
        cn_agent.role: cn_agent,
        en_agent.role: en_agent,
    }



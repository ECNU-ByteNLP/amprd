"""
PRD质量基准数据集构建工具

基于顶级公司PRD样例（参考pmprompt.com）构建标准数据集，用于可复现实验。
参考：https://pmprompt.com/blog/prd-templates
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class BenchmarkPRD:
    """基准PRD样例"""
    prd_id: str
    title: str
    domain: str
    source: str  # 来源公司/样例名称
    template_style: Optional[str] = None  # PRD模板风格（如shapeup, miro, intercom等）
    brief_path: Optional[Path] = None  # 对应的Brief JSON
    prd_path: Optional[Path] = None  # PRD JSON路径
    annotations: Optional[Dict] = None  # 人工标注信息


class BenchmarkBuilder:
    """构建和管理PRD基准数据集"""
    
    def __init__(self, benchmark_dir: Path):
        self.benchmark_dir = benchmark_dir
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = benchmark_dir / "benchmark_index.json"
    
    def add_prd_sample(
        self,
        title: str,
        domain: str,
        source: str,
        brief: Dict,
        template_style: Optional[str] = None,
        prd_json: Optional[Dict] = None,
        annotations: Optional[Dict] = None,
    ) -> BenchmarkPRD:
        """添加PRD样例到基准数据集"""
        prd_id = f"{domain}_{title.lower().replace(' ', '_').replace('-', '_')}"
        
        # 保存Brief
        brief_path = self.benchmark_dir / f"{prd_id}_brief.json"
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 保存PRD（如果提供）
        prd_path = None
        if prd_json:
            prd_path = self.benchmark_dir / f"{prd_id}_prd.json"
            prd_path.write_text(json.dumps(prd_json, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 保存标注（如果提供）
        annotations_path = None
        if annotations:
            annotations_path = self.benchmark_dir / f"{prd_id}_annotations.json"
            annotations_path.write_text(json.dumps(annotations, ensure_ascii=False, indent=2), encoding="utf-8")
        
        benchmark_prd = BenchmarkPRD(
            prd_id=prd_id,
            title=title,
            domain=domain,
            source=source,
            template_style=template_style,
            brief_path=brief_path,
            prd_path=prd_path,
            annotations=annotations,
        )
        
        # 更新索引
        self._update_index(benchmark_prd)
        
        return benchmark_prd
    
    def _update_index(self, benchmark_prd: BenchmarkPRD) -> None:
        """更新基准数据集索引"""
        if self.index_path.exists():
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
        else:
            index = {"prds": []}
        
        entry = {
            "prd_id": benchmark_prd.prd_id,
            "title": benchmark_prd.title,
            "domain": benchmark_prd.domain,
            "source": benchmark_prd.source,
            "template_style": benchmark_prd.template_style,
            "brief_path": str(benchmark_prd.brief_path.relative_to(self.benchmark_dir)) if benchmark_prd.brief_path else None,
            "prd_path": str(benchmark_prd.prd_path.relative_to(self.benchmark_dir)) if benchmark_prd.prd_path else None,
            "annotations_path": f"{benchmark_prd.prd_id}_annotations.json" if benchmark_prd.annotations else None,
        }
        
        # 检查是否已存在
        existing = next((p for p in index["prds"] if p["prd_id"] == benchmark_prd.prd_id), None)
        if existing:
            index["prds"].remove(existing)
        
        index["prds"].append(entry)
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def list_prds(self, domain: Optional[str] = None, template_style: Optional[str] = None) -> List[Dict]:
        """列出所有PRD样例，可按领域或模板风格过滤"""
        if not self.index_path.exists():
            return []
        
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        prds = index.get("prds", [])
        
        if domain:
            prds = [p for p in prds if p.get("domain") == domain]
        
        if template_style:
            prds = [p for p in prds if p.get("template_style") == template_style]
        
        return prds
    
    def load_brief(self, prd_id: str) -> Dict:
        """加载Brief JSON"""
        prds = self.list_prds()
        entry = next((p for p in prds if p["prd_id"] == prd_id), None)
        if not entry or not entry.get("brief_path"):
            raise ValueError(f"Brief not found for PRD: {prd_id}")
        
        brief_path = self.benchmark_dir / entry["brief_path"]
        return json.loads(brief_path.read_text(encoding="utf-8"))
    
    def load_prd(self, prd_id: str) -> Dict:
        """加载PRD JSON"""
        prds = self.list_prds()
        entry = next((p for p in prds if p["prd_id"] == prd_id), None)
        if not entry or not entry.get("prd_path"):
            raise ValueError(f"PRD not found: {prd_id}")
        
        prd_path = self.benchmark_dir / entry["prd_path"]
        return json.loads(prd_path.read_text(encoding="utf-8"))


def create_sample_benchmark_prds(benchmark_dir: Path) -> List[BenchmarkPRD]:
    """
    创建扩展的基准PRD数据集（15+个样例，覆盖14种PRD模板风格）
    
    参考：https://pmprompt.com/blog/prd-templates
    """
    builder = BenchmarkBuilder(benchmark_dir)
    samples = []
    
    # ========== 通用领域 (General) ==========
    
    # 1. Google Search Algorithm Update (Google Data-Driven PRD风格)
    google_brief = {
        "title": "Google Search Algorithm Update",
        "domain": "general",
        "goal": "Implement a new machine learning algorithm update to improve content quality assessment and user satisfaction metrics",
        "target_users": [
            {"persona": "Search users", "needs": "High-quality, relevant search results", "pain_points": "Irrelevant or low-quality results"}
        ],
        "key_constraints": [
            {"type": "performance", "description": "Maintain search latency under 100ms for 95% of queries", "priority": "P0"},
            {"type": "compliance", "description": "Compliance with existing privacy and security standards", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "User satisfaction score", "target": "12% improvement", "timeframe": "6 months"},
            {"name": "Click-through rate", "target": "8% increase", "timeframe": "6 months"},
            {"name": "Bounce rate reduction", "target": "5% reduction", "timeframe": "6 months"},
        ],
        "problem_statement": "Current search algorithm struggles to distinguish high-quality content from low-quality content, leading to user dissatisfaction",
        "solution_approach": "Leverage advanced ML models to assess content quality signals including E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)",
    }
    samples.append(builder.add_prd_sample(
        title="Google Search Algorithm Update",
        domain="general",
        source="Google",
        template_style="google_data_driven",
        brief=google_brief,
    ))
    
    # 2. Dropbox Collaboration Feature (Dropbox One-Page Template风格)
    dropbox_brief = {
        "title": "Dropbox Real-time Collaboration",
        "domain": "general",
        "goal": "Enable real-time collaborative editing for documents stored in Dropbox",
        "target_users": [
            {"persona": "Team collaborators", "needs": "Seamless real-time collaboration", "pain_points": "Version conflicts and sync delays"}
        ],
        "key_constraints": [
            {"type": "performance", "description": "Real-time updates within 200ms", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Active collaboration sessions", "target": "50% increase", "timeframe": "3 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Dropbox Real-time Collaboration",
        domain="general",
        source="Dropbox",
        template_style="dropbox_one_page",
        brief=dropbox_brief,
    ))
    
    # 3. Notion AI Assistant (Notion PRD System风格)
    notion_brief = {
        "title": "Notion AI Writing Assistant",
        "domain": "general",
        "goal": "Integrate AI-powered writing assistance into Notion workspace",
        "target_users": [
            {"persona": "Content creators", "needs": "AI-assisted writing and editing", "pain_points": "Time-consuming writing process"}
        ],
        "key_constraints": [
            {"type": "privacy", "description": "User data must remain private", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "User adoption rate", "target": "30%", "timeframe": "6 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Notion AI Writing Assistant",
        domain="general",
        source="Notion",
        template_style="notion_prd",
        brief=notion_brief,
    ))
    
    # ========== 电商领域 (Ecommerce) ==========
    
    # 4. Amazon Prime Video Personalization (Amazon-Style PRD)
    amazon_brief = {
        "title": "Amazon Prime Video Personalization",
        "domain": "ecommerce",
        "goal": "Enhance personalization features including smart recommendations, watch history analysis, and content discovery",
        "target_users": [
            {"persona": "Prime Video subscribers", "needs": "Personalized content recommendations", "pain_points": "Difficulty finding relevant content"},
            {"persona": "Heavy users", "needs": "Watch 5+ hours per week", "pain_points": "Content discovery fatigue"},
            {"persona": "Families", "needs": "Multiple user profiles", "pain_points": "Mixed viewing preferences"},
        ],
        "key_constraints": [
            {"type": "performance", "description": "99.9% uptime for recommendation engine", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "User engagement", "target": "25% increase", "timeframe": "3 months"},
            {"name": "Content discovery rate", "target": "30% improvement", "timeframe": "3 months"},
            {"name": "Time to find content", "target": "40% reduction", "timeframe": "3 months"},
        ],
        "problem_statement": "Users struggle to discover relevant content, leading to low engagement and subscription churn",
        "solution_approach": "Multi-factor recommendation system combining collaborative filtering, content-based filtering, and user behavior analysis",
    }
    samples.append(builder.add_prd_sample(
        title="Amazon Prime Video Personalization",
        domain="ecommerce",
        source="Amazon",
        template_style="amazon_style",
        brief=amazon_brief,
    ))
    
    # 5. Shopify Mobile App (Startup-Focused Template)
    shopify_brief = {
        "title": "Shopify Mobile Store Management",
        "domain": "ecommerce",
        "goal": "Enable merchants to manage their stores on mobile devices",
        "target_users": [
            {"persona": "Small business owners", "needs": "Mobile store management", "pain_points": "Limited to desktop access"}
        ],
        "key_constraints": [
            {"type": "mobile", "description": "iOS and Android support", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Mobile app adoption", "target": "40% of merchants", "timeframe": "6 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Shopify Mobile Store Management",
        domain="ecommerce",
        source="Shopify",
        template_style="startup_focused",
        brief=shopify_brief,
    ))
    
    # ========== 金融领域 (Financial) ==========
    
    # 6. Smart Financial Advisor (Intercom Job Story风格)
    financial_brief = {
        "title": "Smart Financial Advisor",
        "domain": "financial",
        "goal": "Launch intelligent financial advisory service to improve new customer conversion rate",
        "target_users": [
            {"persona": "Young professionals", "needs": "Quick understanding of financial solutions", "pain_points": "Lack of financial knowledge"},
            {"persona": "Beginner investors", "needs": "Risk-controlled portfolio recommendations", "pain_points": "Investment decision paralysis"},
        ],
        "key_constraints": [
            {"type": "compliance", "description": "Meet financial regulatory disclosure requirements", "priority": "P0"},
            {"type": "performance", "description": "User query response time under 2 seconds", "priority": "P1"},
        ],
        "business_metrics": [
            {"name": "New account opening rate", "target": "15%", "timeframe": "Q3"},
            {"name": "Financial product conversion rate", "target": "12%", "timeframe": "6 months"},
        ],
        "problem_statement": "Young professionals lack financial knowledge and confidence to make investment decisions",
        "solution_approach": "AI-powered financial advisor providing personalized recommendations with clear risk explanations",
    }
    samples.append(builder.add_prd_sample(
        title="Smart Financial Advisor",
        domain="financial",
        source="Custom",
        template_style="intercom_job_story",
        brief=financial_brief,
    ))
    
    # 7. Payment Security Enhancement (Microsoft Feature Doc风格)
    payment_brief = {
        "title": "Payment Security Enhancement",
        "domain": "financial",
        "goal": "Implement advanced fraud detection and prevention system",
        "target_users": [
            {"persona": "Payment users", "needs": "Secure transactions", "pain_points": "Fraud concerns"}
        ],
        "key_constraints": [
            {"type": "security", "description": "Zero false positives for legitimate transactions", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Fraud detection rate", "target": "99.5%", "timeframe": "3 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Payment Security Enhancement",
        domain="financial",
        source="Custom",
        template_style="microsoft_feature",
        brief=payment_brief,
    ))
    
    # ========== 设计工具 (Design Tools) ==========
    
    # 8. Figma Real-time Collaboration (Figma Design-First Template)
    figma_brief = {
        "title": "Figma Real-time Collaboration",
        "domain": "general",
        "goal": "Enable multiple designers to collaborate in real-time on design files",
        "target_users": [
            {"persona": "Design teams", "needs": "Real-time collaboration", "pain_points": "File conflicts and version management"}
        ],
        "key_constraints": [
            {"type": "performance", "description": "Real-time sync within 100ms", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Collaboration sessions", "target": "60% increase", "timeframe": "3 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Figma Real-time Collaboration",
        domain="general",
        source="Figma",
        template_style="figma_design_first",
        brief=figma_brief,
    ))
    
    # 9. Miro Template System (Miro Product Alignment Document)
    miro_brief = {
        "title": "Miro Template Marketplace",
        "domain": "general",
        "goal": "Create a marketplace for user-generated templates",
        "target_users": [
            {"persona": "Miro users", "needs": "Pre-built templates", "pain_points": "Starting from scratch"}
        ],
        "key_constraints": [
            {"type": "quality", "description": "Template quality standards", "priority": "P1"},
        ],
        "business_metrics": [
            {"name": "Template usage", "target": "50% of users", "timeframe": "6 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Miro Template Marketplace",
        domain="general",
        source="Miro",
        template_style="miro_alignment",
        brief=miro_brief,
    ))
    
    # ========== 项目管理 (Project Management) ==========
    
    # 10. Linear Priority System (ShapeUp Pitch风格)
    linear_brief = {
        "title": "Linear Priority Micro-Adjustments",
        "domain": "general",
        "goal": "Enable fine-grained priority adjustments for better task management",
        "target_users": [
            {"persona": "Product managers", "needs": "Flexible priority management", "pain_points": "Rigid priority systems"}
        ],
        "key_constraints": [
            {"type": "appetite", "description": "6-week project", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "User satisfaction", "target": "20% improvement", "timeframe": "6 weeks"},
        ],
        "problem_statement": "Current priority system is too rigid, preventing nuanced task prioritization",
        "solution_approach": "Micro-adjustment system allowing fine-grained priority tweaks",
    }
    samples.append(builder.add_prd_sample(
        title="Linear Priority Micro-Adjustments",
        domain="general",
        source="Linear",
        template_style="shapeup_pitch",
        brief=linear_brief,
    ))
    
    # 11. Atlassian Jira Automation (Atlassian Agile Template)
    jira_brief = {
        "title": "Jira Automated Workflow",
        "domain": "general",
        "goal": "Automate repetitive workflow tasks in Jira",
        "target_users": [
            {"persona": "Agile teams", "needs": "Workflow automation", "pain_points": "Manual repetitive tasks"}
        ],
        "key_constraints": [
            {"type": "compatibility", "description": "Support existing workflows", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Time saved", "target": "30% reduction", "timeframe": "3 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Jira Automated Workflow",
        domain="general",
        source="Atlassian",
        template_style="atlassian_agile",
        brief=jira_brief,
    ))
    
    # ========== 医疗领域 (Medical) ==========
    
    # 12. Telemedicine Platform (Lean UX Canvas风格)
    medical_brief = {
        "title": "Telemedicine Consultation Platform",
        "domain": "medical",
        "goal": "Enable remote medical consultations for patients",
        "target_users": [
            {"persona": "Patients", "needs": "Remote medical access", "pain_points": "Limited access to healthcare"}
        ],
        "key_constraints": [
            {"type": "compliance", "description": "HIPAA compliance required", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Consultation volume", "target": "1000/month", "timeframe": "6 months"},
        ],
        "problem_statement": "Patients in remote areas lack access to quality healthcare",
        "solution_approach": "Secure video consultation platform with integrated medical records",
    }
    samples.append(builder.add_prd_sample(
        title="Telemedicine Consultation Platform",
        domain="medical",
        source="Custom",
        template_style="lean_ux_canvas",
        brief=medical_brief,
    ))
    
    # ========== 教育领域 (Education) ==========
    
    # 13. Online Learning Platform (Product School Template)
    education_brief = {
        "title": "Personalized Learning Path",
        "domain": "education",
        "goal": "Create personalized learning paths for students",
        "target_users": [
            {"persona": "Students", "needs": "Personalized learning", "pain_points": "One-size-fits-all curriculum"}
        ],
        "key_constraints": [
            {"type": "pedagogy", "description": "Evidence-based learning methods", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Student completion rate", "target": "40% increase", "timeframe": "6 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Personalized Learning Path",
        domain="education",
        source="Custom",
        template_style="product_school",
        brief=education_brief,
    ))
    
    # ========== AI增强 (AI-Enhanced) ==========
    
    # 14. AI-Powered PRD Generator (AI-Enhanced PRD Template)
    ai_brief = {
        "title": "AI-Powered PRD Assistant",
        "domain": "general",
        "goal": "Use AI to assist product managers in creating better PRDs",
        "target_users": [
            {"persona": "Product managers", "needs": "AI-assisted PRD creation", "pain_points": "Time-consuming PRD writing"}
        ],
        "key_constraints": [
            {"type": "quality", "description": "Maintain human oversight", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "PRD creation time", "target": "50% reduction", "timeframe": "3 months"},
        ],
        "problem_statement": "PRD creation is time-consuming and inconsistent across teams",
        "solution_approach": "AI-powered assistant providing suggestions, validation, and quality checks",
    }
    samples.append(builder.add_prd_sample(
        title="AI-Powered PRD Assistant",
        domain="general",
        source="Custom",
        template_style="ai_enhanced",
        brief=ai_brief,
    ))
    
    # ========== 企业软件 (Enterprise) ==========
    
    # 15. Enterprise SSO Integration (Microsoft Feature Doc风格)
    enterprise_brief = {
        "title": "Enterprise SSO Integration",
        "domain": "general",
        "goal": "Enable single sign-on for enterprise customers",
        "target_users": [
            {"persona": "Enterprise IT admins", "needs": "Centralized authentication", "pain_points": "Multiple login credentials"}
        ],
        "key_constraints": [
            {"type": "security", "description": "SAML 2.0 compliance", "priority": "P0"},
        ],
        "business_metrics": [
            {"name": "Enterprise adoption", "target": "80% of enterprise customers", "timeframe": "12 months"},
        ],
    }
    samples.append(builder.add_prd_sample(
        title="Enterprise SSO Integration",
        domain="general",
        source="Custom",
        template_style="microsoft_feature",
        brief=enterprise_brief,
    ))
    
    return samples

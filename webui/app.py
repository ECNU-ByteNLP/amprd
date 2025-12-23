"""
AMPRD Web UI - FastAPI 后端服务

提供PRD生成、进度查询、结果导出等API接口
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import MultiAgentOrchestrator
from src.utils.brief_parser import parse_brief_text
from src.templates.manager import TemplateManager
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics
from src.exporters.prd_renderer import render_markdown, render_docx

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("webui")

# 全局状态管理
TASKS: Dict[str, Dict[str, Any]] = {}
ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)


# ==================== 工具函数 ====================

def find_expert_prd(prd_id: str) -> Optional[Path]:
    """
    根据PRD ID查找对应的专家PRD
    
    Args:
        prd_id: PRD ID或Brief ID
    
    Returns:
        Optional[Path]: 专家PRD文件路径，如果不存在则返回None
    """
    # 优先使用中文PRD映射
    chinese_mapping_path = PROJECT_ROOT / "data" / "chinese_prds" / "processed" / "brief_to_expert_mapping.json"
    if chinese_mapping_path.exists():
        try:
            mapping_data = json.loads(chinese_mapping_path.read_text(encoding="utf-8"))
            mappings = mapping_data.get("mappings", {})
            expert_info = mappings.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                expert_path = Path(expert_info["expert_prd_path"])
                if expert_path.exists():
                    return expert_path
        except Exception as e:
            logger.warning(f"读取中文PRD映射文件失败: {e}")
    
    # 尝试英文PRD映射
    english_mapping_path = PROJECT_ROOT / "data" / "english_prds" / "processed" / "brief_to_expert_mapping.json"
    if english_mapping_path.exists():
        try:
            mapping_data = json.loads(english_mapping_path.read_text(encoding="utf-8"))
            expert_info = mapping_data.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                expert_path = Path(expert_info["expert_prd_path"])
                if expert_path.exists():
                    return expert_path
        except Exception as e:
            logger.warning(f"读取英文PRD映射文件失败: {e}")
    
    # 如果没有映射文件，尝试默认路径
    expert_dir = PROJECT_ROOT / "data" / "expert_prds"
    if expert_dir.exists():
        expert_path = expert_dir / f"{prd_id}.json"
        if expert_path.exists():
            return expert_path
    
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动AMPRD Web UI服务...")
    yield
    logger.info("关闭AMPRD Web UI服务...")


# 创建FastAPI应用
app = FastAPI(
    title="AMPRD - 多模态双语PRD生成系统",
    description="基于多智能体协作的PRD自动生成系统Web界面",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class BriefInput(BaseModel):
    """Brief输入模型"""
    title: str = Field(..., description="产品标题")
    domain: Optional[str] = Field(None, description="产品领域")
    goal: str = Field(..., description="核心目标")
    target_users: Optional[List[Dict[str, str]]] = Field(default=[], description="目标用户")
    key_constraints: Optional[List[Dict[str, str]]] = Field(default=[], description="关键约束")
    business_metrics: Optional[List[Dict[str, str]]] = Field(default=[], description="业务指标")
    scope: Optional[str] = Field(None, description="范围说明")
    milestones: Optional[List[Dict[str, str]]] = Field(default=[], description="里程碑")


class BriefTextInput(BaseModel):
    """自然语言Brief输入模型"""
    brief_text: str = Field(..., description="自然语言描述的产品需求")
    template_id: Optional[str] = Field(None, description="模板ID")
    output_format: Optional[str] = Field("json", description="输出格式: json, docx, markdown")


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0-100
    current_step: Optional[str] = None
    error: Optional[str] = None
    prd_path: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class GenerateOptions(BaseModel):
    """Optional generation controls (for experiments and reproducible evaluation)."""
    model_provider: Optional[str] = Field(
        default=None, description="Model provider: qwen (default) or openai (OpenAI-compatible)."
    )
    communication_mode: Optional[str] = Field(
        default=None, description="blackboard (default) or async_queue."
    )
    disabled_agents: Optional[List[str]] = Field(
        default=None,
        description="Disable specific agents for ablations, e.g., ['TableAgent'] or ['VisionAgent'].",
    )


class PRDInfo(BaseModel):
    """PRD信息模型"""
    prd_id: str
    title: str
    created_at: str
    file_path: str
    metrics: Optional[Dict[str, Any]] = None
    file_size: int


# ==================== 工具函数 ====================

def generate_task_id() -> str:
    """生成任务ID"""
    return str(uuid.uuid4())


def run_prd_generation(
    task_id: str,
    brief: Dict[str, Any],
    template_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    options: Optional[Dict[str, Any]] = None,
):
    """
    在后台运行PRD生成任务
    
    Args:
        task_id: 任务ID
        brief: Brief字典
        template_id: 模板ID（可选）
        output_dir: 输出目录（可选）
    """
    try:
        # 更新任务状态
        TASKS[task_id]["status"] = "running"
        TASKS[task_id]["progress"] = 10.0
        TASKS[task_id]["current_step"] = "初始化系统..."
        TASKS[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 准备输出目录
        if output_dir is None:
            output_dir = ARTIFACTS_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备输入
        inputs: Dict[str, Any] = {"brief": brief}
        
        # 加载模板（如果有）
        if template_id:
            TASKS[task_id]["current_step"] = f"加载模板: {template_id}..."
            tm = TemplateManager()
            template_spec = tm.load(template_id=template_id)
            inputs["template"] = template_spec
        
        # 初始化Orchestrator
        TASKS[task_id]["progress"] = 20.0
        TASKS[task_id]["current_step"] = "初始化多智能体系统..."
        opts = options or {}
        orchestrator = MultiAgentOrchestrator(
            persist_dir=output_dir,
            disabled_agents=opts.get("disabled_agents"),
            communication_mode=opts.get("communication_mode") or "blackboard",
            model_provider=opts.get("model_provider") or "qwen",
        )
        
        # 运行生成流程
        TASKS[task_id]["progress"] = 30.0
        TASKS[task_id]["current_step"] = "生成PRD中..."
        state = orchestrator.run(inputs)
        
        # 获取生成的PRD路径
        prd_path = state.get("quality", {}).get("artifact_path")
        if not prd_path or not Path(prd_path).exists():
            raise FileNotFoundError("PRD文件未生成")
        
        # 计算质量指标
        TASKS[task_id]["progress"] = 80.0
        TASKS[task_id]["current_step"] = "计算质量指标..."
        
        with open(prd_path, "r", encoding="utf-8") as f:
            prd_json = json.load(f)
        
        # 查找专家PRD
        # 尝试从brief中获取ID（可能是title、domain或其他标识）
        brief_id = brief.get("prd_id") or brief.get("title", "").replace(" ", "_").lower()
        expert_prd_path = find_expert_prd(brief_id)
        
        # 计算指标
        basic_metrics = compute_all_metrics(prd_json)
        extended_metrics = compute_all_extended_metrics(
            prd_json,
            expert_prd_path=expert_prd_path
        )
        all_metrics = {**basic_metrics, **extended_metrics}
        
        # 更新任务状态
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 100.0
        TASKS[task_id]["current_step"] = "完成"
        TASKS[task_id]["prd_path"] = str(prd_path)
        TASKS[task_id]["metrics"] = all_metrics
        TASKS[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"任务 {task_id} 完成，PRD路径: {prd_path}")
        
    except Exception as e:
        # 更新任务状态为失败
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)
        TASKS[task_id]["current_step"] = f"错误: {str(e)}"
        TASKS[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.error(f"任务 {task_id} 失败: {e}", exc_info=True)


# ==================== API Routes ====================

@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "name": "AMPRD Web UI",
        "version": "1.0.0",
        "description": "多模态双语PRD自动生成系统",
        "endpoints": {
            "generate": "/api/generate",
            "status": "/api/status/{task_id}",
            "list": "/api/prds",
            "download": "/api/download/{task_id}",
            "export": "/api/export/{task_id}",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.post("/api/generate")
async def generate_prd(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    生成PRD
    
    支持两种输入方式：
    1. 结构化Brief JSON (brief参数)
    2. 自然语言描述 (brief_text参数)
    
    请求体格式:
    {
        "brief_text": "自然语言描述...",  // 或
        "brief": {...},                   // 结构化Brief JSON
        "template_id": "模板ID"           // 可选
    }
    """
    try:
        # 解析JSON请求体
        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"请求体格式错误: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 初始化任务状态
        TASKS[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "current_step": "等待开始...",
            "error": None,
            "prd_path": None,
            "metrics": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 从请求体中提取参数
        brief_text = body.get("brief_text")
        brief = body.get("brief")
        template_id = body.get("template_id")
        options = body.get("options") or {}
        
        # 处理Brief输入
        brief_dict: Dict[str, Any]
        if brief_text:
            # 解析自然语言Brief
            from src.models.qwen_client import create_qwen_clients_from_env
            text_cn, _, _ = create_qwen_clients_from_env()
            brief_dict, parse_report = parse_brief_text(brief_text, model=text_cn)
            logger.info(f"Brief解析置信度: {parse_report.get('confidence', 0.0)}")
        elif brief:
            # 使用结构化Brief
            if isinstance(brief, dict):
                brief_dict = brief
            else:
                brief_dict = brief
        else:
            raise HTTPException(status_code=400, detail="必须提供brief或brief_text参数")
        
        # 在后台运行生成任务
        background_tasks.add_task(
            run_prd_generation,
            task_id=task_id,
            brief=brief_dict,
            template_id=template_id
            ,
            options=options,
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "PRD生成任务已启动"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成PRD失败: {e}", exc_info=True)
        import traceback
        error_detail = f"生成PRD失败: {str(e)}"
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = TASKS[task_id]
    return TaskStatus(**task)


@app.get("/api/prds")
async def list_prds(limit: int = 50, offset: int = 0):
    """列出所有生成的PRD"""
    prds: List[Dict[str, Any]] = []
    
    # 从artifacts目录扫描
    for task_dir in sorted(ARTIFACTS_DIR.iterdir(), reverse=True):
        if not task_dir.is_dir():
            continue
        
        # 查找PRD JSON文件
        for prd_file in task_dir.glob("prd_*.json"):
            try:
                with open(prd_file, "r", encoding="utf-8") as f:
                    prd_json = json.load(f)
                
                # 获取文件信息
                file_stat = prd_file.stat()
                
                prds.append({
                    "prd_id": prd_file.stem,
                    "title": prd_json.get("title", {}).get("zh-CN", "未命名"),
                    "created_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "file_path": str(prd_file),
                    "file_size": file_stat.st_size
                })
            except Exception as e:
                logger.warning(f"读取PRD文件失败 {prd_file}: {e}")
                continue
    
    # 分页
    total = len(prds)
    prds = prds[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "prds": prds
    }


@app.get("/api/download/{task_id}")
async def download_prd(task_id: str, format: str = "json"):
    """
    下载PRD文件
    
    format: json, docx, markdown
    """
    # 先尝试从TASKS获取
    prd_path_obj = None
    if task_id in TASKS:
        task = TASKS[task_id]
        prd_path = task.get("prd_path")
        if prd_path and Path(prd_path).exists():
            prd_path_obj = Path(prd_path)
    
    # 如果找不到，尝试从artifacts目录查找
    if not prd_path_obj:
        task_dir = ARTIFACTS_DIR / task_id
        if task_dir.exists():
            prd_files = list(task_dir.glob("prd_*.json"))
            if prd_files:
                prd_path_obj = prd_files[0]
    
    # 如果还是找不到，尝试直接搜索所有目录
    if not prd_path_obj:
        for task_dir in ARTIFACTS_DIR.iterdir():
            if not task_dir.is_dir():
                continue
            candidate = task_dir / f"{task_id}.json"
            if candidate.exists():
                prd_path_obj = candidate
                break
    
    if not prd_path_obj or not prd_path_obj.exists():
        raise HTTPException(status_code=404, detail="PRD文件不存在")
    
    # 根据格式返回不同文件
    if format == "json":
        return FileResponse(
            str(prd_path_obj),
            media_type="application/json",
            filename=prd_path_obj.name
        )
    elif format == "docx":
        # 导出为DOCX
        output_path = prd_path_obj.parent / f"{prd_path_obj.stem}.docx"
        
        with open(prd_path_obj, "r", encoding="utf-8") as f:
            prd_json = json.load(f)
        
        render_docx(prd_json, output_path, language="zh")
        
        return FileResponse(
            str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=output_path.name
        )
    elif format == "markdown":
        # 导出为Markdown
        output_path = prd_path_obj.parent / f"{prd_path_obj.stem}.md"
        
        with open(prd_path_obj, "r", encoding="utf-8") as f:
            prd_json = json.load(f)
        
        markdown_content = render_markdown(prd_json, language="zh")
        output_path.write_text(markdown_content, encoding="utf-8")
        
        return FileResponse(
            str(output_path),
            media_type="text/markdown",
            filename=output_path.name
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")


@app.get("/api/prd/{prd_id}")
async def get_prd(prd_id: str):
    """获取PRD内容"""
    # 查找PRD文件
    prd_file = None
    for task_dir in ARTIFACTS_DIR.iterdir():
        if not task_dir.is_dir():
            continue
        candidate = task_dir / f"{prd_id}.json"
        if candidate.exists():
            prd_file = candidate
            break
    
    if not prd_file:
        raise HTTPException(status_code=404, detail="PRD不存在")
    
    with open(prd_file, "r", encoding="utf-8") as f:
        prd_json = json.load(f)
    
    return prd_json


@app.get("/api/metrics/{task_id}")
async def get_prd_metrics(task_id: str):
    """获取PRD质量指标"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = TASKS[task_id]
    metrics = task.get("metrics")
    
    if not metrics:
        raise HTTPException(status_code=404, detail="指标未计算")
    
    return metrics


@app.post("/api/evaluate")
async def evaluate_prd(file: UploadFile = File(...)):
    """
    Evaluate an uploaded PRD JSON and return metrics (basic + extended).

    This enables external users to benchmark their own PRDs against the same metric suite
    without running the generation pipeline.
    """
    try:
        raw = await file.read()
        prd_json = json.loads(raw.decode("utf-8"))

        # Try to infer brief/prd id for expert mapping (best-effort).
        prd_id = (
            prd_json.get("prd_id")
            or prd_json.get("id")
            or prd_json.get("title", {}).get("en-US")
            or prd_json.get("title", {}).get("zh-CN")
            or "uploaded_prd"
        )
        if isinstance(prd_id, str):
            prd_id = prd_id.replace(" ", "_").lower()
        else:
            prd_id = "uploaded_prd"

        expert_prd_path = find_expert_prd(prd_id)
        basic_metrics = compute_all_metrics(prd_json)
        extended_metrics = compute_all_extended_metrics(prd_json, expert_prd_path=expert_prd_path)
        return {
            "prd_id": prd_id,
            "expert_prd_path": str(expert_prd_path) if expert_prd_path else None,
            "metrics": {**basic_metrics, **extended_metrics},
        }
    except Exception as e:
        logger.error(f"evaluate_prd failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"评测失败: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tasks": {
            "total": len(TASKS),
            "pending": sum(1 for t in TASKS.values() if t["status"] == "pending"),
            "running": sum(1 for t in TASKS.values() if t["status"] == "running"),
            "completed": sum(1 for t in TASKS.values() if t["status"] == "completed"),
            "failed": sum(1 for t in TASKS.values() if t["status"] == "failed")
        }
    }


# 静态文件服务（用于前端）
static_dir = PROJECT_ROOT / "webui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 前端HTML文件 - 必须在所有API路由之后定义（最后匹配）
html_file = static_dir / "index.html"
if html_file.exists():
    @app.get("/", include_in_schema=False)
    async def serve_index():
        """返回前端HTML界面"""
        return FileResponse(
            str(html_file),
            media_type="text/html",
            headers={"Cache-Control": "no-cache"}
        )
else:
    logger.warning(f"HTML文件不存在: {html_file}")

# Favicon处理（避免404错误）
@app.get("/favicon.ico")
async def favicon():
    """返回favicon（可选，避免404错误）"""
    # 尝试返回favicon文件
    favicon_path = static_dir / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path), media_type="image/x-icon")
    # 如果没有favicon，返回空响应
    return JSONResponse(content={}, status_code=204)

# 前端构建产物目录（React构建产物，如果有）
frontend_dir = PROJECT_ROOT / "webui" / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


"""
错误分析与案例研究

分析失败的PRD案例，识别错误类型，并选择典型案例进行深入研究。

功能：
1. 分析失败案例的错误类型
2. 选择2-3个典型案例进行深入分析
3. 生成错误分析报告
4. 生成案例研究报告
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name)
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            try:
                setattr(sys, _stream_name, io.TextIOWrapper(_stream.detach(), encoding="utf-8", line_buffering=True))
            except Exception:
                pass

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv()

def get_benchmark_brief_ids() -> List[str]:
    """获取benchmark brief id列表（固定顺序）。"""
    benchmark_dir = Path("data/benchmark")
    ids = [p.stem.replace("_brief", "") for p in benchmark_dir.glob("*_brief.json")]
    return sorted(set(ids))


def infer_domain(prd_id: str) -> str:
    pid = (prd_id or "").lower()
    if "education" in pid:
        return "education"
    if "finance" in pid or "payment" in pid or "financial" in pid:
        return "finance"
    if "healthcare" in pid or "medical" in pid or "telemedicine" in pid:
        return "healthcare"
    if "ecommerce" in pid or "shopping" in pid or "amazon" in pid or "shopify" in pid:
        return "ecommerce"
    return "other"


def safe_load_json(path: Path) -> Optional[Dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_sections_list(prd_data: Dict) -> List[Dict]:
    """兼容两种PRD结构：扁平化 or outputs嵌套。"""
    sections = prd_data.get("outputs", {}).get("sections", prd_data.get("sections", []))
    if isinstance(sections, list):
        return sections
    if isinstance(sections, dict):
        return [v for v in sections.values() if isinstance(v, dict)]
    return []


def compute_flags(prd_data: Dict) -> Dict:
    sections_list = extract_sections_list(prd_data)
    sections_dict = get_sections_dict(sections_list)

    # tables / figures
    table_count = 0
    figure_count = 0
    for sec in sections_list:
        table_count += len(sec.get("tables") or [])
        figure_count += len(sec.get("figures") or [])
    # 也检查顶层
    table_count += len(prd_data.get("tables") or prd_data.get("outputs", {}).get("tables") or [])
    figure_count += len(prd_data.get("figures") or prd_data.get("outputs", {}).get("assets_manifest") or [])

    # bilingual
    bilingual = False
    overview = find_section_by_id(sections_list, "overview")
    if overview:
        content = overview.get("content", {})
        if isinstance(content, dict):
            bilingual = bool(content.get("zh-CN") and content.get("en-US"))

    return {
        "sections": list(sections_dict.keys()) if sections_dict else [],
        "has_tables": table_count > 0,
        "has_figures": figure_count > 0,
        "bilingual": bilingual,
        "table_count": table_count,
        "figure_count": figure_count,
    }


def overview_preview_zh(prd_data: Dict, max_chars: int = 260) -> str:
    overview = find_section_by_id(extract_sections_list(prd_data), "overview")
    if not overview:
        return ""
    content = overview.get("content", {})
    if not isinstance(content, dict):
        return ""
    zh = content.get("zh-CN", "") or ""
    zh = zh.strip()
    if len(zh) <= max_chars:
        return zh
    return zh[:max_chars] + "..."


def compute_metrics_for_prd(prd_data: Dict, prd_id: str) -> Dict:
    """只用于case study：计算一份PRD的基础+扩展指标（少量样本，允许慢一点）。"""
    try:
        from src.metrics.quality import compute_all_metrics
        from src.metrics.extended_quality import compute_all_extended_metrics
    except Exception:
        return {}

    # case study 不强依赖 expert；如果能找到就加上（便于S_expert）
    expert_path = None
    try:
        from scripts.analyze_ablation_results import find_expert_prd  # 复用同一逻辑
        expert_path = find_expert_prd(prd_id)
    except Exception:
        expert_path = None

    basic = compute_all_metrics(prd_data)
    extended = compute_all_extended_metrics(prd_data, expert_prd_path=expert_path)
    return {**basic, **extended}


def pick_case_ids(num_cases: int = 3) -> List[str]:
    """从benchmark里挑跨领域case（最多每领域1个），用于论文案例。"""
    ids = get_benchmark_brief_ids()
    by_domain: Dict[str, List[str]] = defaultdict(list)
    for pid in ids:
        by_domain[infer_domain(pid)].append(pid)
    ordered_domains = ["ecommerce", "education", "finance", "healthcare", "other"]
    picked: List[str] = []
    for d in ordered_domains:
        if by_domain.get(d):
            picked.append(by_domain[d][0])
        if len(picked) >= num_cases:
            break
    return picked


def generate_case_study_tri_report(
    case_ids: List[str],
    output_path: Path,
    ablation_config: str = "no_table",
    baseline_dir: str = "baseline_strong_prompt",
):
    """生成三方对照案例报告：full_system vs ablation vs baseline。"""
    fs_dir = Path("results/full_system")
    ab_dir = Path("results/ablation") / ablation_config
    # baseline选择：优先 strong_prompt（更强、更公平），若不存在则回退到 retrieval
    preferred = Path("results") / baseline_dir
    fallback = Path("results") / "baseline_retrieval"
    bl_dir = preferred if preferred.exists() else fallback
    baseline_dir = bl_dir.name

    report = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "num_cases": len(case_ids),
        "full_system_dir": str(fs_dir),
        "ablation": {"config": ablation_config, "dir": str(ab_dir)},
        "baseline": {"name": baseline_dir, "dir": str(bl_dir)},
        "cases": [],
        "notes": {
            "goal": "同一brief三方对照：full_system vs 关键消融 vs strongest baseline（便于论文附录与误差分析）",
            "metrics": "metrics字段为自动指标（含嵌套overall）；deltas提供full减去对比系统的差值（正=full更好）。",
        },
    }

    key_metrics = ["S_comp", "S_mm", "S_tab", "S_bi", "S_sem", "S_biz", "S_tech", "S_risk", "S_ps", "S_uj", "S_hyp", "S_expert"]

    for prd_id in case_ids:
        fs_path = fs_dir / f"prd_{prd_id}.json"
        ab_path = ab_dir / f"prd_{prd_id}.json"
        bl_path = bl_dir / f"prd_{prd_id}.json"

        fs = safe_load_json(fs_path) if fs_path.exists() else None
        ab = safe_load_json(ab_path) if ab_path.exists() else None
        bl = safe_load_json(bl_path) if bl_path.exists() else None

        # 如果三者缺任意一个，仍然记录，但标注missing，避免静默失败
        case = {
            "prd_id": prd_id,
            "domain": infer_domain(prd_id),
            "paths": {
                "full_system": str(fs_path) if fs_path.exists() else None,
                ablation_config: str(ab_path) if ab_path.exists() else None,
                baseline_dir: str(bl_path) if bl_path.exists() else None,
            },
            "missing": {
                "full_system": fs is None,
                ablation_config: ab is None,
                baseline_dir: bl is None,
            },
            "variants": {},
            "deltas": {},
        }

        variants = {
            "full_system": fs,
            ablation_config: ab,
            baseline_dir: bl,
        }

        # 计算每个版本的flags + metrics + preview
        metrics_map: Dict[str, Dict] = {}
        for name, data in variants.items():
            if not data:
                continue
            flags = compute_flags(data)
            metrics = compute_metrics_for_prd(data, prd_id=prd_id)
            preview = overview_preview_zh(data)
            case["variants"][name] = {
                "flags": flags,
                "overview_preview_zh": preview,
                "metrics": {k: metrics.get(k) for k in key_metrics if k in metrics},
            }
            metrics_map[name] = metrics

        # 计算差值：full - other（只对存在的计算）
        def _single(metric_val) -> float:
            if isinstance(metric_val, (int, float)):
                return float(metric_val)
            if isinstance(metric_val, dict) and "overall" in metric_val:
                try:
                    return float(metric_val["overall"])
                except Exception:
                    return 0.0
            return 0.0

        if fs:
            for other in [ablation_config, baseline_dir]:
                if not variants.get(other):
                    continue
                delta_block = {}
                for m in key_metrics:
                    f = _single(metrics_map.get("full_system", {}).get(m, 0.0))
                    o = _single(metrics_map.get(other, {}).get(m, 0.0))
                    delta_block[m] = round(f - o, 4)
                case["deltas"][f"full_minus_{other}"] = delta_block

        report["cases"].append(case)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ 三方对照案例报告已保存: {output_path}")


def find_section_by_id(sections: List[Dict], section_id: str) -> Optional[Dict]:
    """从sections数组中查找指定section_id的section"""
    if isinstance(sections, list):
        for section in sections:
            if section.get("section_id") == section_id:
                return section
    elif isinstance(sections, dict):
        return sections.get(section_id)
    return None


def get_sections_dict(sections) -> Dict[str, Dict]:
    """将sections（可能是数组或字典）转换为字典格式"""
    if isinstance(sections, dict):
        return sections
    elif isinstance(sections, list):
        return {sec.get("section_id", ""): sec for sec in sections if sec.get("section_id")}
    return {}


def analyze_failed_prds(results_dir: Path) -> List[Dict]:
    """分析失败的PRD"""
    failed_cases = []
    
    # 查找所有metrics_summary.json文件
    for summary_file in results_dir.rglob("metrics_summary.json"):
        try:
            data = json.loads(summary_file.read_text(encoding="utf-8"))
            
            # 检查是否有失败记录
            if "failed" in data and data["failed"] > 0:
                config_name = summary_file.parent.name
                failed_cases.append({
                    "config": config_name,
                    "failed_count": data.get("failed", 0),
                    "total_count": data.get("total_briefs", 0),
                    "summary_path": str(summary_file),
                })
        except Exception as e:
            print(f"  ⚠️  读取 {summary_file} 失败: {e}")
    
    return failed_cases


def classify_error_types(prd_data: Dict, expert_prd_data: Optional[Dict] = None) -> List[str]:
    """分类错误类型"""
    error_types = []
    
    # 处理两种PRD结构：扁平化（sections在顶层）或嵌套（sections在outputs中）
    sections_list = prd_data.get("outputs", {}).get("sections", prd_data.get("sections", []))
    sections_dict = get_sections_dict(sections_list)
    
    # 检查结构完整性
    required_sections = ["overview", "requirements", "features", "technical_specs"]
    for section_id in required_sections:
        section = sections_dict.get(section_id)
        if not section:
            error_types.append(f"missing_section_{section_id}")
    
    # 检查多模态内容（tables和figures可能在section内部或顶层）
    has_tables = False
    has_figures = False
    for section in sections_list if isinstance(sections_list, list) else sections_dict.values():
        if section.get("tables"):
            has_tables = True
        if section.get("figures"):
            has_figures = True
    
    # 也检查顶层是否有tables/figures
    if not has_tables and (prd_data.get("tables") or prd_data.get("outputs", {}).get("tables")):
        has_tables = True
    if not has_figures and (prd_data.get("figures") or prd_data.get("outputs", {}).get("assets_manifest")):
        has_figures = True
    
    if not has_tables:
        error_types.append("missing_tables")
    if not has_figures:
        error_types.append("missing_figures")
    
    # 检查双语对齐
    overview_section = find_section_by_id(sections_list, "overview")
    if overview_section:
        content = overview_section.get("content", {})
        cn_content = content.get("zh-CN", "") if isinstance(content, dict) else ""
        en_content = content.get("en-US", "") if isinstance(content, dict) else ""
        
        if not cn_content or not en_content:
            error_types.append("missing_bilingual_content")
        elif len(cn_content) < 100 or len(en_content) < 100:
            error_types.append("insufficient_content")
    else:
        error_types.append("missing_bilingual_content")
    
    # 检查技术可行性
    tech_specs_section = find_section_by_id(sections_list, "technical_specs")
    if not tech_specs_section:
        error_types.append("missing_technical_specs")
    
    return error_types


def select_case_studies(results_dir: Path, num_cases: int = 3) -> List[Dict]:
    """选择典型案例"""
    case_studies = []
    
    # 优先选择不同领域的PRD
    domains = defaultdict(list)
    
    # 查找所有成功的PRD
    for prd_file in results_dir.rglob("prd_*.json"):
        try:
            prd_data = json.loads(prd_file.read_text(encoding="utf-8"))
            
            # 提取领域信息（从brief或prd_id推断）
            prd_id = prd_file.stem.replace("prd_", "")
            domain = "unknown"
            
            # 根据prd_id推断领域
            if "education" in prd_id.lower():
                domain = "education"
            elif "finance" in prd_id.lower() or "payment" in prd_id.lower():
                domain = "finance"
            elif "healthcare" in prd_id.lower() or "medical" in prd_id.lower():
                domain = "healthcare"
            elif "ecommerce" in prd_id.lower() or "shopping" in prd_id.lower():
                domain = "ecommerce"
            else:
                domain = "other"
            
            domains[domain].append({
                "prd_id": prd_id,
                "prd_path": str(prd_file),
                "prd_data": prd_data,
                "domain": domain,
            })
        except Exception as e:
            print(f"  ⚠️  读取 {prd_file} 失败: {e}")
    
    # 从每个领域选择一个案例
    selected_domains = list(domains.keys())[:num_cases]
    for domain in selected_domains:
        if domains[domain]:
            case_studies.append(domains[domain][0])
    
    return case_studies


def generate_error_analysis_report(failed_cases: List[Dict], output_path: Path):
    """生成错误分析报告"""
    report = {
        "analysis_date": "2025-11-23",
        "total_failed_configs": len(failed_cases),
        "failed_cases": failed_cases,
        "error_summary": {
            "total_failures": sum(c["failed_count"] for c in failed_cases),
            "failure_rate": sum(c["failed_count"] for c in failed_cases) / sum(c["total_count"] for c in failed_cases) * 100 if sum(c["total_count"] for c in failed_cases) > 0 else 0,
        },
        "recommendations": [
            "检查API连接和网络稳定性",
            "增加重试机制和错误处理",
            "优化提示词和Few-shot示例",
            "检查模型响应格式",
        ],
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"  ✅ 错误分析报告已保存: {output_path}")


def generate_case_study_report(case_studies: List[Dict], output_path: Path):
    """生成案例研究报告"""
    report = {
        "analysis_date": "2025-11-23",
        "num_cases": len(case_studies),
        "case_studies": [],
    }
    
    for case in case_studies:
        prd_data = case["prd_data"]
        
        # 处理两种PRD结构
        sections_list = prd_data.get("outputs", {}).get("sections", prd_data.get("sections", []))
        sections_dict = get_sections_dict(sections_list)
        
        # 检查tables和figures
        has_tables = False
        has_figures = False
        for section in sections_list if isinstance(sections_list, list) else sections_dict.values():
            if section.get("tables"):
                has_tables = True
            if section.get("figures"):
                has_figures = True
        
        # 检查双语对齐
        overview_section = find_section_by_id(sections_list, "overview")
        bilingual = False
        overview_preview = ""
        if overview_section:
            content = overview_section.get("content", {})
            if isinstance(content, dict):
                cn_content = content.get("zh-CN", "")
                en_content = content.get("en-US", "")
                bilingual = bool(cn_content and en_content)
                overview_preview = (cn_content[:200] + "...") if cn_content else ""
        
        # 提取关键信息
        case_info = {
            "prd_id": case["prd_id"],
            "domain": case["domain"],
            "prd_path": case["prd_path"],
            "sections": list(sections_dict.keys()) if sections_dict else [],
            "has_tables": has_tables,
            "has_figures": has_figures,
            "bilingual": bilingual,
            "overview_preview": overview_preview,
        }
        
        report["case_studies"].append(case_info)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"  ✅ 案例研究报告已保存: {output_path}")


def main():
    print("=" * 70)
    print("错误分析与案例研究")
    print("=" * 70)
    print()
    
    results_dir = Path("results")
    output_dir = Path("results/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 分析失败的PRD
    print("📊 分析失败的PRD...")
    failed_cases = analyze_failed_prds(results_dir)
    
    if failed_cases:
        print(f"  找到 {len(failed_cases)} 个配置有失败案例")
        for case in failed_cases:
            print(f"    - {case['config']}: {case['failed_count']}/{case['total_count']} 失败")
    else:
        print("  ✅ 未发现失败案例")
    
    print()
    
    # 2. 生成错误分析报告
    print("📝 生成错误分析报告...")
    generate_error_analysis_report(
        failed_cases,
        output_dir / "error_analysis_report.json"
    )
    print()
    
    # 3. 选择典型案例（论文用：同一brief三方对照）
    print("📚 选择典型案例（benchmark跨领域）...")
    tri_case_ids = pick_case_ids(num_cases=3)
    if tri_case_ids:
        print(f"  选择了 {len(tri_case_ids)} 个案例:")
        for pid in tri_case_ids:
            print(f"    - {pid} ({infer_domain(pid)})")
    else:
        print("  ⚠️  未找到benchmark案例")

    print()

    # 4. 生成三方对照案例研究报告（full_system vs 关键消融 vs strongest baseline）
    if tri_case_ids:
        print("📝 生成三方对照案例研究报告...")
        generate_case_study_tri_report(
            tri_case_ids,
            output_dir / "case_study_tri_report.json",
            ablation_config="no_table",
            baseline_dir="baseline_strong_prompt",
        )

    # 5. 保留原先“单PRD概览”case study（便于快速浏览）
    print("\n📚 生成快速浏览用案例（旧格式，供对照）...")
    case_studies = select_case_studies(results_dir, num_cases=3)
    if case_studies:
        generate_case_study_report(case_studies, output_dir / "case_study_report.json")
    else:
        print("  ⚠️  未找到合适的PRD用于旧格式case study")
    
    print("\n" + "=" * 70)
    print("错误分析与案例研究完成")
    print("=" * 70)
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()


"""
人工评估框架

创建人工评估问卷和数据收集工具。

功能：
1. 生成评估问卷（HTML格式）
2. 准备评估样本（PRD对比对）
3. 数据收集模板
4. 计算评分者间一致性（Krippendorff's α）

输出：
- results/human_evaluation/questionnaire.html: 评估问卷
- results/human_evaluation/samples.json: 评估样本
- results/human_evaluation/results_template.json: 结果模板
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv()


def prepare_evaluation_samples(
    full_system_dir: Path,
    baseline_dir: Path,
    num_samples_per_domain: int = 5,
) -> List[Dict]:
    """准备评估样本"""
    samples = []
    
    # 按领域分组
    domains = defaultdict(list)
    
    # 查找完整系统的PRD
    for prd_file in full_system_dir.glob("prd_*.json"):
        try:
            prd_id = prd_file.stem.replace("prd_", "")
            
            # 推断领域
            domain = "other"
            if "education" in prd_id.lower():
                domain = "education"
            elif "finance" in prd_id.lower() or "payment" in prd_id.lower():
                domain = "finance"
            elif "healthcare" in prd_id.lower() or "medical" in prd_id.lower():
                domain = "healthcare"
            elif "ecommerce" in prd_id.lower() or "shopping" in prd_id.lower():
                domain = "ecommerce"
            
            # 查找对应的基线PRD
            baseline_prd = baseline_dir / f"prd_{prd_id}.json"
            if baseline_prd.exists():
                domains[domain].append({
                    "prd_id": prd_id,
                    "domain": domain,
                    "full_system_prd": str(prd_file),
                    "baseline_prd": str(baseline_prd),
                })
        except Exception as e:
            print(f"  ⚠️  处理 {prd_file} 失败: {e}")
    
    # 从每个领域选择样本
    for domain, prds in domains.items():
        selected = prds[:num_samples_per_domain]
        samples.extend(selected)
    
    return samples


def generate_questionnaire_html(samples: List[Dict], output_path: Path):
    """生成评估问卷（HTML格式）"""
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRD质量人工评估问卷</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2E86AB;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .sample {
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .sample-header {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2E86AB;
        }
        .prd-section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #2E86AB;
        }
        .prd-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .rating-scale {
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
        }
        .rating-item {
            text-align: center;
            flex: 1;
        }
        .rating-item input[type="radio"] {
            margin: 5px;
        }
        .rating-item label {
            display: block;
            font-size: 12px;
            margin-top: 5px;
        }
        .criteria {
            margin: 10px 0;
            padding: 10px;
            background-color: #fff;
            border-radius: 4px;
        }
        .criteria-title {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .submit-btn {
            background-color: #2E86AB;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
        .submit-btn:hover {
            background-color: #1a5f7a;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>PRD质量人工评估问卷</h1>
        <p>请仔细阅读每个PRD样本，并根据以下标准进行评分。</p>
        <p><strong>评估标准：</strong></p>
        <ul>
            <li><strong>1分</strong>：非常差，完全不符合要求</li>
            <li><strong>2分</strong>：较差，基本不符合要求</li>
            <li><strong>3分</strong>：一般，部分符合要求</li>
            <li><strong>4分</strong>：良好，基本符合要求</li>
            <li><strong>5分</strong>：优秀，完全符合要求</li>
        </ul>
    </div>
    
    <form id="evaluationForm">
"""
    
    # 评估维度
    criteria = [
        {"name": "结构完整性", "key": "structure", "desc": "PRD是否包含所有必需章节"},
        {"name": "内容质量", "key": "content", "desc": "内容是否详细、清晰、可执行"},
        {"name": "技术可行性", "key": "technical", "desc": "技术方案是否可行"},
        {"name": "业务对齐度", "key": "business", "desc": "是否符合业务需求"},
        {"name": "多模态支持", "key": "multimodal", "desc": "是否包含表格、图片等多模态内容"},
        {"name": "双语一致性", "key": "bilingual", "desc": "中英文内容是否一致"},
    ]
    
    for idx, sample in enumerate(samples, 1):
        html_content += f"""
        <div class="sample">
            <div class="sample-header">样本 {idx}: {sample['prd_id']} ({sample['domain']})</div>
            
            <div class="prd-section">
                <div class="prd-title">系统A（完整系统）</div>
                <p>PRD文件: {Path(sample['full_system_prd']).name}</p>
                <p><em>请打开文件查看内容</em></p>
            </div>
            
            <div class="prd-section">
                <div class="prd-title">系统B（基线系统）</div>
                <p>PRD文件: {Path(sample['baseline_prd']).name}</p>
                <p><em>请打开文件查看内容</em></p>
            </div>
            
            <h3>请对系统A进行评分：</h3>
"""
        
        for criterion in criteria:
            html_content += f"""
            <div class="criteria">
                <div class="criteria-title">{criterion['name']} ({criterion['desc']})</div>
                <div class="rating-scale">
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemA_{criterion['key']}" value="1" required>
                        <label>1分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemA_{criterion['key']}" value="2" required>
                        <label>2分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemA_{criterion['key']}" value="3" required>
                        <label>3分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemA_{criterion['key']}" value="4" required>
                        <label>4分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemA_{criterion['key']}" value="5" required>
                        <label>5分</label>
                    </div>
                </div>
            </div>
"""
        
        html_content += f"""
            <h3>请对系统B进行评分：</h3>
"""
        
        for criterion in criteria:
            html_content += f"""
            <div class="criteria">
                <div class="criteria-title">{criterion['name']} ({criterion['desc']})</div>
                <div class="rating-scale">
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemB_{criterion['key']}" value="1" required>
                        <label>1分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemB_{criterion['key']}" value="2" required>
                        <label>2分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemB_{criterion['key']}" value="3" required>
                        <label>3分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemB_{criterion['key']}" value="4" required>
                        <label>4分</label>
                    </div>
                    <div class="rating-item">
                        <input type="radio" name="sample_{idx}_systemB_{criterion['key']}" value="5" required>
                        <label>5分</label>
                    </div>
                </div>
            </div>
"""
        
        html_content += """
            <hr style="margin: 30px 0;">
        </div>
"""
    
    html_content += """
        <button type="submit" class="submit-btn">提交评估</button>
    </form>
    
    <script>
        document.getElementById('evaluationForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            console.log(JSON.stringify(data, null, 2));
            alert('评估数据已输出到控制台，请复制保存为JSON文件。');
        });
    </script>
</body>
</html>
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"  ✅ 评估问卷已生成: {output_path}")


def generate_results_template(samples: List[Dict], output_path: Path):
    """生成结果收集模板"""
    template = {
        "evaluation_info": {
            "evaluator_id": "填写评估者ID",
            "evaluation_date": "填写评估日期",
            "evaluator_role": "PM/研发/QA",
        },
        "samples": [],
    }
    
    for idx, sample in enumerate(samples, 1):
        template["samples"].append({
            "sample_id": idx,
            "prd_id": sample["prd_id"],
            "domain": sample["domain"],
            "systemA_scores": {
                "structure": None,
                "content": None,
                "technical": None,
                "business": None,
                "multimodal": None,
                "bilingual": None,
            },
            "systemB_scores": {
                "structure": None,
                "content": None,
                "technical": None,
                "business": None,
                "multimodal": None,
                "bilingual": None,
            },
            "preference": None,  # "A" or "B" or "tie"
            "comments": "",
        })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"  ✅ 结果模板已生成: {output_path}")


def calculate_krippendorff_alpha(results: List[Dict]) -> float:
    """计算Krippendorff's α（评分者间一致性）"""
    # 简化实现，实际需要更复杂的计算
    # 这里提供一个占位符
    return 0.0


def main():
    print("=" * 70)
    print("人工评估框架")
    print("=" * 70)
    print()
    
    full_system_dir = Path("results/full_system")
    baseline_dir = Path("results/baseline_text_only")
    output_dir = Path("results/human_evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not full_system_dir.exists():
        print(f"❌ 完整系统目录不存在: {full_system_dir}")
        return
    
    if not baseline_dir.exists():
        print(f"❌ 基线系统目录不存在: {baseline_dir}")
        return
    
    # 准备评估样本
    print("📋 准备评估样本...")
    samples = prepare_evaluation_samples(
        full_system_dir,
        baseline_dir,
        num_samples_per_domain=5,
    )
    
    if not samples:
        print("  ⚠️  未找到评估样本")
        return
    
    print(f"  ✅ 准备了 {len(samples)} 个评估样本")
    print()
    
    # 保存样本列表
    samples_path = output_dir / "samples.json"
    samples_path.write_text(
        json.dumps(samples, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  ✅ 样本列表已保存: {samples_path}")
    print()
    
    # 生成评估问卷
    print("📝 生成评估问卷...")
    generate_questionnaire_html(
        samples,
        output_dir / "questionnaire.html"
    )
    print()
    
    # 生成结果模板
    print("📝 生成结果收集模板...")
    generate_results_template(
        samples,
        output_dir / "results_template.json"
    )
    
    print("\n" + "=" * 70)
    print("人工评估框架创建完成")
    print("=" * 70)
    print(f"输出目录: {output_dir}")
    print("\n下一步:")
    print("1. 打开 questionnaire.html 进行评估")
    print("2. 收集所有评估者的结果")
    print("3. 使用 results_template.json 整理数据")
    print("4. 计算评分者间一致性（Krippendorff's α）")


if __name__ == "__main__":
    main()


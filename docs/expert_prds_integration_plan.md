# 真实PRD参考整合方案

## 一、确认：确实有真实PRD参考

您说得对！确实有真实的PRD参考标准可用：

### 1.1 已确认的真实PRD来源

1. **Linear Priority Micro-Adjust PRD**（PDF）
   - 来源：https://cdn.48web.com/sites/pmprompt/Linear%20example%20PRD_%20priority%20micro-adjust.pdf
   - 类型：真实产品文档（Linear公司）
   - 格式：PDF

2. **pmprompt.com提供的12个真实PRD示例**
   - 来源：https://pmprompt.com/blog/prd-examples
   - 包括：
     - Google Search Algorithm Update
     - Amazon Prime Video Features
     - AI-Powered PRD Reviewer
     - **Linear Priority Micro-Adjust**（与上面相同）
     - Make Story Time AI Bedtime Stories
     - Slack Channel Management
     - Spotify Music Discovery
     - Uber Ride Sharing Optimization
     - Airbnb Booking Experience
     - Notion Database Templates
     - **Figma Real-time Collaboration**
     - Stripe Payment Processing

### 1.2 当前系统状态

**问题**：当前系统**没有使用这些真实PRD**作为参考标准！

**证据**：
1. `data/`目录下**没有**`expert_prds/`或`gold/`目录
2. `scripts/quick_start_experiment.py`计算指标时**没有提供**`expert_prd_path`
3. `S_expert`指标虽然支持参考PRD，但实际计算时只使用了结构相似度

---

## 二、当前系统如何支持专家PRD

### 2.1 S_expert指标的支持情况

`src/metrics/extended_quality.py`中的`compute_expert_alignment`函数**已经支持**专家PRD：

```python
def compute_expert_alignment(prd: Dict, expert_prd_path: Optional[Path] = None) -> Dict[str, float]:
    """
    计算专家对齐度 S_expert
    
    对比维度：
    - 结构相似度（章节覆盖度）
    - 内容相似度（基于语义相似度，需要sentence-transformers）
    """
    # 1. 结构相似度（默认计算）
    structure_overlap = ...
    
    # 2. 内容相似度（如果提供了专家PRD）
    content_similarity = 0.0
    if expert_prd_path and expert_prd_path.exists() and HAS_SENTENCE_TRANSFORMERS:
        # 使用sentence-transformers计算语义相似度
        expert_prd = json.loads(expert_prd_path.read_text(encoding="utf-8"))
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # ... 计算相似度 ...
```

**问题**：虽然代码支持，但**实际使用时没有提供`expert_prd_path`**！

### 2.2 当前指标计算流程

```python
# scripts/quick_start_experiment.py
extended_metrics = compute_all_extended_metrics(prd)  # 没有提供expert_prd_path
```

**结果**：`S_expert`只计算了结构相似度（默认值），没有使用真实PRD的内容相似度。

---

## 三、整合真实PRD的方案

### 3.1 步骤1：收集真实PRD（优先级：高）

#### 方案A：手动下载并转换（推荐）

**步骤**：

1. **创建专家PRD目录**：
   ```bash
   mkdir -p data/expert_prds
   ```

2. **下载真实PRD**：
   - 从pmprompt.com下载12个真实PRD示例（PDF格式）
   - 保存到`data/expert_prds/`目录

3. **转换为JSON格式**：
   - 将PDF转换为文本
   - 解析为系统PRD格式（符合`schemas/prd_schema_v0_9.json`）
   - 保存为JSON文件

#### 方案B：自动收集（可选）

**使用工具**：
- PDF解析：`pypdf`或`pdfplumber`
- 文本提取：转换为系统PRD格式

### 3.2 步骤2：建立映射关系（优先级：高）

**目标**：将12个Brief与12个真实PRD建立映射关系

**映射表**（示例）：

| Brief ID | Brief名称 | 对应的真实PRD | 来源 |
|---------|----------|-------------|------|
| general_linear_priority_micro_adjustments | Linear优先级微调 | Linear Priority Micro-Adjust | pmprompt.com |
| general_figma_real_time_collaboration | Figma实时协作 | Figma Real-time Collaboration | pmprompt.com |
| general_google_search_algorithm_update | Google搜索算法更新 | Google Search Algorithm Update | pmprompt.com |
| ecommerce_amazon_prime_video_personalization | Amazon Prime视频个性化 | Amazon Prime Video Features | pmprompt.com |
| ... | ... | ... | ... |

**存储位置**：`data/expert_prds/mapping.json`

### 3.3 步骤3：修改指标计算（优先级：高）

#### 修改`scripts/quick_start_experiment.py`

```python
# 在计算指标时提供expert_prd_path
for prd_path in prd_files:
    prd = json.loads(prd_path.read_text(encoding="utf-8"))
    
    # 查找对应的专家PRD
    prd_id = prd.get("metadata", {}).get("prd_id", prd_path.stem)
    expert_prd_path = find_expert_prd(prd_id)  # 从mapping.json查找
    
    # 基础指标
    basic_metrics = compute_all_metrics(prd)
    
    # 扩展指标（提供expert_prd_path）
    extended_metrics = compute_all_extended_metrics(prd, expert_prd_path=expert_prd_path)
    
    all_metrics = {**basic_metrics, **extended_metrics}
```

#### 修改`src/metrics/extended_quality.py`

```python
def compute_all_extended_metrics(
    prd: Dict,
    expert_prd_path: Optional[Path] = None,  # 添加这个参数
) -> Dict[str, Dict | float]:
    return {
        "S_sem": compute_semantic_quality(prd),
        "S_biz": compute_business_alignment(prd),
        "S_tech": compute_technical_feasibility(prd),
        "S_risk": compute_risk_identification(prd),
        "S_expert": compute_expert_alignment(prd, expert_prd_path),  # 传递expert_prd_path
        "S_ps": compute_problem_solution_separation(prd),
        "S_uj": compute_user_journey_completeness(prd),
        "S_hyp": compute_hypothesis_validation(prd),
    }
```

### 3.4 步骤4：创建专家PRD转换脚本（优先级：中）

**目标**：将PDF/文本格式的真实PRD转换为系统PRD格式

**脚本**：`scripts/convert_expert_prd.py`

```python
"""
将真实PRD（PDF/文本）转换为系统PRD格式（JSON）
"""

def convert_pdf_to_prd_json(pdf_path: Path, output_path: Path) -> None:
    """
    将PDF格式的真实PRD转换为系统PRD格式
    
    Args:
        pdf_path: PDF文件路径
        output_path: 输出JSON文件路径
    """
    # 1. 提取PDF文本
    text = extract_text_from_pdf(pdf_path)
    
    # 2. 解析为PRD结构
    prd_json = {
        "metadata": {
            "prd_id": output_path.stem,
            "source": "expert",
            "original_file": str(pdf_path),
        },
        "sections": parse_prd_sections(text),  # 需要实现解析逻辑
        # ...
    }
    
    # 3. 保存为JSON
    output_path.write_text(
        json.dumps(prd_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
```

---

## 四、立即行动计划

### 优先级1：收集真实PRD（今天）

**步骤**：

1. **下载真实PRD**：
   ```bash
   # 创建目录
   mkdir -p data/expert_prds
   
   # 下载Linear PRD（示例）
   curl -o data/expert_prds/linear_priority_micro_adjust.pdf \
        "https://cdn.48web.com/sites/pmprompt/Linear%20example%20PRD_%20priority%20micro-adjust.pdf"
   ```

2. **手动转换**（如果自动转换困难）：
   - 打开PDF
   - 提取关键章节（Overview、Problem、Solution、Success Metrics等）
   - 转换为系统PRD JSON格式

3. **创建映射文件**：
   ```json
   // data/expert_prds/mapping.json
   {
     "general_linear_priority_micro_adjustments": {
       "expert_prd_path": "data/expert_prds/linear_priority_micro_adjust.json",
       "source": "pmprompt.com",
       "company": "Linear"
     },
     "general_figma_real_time_collaboration": {
       "expert_prd_path": "data/expert_prds/figma_real_time_collaboration.json",
       "source": "pmprompt.com",
       "company": "Figma"
     },
     // ... 其他映射
   }
   ```

### 优先级2：修改指标计算（今天）

**修改`scripts/quick_start_experiment.py`**：

```python
# 添加专家PRD查找函数
def find_expert_prd(prd_id: str) -> Optional[Path]:
    """根据PRD ID查找对应的专家PRD"""
    mapping_path = Path("data/expert_prds/mapping.json")
    if not mapping_path.exists():
        return None
    
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    expert_info = mapping.get(prd_id)
    if expert_info:
        expert_path = Path(expert_info["expert_prd_path"])
        if expert_path.exists():
            return expert_path
    return None

# 修改指标计算
for prd_path in prd_files:
    prd = json.loads(prd_path.read_text(encoding="utf-8"))
    prd_id = prd.get("metadata", {}).get("prd_id", prd_path.stem)
    
    # 查找专家PRD
    expert_prd_path = find_expert_prd(prd_id)
    
    # 基础指标
    basic_metrics = compute_all_metrics(prd)
    
    # 扩展指标（提供expert_prd_path）
    extended_metrics = compute_all_extended_metrics(prd, expert_prd_path=expert_prd_path)
    
    all_metrics = {**basic_metrics, **extended_metrics}
```

**修改`src/metrics/extended_quality.py`**：

```python
def compute_all_extended_metrics(
    prd: Dict,
    expert_prd_path: Optional[Path] = None,  # 添加这个参数
) -> Dict[str, Dict | float]:
    return {
        "S_sem": compute_semantic_quality(prd),
        "S_biz": compute_business_alignment(prd),
        "S_tech": compute_technical_feasibility(prd),
        "S_risk": compute_risk_identification(prd),
        "S_expert": compute_expert_alignment(prd, expert_prd_path),  # 传递expert_prd_path
        "S_ps": compute_problem_solution_separation(prd),
        "S_uj": compute_user_journey_completeness(prd),
        "S_hyp": compute_hypothesis_validation(prd),
    }
```

### 优先级3：验证效果（明天）

**步骤**：

1. **重新运行快速实验**：
   ```bash
   python scripts/quick_start_experiment.py
   ```

2. **检查S_expert指标**：
   - 应该从只计算结构相似度（默认值）变为包含内容相似度
   - S_expert的`content_similarity`字段应该有实际值（>0）

3. **对比结果**：
   - 有专家PRD的PRD：S_expert应该更高（更接近真实PRD）
   - 没有专家PRD的PRD：S_expert只计算结构相似度

---

## 五、预期效果

### 5.1 改进前

```json
{
  "S_expert": {
    "overall": 0.75,  // 只计算结构相似度
    "structure_similarity": 0.75,
    "content_similarity": 0.0  // 没有参考PRD
  }
}
```

### 5.2 改进后

```json
{
  "S_expert": {
    "overall": 0.65,  // 综合结构和内容相似度
    "structure_similarity": 0.75,
    "content_similarity": 0.55  // 基于真实PRD的语义相似度
  }
}
```

---

## 六、资源列表

### 6.1 真实PRD来源

1. **pmprompt.com**（12个真实PRD示例）：
   - https://pmprompt.com/blog/prd-examples
   - 包括：Google、Amazon、Linear、Figma、Slack、Spotify等

2. **Linear Priority Micro-Adjust**（PDF）：
   - https://cdn.48web.com/sites/pmprompt/Linear%20example%20PRD_%20priority%20micro-adjust.pdf

### 6.2 需要收集的PRD（与Brief对应）

| Brief名称 | 对应的真实PRD | 来源 |
|---------|-------------|------|
| general_linear_priority_micro_adjustments | Linear Priority Micro-Adjust | pmprompt.com |
| general_figma_real_time_collaboration | Figma Real-time Collaboration | pmprompt.com |
| general_google_search_algorithm_update | Google Search Algorithm Update | pmprompt.com |
| ecommerce_amazon_prime_video_personalization | Amazon Prime Video Features | pmprompt.com |
| ... | ... | ... |

---

## 七、总结

### 7.1 当前状态

- ✅ **系统支持**：`S_expert`指标已支持专家PRD参考
- ❌ **实际使用**：计算指标时**没有提供**`expert_prd_path`
- ❌ **数据缺失**：`data/expert_prds/`目录**不存在**，没有收集真实PRD

### 7.2 需要做的事情

1. **立即收集**：从pmprompt.com下载12个真实PRD
2. **转换为JSON**：将PDF/文本转换为系统PRD格式
3. **建立映射**：创建Brief与专家PRD的映射关系
4. **修改代码**：在计算指标时提供`expert_prd_path`

### 7.3 预期改进

- **S_expert指标**：从只计算结构相似度变为包含内容相似度
- **评估准确性**：能够准确评估生成PRD与真实PRD的差距
- **论文价值**：可以展示与真实PRD的对齐度，增强论文说服力

---

**您说得对，这些确实是真实PRD参考！我们应该立即整合它们。**


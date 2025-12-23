# 中文PRD数据集使用方案

## 一、数据集概况

### 1.1 数据统计

- **总文件数**：300个
- **文件格式**：
  - PDF：227个（76%）
  - DOCX：36个（12%）
  - DOC：29个（10%）
  - 其他：8个（2%）

- **文档类型**：
  - **PRD**：191个（64%）✅ **核心数据**
  - 方法/模板：29个（10%）✅ **用于Prompt优化**
  - MRD：22个（7%）
  - BRD：11个（4%）
  - 其他：47个（15%）

- **领域分布**：
  - 电商：25个
  - 娱乐：18个
  - 社交：15个
  - 企业服务：13个
  - 工具：11个
  - 教育：10个
  - 金融：7个
  - 旅游：6个
  - 生活服务：5个

- **高质量样本**：
  - 倒推案例：48个（从成熟产品反推，质量高）✅
  - 大厂案例：22个（腾讯9、网易5、阿里3、滴滴2、京东2、美团1）✅
  - 方法论文档：56个（用于Prompt优化）✅

---

## 二、使用策略（分阶段）

### 阶段一：数据组织与筛选（优先级：高）

#### 2.1 数据分类

**目标**：将300个文件按类型和质量分类，便于后续使用

**分类标准**：

1. **核心PRD案例**（用于Few-shot和评估标准）
   - 完整PRD文档
   - 倒推案例（48个，高质量）
   - 大厂案例（22个，权威性强）
   - PDF格式（质量更好）

2. **方法论文档**（用于Prompt优化）
   - "如何写PRD"类文档（56个）
   - 模板类文档
   - 规范类文档

3. **领域知识库**（用于领域增强）
   - 按领域分类（电商、社交、教育等）
   - 提取领域特定术语和模式

#### 2.2 目录结构

```
data/chinese_prds/
├── prd_cases/                    # 核心PRD案例（191个）
│   ├── high_quality/            # 高质量样本（优先使用）
│   │   ├── reverse_analysis/    # 倒推案例（48个）
│   │   └── big_company/         # 大厂案例（22个）
│   └── by_domain/               # 按领域分类
│       ├── ecommerce/           # 电商（25个）
│       ├── social/              # 社交（15个）
│       ├── entertainment/       # 娱乐（18个）
│       ├── education/           # 教育（10个）
│       ├── enterprise/          # 企业服务（13个）
│       ├── finance/             # 金融（7个）
│       └── tools/               # 工具（11个）
├── methodology/                  # 方法论文档（56个）
│   ├── how_to_write/           # "如何写PRD"类
│   ├── templates/               # 模板类
│   └── standards/               # 规范类
└── processed/                    # 处理后的数据
    ├── json/                    # JSON格式（标准化）
    └── extracted_sections/      # 提取的章节
```

---

### 阶段二：数据提取与标准化（优先级：高）

#### 2.1 提取核心信息

**目标**：从PDF/DOC中提取结构化信息，转换为系统PRD格式

**提取内容**：

1. **标准章节**：
   - Overview（概述）
   - Problem Statement（问题陈述）
   - User Persona（用户画像）
   - User Stories（用户故事）
   - Functional Requirements（功能需求）
   - Non-functional Requirements（非功能需求）
   - User Flows（用户流程）
   - Key Interfaces（关键界面）
   - KPI and Milestones（KPI和里程碑）
   - Risks and Mitigations（风险和缓解措施）

2. **元数据**：
   - 领域（domain）
   - 产品名称（title）
   - 公司/来源（company/source）
   - 文档类型（doc_type）
   - 质量等级（quality_level）

#### 2.2 转换为JSON格式

**目标**：将所有PRD转换为统一的JSON格式（符合`schemas/prd_schema_v0_9.json`）

**转换流程**：

```
PDF/DOC文件
    ↓
文本提取（pypdf/pdfplumber）
    ↓
章节识别（基于标题、格式）
    ↓
结构化提取（提取标准章节内容）
    ↓
JSON转换（符合PRD Schema）
    ↓
验证与清洗（去除噪声、格式统一）
    ↓
标准化PRD JSON
```

---

### 阶段三：核心应用（优先级：高）

#### 3.1 Few-shot学习（用于生成）

**目标**：在Prompt中提供高质量PRD示例，提升生成质量

**实施方案**：

1. **为每个Brief选择1-2个相似领域的真实PRD**
   - 基于Brief的domain匹配
   - 选择高质量样本（倒推案例或大厂案例）

2. **在LeadAnalyst的Prompt中注入Few-shot示例**
   ```python
   # 示例：为电商Brief提供电商PRD示例
   few_shot_examples = load_similar_expert_prds(brief["domain"], top_k=2)
   
   prompt = f"""
   以下是真实PRD示例（参考风格和结构）：
   {format_prd_examples(few_shot_examples)}
   
   请基于以下Brief生成PRD：
   {brief}
   """
   ```

3. **动态选择Few-shot示例**
   - 根据Brief的domain自动选择
   - 优先选择倒推案例或大厂案例
   - 确保示例质量和相关性

**预期效果**：
- 生成PRD的结构更规范
- 写作风格更接近真实PRD
- 领域术语使用更准确

#### 3.2 S_expert指标计算（用于评估）

**目标**：使用真实中文PRD作为参考标准，计算S_expert指标

**实施方案**：

1. **建立Brief与真实PRD的映射关系**
   ```json
   {
     "ecommerce_amazon_prime_video_personalization": {
       "expert_prd_path": "data/chinese_prds/processed/json/电商_每日优鲜.json",
       "domain": "ecommerce",
       "quality_level": "high",
       "source": "reverse_analysis"
     }
   }
   ```

2. **计算语义相似度**
   - 使用中文sentence-transformers模型
   - 对比生成PRD与真实PRD的语义相似度
   - 评估结构和内容对齐度

3. **更新S_expert指标计算**
   ```python
   # 查找对应的中文PRD参考
   expert_prd_path = find_chinese_expert_prd(prd_id, domain)
   
   # 计算S_expert（使用中文PRD参考）
   s_expert = compute_expert_alignment(generated_prd, expert_prd_path)
   ```

**预期效果**：
- S_expert指标更准确（有真实参考标准）
- 可以评估生成PRD与真实PRD的差距
- 提供改进方向的量化指标

#### 3.3 Prompt优化（提升生成质量）

**目标**：从方法论文档中提取最佳实践，优化Agent的Prompt

**实施方案**：

1. **分析方法论文档**
   - 提取PRD写作规范和标准
   - 识别关键章节要求
   - 总结写作技巧和注意事项

2. **更新Agent Prompt**
   - **LeadAnalyst**：参考PRD结构规范和问题分析方法
   - **TextGen_CN**：学习真实PRD的写作风格和表达方式
   - **VisionAgent**：参考真实PRD中的流程图和界面图风格
   - **TableAgent**：参考真实PRD中的表格格式和KPI定义方式

3. **领域特定Prompt增强**
   - 为不同领域定制Prompt
   - 提取领域术语和常用表达
   - 参考领域特定PRD的结构模式

**预期效果**：
- 生成PRD更符合行业标准
- 写作风格更专业
- 领域特定内容更准确

---

### 阶段四：领域知识增强（优先级：中）

#### 4.1 提取领域术语库

**目标**：从各领域PRD中提取标准术语，用于术语一致性检查

**实施方案**：

1. **按领域提取术语**
   - 电商：订单、商品、库存、支付、物流等
   - 社交：用户关系、消息、动态、关注等
   - 教育：课程、作业、学习进度、成绩等

2. **建立术语映射表**
   ```json
   {
     "ecommerce": {
       "订单": "order",
       "商品": "product",
       "库存": "inventory",
       ...
     }
   }
   ```

3. **用于双语一致性检查**
   - 确保中文术语与英文术语正确映射
   - 检查术语使用的一致性

#### 4.2 提取领域模式

**目标**：从各领域PRD中提取通用模式，用于生成指导

**实施方案**：

1. **功能模式**：
   - 电商：商品管理、订单管理、支付流程、物流跟踪
   - 社交：用户注册、好友关系、消息推送、内容发布

2. **KPI模式**：
   - 电商：GMV、转化率、复购率、客单价
   - 社交：DAU、MAU、留存率、互动率

3. **风险模式**：
   - 通用：性能风险、安全风险、合规风险
   - 领域特定：电商-库存风险、金融-风控风险

---

### 阶段五：评估与改进（优先级：中）

#### 5.1 建立评估基准

**目标**：从高质量PRD中提取评估标准

**实施方案**：

1. **结构完整性基准**
   - 分析真实PRD的章节覆盖率
   - 建立标准章节列表
   - 用于S_comp指标计算

2. **内容质量基准**
   - 分析真实PRD的内容深度
   - 提取各章节的最小内容要求
   - 用于S_sem指标计算

3. **多模态基准**
   - 分析真实PRD中流程图和界面图的使用
   - 建立多模态内容的评估标准
   - 用于S_mm指标计算

#### 5.2 持续改进

**目标**：基于评估结果持续优化生成质量

**实施方案**：

1. **对比分析**
   - 对比生成PRD与真实PRD的差异
   - 识别常见问题（如缺少章节、内容浅薄等）

2. **Prompt迭代优化**
   - 根据对比结果调整Prompt
   - 增加缺失内容的要求
   - 优化写作风格指导

3. **指标校准**
   - 根据真实PRD的标准校准指标阈值
   - 确保指标评估的准确性

---

## 三、实施优先级

### 🔴 高优先级（立即实施）

1. **数据分类与组织**（1天）
   - 创建目录结构
   - 按类型和质量分类300个文件

2. **提取高质量样本**（1天）
   - 提取48个倒推案例
   - 提取22个大厂案例
   - 转换为JSON格式（优先处理）

3. **建立映射关系**（1天）
   - 将15个Brief与对应领域的高质量PRD建立映射
   - 创建`data/chinese_prds/mapping.json`

4. **Few-shot集成**（2天）
   - 修改LeadAnalyst，支持Few-shot示例
   - 在Prompt中注入相似领域的真实PRD

5. **S_expert指标更新**（1天）
   - 修改指标计算，使用中文PRD作为参考
   - 使用中文sentence-transformers模型

**总计**：约1周

### 🟡 中优先级（后续实施）

6. **数据标准化**（2周）
   - 批量提取和转换所有PRD
   - 建立完整的PRD数据库

7. **Prompt优化**（1周）
   - 分析方法论文档
   - 更新各Agent的Prompt

8. **领域知识提取**（1周）
   - 提取术语库
   - 提取领域模式

**总计**：约1个月

---

## 四、技术实现

### 4.1 数据提取工具

**需要的库**：
```bash
pip install pypdf2 pdfplumber python-docx
```

**提取脚本**：
```python
# scripts/extract_chinese_prd.py
def extract_prd_from_pdf(pdf_path: Path) -> Dict:
    """从PDF提取PRD内容"""
    # 1. 提取文本
    # 2. 识别章节（基于标题、格式）
    # 3. 提取标准章节内容
    # 4. 转换为JSON格式
    pass
```

### 4.2 Few-shot集成

**修改`src/agents/lead_analyst.py`**：
```python
def load_few_shot_examples(domain: str, top_k: int = 2) -> List[Dict]:
    """加载相似领域的真实PRD示例"""
    expert_prds_dir = Path("data/chinese_prds/processed/json")
    # 按domain匹配，选择top_k个高质量样本
    pass

def _build_plan_prompt(self, brief: Dict) -> str:
    # 添加Few-shot示例
    few_shot_examples = load_few_shot_examples(brief.get("domain"))
    prompt = f"""
    以下是真实PRD示例（参考风格和结构）：
    {format_prd_examples(few_shot_examples)}
    
    ...原有prompt...
    """
    return prompt
```

### 4.3 S_expert指标更新

**修改`src/metrics/extended_quality.py`**：
```python
def compute_expert_alignment(prd: Dict, expert_prd_path: Optional[Path] = None) -> Dict[str, float]:
    """计算专家对齐度（支持中文PRD）"""
    if expert_prd_path and expert_prd_path.exists():
        # 使用中文sentence-transformers模型
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # 支持中文
        
        # 计算语义相似度
        content_similarity = compute_semantic_similarity(
            generated_prd, expert_prd, model
        )
    ...
```

---

## 五、预期效果

### 5.1 生成质量提升

- **结构规范性**：生成PRD的结构更接近真实PRD（Few-shot学习）
- **内容深度**：内容更专业、更完整（参考真实PRD标准）
- **领域准确性**：领域术语和模式使用更准确（领域知识增强）

### 5.2 评估准确性提升

- **S_expert指标**：有真实参考标准，评估更准确
- **指标校准**：基于真实PRD标准校准指标阈值
- **问题识别**：能准确识别生成PRD与真实PRD的差距

### 5.3 系统改进方向

- **Prompt优化**：基于真实PRD最佳实践优化Prompt
- **领域定制**：为不同领域定制生成策略
- **持续迭代**：基于评估结果持续改进

---

## 六、下一步行动

### 立即执行（本周）

1. ✅ **分析数据集**（已完成）
2. ⏳ **数据分类**：创建目录结构，分类300个文件
3. ⏳ **提取高质量样本**：提取48个倒推案例和22个大厂案例
4. ⏳ **建立映射关系**：将Brief与真实PRD建立映射
5. ⏳ **Few-shot集成**：修改LeadAnalyst支持Few-shot示例
6. ⏳ **S_expert更新**：使用中文PRD作为参考标准

### 后续执行（下月）

7. ⏳ **批量数据转换**：转换所有PRD为JSON格式
8. ⏳ **Prompt优化**：分析方法论文档，优化Agent Prompt
9. ⏳ **领域知识提取**：提取术语库和领域模式

---

## 七、注意事项

### 7.1 数据处理

- **格式问题**：PDF/DOC格式多样，需要处理各种格式
- **编码问题**：注意中文编码（UTF-8）
- **噪声处理**：去除水印、页眉页脚等

### 7.2 质量控制

- **优先使用高质量样本**：倒推案例、大厂案例
- **确保相关性**：Few-shot示例要与Brief相关
- **定期更新**：随着数据增加，持续更新映射关系

### 7.3 知识产权

- **使用范围**：仅用于研究和实验
- **引用来源**：在论文中引用数据来源
- **遵守许可**：遵守原始数据的许可要求

---

## 八、总结

这300份真实中文PRD数据是**非常宝贵的资源**，可以：

1. **提升生成质量**：Few-shot学习、领域知识增强
2. **改进评估准确性**：S_expert指标有真实参考标准
3. **优化系统设计**：基于真实PRD最佳实践优化Prompt和架构

**建议优先实施**：
- 数据分类与组织
- 提取高质量样本（倒推案例、大厂案例）
- Few-shot集成
- S_expert指标更新

这些工作可以在**1周内完成**，并立即提升系统生成质量！


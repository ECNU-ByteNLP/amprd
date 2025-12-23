# 评价指标与对比逻辑分析

## 一、评价指标是如何得到的？

### 1.1 当前指标计算方式（自包含，无参考）

**重要发现**：当前所有指标都是**自包含计算**，即只基于生成的PRD本身，**没有参考PRD或专家PRD**。

#### 基础指标（5个）

1. **S_comp（结构完整度）**：检查是否包含所有标准章节
   - 方法：统计已生成章节数 / 标准章节数
   - 参考：无，仅检查是否有内容

2. **S_mm（跨模态一致性）**：检查文本与图表引用是否一致
   - 方法：检查anchors中的ref_id是否在assets_manifest中存在
   - 参考：无，仅检查内部引用完整性

3. **S_tab（表格一致性）**：检查表格是否有有效行
   - 方法：统计有效行数 / 总行数
   - 参考：无，仅检查表格格式

4. **S_bi（双语一致性）**：检查中英文内容长度是否接近
   - 方法：计算中英文词数差异比例
   - 问题：**中英文词数天然不同**（中文词短，英文词长），导致指标偏低
   - 参考：无，仅基于词数差异

5. **S_var（稳定性）**：检查多次生成结果的方差
   - 方法：计算多次运行的标准差
   - 参考：无，仅基于重复生成结果

#### 扩展指标（8个）

6. **S_sem（语义质量）**：检查问题陈述、需求可执行性、术语一致性
   - 方法：关键词匹配（如"问题"、"验收"等）
   - 参考：无，仅基于关键词检测

7. **S_biz（业务对齐度）**：检查goal与KPI一致性
   - 方法：检查overview中的关键词是否在KPI表格中出现
   - 参考：无，仅检查内部一致性

8. **S_tech（技术可行性）**：检查是否包含技术关键词
   - 方法：关键词匹配（如"性能"、"架构"等）
   - 参考：无，仅基于关键词检测

9. **S_risk（风险识别）**：检查是否包含风险关键词
   - 方法：关键词匹配（如"风险"、"缓解"等）
   - 参考：无，仅基于关键词检测

10. **S_expert（专家对齐度）**：**唯一需要参考PRD的指标**
    - 方法：如果提供了`expert_prd_path`，使用sentence-transformers计算语义相似度
    - 参考：需要提供专家PRD文件（**当前未使用**）
    - 问题：**当前没有专家PRD数据**，S_expert实际上只计算了结构相似度

11. **S_ps（问题-解决方案分离度）**：检查问题陈述与解决方案是否分离
    - 方法：检查plan中的problem_space和solution_space
    - 参考：无，仅基于内部结构

12. **S_uj（用户旅程完整性）**：检查用户旅程描述是否完整
    - 方法：检查user_flows章节是否存在且包含流程步骤
    - 参考：无，仅检查结构完整性

13. **S_hyp（假设验证度）**：检查是否包含假设验证
    - 方法：检查是否包含"假设"、"假设验证"等关键词
    - 参考：无，仅基于关键词检测

### 1.2 指标计算的问题

#### 问题1：S_bi（双语一致性）计算不准确

**当前方法**：
```python
zh = len(zh_text.split())  # 中文按空格分词（错误）
en = len(en_text.split())  # 英文按空格分词
diffs.append(abs(zh - en) / max(zh, en))
```

**问题**：
- 中文按空格分词会严重低估词数（中文词之间没有空格）
- 中英文词数天然不同（中文词短，英文词长）
- 导致S_bi指标普遍偏低（当前平均值0.106）

**正确方法**：
1. 使用中文分词工具（如jieba）进行中文分词
2. 或使用字符数对比（更公平）
3. 或使用语义相似度（更准确，但需要模型）

#### 问题2：缺少真实参考标准

**当前状态**：
- 所有指标都是自包含计算，没有参考标准
- S_expert指标虽然支持参考PRD，但**没有提供专家PRD数据**
- 无法评估生成质量与真实PRD的差距

**需要的参考标准**：
1. **专家PRD**：人类产品经理撰写的PRD（用于S_expert）
2. **基线系统PRD**：简单系统生成的PRD（用于对比实验）
3. **人工评估**：产品经理对生成PRD的评分（用于验证自动指标）

---

## 二、关于"12个真实PRD"的说明

### 2.1 当前状态

**您提到的"12个真实PRD"**指的是：
- **生成的PRD**（`results/full_system/prd_*.json`）
- **不是**专家PRD或真实PRD
- 这些是**系统生成的输出**，不是参考标准

### 2.2 对比逻辑应该是

#### 当前对比逻辑（快速实验）

```
生成的PRD（12个）
  ↓
计算指标（自包含）
  ↓
显示平均指标
```

**问题**：没有对比对象，无法评估改进效果

#### 正确的对比逻辑应该是

```
方案A：与基线系统对比（推荐）
  基线系统PRD（12个）
    ↓
  完整系统PRD（12个）
    ↓
  对比指标（Wilcoxon检验）

方案B：与专家PRD对比（可选）
  专家PRD（12个）
    ↓
  完整系统PRD（12个）
    ↓
  计算S_expert指标（语义相似度）

方案C：人工评估（可选）
  生成的PRD（12个）
    ↓
  产品经理评分（1-7分）
    ↓
  与自动指标对比
```

---

## 三、系统存在的问题

### 3.1 当前发现的问题

#### 🔴 严重问题

1. **双语一致性（S_bi）严重不足**
   - 当前平均值：**0.106**
   - 原因：计算方法不准确（中文分词问题）
   - 影响：无法准确评估双语对齐质量

2. **缺少专家PRD数据**
   - S_expert指标无法正确计算
   - 无法评估与真实PRD的差距

#### 🟡 中等问题

3. **指标计算依赖关键词匹配**
   - S_sem、S_biz、S_tech、S_risk都基于关键词匹配
   - 容易误判（缺少关键词不一定质量差）

4. **缺少基线系统对比**
   - 无法评估系统改进效果
   - 无法证明多智能体系统的优势

### 3.2 应该先完善的问题

#### 优先级1：修复S_bi计算（必须）

**问题**：当前S_bi=0.106，无法准确评估双语一致性

**修复方案**：
```python
# 方案A：使用中文分词工具
import jieba

zh_words = list(jieba.cut(zh_text))  # 中文分词
en_words = en_text.split()  # 英文分词
diffs.append(abs(len(zh_words) - len(en_words)) / max(len(zh_words), len(en_words)))

# 方案B：使用字符数对比（更公平）
zh_chars = len(zh_text.replace(' ', ''))
en_chars = len(en_text.replace(' ', ''))
diffs.append(abs(zh_chars - en_chars) / max(zh_chars, en_chars))

# 方案C：使用语义相似度（最准确，但需要模型）
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
sim = model.encode([zh_text, en_text])
similarity = cosine_similarity(sim[0], sim[1])
```

**建议**：使用方案A（jieba分词），最简单且有效

#### 优先级2：运行基线系统对比（必须）

**目的**：证明多智能体系统的优势

**步骤**：
1. 使用相同Brief生成基线系统PRD
2. 计算基线系统指标
3. 与完整系统对比
4. 进行统计检验（Wilcoxon）

**时间**：15-30分钟

#### 优先级3：收集专家PRD（可选）

**目的**：用于S_expert指标计算

**方法**：
1. 邀请产品经理撰写12个PRD（对应12个Brief）
2. 保存到`data/expert_prds/`目录
3. 在计算指标时提供`expert_prd_path`

**时间**：需要人工参与，时间较长

---

## 四、对比逻辑的正确理解

### 4.1 当前快速实验的对比逻辑

**实际上没有对比**，只是：
1. 生成12个PRD
2. 计算指标
3. 显示平均指标

**这不是对比实验**，只是系统验证。

### 4.2 正确的对比实验应该是

#### 实验1：完整系统 vs 基线系统

```
输入：15个Brief
  ↓
基线系统（TextOnly）生成15个PRD
  ↓
完整系统（MultiAgent）生成15个PRD
  ↓
对比指标：
  - 完整系统平均指标 vs 基线系统平均指标
  - Wilcoxon检验（p值）
  - Cliff's δ（效应量）
  - Bootstrap CI（置信区间）
```

**预期结果**：
- 完整系统的S_comp、S_mm、S_bi等指标应该显著高于基线系统
- 统计检验应该显示显著性（p < 0.05）

#### 实验2：消融实验

```
输入：15个Brief
  ↓
完整系统（full_system）
  ↓
消融系统（no_alignment, no_vision, no_table等）
  ↓
对比指标：各消融配置与完整系统的差异
```

**预期结果**：
- no_alignment的S_bi应该显著低于full_system
- no_vision的S_mm应该显著低于full_system

#### 实验3：与专家PRD对比（可选）

```
输入：15个Brief
  ↓
专家PRD（15个，人工撰写）
  ↓
完整系统PRD（15个）
  ↓
计算S_expert指标（语义相似度）
```

**预期结果**：
- S_expert平均值应该在0.6-0.8之间（较好的相似度）

---

## 五、建议的行动计划

### 5.1 立即修复（优先级最高）

#### 步骤1：修复S_bi计算（10分钟）

```python
# 修改 src/metrics/quality.py
import jieba

def compute_bilingual_consistency(prd: Dict) -> float:
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    diffs = []
    for section in sections:
        content = section.get("content", {})
        zh_text = content.get("zh-CN") or ""
        en_text = content.get("en-US") or ""
        
        if "[mock" in zh_text.lower() or "[mock" in en_text.lower():
            continue
        
        # 修复：使用jieba进行中文分词
        zh_words = list(jieba.cut(zh_text))
        en_words = en_text.split()
        
        if len(zh_words) == 0 or len(en_words) == 0:
            diffs.append(1.0)
        else:
            # 使用词数比例差异
            diff = abs(len(zh_words) - len(en_words)) / max(len(zh_words), len(en_words))
            diffs.append(diff)
    
    if not diffs:
        return 0.0
    avg_diff = sum(diffs) / len(diffs)
    return round(max(0.0, 1.0 - avg_diff), 4)
```

**验证**：
```bash
# 重新计算指标
python scripts/quick_start_experiment.py
# 检查S_bi是否提升（应该从0.106提升到0.5+）
```

#### 步骤2：运行基线系统对比（30分钟）

```bash
# 生成基线系统PRD
python scripts/run_baseline_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results/baseline \
    --baseline-type text_only

# 对比指标
python scripts/compare_baseline.py \
    --baseline-dir results/baseline_text_only \
    --ours-dir results/full_system \
    --output reports/baseline_comparison.json
```

### 5.2 后续优化（优先级中）

#### 步骤3：改进指标计算（可选）

- 使用语义相似度替代关键词匹配
- 使用更准确的语义评估模型

#### 步骤4：收集专家PRD（可选）

- 邀请产品经理撰写PRD
- 计算S_expert指标

---

## 六、总结

### 6.1 当前状态

1. **指标计算方式**：自包含计算，无参考PRD
2. **对比逻辑**：**实际上没有对比**，只是系统验证
3. **系统问题**：S_bi计算不准确（0.106），双语一致性无法评估

### 6.2 正确理解

1. **"12个真实PRD"**：实际上是**生成的PRD**，不是参考标准
2. **对比实验**：应该是**完整系统 vs 基线系统**，不是与专家PRD对比
3. **专家PRD**：可选，用于S_expert指标（当前未使用）

### 6.3 建议行动

1. **立即修复**：S_bi计算问题（10分钟）
2. **运行对比**：基线系统 vs 完整系统（30分钟）
3. **后续优化**：收集专家PRD、改进指标计算（可选）

---

## 七、参考文档

- [实验步骤详解](experiment_steps.md)
- [基线系统说明](baselines.md)
- [指标计算代码](../src/metrics/quality.py)
- [扩展指标计算代码](../src/metrics/extended_quality.py)


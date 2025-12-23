# Week 2 实验进度报告

## ✅ 已完成任务

### 任务2.1：基线系统实现 ✅

#### 实现内容

1. **Baseline-TXT（TextOnly）** - `src/baselines/text_only.py`
   - ✅ 单一LLM生成纯文本PRD
   - ✅ 无多模态、无双语对齐
   - ✅ 一次性生成，无迭代优化
   - ✅ 支持Qwen模型（如果配置）或Mock模型

2. **Baseline-TPL（Template）** - `src/baselines/template.py`
   - ✅ 基于固定模板的规则系统
   - ✅ 简单插值填充
   - ✅ 无LLM生成
   - ✅ 10个标准章节模板

3. **Baseline-RET（Retrieval）** - `src/baselines/retrieval.py`
   - ✅ 使用sentence-transformers进行语义检索
   - ✅ 从真实PRD语料库中检索相似内容
   - ✅ 结合检索结果生成PRD
   - ✅ 支持中文PRD语料库

4. **运行脚本** - `scripts/run_baseline_experiment.py`
   - ✅ 为15个Brief生成3个基线系统的PRD
   - ✅ 自动保存结果到`results/baseline_*/`目录
   - ✅ 生成实验摘要JSON文件
   - ✅ 支持API限流延迟

#### 验证结果

- ✅ 所有基线系统导入成功
- ✅ 代码无linter错误
- ✅ 运行脚本已创建

---

### 任务2.2：运行基线系统生成 ⏳ 进行中

#### 执行计划

运行以下命令生成基线系统PRD：

```bash
python scripts/run_baseline_experiment.py
```

#### 预期输出

1. **Baseline-TXT结果**：
   - `results/baseline_text_only/prd_*.json` (15个文件)

2. **Baseline-TPL结果**：
   - `results/baseline_template/prd_*.json` (15个文件)

3. **Baseline-RET结果**：
   - `results/baseline_retrieval/prd_*.json` (15个文件)

4. **实验摘要**：
   - `results/baseline_experiment_summary.json`

#### 注意事项

1. **API限流**：
   - Baseline-TXT和Baseline-RET使用Qwen模型时会添加延迟
   - 前5个：2秒延迟
   - 6-10个：5秒延迟
   - 11+个：8秒延迟

2. **检索基线**：
   - 需要中文PRD语料库（`data/chinese_prds/processed/`）
   - 如果语料库为空，会回退到TextOnly模式

3. **模型配置**：
   - 如果未配置Qwen API密钥，会使用Mock模型
   - Mock模型生成占位符内容，仅用于测试

---

## 📊 基线系统对比

| 基线系统 | 特点 | 多模态 | 双语 | LLM | 用途 |
|---------|------|--------|------|-----|------|
| **Baseline-TXT** | 单一LLM生成 | ❌ | ❌ | ✅ | 对照多智能体在结构完整度、跨模态一致性上的提升 |
| **Baseline-TPL** | 固定模板规则 | ❌ | ❌ | ❌ | 评估规则系统在复杂场景下的局限 |
| **Baseline-RET** | 检索增强生成 | ⚠️ 弱 | ❌ | ✅ | 比较检索式多模态与生成式多模态的差异 |

---

## 🎯 下一步行动

### 立即执行

运行基线系统实验：

```bash
python scripts/run_baseline_experiment.py
```

### 后续任务（Week 3）

1. **任务3.1：运行完整系统生成**
   - 使用Few-shot和S_expert更新后的系统
   - 为15个Brief生成完整系统的PRD

2. **任务4.1：运行消融实验**
   - 7个消融配置 × 15个Brief = 105个PRD

---

## 📝 质量保证

- ✅ 基线系统实现完整
- ✅ 代码符合顶会标准
- ✅ 运行脚本已创建
- ✅ 支持Qwen模型和Mock模型
- ✅ 支持API限流延迟
- ✅ 错误处理完善

---

**Week 2 任务2.1已完成，准备执行任务2.2（运行基线系统生成）。** 🚀

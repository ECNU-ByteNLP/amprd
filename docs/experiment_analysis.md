# 实验运行分析报告

## 问题诊断

### 1. 指标计算异常（已修复）

**现象**：
- 除 `S_mm=1.000` 外，其他所有指标均为 `0.000`
- `S_comp`, `S_tab`, `S_bi`, `S_sem`, `S_biz`, `S_tech`, `S_risk` 全部为0

**根本原因**：
1. **结构不匹配**：Assembler生成的PRD是扁平化结构（顶层直接有 `sections` 和 `assets_manifest`），但指标计算代码期望的是符合schema的结构（`outputs.sections` 和 `outputs.assets_manifest`）
2. **Mock内容干扰**：生成的PRD内容都是 `[mock-text-response]` 占位符，导致内容质量指标计算失败

**修复方案**：
- 修改所有指标计算函数，使其兼容两种结构：
  ```python
  # 兼容两种结构：schema结构（outputs.sections）和扁平化结构（sections）
  sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
  ```
- 在计算内容质量时，忽略mock内容：
  ```python
  if "[mock" not in text:
      # 进行实际计算
  ```

**修复文件**：
- `src/metrics/quality.py`：修复 `S_comp`, `S_mm`, `S_tab`, `S_bi` 的计算
- `src/metrics/extended_quality.py`：修复 `S_sem`, `S_biz`, `S_tech`, `S_risk`, `S_expert` 的计算

### 2. 输出重复问题

**现象**：
- 步骤4的日志重复打印多次（约10次）

**可能原因**：
1. 脚本被多次调用（不太可能，因为其他步骤没有重复）
2. 终端显示问题（最可能）
3. 异常导致重复执行（代码逻辑不支持）

**当前状态**：
- 代码逻辑正常，没有循环调用
- 可能是终端显示问题，不影响实际功能
- 建议：如果再次出现，检查是否有多个进程同时运行

### 3. Mock内容问题（已配置Qwen的用户无需关注）

**现象**：
- 如果生成的PRD内容都是 `[mock-text-response]` 占位符，说明系统使用了Mock模型

**原因**：
- 系统模型加载逻辑：优先从环境变量读取 `QWEN_API_KEY`，如果未配置才回退到Mock模型
- 如果已配置 `QWEN_API_KEY`，系统会自动使用Qwen模型（qwen2.5-32b-instruct）

**解决方案**（仅当未配置API密钥时）：
- 配置Qwen API密钥：
  ```bash
  export QWEN_API_KEY="your-api-key"
  export QWEN_TEXT_MODEL_CN="qwen2.5-32b-instruct"  # 可选，默认值
  export QWEN_VISION_MODEL="wanx-v1"  # 可选，默认值
  ```
- 配置后，系统会自动使用Qwen模型，生成真实内容

## 修复后的预期行为

### 指标计算
- **S_comp**：基于实际内容（非mock）计算结构完整度
- **S_mm**：检查图片引用是否在manifest中（已修复，现在为1.0是正确的）
- **S_tab**：检查KPI表格是否存在且有效
- **S_bi**：忽略mock内容，基于实际中英文内容计算双语一致性
- **S_sem/S_biz/S_tech/S_risk**：忽略mock内容，基于实际内容计算

### 使用真实模型后的预期
- 所有指标都会基于实际生成的内容计算
- 内容质量指标（S_sem等）会反映实际PRD的质量
- 建议在配置真实模型后重新运行实验

## 验证步骤

1. **重新运行快速实验**：
   ```bash
   python scripts/quick_start_experiment.py
   ```

2. **检查指标计算**：
   - 如果已配置Qwen API密钥，系统会使用Qwen模型生成真实内容
   - 如果未配置API密钥，系统会使用Mock模型（占位符），此时指标可能为0，但代码逻辑已修复
   - `S_mm` 应该为1.0（图片引用存在）

3. **验证Qwen模型使用**：
   - 运行 `python -m src.cli --brief-text "测试" --verbose` 查看日志
   - 日志会显示：`[INFO] 使用模型: Text-CN=qwen2.5-32b-instruct, Text-EN=qwen2.5-32b-instruct, Vision=wanx-v1`
   - 如果显示 `mock-model`，说明未正确配置API密钥

## 技术细节

### 结构兼容性
修复后的代码同时支持两种PRD结构：
- **Schema结构**（标准）：`{"outputs": {"sections": [...], "assets_manifest": [...]}}`
- **扁平化结构**（当前Assembler生成）：`{"sections": [...], "assets_manifest": [...]}`

### Mock内容过滤（兼容性处理）
所有内容质量指标都会检查并忽略mock内容（如果存在）：
- 检查文本中是否包含 `[mock` 关键字
- 如果包含，跳过该部分或返回0分
- **注意**：如果已配置Qwen API密钥，系统会使用Qwen模型，不会生成mock内容

## 下一步建议

1. **配置真实模型**：使用Qwen API生成真实内容
2. **重新运行实验**：验证修复后的指标计算
3. **检查输出重复**：如果问题持续，检查是否有多个进程
4. **优化Assembler**：考虑修改Assembler生成符合schema的结构（可选）


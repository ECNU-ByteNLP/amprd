# PRD JSON 导出为 DOCX 文档指南

## 📝 功能说明

系统已支持将生成的PRD JSON文件批量导出为DOCX格式文档。

## 🔧 前置要求

### 1. 安装 python-docx 模块

```bash
pip install python-docx>=0.8.11
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

## 🚀 使用方法

### 批量导出（推荐）

批量导出目录中的所有PRD JSON文件：

```bash
# 导出完整系统的所有成功PRD为双语DOCX
python scripts/export_prds_to_docx.py \
  --input results/full_system \
  --output results/full_system_docx \
  --from-metrics results/full_system/metrics_summary.json

# 导出为仅中文DOCX
python scripts/export_prds_to_docx.py \
  --input results/full_system \
  --output results/full_system_docx \
  --language zh \
  --from-metrics results/full_system/metrics_summary.json

# 导出为仅英文DOCX
python scripts/export_prds_to_docx.py \
  --input results/full_system \
  --output results/full_system_docx \
  --language en \
  --from-metrics results/full_system/metrics_summary.json

# 导出所有PRD（不指定--from-metrics）
python scripts/export_prds_to_docx.py \
  --input results/full_system \
  --output results/full_system_docx \
  --language zh
```

### 单个PRD导出

如果只需要导出单个PRD：

```bash
python -m src.cli_export \
  --input results/full_system/prd_general_google_search_algorithm_update.json \
  --output results/full_system_docx/general_google_search_algorithm_update_zh.docx \
  --format docx \
  --language zh
```

## 📋 参数说明

### 批量导出脚本参数

- `--input`: 输入目录（包含PRD JSON文件），必需
- `--output`: 输出目录（DOCX文件将保存在此处），必需
- `--language`: 输出语言（可选，默认：`auto`）
  - `auto`: 双语（中文+英文）
  - `zh`: 仅中文
  - `en`: 仅英文
- `--from-metrics`: 从 `metrics_summary.json` 中读取成功的PRD ID列表，仅导出这些PRD（可选）
- `--overwrite`: 覆盖已存在的文件（默认：跳过已存在的文件）

### 单个导出脚本参数

- `--input`: 输入PRD JSON文件路径，必需
- `--output`: 输出DOCX文件路径，必需
- `--format`: 导出格式（`markdown` 或 `docx`），默认：`markdown`
- `--language`: 输出语言（`auto`、`zh`、`en`），默认：`auto`

## 📁 输出文件格式

导出的DOCX文件名格式：
- 双语：`{prd_id}_zh_en.docx`
- 仅中文：`{prd_id}_zh.docx`
- 仅英文：`{prd_id}_en.docx`

例如：
- `general_google_search_algorithm_update_zh.docx`
- `general_google_search_algorithm_update_zh_en.docx`
- `general_google_search_algorithm_update_en.docx`

## ✨ 功能特性

1. **批量导出**：支持目录下所有PRD JSON批量导出
2. **语言选择**：支持双语、仅中文、仅英文三种模式
3. **智能过滤**：可从 `metrics_summary.json` 读取成功PRD列表，仅导出成功的
4. **自动创建目录**：输出目录不存在时自动创建
5. **跳过已存在**：默认跳过已存在的文件，避免重复生成
6. **支持表格**：自动导出表格（格式化为Word表格）
7. **支持图片**：自动插入图片（如果路径存在）
8. **中文友好**：使用微软雅黑字体，确保中文显示正常

## 📊 导出内容

DOCX文档包含：
1. **元数据**：
   - PRD ID
   - 生成时间
   - 领域（domain）

2. **章节内容**：
   - 所有章节的文本内容（根据语言选择）
   - 表格（自动格式化为Word表格）
   - 图片（如果路径存在）

3. **格式**：
   - 标题层级（Heading 1, Heading 2等）
   - 段落格式（中文使用微软雅黑）
   - 表格样式（Light Grid）

## ⚠️ 注意事项

1. **安装依赖**：确保已安装 `python-docx>=0.8.11`
   ```bash
   pip install python-docx>=0.8.11
   ```

2. **图片路径**：
   - 如果PRD JSON中的图片路径是相对路径，确保相对路径正确
   - 如果图片不存在，会显示占位文本 `[未找到图片]`

3. **文件覆盖**：
   - 默认不会覆盖已存在的文件
   - 如需覆盖，使用 `--overwrite` 参数

4. **路径问题**：
   - 输出目录可以是相对路径或绝对路径
   - 脚本会自动转换为绝对路径

## 🔍 示例输出

运行批量导出后，输出示例：

```
📋 从 metrics_summary.json 中读取到 9 个成功的PRD ID

📋 找到 9 个PRD JSON文件
📂 输入目录: results\full_system
📂 输出目录: results\full_system_docx
🌐 输出语言: zh

[1/9] 处理: prd_general_google_search_algorithm_update.json... ✅ general_google_search_algorithm_update_zh.docx
[2/9] 处理: prd_general_dropbox_real_time_collaboration.json... ✅ general_dropbox_real_time_collaboration_zh.docx
...

======================================================================
批量导出完成！
======================================================================
✅ 成功: 9/9
📁 输出目录: results\full_system_docx
📝 导出结果已保存: results\full_system_docx\export_results.json
```

## 📚 相关文档

- 系统使用指南：`docs/system_guide.md`
- PRD Schema说明：`docs/schema_overview.md`
- 导出功能源码：`src/exporters/prd_renderer.py`
- 批量导出脚本：`scripts/export_prds_to_docx.py`


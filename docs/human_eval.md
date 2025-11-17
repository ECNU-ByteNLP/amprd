# 人工评测方案

## 评测设置

- 角色：PM、研发、QA 各 ≥5 人。
- 样本：每领域选取 ≥15 对（基线 vs 多智能体），确保跨平台覆盖。
- 维度（Likert 1–7）：
  - `usability` 可执行性；
  - `ambiguity` 歧义率（反向题，可取 7-评分）；
  - `multimodal_alignment` 跨模态一致性；
  - `bilingual_alignment` 双语一致性；
  - `overall` 总体可用性。

## 工具链

- `src/evaluation/human_eval.py`
  - `create_eval_tasks`：生成评测任务 JSON。
  - `load_results`：读取标注 CSV。
  - `krippendorff_alpha`：计算 IAA。
  - `summarize_results`：统计平均分。

## 流程

1. 使用 `create_eval_tasks` 生成任务清单并分配给评测者。
2. 评测者在独立界面填写 CSV（字段：`prd_path,rater_id,dimension,score`）。
3. 汇总 CSV，运行：
   ```python
   from pathlib import Path
   from src.evaluation.human_eval import load_results, krippendorff_alpha

   results = load_results(Path("human_eval/results.csv"))
   alpha = krippendorff_alpha(results, dimension="overall")
   print("Krippendorff α:", alpha)
   ```
4. 将评测平均分与自动指标报表合并，供论文撰写与分析。

## 注意事项

- 采用双盲：评测者不知样本来源（基线或多智能体）。
- 保证任务随机顺序，避免顺序效应。
- 记录评测时间，后续用于效率分析。 


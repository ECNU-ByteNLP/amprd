# 剩余消融实验命令

## 当前进度总结

**已完成 (61/105 PRD, 58.1%)**：
- ✅ full_system: 15/15 (100%)
- ✅ no_vision: 15/15 (100%)
- ✅ no_table: 15/15 (100%)

**进行中/待完成 (剩余44个PRD)**：
- 🔄 no_alignment: 1/15 (还需14个)
- 🔄 no_consistency: 14/15 (还需1个) - **优先完成，只剩1个**
- 🔄 async_queue: 1/15 (还需14个)
- ⏳ mock_model: 0/15 (还需15个)

**预计剩余时间**: 约11小时

---

## 需要运行的命令（按优先级）

### 优先级1：快速完成（1个PRD）

```bash
# no_consistency - 完成最后一个PRD（约15分钟）
python scripts/run_ablation_single_config.py --config no_consistency
```

### 优先级2：完成已开始的配置（各14个PRD）

```bash
# no_alignment - 完成剩余14个Brief（约3.5小时）
python scripts/run_ablation_single_config.py --config no_alignment

# async_queue - 完成剩余14个Brief（约3.5小时）
python scripts/run_ablation_single_config.py --config async_queue
```

### 优先级3：可选的Mock模型配置（15个PRD）

```bash
# mock_model - 如果需要验证模型重要性（约3.75小时）
python scripts/run_ablation_single_config.py --config mock_model
```

---

## 推荐执行顺序

### 方案1：顺序执行（稳定，推荐）

```bash
# 1. 先完成no_consistency（1个PRD，最快）
python scripts/run_ablation_single_config.py --config no_consistency

# 2. 然后完成no_alignment（14个PRD）
python scripts/run_ablation_single_config.py --config no_alignment

# 3. 最后完成async_queue（14个PRD）
python scripts/run_ablation_single_config.py --config async_queue

# 4. （可选）运行mock_model（15个PRD）
python scripts/run_ablation_single_config.py --config mock_model
```

### 方案2：并行执行（更快，需要2个终端）

**终端1：**
```bash
python scripts/run_ablation_single_config.py --config no_alignment
```

**终端2：**
```bash
python scripts/run_ablation_single_config.py --config async_queue
```

等两个都完成后，再运行：
```bash
python scripts/run_ablation_single_config.py --config no_consistency
```

---

## 检查进度

随时检查进度：
```bash
python scripts/check_ablation_progress.py
```

---

## 预计完成时间

如果按顺序执行：
- no_consistency: ~15分钟（1个PRD）
- no_alignment: ~3.5小时（14个PRD）
- async_queue: ~3.5小时（14个PRD）
- **总计**: 约7.5小时

如果并行执行no_alignment和async_queue：
- 并行部分: ~3.5小时（两个同时进行）
- no_consistency: ~15分钟
- **总计**: 约3.75小时

---

## 注意事项

1. **脚本会自动跳过已完成的Brief**，重新运行命令不会重复生成
2. **如果中断**，重新运行相同命令即可继续
3. **建议定期运行进度检查**：`python scripts/check_ablation_progress.py`


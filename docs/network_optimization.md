# 网络优化与超时问题解决方案

## 问题描述

在批量生成PRD时，可能会遇到以下网络问题：
- `Read timed out. (read timeout=60)`: 请求超时
- `SSLZeroReturnError`: SSL连接被关闭
- `Max retries exceeded`: 达到最大重试次数

## 已实施的优化

### 1. 增加超时时间

- **文本生成**：从60秒增加到120秒（大模型如qwen3-max自动使用180秒）
- **图像生成**：从120秒增加到180秒

### 2. 自动重试机制

- **重试次数**：默认3次
- **重试策略**：指数退避（2秒、4秒、8秒）
- **重试条件**：超时、SSL错误、网络错误

### 3. 批量处理延迟

- **延迟时间**：每个PRD之间延迟2秒
- **目的**：避免API限流和网络拥塞

### 4. 错误处理优化

- 单个PRD失败不影响其他PRD
- 详细的错误日志
- 继续处理剩余PRD

## 使用建议

### 方案1：分批处理（推荐）

如果网络不稳定，建议分批处理：

```python
# 只处理前5个
python -c "
from pathlib import Path
from src.data.benchmark_builder import BenchmarkBuilder
from src.pipeline import MultiAgentOrchestrator

builder = BenchmarkBuilder(Path('data/benchmark'))
prds = builder.list_prds()[:5]  # 只处理前5个

orchestrator = MultiAgentOrchestrator(persist_dir=Path('results/full_system'))
for prd_info in prds:
    brief = builder.load_brief(prd_info['prd_id'])
    orchestrator.run({'brief': brief})
"
```

### 方案2：增加延迟

如果仍然遇到超时，可以增加延迟时间：

修改 `scripts/quick_start_experiment.py` 中的延迟：
```python
delay = 5.0  # 增加到5秒
```

### 方案3：使用环境变量配置

可以通过环境变量调整超时和重试：

```bash
# 增加超时时间（秒）
export QWEN_TIMEOUT=300

# 增加重试次数
export QWEN_MAX_RETRIES=5
```

### 方案4：检查网络连接

1. **测试API连接**：
   ```bash
   curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
     -H "Authorization: Bearer $QWEN_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"qwen2.5-32b-instruct","messages":[{"role":"user","content":"test"}]}'
   ```

2. **检查代理设置**：
   - 如果使用代理，确保代理配置正确
   - 可以设置 `HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量

3. **检查防火墙**：
   - 确保防火墙允许访问 `dashscope.aliyuncs.com`

## 故障排查

### 问题1：所有请求都超时

**可能原因**：
- 网络连接不稳定
- API服务器负载过高
- 防火墙阻止连接

**解决方案**：
1. 检查网络连接
2. 增加超时时间到300秒
3. 减少并发请求（分批处理）

### 问题2：部分请求成功，部分失败

**可能原因**：
- 网络波动
- API限流

**解决方案**：
1. 增加延迟时间（5-10秒）
2. 使用重试机制（已自动启用）
3. 失败后单独重试失败的PRD

### 问题3：SSL错误

**可能原因**：
- SSL证书问题
- 代理配置问题

**解决方案**：
1. 更新Python和requests库
2. 检查代理设置
3. 禁用SSL验证（不推荐，仅用于测试）

## 性能优化建议

### 1. 使用更小的模型（如果质量可接受）

```bash
# 使用较小的模型，响应更快
export QWEN_TEXT_MODEL_CN="qwen2.5-7b-instruct"
export QWEN_TEXT_MODEL_EN="qwen2.5-7b-instruct"
```

### 2. 减少生成内容

- 可以禁用某些Agent（如VisionAgent）来减少API调用
- 使用 `--disabled-agents` 参数

### 3. 缓存结果

- 已生成的PRD不会重新生成
- 可以手动删除失败的PRD文件后重试

## 监控和日志

系统会自动记录：
- 每个API调用的耗时
- 重试次数和原因
- 失败的具体错误信息

查看日志：
```bash
# 查看详细日志
python scripts/quick_start_experiment.py 2>&1 | tee experiment.log
```

## 最佳实践

1. **首次运行**：先测试1-2个PRD，确认网络正常
2. **批量运行**：使用默认的2秒延迟
3. **网络不稳定时**：增加延迟到5-10秒
4. **失败处理**：记录失败的PRD ID，单独重试

## 参考

- [Qwen API文档](https://help.aliyun.com/zh/model-studio/)
- [requests库超时设置](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts)


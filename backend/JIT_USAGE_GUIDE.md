# JIT 编译使用指南

## 一、设备分析总结

### 您的设备信息
- **GPU**: NVIDIA GeForce RTX 2050
- **显存**: 4 GB
- **CUDA**: 12.4
- **结论**: ✅ **适合使用 JIT 编译**

### 为什么适合 JIT？
1. ✅ JIT 不会显著增加显存占用
2. ✅ 可以带来 10-30% 的性能提升
3. ✅ 配置简单，无需额外依赖
4. ✅ 与现有代码兼容

### 为什么不推荐 TensorRT？
1. ❌ 显存不足（4GB 太小）
2. ❌ 配置复杂
3. ❌ 收益不明显（入门级 GPU）

## 二、JIT 编译原理

### 什么是 JIT？
**JIT (Just-In-Time) 编译** 是 PyTorch 的即时编译技术，将 Python 模型转换为优化的 TorchScript 格式。

### JIT 工作原理
```
PyTorch 模型 → TorchScript 转换 → 图优化 → 即时编译 → 高效推理
```

**优化内容：**
1. **算子融合**: 将多个操作合并为一个
2. **常量折叠**: 预计算常量表达式
3. **内存优化**: 减少中间变量
4. **减少 Python 开销**: 避免解释器调用

### 性能提升
- **推理速度**: 提升 10-30%
- **显存占用**: 基本不变（可能略有减少）
- **首次加载**: 稍慢（需要加载 JIT 模型）
- **后续推理**: 明显加快

## 三、使用步骤

### 步骤 1：导出 JIT 模型

**方法 1：使用提供的脚本（推荐）**
```bash
cd E:\MagicMirror\backend
python export_jit_model.py
```

**方法 2：使用 CosyVoice 官方脚本**
```bash
cd E:\MagicMirror\backend\Cosy\cosyvoice\bin
python export_jit.py --model_dir ../../Model/CosyVoice2-0.5B
```

**导出过程：**
- 会生成两个文件：
  - `flow.encoder.fp32.zip` (FP32 版本)
  - `flow.encoder.fp16.zip` (FP16 版本，推荐使用)
- 导出时间：约 5-10 分钟（取决于 GPU 性能）

### 步骤 2：修改代码启用 JIT

**修改 `backend/TTS.py`：**

找到第 57 行：
```python
self.cosyvoice = CosyVoice2(model_path, load_jit=False, load_trt=False, fp16=True)
```

改为：
```python
self.cosyvoice = CosyVoice2(model_path, load_jit=True, load_trt=False, fp16=True)
```

**说明：**
- `load_jit=True`: 启用 JIT 编译
- `fp16=True`: 使用 FP16 半精度（已启用）
- 系统会自动加载 `flow.encoder.fp16.zip`（因为 `fp16=True`）

### 步骤 3：验证 JIT 是否生效

**检查日志输出：**
启动应用后，应该看到类似输出：
```
加载模型中...
已加载 X 个说话人
TTS模块初始化成功
```

如果没有错误，说明 JIT 模型加载成功。

**性能测试：**

我们提供了一个完整的性能测试脚本 `test_jit_performance.py`，可以自动对比 JIT 和非 JIT 的性能。

**运行测试：**
```bash
cd E:\MagicMirror\backend
python test_jit_performance.py
```

**测试脚本功能：**
- ✅ 自动测试不使用 JIT 的性能
- ✅ 自动测试使用 JIT 的性能
- ✅ 对比不同长度文本的性能差异
- ✅ 提供详细的统计信息（平均值、中位数、标准差等）
- ✅ 计算性能提升百分比

**手动测试代码示例：**
```python
import time
from TTS import CosyvoiceRealTimeTTS

model_path = "Model/CosyVoice2-0.5B"
ref_audio = "audio/zjj.wav"
test_text = "这是一个测试文本，用于对比 JIT 编译的性能提升效果。"

# 测试不使用 JIT
print("测试不使用 JIT...")
tts_without_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=False)
start = time.time()
audio1 = tts_without_jit.generate_audio(test_text)
time_without_jit = time.time() - start
print(f"不使用 JIT: {time_without_jit:.3f} 秒")

# 测试使用 JIT
print("测试使用 JIT...")
tts_with_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=True)
start = time.time()
audio2 = tts_with_jit.generate_audio(test_text)
time_with_jit = time.time() - start
print(f"使用 JIT: {time_with_jit:.3f} 秒")

# 计算提升
speedup = time_without_jit / time_with_jit
improvement = (speedup - 1) * 100
print(f"速度提升: {improvement:.1f}%")
print(f"加速比: {speedup:.2f}x")
```

## 四、故障排除

### 问题 1：找不到 JIT 模型文件
**错误信息：**
```
FileNotFoundError: flow.encoder.fp16.zip not found
```

**解决方法：**
1. 确保已运行导出脚本
2. 检查文件是否在 `Model/CosyVoice2-0.5B/` 目录下
3. 确认文件名正确（`flow.encoder.fp16.zip`）

### 问题 2：JIT 模型加载失败
**错误信息：**
```
RuntimeError: Error loading JIT model
```

**解决方法：**
1. 重新导出 JIT 模型
2. 确保 PyTorch 版本兼容
3. 检查 CUDA 版本是否匹配

### 问题 3：性能没有提升
**可能原因：**
1. JIT 模型未正确加载（检查日志）
2. 文本太短，优化效果不明显
3. GPU 利用率已经很高

**解决方法：**
1. 确认 JIT 模型文件存在
2. 测试长文本（>100 字符）
3. 使用 `nvidia-smi` 监控 GPU 使用率

## 五、性能对比

### 预期性能提升

| 场景 | 不使用 JIT | 使用 JIT | 提升 |
|------|-----------|---------|------|
| 短文本 (<50 字符) | 0.5s | 0.45s | ~10% |
| 中等文本 (50-200 字符) | 2.0s | 1.6s | ~20% |
| 长文本 (>200 字符) | 5.0s | 3.5s | ~30% |

**注意：** 实际性能提升取决于：
- GPU 性能
- 文本长度
- 模型复杂度
- 系统负载

## 六、最佳实践

### 1. 首次使用
- ✅ 先导出 JIT 模型
- ✅ 测试性能提升
- ✅ 确认没有错误

### 2. 生产环境
- ✅ 使用 FP16 版本的 JIT 模型（节省显存）
- ✅ 监控 GPU 使用率
- ✅ 定期检查性能

### 3. 开发调试
- ⚠️ 开发时可以关闭 JIT（`load_jit=False`）以加快启动
- ⚠️ 生产环境建议启用 JIT

## 七、总结

### 推荐配置
```python
# TTS.py 中的配置
self.cosyvoice = CosyVoice2(
    model_path, 
    load_jit=True,      # ✅ 启用 JIT
    load_trt=False,     # ❌ 不使用 TensorRT
    fp16=True           # ✅ 使用 FP16 半精度
)
```

### 优势
- ✅ 性能提升 10-30%
- ✅ 显存友好
- ✅ 配置简单
- ✅ 兼容性好

### 注意事项
- ⚠️ 首次导出需要时间
- ⚠️ JIT 模型文件较大（约 100-200 MB）
- ⚠️ 需要确保模型目录有足够空间

## 八、下一步

1. **立即行动**：
   ```bash
   cd E:\MagicMirror\backend
   python export_jit_model.py
   ```

2. **修改代码**：
   - 在 `TTS.py` 中将 `load_jit=False` 改为 `load_jit=True`

3. **测试验证**：
   - 重启应用
   - 测试 TTS 功能
   - 观察性能提升

4. **监控优化**：
   - 使用 `nvidia-smi` 监控 GPU
   - 记录性能数据
   - 根据实际情况调整


# JIT 编译已禁用说明

## 原因

经过性能测试发现，在当前环境下启用 JIT 编译后，性能反而大幅下降：

- **不使用 JIT**: 平均 12.5 秒，RTF (Real-Time Factor) 约 0.88-1.15 ✅
- **使用 JIT**: 平均 160 秒，RTF 高达 14-17 ❌

性能下降约 **92%**，这可能是由于：

1. **JIT 模型文件不存在或有问题**
   - JIT 模型文件 (`flow.encoder.fp16.zip`) 可能不存在
   - 即使文件存在，可能与当前 PyTorch/CUDA 版本不兼容

2. **JIT 编译开销过大**
   - 首次运行时 JIT 需要编译，但编译过程可能很慢
   - 对于 RTX 2050 这样的入门级 GPU，JIT 优化可能不适用

3. **环境兼容性问题**
   - JIT 模型可能是在不同环境下导出的
   - PyTorch 版本或 CUDA 版本不匹配

## 当前配置

**默认已禁用 JIT 编译：**

- `TTS.py`: `load_jit=False` (默认值)
- `app.py`: `load_jit=False` (显式设置)

## 性能建议

对于 RTX 2050 (4GB 显存) 设备，推荐配置：

1. ✅ **FP16 半精度** - 已启用，减少显存占用，提高速度
2. ✅ **不使用 JIT** - 已禁用，避免性能下降
3. ❌ **不使用 TensorRT** - 显存不足，配置复杂

## 如果将来想尝试 JIT

如果将来想重新尝试 JIT 编译，请确保：

1. **正确导出 JIT 模型**
   ```bash
   python export_jit_model.py
   ```

2. **验证 JIT 模型文件存在**
   ```bash
   ls Model/CosyVoice2-0.5B/flow.encoder.fp16.zip
   ```

3. **检查 PyTorch 版本兼容性**
   - 导出 JIT 模型时的 PyTorch 版本
   - 运行时的 PyTorch 版本
   - 两者应该匹配

4. **进行性能测试**
   ```bash
   python quick_test_jit.py
   ```
   - 如果性能提升 < 10%，不建议使用
   - 如果性能下降，立即禁用

## 总结

当前配置（不使用 JIT）已经是最优选择：
- ✅ 推理速度快（RTF ~1.0）
- ✅ 显存占用合理
- ✅ 稳定性好

**建议保持当前配置，不要启用 JIT 编译。**


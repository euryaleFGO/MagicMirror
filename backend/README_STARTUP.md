# MagicMirror 应用启动说明

## ✅ 当前状态
应用已成功启动并运行！

## 🚀 启动方式

### 方式1：使用启动脚本（推荐）
```bash
cd /root/autodl-tmp/MagicMirror/backend
./start_app.sh
```

### 方式2：直接运行
```bash
cd /root/autodl-tmp/MagicMirror/backend
python app.py
```

## 🛑 停止应用
```bash
./stop_app.sh
```

## 📋 重要说明

### TTS 模块延迟初始化
- TTS 模块**不在启动时初始化**，避免崩溃
- TTS 将在**首次使用时自动初始化**
- 如果首次使用 TTS 时出现问题，应用不会崩溃，只会返回错误信息

### 已完成的修复
1. ✅ 升级依赖版本（PyTorch 2.3.1, onnxruntime-gpu 1.18.0）
2. ✅ 重新下载 CosyVoice 项目代码
3. ✅ 实现 TTS 延迟初始化
4. ✅ 音频转换为 16000Hz
5. ✅ 禁用 Flask reloader
6. ✅ 添加 monkey patch 避免重复下载模型

### 日志文件
- 应用日志: `/tmp/magicmirror_app.log`
- 实时查看: `tail -f /tmp/magicmirror_app.log`

### 访问地址
- http://localhost:5000
- http://172.17.0.10:5000

## ⚠️ 如果应用闪退

1. **查看日志**: `tail -50 /tmp/magicmirror_app.log`
2. **检查错误**: `grep -i error /tmp/magicmirror_app.log`
3. **检查进程**: `ps aux | grep app.py`
4. **检查端口**: `netstat -tlnp | grep 5000`

如果是在访问 TTS 接口时崩溃，这是延迟初始化的问题，需要进一步调试。

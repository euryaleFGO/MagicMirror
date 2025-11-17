# TTS 服务独立部署说明

## 架构说明

TTS 功能已分离为独立服务，避免在 Flask 应用中初始化导致崩溃。

- **app.py (端口 5000)**: 主应用，处理 Web 请求、数据库、AI 对话等
- **tts_service.py (端口 5001)**: 独立的 TTS 服务，专门处理语音合成

## 启动方式

### 1. 启动 TTS 服务（必须先启动）

```bash
cd /root/autodl-tmp/MagicMirror/backend
./start_tts_service.sh
```

### 2. 启动主应用

```bash
cd /root/autodl-tmp/MagicMirror/backend
./start_app.sh
# 或
python app.py
```

## 停止服务

### 停止 TTS 服务
```bash
./stop_tts_service.sh
```

### 停止主应用
```bash
./stop_app.sh
```

## 服务检查

### 检查 TTS 服务状态
```bash
curl http://localhost:5001/health
```

### 测试 TTS 功能
```bash
curl -X POST http://localhost:5001/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，这是一个测试","use_clone":true}'
```

## 日志文件

- TTS 服务日志: `/tmp/tts_service.log`
- 主应用日志: `/tmp/magicmirror_app.log`

## 优势

1. **避免崩溃**: TTS 服务独立运行，不会影响主应用
2. **易于维护**: TTS 服务可以单独重启，不影响主应用
3. **资源隔离**: TTS 服务的资源问题不会影响主应用
4. **可扩展**: 可以部署多个 TTS 服务实例

## 注意事项

- TTS 服务必须在主应用之前启动
- 如果 TTS 服务未启动，主应用的 TTS 接口会返回 503 错误
- TTS 服务在主线程中初始化，避免 kaldifst segfault 问题


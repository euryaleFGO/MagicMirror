#!/bin/bash
# 启动所有服务（TTS 服务 + 主应用）

echo "=========================================="
echo "启动 MagicMirror 所有服务"
echo "=========================================="

# 1. 启动 TTS 服务
echo ""
echo "1. 启动 TTS 服务..."
cd /root/autodl-tmp/MagicMirror/backend
./start_tts_service.sh

# 等待 TTS 服务初始化
echo ""
echo "等待 TTS 服务初始化..."
sleep 10

# 检查 TTS 服务状态
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ TTS 服务已就绪"
else
    echo "⚠️  TTS 服务可能未完全启动，但继续启动主应用..."
fi

# 2. 启动主应用
echo ""
echo "2. 启动主应用..."
./start_app.sh

echo ""
echo "=========================================="
echo "所有服务启动完成"
echo "=========================================="
echo "TTS 服务: http://localhost:5001"
echo "主应用: http://localhost:5000"
echo ""
echo "停止所有服务: ./stop_all.sh"


#!/bin/bash
# 启动 TTS 服务脚本

cd /root/autodl-tmp/MagicMirror/backend

# 设置日志文件
LOG_FILE="/tmp/tts_service.log"
PID_FILE="/tmp/tts_service.pid"

# 清理旧的进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "发现旧进程 $OLD_PID，正在停止..."
        kill $OLD_PID 2>/dev/null
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# 清理端口占用
fuser -k 5001/tcp 2>/dev/null || true

echo "启动 TTS 服务..."
echo "日志文件: $LOG_FILE"
echo "PID 文件: $PID_FILE"

# 启动服务
nohup python -u tts_service.py > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# 保存 PID
echo $SERVICE_PID > "$PID_FILE"

# 等待启动
sleep 5

# 检查是否启动成功
if ps -p $SERVICE_PID > /dev/null 2>&1; then
    echo "✅ TTS 服务启动成功！"
    echo "PID: $SERVICE_PID"
    echo "端口: 5001"
    echo "日志: tail -f $LOG_FILE"
    echo "停止: kill $SERVICE_PID 或 ./stop_tts_service.sh"
    
    # 检查服务是否响应
    sleep 3
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo "✅ TTS 服务正常响应"
    else
        echo "⚠ TTS 服务未响应，请检查日志"
    fi
else
    echo "❌ TTS 服务启动失败"
    echo "=== 错误日志 ==="
    tail -30 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi


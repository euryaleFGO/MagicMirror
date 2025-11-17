#!/bin/bash
# 停止 TTS 服务

PID_FILE="/tmp/tts_service.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止 TTS 服务 (PID: $PID)..."
        kill $PID 2>/dev/null
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止..."
            kill -9 $PID 2>/dev/null
        fi
        echo "✅ TTS 服务已停止"
    else
        echo "TTS 服务未运行"
    fi
    rm -f "$PID_FILE"
else
    echo "未找到 PID 文件，尝试查找进程..."
    pkill -f "tts_service.py" && echo "✅ 已停止" || echo "未找到运行中的 TTS 服务"
fi


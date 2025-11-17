#!/bin/bash
# Flask 应用启动脚本，带错误处理和日志记录

cd /root/autodl-tmp/MagicMirror/backend

# 设置日志文件
LOG_FILE="/tmp/magicmirror_app.log"
PID_FILE="/tmp/magicmirror_app.pid"

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
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

echo "启动 Flask 应用..."
echo "日志文件: $LOG_FILE"
echo "PID 文件: $PID_FILE"

# 启动应用
nohup python -u app.py > "$LOG_FILE" 2>&1 &
APP_PID=$!

# 保存 PID
echo $APP_PID > "$PID_FILE"

# 等待启动
sleep 5

# 检查是否启动成功
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ 应用启动成功！"
    echo "PID: $APP_PID"
    echo "日志: tail -f $LOG_FILE"
    echo "停止: kill $APP_PID 或 ./stop_app.sh"
    
    # 检查服务是否响应
    sleep 3
    if curl -s http://localhost:5000/login > /dev/null 2>&1; then
        echo "✅ HTTP 服务正常响应"
    else
        echo "⚠ HTTP 服务未响应，请检查日志"
    fi
else
    echo "❌ 应用启动失败"
    echo "=== 错误日志 ==="
    tail -30 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi


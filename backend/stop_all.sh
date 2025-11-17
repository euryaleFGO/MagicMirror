#!/bin/bash
# 停止所有服务

echo "停止所有服务..."

./stop_tts_service.sh
./stop_app.sh

echo "✅ 所有服务已停止"


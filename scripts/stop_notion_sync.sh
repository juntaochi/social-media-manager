#!/bin/bash
# Notion 同步服务停止脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/notion_sync.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Notion 同步服务未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "停止 Notion 同步服务 (PID: $PID)..."
    kill $PID
    rm -f "$PID_FILE"
    echo "✓ Notion 同步服务已停止"
else
    echo "进程 $PID 不存在，清理 PID 文件..."
    rm -f "$PID_FILE"
fi

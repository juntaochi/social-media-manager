#!/bin/bash
# Notion 同步服务启动脚本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/notion_sync.pid"
LOG_FILE="$LOG_DIR/notion_sync.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 加载环境变量
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    echo "错误：.env 文件不存在"
    exit 1
fi

# 检查必要的环境变量
if [ -z "$NOTION_TOKEN" ]; then
    echo "错误：NOTION_TOKEN 未设置"
    exit 1
fi

if [ -z "$NOTION_DATABASE_ID" ]; then
    echo "错误：NOTION_DATABASE_ID 未设置"
    exit 1
fi

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Notion 同步服务已在运行 (PID: $PID)"
        exit 0
    else
        echo "清理旧的 PID 文件..."
        rm -f "$PID_FILE"
    fi
fi

# 启动同步服务
echo "启动 Notion 同步服务..."
cd "$PROJECT_ROOT"

nohup python3 scripts/bridge_notion.py --watch --interval 300 \
    >> "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

echo "✓ Notion 同步服务已启动 (PID: $PID)"
echo "  日志文件: $LOG_FILE"
echo "  停止服务: $SCRIPT_DIR/stop_notion_sync.sh"

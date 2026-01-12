#!/bin/bash
# 完整运行周期：同步 + Pipeline + 再同步

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=================================="
echo "  📱 完整任务处理周期"
echo "=================================="
echo

cd "$PROJECT_ROOT"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🔄 [1/3] 从 Notion 同步最新任务..."
python3 scripts/bridge_notion.py --pull-only

echo "⚙️  [2/3] 运行 Pipeline 处理任务..."
./scripts/run_pipeline.sh full

echo "📤 [3/3] 推送结果回 Notion..."
python3 scripts/bridge_notion.py --push-only

echo "=================================="
echo "  ✅ 完整周期执行完成！"
echo "=================================="
echo
echo "📱 打开 Notion app 查看更新"

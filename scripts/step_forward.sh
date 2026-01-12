#!/bin/bash
# Step Forward - 让 Manager Agent 自主决策下一步行动

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 呼叫 Manager Agent 进行自主决策..."
opencode run --agent manager-agent "Check the current pipeline status and take all necessary next steps to move tasks forward. Execute analysis, writing, or publishing as needed based on ticket states."

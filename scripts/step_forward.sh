#!/bin/bash
# Step Forward - 让 Manager Agent 自主决策下一步行动

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 呼叫 Manager Agent 进行阶段化决策..."
opencode run --agent manager-agent "Execute the pipeline in strict order: 
1. Move all PROPOSED tickets to WAITING_APPROVAL by running Analyst Deep Dive.
2. For all APPROVED tickets, run Writer and Publisher to create Typefully drafts.
3. Report progress for each stage separately."

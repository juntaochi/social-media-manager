#!/bin/bash

# Ralphloop Automation Script
# Usage: ./ralphloop_automation.sh "Task description"

set -e

TASK_DESCRIPTION=$1
if [ -z "$TASK_DESCRIPTION" ]; then
    echo "Error: Task description required."
    exit 1
fi

TIMESTAMP=$(date +%s)
SESSION_NAME="ralphloop-$TIMESTAMP"
BRANCH_NAME="ralph/task-$TIMESTAMP"

echo "🚀 Starting Ralphloop Automation: $TASK_DESCRIPTION"

# 1. Git Branch
echo "📂 Creating git branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# 2. Prepare Zellij Command
AGENT_PROMPT="You are in a dedicated Zellij session for a long-running task. 
TASK: $TASK_DESCRIPTION

1. Create a massive, detailed TODO list in data/tasks.md for this feature.
2. Implement every item one by one.
3. Debug thoroughly after implementation.
4. Document the entire process in both Chinese and English in a new file under docs/archive/ralphloop-$TIMESTAMP.md.
5. When finished, use 'zellij detach' or simply notify that you are done.

Start now."

# 3. Launch Zellij Session (Detached)
echo "🖥️ Launching Zellij session: $SESSION_NAME"
# Use 'zellij run' to start the agent in a new session and background it
zellij --session "$SESSION_NAME" run --name "sisyphus-ralph" -- bash -c "opencode '$AGENT_PROMPT'; zellij detach" &

sleep 2

echo "✅ Automation triggered."
echo "Branch: $BRANCH_NAME"
echo "Session: $SESSION_NAME"
echo "To monitor: zellij attach $SESSION_NAME"
echo "The agent will implement, debug, document, and detach automatically."

# Skill: Ralphloop Automation

## Description
Automates a deep work cycle ("睡前任务"): creates a git branch, starts a Zellij session with OpenCode, generates a comprehensive TODO list, implements tasks autonomously, debugs, documents the process in Chinese and English, and detaches the session.

## Triggers
- "睡前任务"
- "ralphloop automation"
- "start a long-running autonomous task"

## Workflow
1. **Context Sync**: Check current branch and git status.
2. **Branch Creation**: Create a new git branch \`ralph/feature-name\`.
3. **Zellij Session**: Launch a new Zellij session named \`ralphloop-<timestamp>\`.
4. **OpenCode RalphLoop**:
   - Create tickets in \`data/tickets/\` directory.
   - Run OpenCode with a "RalphLoop" prompt to implement and debug.
5. **Documentation**: Generate \`docs/archive/ralphloop-<timestamp>.md\` in CN/EN.
6. **Detach**: Detach from Zellij using \`zellij detach\`.

## Requirements
- \`zellij\` CLI installed.
- \`opencode\` CLI installed.
- \`git\` configured.

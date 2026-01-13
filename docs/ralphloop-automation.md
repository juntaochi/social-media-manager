# Ralphloop Automation Guide / Ralphloop 自动化指南

## Overview / 概览
The Ralphloop automation skill is designed for long-running, autonomous tasks (e.g., "睡前任务" - bedtime tasks). It leverages git branching, Zellij session multiplexing, and OpenCode's RalphLoop logic to execute complex workflows while the user is away.

Ralphloop 自动化技能专为长时间运行的自主任务设计（例如“睡前任务”）。它利用 git 分支、Zellij 会话复用和 OpenCode 的 RalphLoop 逻辑，在用户离开时执行复杂的工作流程。

## Key Components / 核心组件
1. **Git Branching**: Every task starts in a fresh `ralph/task-<timestamp>` branch to ensure isolation.
   **Git 分支**：每个任务都在全新的 `ralph/task-<timestamp>` 分支中开始，以确保隔离。
2. **Zellij Sessions**: Tasks run in named background sessions, allowing the agent to persist even if the main terminal is closed.
   **Zellij 会话**：任务在命名的后台会话中运行，即使主终端关闭，代理也能继续存在。
3. **Autonomous Implementation**: The agent generates its own TODO list and loops through implementation and debugging.
   **自主实现**：代理生成自己的 TODO 列表，并循环执行实现和调试。
4. **Bilingual Documentation**: Final results and the process log are documented in both Chinese and English.
   **中英双语文档**：最终结果和过程日志以中英文记录。

## Usage / 使用方法
To trigger the automation, use the following command:
要触发自动化，请使用以下命令：

```bash
./scripts/ralphloop_automation.sh "Your task description here"
```

### Automation Steps / 自动化步骤
1. **Initialize**: Script creates a new branch.
   **初始化**：脚本创建一个新分支。
2. **Session Launch**: A Zellij session is created and OpenCode is triggered with the "RalphLoop" prompt.
   **会话启动**：创建一个 Zellij 会话，并使用 “RalphLoop” 提示词触发 OpenCode。
3. **Execution**: OpenCode creates tickets in `data/tickets/`, implements, and debugs.
   **执行**：OpenCode 在 `data/tickets/` 创建工单，执行并调试。
4. **Documentation**: A detailed process log is saved to `docs/archive/ralphloop-<timestamp>.md`.
   **文档记录**：详细的过程日志保存在 `docs/archive/ralphloop-<timestamp>.md`。
5. **Cleanup**: The session detaches automatically.
   **清理**：会话自动分离（Detach）。

## Monitoring / 监控
You can re-attach to the session at any time:
您可以随时重新连接到会话：

```bash
zellij attach ralphloop-<timestamp>
```

To see active sessions:
查看活动会话：

```bash
zellij ls
```

# Media Agent System

![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![MCP](https://img.shields.io/badge/MCP-Enabled-blue)
![OpenCode](https://img.shields.io/badge/OpenCode-Agentic-orange)

A multi-agent automation pipeline for creating and publishing "Build in Public" content from real code activity, powered by OpenCode + MCP.

[English](#english) | [中文](#中文)

---

## English

### Overview

Media Agent System turns code changes into high-quality social posts through a transparent, ticket-based workflow. It pairs semantic code analysis with a human approval gate, so every post stays accurate, intentional, and safe to publish.

### Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Why Agents](#why-agents)
- [Installation](#installation)
- [Notion Setup](#notion-setup)
- [Workflow](#workflow)
- [Monitoring](#monitoring)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

### Features

- **Build in Public focus** with clear, human-sounding narratives.
- **Semantic code analysis** from GitHub commits, not just templates.
- **Ticket-centric SSOT** in `data/tickets/` for transparency and Git history.
- **Bidirectional Notion sync** as a mobile-friendly approval UI.
- **Human-in-the-loop** publishing gate with status-driven controls.
- **Multi-platform ready** via MCP + Typefully integration.
- **Bilingual documentation** for global teams.

### Architecture

**Manager-Agent Orchestration Model**

The `manager-agent` is the system brain. It reads the ticket state, acquires locks, dispatches specialized agents, and moves tickets through the lifecycle.

- **Analyst Agent**: scans repositories, detects meaningful changes, creates `proposed` tickets.
- **Writer Agent**: turns approved tickets into drafts, status → `ready`.
- **Publisher Agent**: publishes via Typefully and records URLs, status → `published`.

**Ticket SSOT (Single Source of Truth)**

```
data/
├── tickets/                  # SSOT: one ticket per post
├── context/                  # Analyst summaries
├── drafts/                   # Writer output
└── published/                # Published archive
```

Tickets are Markdown files with YAML frontmatter. See `data/tickets/_TEMPLATE.md` for the state model and required fields.

### Why Agents

Traditional automation tools are rule-based. This system is reasoning-based: the Analyst understands code intent, the Writer adapts story tone, and the Publisher enforces safety. The result is higher signal content without sacrificing control or auditability.

### Installation

**Prerequisites**

- **OpenCode**: `opencode --version`
- **Python 3.8+**: `python3 --version`
- **Node.js 18+**: `node --version`

**Setup**

```bash
cd social-media-manager
chmod +x scripts/*.sh
chmod +x scripts/*.py
cp .env.example .env
```

Add keys to `.env`:

```bash
GITHUB_TOKEN=ghp_your_token_here
TYPEFULLY_KEY=your_typefully_key_here
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
```

Load environment variables:

```bash
export $(cat .env | grep -v '^#' | xargs)
```

### Notion Setup

Notion is the primary mobile-friendly UI for approvals. It mirrors `data/tickets/` and syncs status changes in both directions.

1. **Create a Notion Integration**: https://www.notion.so/my-integrations
2. **Create a Database** with these properties:
   - **Ticket ID** (Title)
   - **Status** (Select)
   - **Project** (Text)
   - **Type** (Select)
   - **Priority** (Select)
   - **Draft Content** (Text)
   - **Draft Path** (URL)
   - **Published URL** (URL)
   - **Error** (Text)
3. **Install Notion client**:
   ```bash
   pip install notion-client
   ```
4. **Run the sync loop**:
   ```bash
   nohup bash -c 'export $(cat .env | grep -v "^#" | xargs) && python3 scripts/bridge_tickets.py --watch --interval 60' > logs/ticket_sync.log 2>&1 &
   ```

### Workflow

1. **Analyze**: `./scripts/run_pipeline.sh analyze` creates `proposed` tickets.
2. **Approve**: update `status: approved` in Notion (or the Markdown file).
3. **Process**: `./scripts/run_pipeline.sh full` dispatches Writer and generates drafts.
4. **Publish**: The same run handles publishing once status reaches `ready`.
5. **Inspect**: use `./scripts/run_pipeline.sh status` or `./scripts/monitor.sh` for a quick report.

Ticket lifecycle:
`proposed → approved → drafting → ready → publishing → published`

### Monitoring

The monitoring dashboard is built-in:

```bash
./scripts/monitor.sh
```

It shows Notion sync status, pipeline processes, ticket counts by state, latest drafts, and recent logs with a 5-second refresh.

### License

MIT License

---

## 中文

### 概览

Media Agent System 将代码变化转化为可发布的 "Build in Public" 内容，采用可审计的票据（Ticket）工作流与人工审批机制，确保每条内容准确、可控、可追踪。

### 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [为何采用多智能体](#为何采用多智能体)
- [安装与配置](#安装与配置)
- [Notion 配置](#notion-配置)
- [工作流程](#工作流程)
- [监控与观察](#监控与观察)
- [路线图](#路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

### 功能特性

- **面向 Build in Public** 的内容表达与叙事结构
- **语义级代码分析**，理解变更意图而非模板填充
- **Ticket SSOT**：`data/tickets/` 为单一事实来源，方便 Git 追踪
- **Notion 双向同步**，手机上即可审批与跟踪
- **人工审批** 作为发布安全门禁
- **MCP 集成**，可扩展到多平台发布
- **中英双语文档**，团队协作更友好

### 系统架构

**Manager-Agent 编排模型**

`manager-agent` 负责读取 Ticket 状态、加锁、分派任务并推动状态流转。其他 Agent 各司其职，减少耦合并提升可维护性。

**Ticket 单一事实源**

`data/tickets/` 中每个 Markdown 文件都是一条内容的完整历史与元数据。字段规范请参考 `data/tickets/_TEMPLATE.md`。

### 为何采用多智能体

相比传统自动化流程，多智能体能够理解代码语义、用更自然的方式讲述变化，同时保留人工审批控制。它兼顾了内容质量与安全性。

### 安装与配置

```bash
cd social-media-manager
chmod +x scripts/*.sh
chmod +x scripts/*.py
cp .env.example .env
```

填写 `.env`：

```bash
GITHUB_TOKEN=ghp_your_token_here
TYPEFULLY_KEY=your_typefully_key_here
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### Notion 配置

Notion 是主要的移动端审批界面，与 `data/tickets/` 双向同步。

1. 创建 Integration: https://www.notion.so/my-integrations
2. 创建数据库并包含字段：Ticket ID、Status、Project、Type、Priority、Draft Content、Draft Path、Published URL、Error
3. 安装依赖：
   ```bash
   pip install notion-client
   ```
4. 启动同步：
   ```bash
   nohup bash -c 'export $(cat .env | grep -v "^#" | xargs) && python3 scripts/bridge_tickets.py --watch --interval 60' > logs/ticket_sync.log 2>&1 &
   ```

### 工作流程

- `./scripts/run_pipeline.sh analyze` 生成 `proposed` 票据
- 在 Notion 或 Markdown 中将 `status` 改为 `approved`
- `./scripts/run_pipeline.sh full` 自动生成草稿并发布
- `./scripts/run_pipeline.sh status` 查看总体状态

状态流转：`proposed → approved → drafting → ready → publishing → published`

### 监控与观察

```bash
./scripts/monitor.sh
```

显示同步状态、运行进程、各类 Ticket 数量、草稿列表和最近日志，默认每 5 秒刷新。

### 路线图

- 多平台发布支持（LinkedIn、Mastodon、Threads）
- 内容效果分析反馈
- 自动化媒体素材生成
- 团队协作审批

### 许可证

MIT License

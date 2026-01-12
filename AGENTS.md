# Media Agent System - Agent Guidelines

## 🤖 Agent Orchestration Model

The system operates on a **Manager-Subagent** architecture. All workflow decisions are delegated to the **Manager Agent**, which orchestrates specialized sub-agents.

### Agent Hierarchy
- **Manager Agent** (`@manager-agent`): The brain. Orchestrates the pipeline, manages ticket states, and dispatches sub-agents.
- **Analyst Agent** (`@analyst-agent`): The eyes. Scans projects, detects changes, and creates `proposed` tickets.
- **Writer Agent** (`@writer-agent`): The voice. Transforms `approved` tickets into engaging multi-platform drafts.
- **Publisher Agent** (`@publisher-agent`): The hands. Publishes `ready` drafts to Typefully via official MCP.

---

## 📂 Project Structure & SSOT

- **`.opencode/agent/`**: Contains the core logic and manifests for each agent. These are the "manuals" the agents follow.
- **`data/tickets/`**: **Single Source of Truth (SSOT)**. Every content piece is a ticket (`TKT-xxx.md`) with state managed in YAML frontmatter.
- **`scripts/bridge_tickets.py`**: Synchronization layer between local tickets and the Notion Dashboard.
- **`scripts/run_pipeline.sh`**: The primary entry point for executing the manager agent.

---

## 🚀 Development Commands

### Running the Pipeline
```bash
# Process everything (Analyze -> Write -> Publish)
./scripts/run_pipeline.sh full

# Specifically run analysis or status report
./scripts/run_pipeline.sh analyze
./scripts/run_pipeline.sh status
```

### Automation & Sync
```bash
# Start background sync (Notion <-> Tickets)
nohup bash -c 'export $(cat .env | grep -v "^#" | xargs) && python3 scripts/bridge_tickets.py --watch --interval 60' > logs/ticket_sync.log 2>&1 &

# Monitor all activity
./scripts/monitor.sh
```

---

## 📏 Standards & Conventions

### Ticket Lifecycle
1. `proposed`: Created by Analyst after scanning projects.
2. `approved`: Human approval (via Notion or by editing the MD file).
3. `drafting`: Manager dispatches Writer.
4. `ready`: Writer finishes the draft.
5. `published`: Publisher successfully posts to Typefully.

### Code & Config
- **Python**: PEP 8, snake_case, 4-space indents.
- **Markdown**: YAML frontmatter must include `id`, `status`, `project`, `type`.
- **Agents**: Never hardcode logic in scripts that belongs in agent manifests. Keep scripts as thin wrappers around `opencode run`.

---

## 🔐 Security
- **No Secrets**: Never commit `.env` or print tokens to logs.
- **Locking**: Manager Agent implements a locking mechanism (`locked_by`) in ticket frontmatter to prevent concurrent processing.

---

**Last Updated**: 2026-01-13
**Current Orchestrator**: `manager-agent`

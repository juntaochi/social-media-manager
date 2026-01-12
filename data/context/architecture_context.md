# Architecture Context: Media Agent System

**Last Updated**: 2026-01-12T20:43:37Z

## Project Mission

Automate "Build in Public" content creation from code changes using multi-agent AI orchestration with human approval gates. Transform commits into compelling social media narratives while maintaining transparency, safety, and version control.

## Core Modules

### 1. Agent Layer (`/.opencode/agent/`)
**Purpose**: Agent manifests defining specialized behaviors

- **manager-agent.md**: Orchestrator, state machine controller, dispatcher
- **analyst-agent.md**: Repository scanner, change detector, ticket creator
- **writer-agent.md**: Content generator, storytelling, platform adaptation
- **publisher-agent.md**: Typefully integration, media handler, safety validator

**Key Pattern**: Manager-worker orchestration with clear separation of concerns

### 2. Data Layer (`/data/`)
**Purpose**: Single Source of Truth (SSOT) for content lifecycle

- **tickets/**: Markdown files with YAML frontmatter (one ticket = one post)
- **context/**: Semantic analysis summaries (architecture + commit analysis)
- **drafts/**: Generated content ready for publication
- **published/**: Archive of successful posts
- **projects.yaml**: Registry of monitored repositories

**Key Pattern**: Git-tracked state machines with atomic writes

### 3. Bridge Layer (`/scripts/`)
**Purpose**: External integrations and synchronization

- **bridge_tickets.py**: Notion ↔ Local Markdown bidirectional sync
- **bridge_typefully.py**: Media upload and Typefully API wrapper
- **run_pipeline.sh**: Main entry point for agent execution
- **monitor.sh**: Real-time dashboard for pipeline observation
- **atomic_write.py**: Safe file operations (write-to-temp → fsync → rename)

**Key Pattern**: Thin wrappers around agent logic, scripts execute not decide

## Entry Points

1. **Analysis**: `./scripts/run_pipeline.sh analyze`
   - Triggers: manager-agent → analyst-agent
   - Output: New tickets in `data/tickets/` with `status: proposed`

2. **Drafting**: `./scripts/run_pipeline.sh write`
   - Triggers: manager-agent → writer-agent (for `approved` tickets)
   - Output: Drafts in `data/drafts/`, status → `ready`

3. **Publishing**: `./scripts/run_pipeline.sh publish`
   - Triggers: manager-agent → publisher-agent (for `ready` tickets)
   - Output: Published posts, Typefully URLs, status → `published`

4. **Full Pipeline**: `./scripts/run_pipeline.sh full`
   - Runs analyze → write → publish sequentially

## Key Abstractions

### Ticket State Machine
```
proposed → approved → drafting → ready → publishing → published
         ↓                                           ↓
      rejected                                   failed
```

**Critical Gates**:
- `proposed → approved`: Human approval required (via Notion or manual edit)
- `ready → publishing`: Safety validation (no secrets, proper formatting)

### Locking Mechanism
**Fields**: `locked_by`, `locked_at`
**Timeout**: 10 minutes (prevents zombie locks)
**Purpose**: Prevent concurrent agent processing of same ticket

### Notion Sync Protocol
**Direction 1 (Local → Notion)**:
- New tickets automatically create Notion pages
- Status changes propagate to Notion

**Direction 2 (Notion → Local)**:
- Notion status changes (especially `approved`) trigger local updates
- Bridge runs in watch mode (`--watch --interval 60`)

## Search Hints

**Finding State Transitions**:
- Search for `status:` in `data/tickets/*.md`
- Grep for `def update_ticket_status` in scripts

**Finding Agent Dispatch Logic**:
- Read `.opencode/agent/manager-agent.md`
- Search for `opencode run --agent` in `scripts/run_pipeline.sh`

**Finding Ticket Creation**:
- Analyst agent creates tickets via `write_file` tool
- Pattern: `TKT-{number:03d}-{slug}.md`

**Finding Content Generation**:
- Writer agent reads tickets + context files
- Output format defined in `docs/agents/writer/templates/`

**Finding Publication Logic**:
- Publisher agent calls `typefully_create_draft` (MCP tool)
- Media handling via `bridge_typefully.py upload`

## Technical Innovations

1. **Semantic Context Caching**: Store `{commit_hash}_summary.md` to avoid re-scanning
2. **Zoom-In Retrieval**: Trace symbols through code using `search_code` + LSP
3. **Notion-as-CMS**: Use Notion for mobile UI while Git remains SSOT
4. **Atomic State Updates**: Prevent corruption via write-to-temp pattern
5. **MCP Tool Discovery**: Dynamic capability registration via Model Context Protocol

## Common Workflows

### Creating a Ticket Manually
```bash
cp data/tickets/_TEMPLATE.md data/tickets/TKT-XXX-my-feature.md
# Edit frontmatter and content
# Set status: proposed
# Run pipeline to process
```

### Approving a Ticket
**Via Notion**: Change Status column to "Approved"
**Via File**: Edit MD file, set `status: approved`

### Debugging Failed Tickets
```bash
grep "status: failed" data/tickets/*.md
# Check error field in frontmatter
# Review logs in logs/
./scripts/monitor.sh  # Real-time dashboard
```

### Adding a New Project
```yaml
# In data/projects.yaml
- repo: username/repo-name
  name: "Project Name"
  description: "What it does"
  local_path: "/path/to/repo"
  typefully_social_set_id: "12345"
```

## Integration Points

- **GitHub**: Used by Analyst for commit/file access (via MCP)
- **Typefully**: Used by Publisher for multi-platform posting (via MCP)
- **Notion**: Used by humans for approval workflow (via bridge script)
- **OpenCode**: Runtime that executes agent manifests
- **MCP**: Protocol for standardized tool calling

## Current State (2026-01-12)

- Repository initialized, no commits yet
- Architecture fully implemented
- First ticket (TKT-001) created: system introduction
- Ready for initial git commit and first content cycle

# Architecture Overview

## System Design Philosophy

The Media Agent system is built on three core principles:

1. **File-Based State**: All state is stored in human-readable files (Markdown, JSON) rather than databases
2. **Multi-Agent Specialization**: Each agent has a focused responsibility with specialized prompts
3. **Human-in-the-Loop**: Critical decisions (publishing) require explicit human approval

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                 (Notion Dashboard / data/tickets/*.md)          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Synchronization Layer                      │
│                    scripts/bridge_tickets.py                    │
│                                                                 │
│  • Syncs tickets between Notion and data/tickets/               │
│  • Primary state transition bridge (Proposed <-> Published)     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Orchestration Layer                           │
│                   scripts/run_pipeline.py                       │
│                                                                 │
│  • Reads ticket directory (data/tickets/*.md)                   │
│  • Manages agent-driven state transitions                      │
│  • Dispatches work to agents                                    │
│  • Handles errors and retries                                   │
└───┬─────────────┬─────────────┬─────────────┬──────────────────┘
    │             │             │             │
    ▼             ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐   ┌───────────┐
│Manager │   │ Analyst│   │ Writer │   │ Publisher │
│ Agent  │   │ Agent  │   │ Agent  │   │  Agent    │
└───┬────┘   └───┬────┘   └───┬────┘   └─────┬─────┘
    │            │            │              │
    │            │            │              │
    ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Integration Layer                        │
│                     (.claude/config.json)                        │
├──────────────┬─────────────────┬──────────────────┬─────────────┤
│   GitHub     │   Typefully     │   Filesystem     │   Custom    │
│  MCP Server  │   MCP Server    │   MCP Server     │   Scripts   │
└──────┬───────┴────────┬────────┴────────┬─────────┴──────┬──────┘
       │                │                 │                │
       ▼                ▼                 ▼                ▼
┌──────────┐    ┌──────────────┐   ┌──────────┐   ┌──────────────┐
│  GitHub  │    │  Typefully   │   │   Local  │   │    Bridge    │
│   API    │    │     API      │   │   Files  │   │   Scripts    │
┌──────────┘    └──────────────┘   └──────────┘   └──────────────┘
```

## Data Flow

### Ticket-Centric Workflow

1. **Analyst Agent** scans projects and creates tickets in `data/tickets/*.md` (Status: `proposed`)
   │
   ▼
2. **bridge_tickets.py** syncs new tickets to **Notion Dashboard**
   │
   ▼
3. **[HUMAN REVIEW]** User reviews tickets in Notion or Markdown, changes status → `approved`
   │
   ▼
4. **bridge_tickets.py** syncs `approved` status back to local ticket files
   │
   ▼
5. **Manager Agent** identifies `approved` ticket
   │
   ▼
6. **Writer Agent** 
    - Reads ticket rationale and references
    - Creates social content
    - Saves to `data/drafts/`
    - Status → `ready`
   │
   ▼
7. **Publisher Agent**
    - Reads `ready` ticket and draft
    - Uploads media (if any)
    - Creates Typefully draft
    - Status → `published`
   │
   ▼
8. **bridge_tickets.py** syncs `published` status and Typefully URLs back to Notion

## Agent Architecture

### 1. Manager Agent

**Role**: Orchestrator and state machine controller

**Responsibilities**:
- Scan `data/tickets/*.md` for actionable items
- Identify tickets ready for processing based on status
- Dispatch work to specialized agents
- Update ticket frontmatter statuses
- Handle locks and retries

**Tools Access**:
- File system (read/write tickets)
- Python subprocess (to call other agents)

**Decision Logic**:
```python
if ticket.status == 'approved':
    dispatch_to_writer(ticket)

elif ticket.status == 'ready':
    dispatch_to_publisher(ticket)
```

### 2. Analyst Agent (formerly Reader)

**Role**: Project intelligence and discovery

**Responsibilities**:
- Fetch commit data from GitHub
- Analyze code changes (diff)
- Identify "post-worthy" updates
- Create new tickets in `data/tickets/` with `proposed` status

**Tools Access**:
- GitHub MCP Server
- Filesystem (create tickets)

**Output**: Ticket in `data/tickets/`
```markdown
---
id: TKT-001
status: proposed
project: social-media-manager
type: feature
---
# Ticket Title
...
```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                  (data/tasks.md - Text File)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Orchestration Layer                           │
│                   scripts/run_pipeline.py                       │
│                                                                 │
│  • Reads task queue (tasks.md)                                 │
│  • Manages state transitions                                   │
│  • Dispatches work to agents                                   │
│  • Handles errors and retries                                  │
└───┬─────────────┬─────────────┬─────────────┬──────────────────┘
    │             │             │             │
    ▼             ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐   ┌───────────┐
│Manager │   │ Reader │   │ Writer │   │ Publisher │
│ Agent  │   │ Agent  │   │ Agent  │   │  Agent    │
└───┬────┘   └───┬────┘   └───┬────┘   └─────┬─────┘
    │            │            │              │
    │            │            │              │
    ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Integration Layer                        │
│                     (.claude/config.json)                        │
├──────────────┬─────────────────┬──────────────────┬─────────────┤
│   GitHub     │   Typefully     │   Filesystem     │   Custom    │
│  MCP Server  │   MCP Server    │   MCP Server     │   Scripts   │
└──────┬───────┴────────┬────────┴────────┬─────────┴──────┬──────┘
       │                │                 │                │
       ▼                ▼                 ▼                ▼
┌──────────┐    ┌──────────────┐   ┌──────────┐   ┌──────────────┐
│  GitHub  │    │  Typefully   │   │   Local  │   │    Bridge    │
│   API    │    │     API      │   │   Files  │   │   Scripts    │
└──────────┘    └──────────────┘   └──────────┘   └──────────────┘
```

## Data Flow

### Complete Pipeline Flow

```
1. User adds task to tasks.md
   │
   ▼
2. run_pipeline.py scans tasks.md
   │
   ▼
3. Manager Agent identifies TODO task
   │
   ├─ GitHub Commit? ──────────────────────────┐
   │                                           │
   ▼                                           ▼
4a. Reader Agent                          4b. Writer Agent (direct)
    - Calls GitHub MCP                        - Creates content
    - Analyzes commit                         - Saves to drafts/
    - Saves to context/                       │
    │                                         │
    ▼                                         │
5. Writer Agent ──────────────────────────────┘
    - Reads context file
    - Creates social content
    - Saves to drafts/
    │
    ▼
6. Status → WAITING_APPROVAL
    │
    ▼
7. [HUMAN REVIEW]
    - Reads draft
    - Edits if needed
    - Changes status → APPROVED
    │
    ▼
8. Publisher Agent
    - Reads approved draft
    - Uploads media (if any)
    - Creates Typefully draft
    │
    ▼
9. Status → DONE
    - Task complete
    - URL saved in tasks.md
```

## Agent Architecture

### 1. Manager Agent

**Role**: Orchestrator and state machine controller

**Responsibilities**:
- Read and parse `tasks.md`
- Identify tasks ready for processing
- Dispatch work to specialized agents
- Update task statuses
- Handle errors and retries

**Tools Access**:
- File system (read/write tasks.md)
- Python subprocess (to call other agents)

**Decision Logic**:
```python
if task.status == 'TODO':
    if is_github_commit(task):
        dispatch_to_reader(task)
    elif is_summary_based(task):
        dispatch_to_writer(task)
    elif is_freeform(task):
        dispatch_to_writer(task)

elif task.status == 'PROCESSING':
    check_if_agent_completed()

elif task.status == 'APPROVED':
    dispatch_to_publisher(task)
```

### 2. Reader Agent

**Role**: Technical code analyst

**Responsibilities**:
- Fetch commit data from GitHub
- Analyze code changes (diff)
- Extract meaningful context
- Generate technical summary

**Tools Access**:
- GitHub MCP Server
  - `get_commit`
  - `get_file_contents`
  - `search_code`

**Input**: Commit hash + repository name

**Output**: Technical summary in Markdown
```markdown
# Technical Summary: [Commit Title]

## Core Change
[One-sentence explanation]

## Technical Details
[Specific implementation notes]

## Impact Analysis
[UI, API, Database, Performance implications]

## Context for Content Creation
[Why this matters]
```

### 2. Analyst Agent (formerly Reader)

**Role**: Project intelligence and discovery

**Responsibilities**:
- Fetch commit data from GitHub
- Analyze code changes (diff)
- Identify "post-worthy" updates
- Create new tickets in `data/tickets/` with `proposed` status

**Tools Access**:
- GitHub MCP Server
- Filesystem (create tickets)

**Output**: Ticket in `data/tickets/`
```markdown
---
id: TKT-001
status: proposed
project: social-media-manager
type: feature
---
# Ticket Title
...
```

### 3. Writer Agent

**Role**: Content creator and storyteller

**Responsibilities**:
- Transform ticket rationale and references into engaging content
- Apply "Build in Public" narrative style
- Structure content for Twitter/LinkedIn
- Suggest media assets needed
- Update ticket status to `ready` upon completion

**Tools Access**:
- Filesystem (to read tickets and context)
- Optional: Web search (for additional context)

**Input**: Ticket ID (e.g., `TKT-001`)

**Output**: Social media draft in `data/drafts/`

### 4. Publisher Agent

**Role**: Distribution and media handler

**Responsibilities**:
- Verify ticket status is `ready`
- Parse draft content
- Handle media uploads via `bridge_typefully.py`
- Create Typefully draft/post
- Update ticket status to `published` and record URLs

**Tools Access**:
- Typefully MCP Server
- Custom bridge script (for media)
- Bash (to call bridge_typefully.py)


**Style Guidelines** (in prompt):
- Authentic, transparent tone
- Lead with value/impact
- Simplify technical concepts
- Include relevant emojis
- Proper thread structure

### 4. Publisher Agent

**Role**: Distribution and media handler

**Responsibilities**:
- Verify approval status (security check)
- Parse draft content
- Handle media uploads
- Create Typefully draft/post
- Return confirmation URL

**Tools Access**:
- Typefully MCP Server
  - `create_draft`
  - `schedule_post`
- Custom bridge script (for media)
- Bash (to call bridge_typefully.py)

**Security**:
- **MUST** verify task status is `APPROVED`
- **MUST** validate no sensitive data in content
- Dry-run mode available for testing

**Media Handling**:
```python
1. Scan draft for media references
2. For each image:
   - Call bridge_typefully.py upload
   - Collect media_id
3. Create draft with media_ids array
4. Return Typefully URL
```

## State Machine

### Ticket States

The system uses a unified state machine for both local tickets and Notion synchronization.

```
    ┌──────────┐
    │ proposed │ ← Analyst creates from commit or user creates manually
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │ approved │ ← User approves in Notion or Markdown
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │ drafting │ ← Writer Agent processing
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │  ready   │ ← Draft created in data/drafts/
    └─────┬────┘
          │
          ▼
    ┌────────────┐
    │ publishing │ ← Publisher Agent sending to Typefully
    └─────┬──────┘
          │
          ▼
    ┌───────────┐
    │ published │ ← Success! Typefully URL acquired
    └───────────┘
```

### State Transition Rules

| From State | To State | Trigger | Conditions |
|------------|----------|---------|------------|
| (none) | proposed | Analyst Agent | New post-worthy commit found |
| proposed | approved | Human | Manual change in Notion or MD file |
| approved | drafting | Manager Agent | Writer agent dispatched |
| drafting | ready | Writer Agent | Draft file written to `data/drafts/` |
| ready | publishing | Manager Agent | Publisher agent dispatched |
| publishing | published | Publisher Agent | Typefully API returns success |
| * | failed | Any Agent | Error encountered (with retry logic) |

## File System Structure

```
social-media-manager/
│
├── .claude/                    # Claude Code configuration
│   ├── config.json            # MCP servers configuration
│   └── agents/                # Agent manifests
│       ├── manager-agent.md
│       ├── analyst-agent.md
│       ├── writer-agent.md
│       └── publisher-agent.md
│
├── data/                      # State and content storage
│   ├── tickets/               # ** SINGLE SOURCE OF TRUTH **
│   │   ├── TKT-001.md         # Individual ticket state
│   │   └── _TEMPLATE.md       # Ticket template
│   ├── context/               # Technical summaries
│   └── drafts/                # Social content (Typefully-ready)
│
├── scripts/                   # Executable logic
│   ├── run_pipeline.py       # Main orchestrator
│   ├── bridge_tickets.py      # Notion sync bridge
│   └── bridge_typefully.py    # Media/Typefully bridge
│
└── assets/                    # Media files for posts
```

### Why Ticket-Based State?

**Advantages**:
1. **Single Source of Truth**: One file per post, containing both metadata and rationale.
2. **Notion Integration**: `bridge_tickets.py` enables a professional UI via Notion.
3. **Concurrency Control**: Lock fields (`locked_by`, `locked_at`) prevent multiple agents from working on the same ticket.
4. **Audit Trail**: Git history shows exactly how a ticket evolved from `proposed` to `published`.

## Notion Integration

The `scripts/bridge_tickets.py` script acts as the synchronization layer between the local filesystem and a Notion Database.

### Sync Directions

1. **Local -> Notion**:
   - New `TKT-*.md` files are created as pages in Notion.
   - Updates to ticket metadata (priority, project) are pushed to Notion.
   - Draft content from `data/drafts/` is synced to a "Draft Content" property for easy review.

2. **Notion -> Local**:
   - Status changes in Notion (e.g., `PROPOSED` -> `APPROVED`) are pulled to local Markdown files.
   - This allows the user to manage the entire pipeline from a mobile Notion app or desktop dashboard.


## MCP Integration

### What is MCP?

Model Context Protocol (MCP) is a standardized way for LLMs to access external tools and data sources. Think of it as "USB-C for AI" - a universal connector.

### MCP Server Configuration

Each MCP server runs as a separate process, communicating via stdio or HTTP:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### How Agents Use MCP

When an agent needs to access GitHub:

1. Claude Code reads MCP config
2. Spawns the GitHub MCP server process
3. Server advertises available tools (e.g., `get_commit`)
4. Agent can call tools by name
5. MCP server translates to GitHub API calls
6. Results returned to agent in standardized format

```
Agent → Claude Code → MCP Client → MCP Server → GitHub API
                                        ↓
                                    Response
                                        ↓
Agent ← Claude Code ← MCP Client ← MCP Server
```

## Security Model

### Environment Isolation

- API keys in environment variables (never in code)
- `.env` file excluded from Git
- `--dangerously-skip-permissions` only for trusted scripts

### Human-in-the-Loop

Critical gate: **APPROVED** status required for publishing

```python
# Publisher Agent verification
if task.status != 'APPROVED':
    raise SecurityError("Cannot publish unapproved content")
```

Even if an agent is compromised, it cannot publish without human approval.

### Media Validation

Before uploading:
- File type validation (PNG, JPG, GIF, MP4 only)
- Size limits enforced
- Path traversal prevention

```python
def validate_media(file_path):
    if not file_path.exists():
        return False
    if file_path.suffix not in ALLOWED_TYPES:
        return False
    if file_path.stat().st_size > MAX_SIZE:
        return False
    return True
```

## Scalability Considerations

### Current Design

- Sequential processing (one task at a time)
- Synchronous agent calls
- Single pipeline instance

**Suitable for**:
- Individual developers
- Small teams (< 10 people)
- Low frequency (< 100 tasks/day)

### Scaling Options

**Parallel Processing**:
```python
# Process multiple TODO tasks concurrently
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_task, task) for task in todos]
```

**Background Queue**:
```python
# Use Celery or similar for async processing
@celery.task
def process_github_commit(commit_hash, repo):
    # ... processing logic
```

**Distributed State**:
- Replace tasks.md with Redis or PostgreSQL
- Add task locking mechanism
- Event-driven architecture

## Extension Points

### Adding New Agents

1. Create prompt file in `.claude/prompts/new_agent.md`
2. Add dispatch logic in `run_pipeline.py`:
```python
def process_custom_task(task, task_idx, lines):
    result = call_claude_agent(
        prompt=task['content'],
        system_prompt_path=PROMPTS_DIR / "new_agent.md",
        agent_name="NewAgent"
    )
    # Process result...
```

### Adding New MCP Servers

1. Update `.claude/config.json`:
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "npx",
      "args": ["-y", "linkedin-mcp-server"],
      "env": {
        "LINKEDIN_API_KEY": "${LINKEDIN_KEY}"
      }
    }
  }
}
```

2. Update agent prompts to use new tools

### Custom Media Processing

Add new handlers to `bridge_typefully.py`:

```python
def generate_video_thumbnail(video_path):
    # Use ffmpeg to extract frame
    subprocess.run(['ffmpeg', '-i', video_path, ...])

def optimize_image(image_path):
    # Use PIL or ImageMagick
    ...
```

## Comparison: Media Agent vs Traditional Automation

### Architecture Comparison

| Aspect | n8n / Zapier | Media Agent |
|--------|-------------|-------------|
| **Execution Model** | DAG workflow | Multi-agent orchestration |
| **State Storage** | Internal DB | Local files (Git-trackable) |
| **Logic Type** | If-then rules | LLM reasoning |
| **Extensibility** | Custom nodes | Any CLI tool |
| **Context Depth** | Webhook payload only | Full repo access |
| **Content Creation** | Templates | AI-generated |

### When to Use Each

**Use n8n/Zapier when**:
- Linear, predictable workflows
- Simple data transformations
- No natural language understanding needed
- Team prefers visual programming

**Use Media Agent when**:
- Content requires semantic understanding
- Creative/contextual output needed
- Workflow logic is complex or dynamic
- Developer-friendly tools preferred
- Version control of workflow is important

## Future Enhancements

### Planned Features

1. **Webhook Integration**
   - Auto-create tasks from GitHub pushes
   - Real-time commit monitoring

2. **Multi-Platform Support**
   - LinkedIn native posting
   - Mastodon integration
   - Discord/Slack notifications

3. **Analytics Integration**
   - Track engagement metrics
   - A/B test content variants
   - Learn from performance data

4. **Advanced Media**
   - Auto-generate code screenshots
   - Create demo GIFs from diffs
   - AI-generated cover images

5. **Collaborative Features**
   - Team review workflow
   - Approval delegation
   - Scheduled posting calendar

## Debugging and Monitoring

### Log Analysis

```bash
# View real-time logs
tail -f logs/pipeline_$(date +%Y%m%d).log

# Search for errors
grep ERROR logs/*.log

# Count successful completions
grep "DONE" logs/*.log | wc -l
```

### State Inspection

```bash
# Current task statuses
grep -E "\[.*\]" data/tasks.md | cut -d']' -f2 | cut -d'[' -f2 | sort | uniq -c

# Pending approvals
grep "WAITING_APPROVAL" data/tasks.md
```

### Agent Testing

Test individual agents without the full pipeline:

```bash
# Test Reader Agent
claude -p "$(cat .claude/prompts/reader.md)\n\nAnalyze commit abc123 in repo user/repo"

# Test Writer Agent
claude -p "$(cat .claude/prompts/writer.md)\n\nCreate thread from: $(cat data/context/summary.md)"
```

## Conclusion

The Media Agent system demonstrates how **LLM-powered multi-agent architectures** can create more flexible, intelligent automation than traditional workflow tools. By combining:

- **File-based state** for transparency
- **Specialized agents** for focused tasks
- **Human-in-the-loop** for quality control
- **MCP integration** for tool access

...we achieve a system that is both powerful and maintainable, suitable for individual developers and small teams building in public.

---

For implementation details, see [README.md](README.md)
For quick setup, see [QUICKSTART.md](QUICKSTART.md)

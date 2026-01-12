# Pipeline Manager Workflow Diagram

## Complete Workflow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ADDS TASK                          │
│                  (Edit data/tasks.md manually)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    [TODO] Status                               │
│  - [ ] [TODO] Analyze commit abc123 in repo user/project       │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ Pipeline Manager detects TODO
                         │
                         ▼
          ┌──────────────────────────┐
          │  Update to [PROCESSING]  │
          └──────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Dispatch to Agents   │
        └┬──────────────────────┬┘
         │                      │
         ▼                      │
┌───────────────────┐           │
│   Reader Agent    │           │
│  (if GitHub task) │           │
└────────┬──────────┘           │
         │                      │
         │ Creates summary      │
         │ data/context/        │
         │                      │
         ▼                      ▼
┌────────────────────────────────────┐
│        Writer Agent                │
│  Reads summary or topic            │
│  Creates social media content      │
└──────────────┬─────────────────────┘
               │
               │ Creates draft
               │ data/drafts/
               ▼
┌────────────────────────────────────────────────────────────────┐
│                   [WAITING_APPROVAL] Status                     │
│  - [ ] [WAITING_APPROVAL] ... | draft: data/drafts/abc_draft.md│
└────────────────────────────┬───────────────────────────────────┘
                             │
                             │
                   ┌─────────┴──────────┐
                   │                    │
                   │   HUMAN REVIEWS    │
                   │   - Read draft     │
                   │   - Edit if needed │
                   │   - Manually set   │
                   │     to [APPROVED]  │
                   │                    │
                   └─────────┬──────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                      [APPROVED] Status                          │
│  - [ ] [APPROVED] ... | draft: data/drafts/abc_draft.md        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ Pipeline Manager detects APPROVED
                         │
                         ▼
          ┌──────────────────────────┐
          │  Update to [PUBLISHING]  │
          └──────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Publisher Agent      │
        │  - Verify approval     │
        │  - Upload media        │
        │  - Create Typefully    │
        │    draft               │
        └────────┬───────────────┘
                 │
                 │ Returns Typefully URL
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                        [DONE] Status                            │
│  - [ ] [DONE] ... | published: https://typefully.com/t/xyz     │
└────────────────────────────────────────────────────────────────┘
                             │
                             │
                   ┌─────────┴──────────┐
                   │                    │
                   │   USER SCHEDULES   │
                   │   OR PUBLISHES     │
                   │   FROM TYPEFULLY   │
                   │   WEB APP          │
                   │                    │
                   └────────────────────┘
```

## State Transition Diagram

```
    TODO ────────┐
      │          │
      │          │ (on error)
      ▼          │
  PROCESSING ────┼──────────┐
      │          │          │
      │          │          │
      ▼          │          ▼
WAITING_APPROVAL │       FAILED
      │          │          │
      │ (human   │          │ (human fixes
      │  review) │          │  and retries)
      │          │          │
      ▼          │          │
  APPROVED ──────┼──────────┤
      │          │          │
      │          │          │
      ▼          │          │
  PUBLISHING ────┘          │
      │                     │
      │                     │
      ▼                     │
    DONE ◄──────────────────┘
                  (if fixed)
```

## Agent Interaction Flow

```
┌──────────────────┐
│ Pipeline Manager │  Orchestrates everything
└────┬──────┬─────┬┘
     │      │     │
     │      │     └──────────────┐
     │      │                    │
     │      └──────┐             │
     │             │             │
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ Reader  │  │ Writer  │  │Publisher │
│ Agent   │  │ Agent   │  │ Agent    │
└────┬────┘  └────┬────┘  └────┬─────┘
     │            │            │
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ GitHub  │  │ Local   │  │Typefully │
│   MCP   │  │ Files   │  │   MCP    │
└─────────┘  └─────────┘  └──────────┘
```

## Typical Task Lifecycle Timeline

```
Day 1, 9:00 AM
├─ User adds task to tasks.md
│  Status: [TODO]
│
├─ 9:05 AM: User runs pipeline
│  Status: [PROCESSING]
│
├─ 9:06 AM: Reader Agent analyzes commit
│  Output: data/context/abc123_summary.md
│
├─ 9:07 AM: Writer Agent creates content
│  Output: data/drafts/abc123_draft.md
│  Status: [WAITING_APPROVAL]
│
├─ 10:30 AM: Human reviews draft
│  Action: Minor edits, approve
│  Status: [APPROVED]
│
├─ 10:35 AM: User runs pipeline again
│  Status: [PUBLISHING]
│
├─ 10:36 AM: Publisher Agent uploads to Typefully
│  Output: https://typefully.com/t/xyz789
│  Status: [DONE]
│
└─ 2:00 PM: Human schedules post from Typefully UI
   Result: Post goes live on Twitter at scheduled time
```

## Error Handling Flow

```
                 [PROCESSING]
                      │
                      │ Error occurs
                      ▼
                  [FAILED]
                   │     │
                   │     └─ (If transient error: network, rate limit)
                   │        Pipeline Manager retries
                   │        └─→ Back to [TODO]
                   │
                   └─ (If permanent error: bad format, missing file)
                      Human intervention required
                      │
                      ├─ Fix issue
                      │  └─→ Change to [TODO]
                      │
                      └─ Or remove task if no longer needed
```

## Data Flow Through System

```
GitHub Commit
    │
    ▼
┌───────────────────┐
│  Reader Agent     │
│  ┌──────────┐     │
│  │ Fetch    │     │ ──→ GitHub MCP
│  │ Analyze  │     │
│  │ Summarize│     │
│  └─────┬────┘     │
└────────┼──────────┘
         │
         ▼
    summary.md
         │
         ▼
┌───────────────────┐
│  Writer Agent     │
│  ┌──────────┐     │
│  │ Read     │     │ ←── summary.md
│  │ Transform│     │
│  │ Format   │     │
│  └─────┬────┘     │
└────────┼──────────┘
         │
         ▼
    draft.md
         │
         │ [Human reviews & approves]
         │
         ▼
┌───────────────────┐
│  Publisher Agent  │
│  ┌──────────┐     │
│  │ Parse    │     │ ←── draft.md
│  │ Upload   │     │ ──→ Typefully MCP
│  │ Publish  │     │
│  └─────┬────┘     │
└────────┼──────────┘
         │
         ▼
    Typefully Draft URL
         │
         ▼
    [Human schedules from Typefully]
         │
         ▼
    Live on Social Media
```

## Parallel Processing (Future Enhancement)

```
Current: Sequential
┌────────┐    ┌────────┐    ┌────────┐
│ Task 1 │ ─→ │ Task 2 │ ─→ │ Task 3 │
└────────┘    └────────┘    └────────┘
   2 min         2 min         2 min
   Total: 6 minutes

Future: Parallel (if implemented)
┌────────┐
│ Task 1 │
└────┬───┘
     │
┌────┼───┐
│ Task 2 │
└────┼───┘
     │
┌────▼───┐
│ Task 3 │
└────────┘
   All start simultaneously
   Total: ~2 minutes
```

## File System State

```
Project Root
│
├── data/
│   ├── tasks.md ◄─────────────── Single source of truth
│   │                             (All state stored here)
│   │
│   ├── context/ ◄─────────────── Reader Agent outputs
│   │   ├── abc123_summary.md
│   │   ├── def456_summary.md
│   │   └── ...
│   │
│   └── drafts/ ◄──────────────── Writer Agent outputs
│       ├── abc123_draft.md
│       ├── def456_draft.md
│       └── ...
│
├── logs/ ◄────────────────────── Execution logs
│   ├── pipeline_manager_20240110.log
│   ├── reader_agent_20240110.log
│   ├── writer_agent_20240110.log
│   └── publisher_agent_20240110.log
│
└── skills/ ◄──────────────────── Agent definitions
    ├── reader-agent/
    ├── writer-agent/
    ├── publisher-agent/
    └── pipeline-manager/
```

## Integration Points

```
External Systems
├── GitHub (via MCP)
│   └─→ Reader Agent fetches commits
│
├── Typefully (via MCP + bridge script)
│   ├─→ Publisher Agent creates drafts
│   └─→ bridge_typefully.py handles media
│
└── File System (via MCP)
    ├─→ All agents read/write local files
    └─→ tasks.md is the state machine
```

## Key Decision Points

```
1. New Task Detected
   ├─ Contains "commit" + "repo"? ──→ GitHub workflow
   ├─ Contains "summary:"? ─────────→ Direct to Writer
   ├─ Contains "Write about:"? ─────→ Free-form Writer
   └─ None match? ──────────────────→ Mark as FAILED

2. Draft Created
   ├─ Auto-approve? ────────────────→ NO (security)
   └─ Human review required ─────────→ WAITING_APPROVAL

3. Publishing
   ├─ Status = APPROVED? ───────────→ Proceed
   └─ Status ≠ APPROVED? ───────────→ BLOCK (security)

4. Error Occurred
   ├─ Transient (network)? ─────────→ Retry
   ├─ Rate limit? ──────────────────→ Wait and retry
   └─ Permanent (bad data)? ────────→ Mark FAILED, need fix
```

## Security Gates

```
┌────────────────────────────────────────────┐
│          APPROVAL GATE (Required)          │
│                                            │
│  Human must explicitly change:             │
│  [WAITING_APPROVAL] ──→ [APPROVED]         │
│                                            │
│  No bypass. No automation. Period.         │
└────────────────────────────────────────────┘
         │
         │ Only after this gate...
         ▼
┌────────────────────────────────────────────┐
│         PUBLISHING ALLOWED                 │
└────────────────────────────────────────────┘
```

---

## Summary

The Pipeline Manager orchestrates a multi-stage workflow where:

1. **Detection**: Scans tasks.md for work
2. **Dispatch**: Routes to appropriate agents
3. **Sequential Processing**: Reader → Writer (for GitHub tasks)
4. **Human Gate**: Requires explicit approval
5. **Publishing**: Only after approval
6. **State Management**: All state in tasks.md (transparent, Git-friendly)

**Key principle**: Automation assists, humans decide.

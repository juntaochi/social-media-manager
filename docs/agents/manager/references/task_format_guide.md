# Task Format Guide for tasks.md

## Overview

`data/tasks.md` is the single source of truth for the Media Agent system. It serves as both a task queue and a state machine. This document defines the syntax and patterns for task entries.

## Basic Syntax

### Task Line Format

```markdown
- [ ] [STATUS] Task description | metadata
```

**Components**:
1. `- [ ]` - Markdown checkbox (always unchecked for this system)
2. `[STATUS]` - Current state of the task (see Status Values below)
3. `Task description` - Human-readable description of what to do
4. `| metadata` - Optional key-value pairs (separated by `|`)

### Example
```markdown
- [ ] [TODO] Analyze commit abc123 in repo username/project-name
- [ ] [WAITING_APPROVAL] Create thread about new feature | draft: data/drafts/feature_draft.md
- [ ] [DONE] API optimization post | published: https://typefully.com/t/xyz789
```

## Status Values

### Valid Statuses

| Status | Meaning | Set By | Next State |
|--------|---------|--------|------------|
| `TODO` | New task, not started | Human | PROCESSING |
| `PROCESSING` | Currently being worked on | Pipeline | WAITING_APPROVAL or FAILED |
| `WAITING_APPROVAL` | Draft created, needs review | Pipeline | APPROVED or TODO (if needs rework) |
| `APPROVED` | Human approved for publishing | **Human** | PUBLISHING |
| `PUBLISHING` | Currently publishing | Pipeline | DONE or FAILED |
| `DONE` | Successfully completed | Pipeline | (terminal) |
| `FAILED` | Error occurred | Pipeline | TODO (retry) or (remove task) |

### State Transition Rules

**Automated Transitions** (by Pipeline Manager):
- `TODO` → `PROCESSING` (when work starts)
- `PROCESSING` → `WAITING_APPROVAL` (when draft created)
- `PROCESSING` → `FAILED` (on error)
- `APPROVED` → `PUBLISHING` (when publishing starts)
- `PUBLISHING` → `DONE` (when publishing succeeds)
- `PUBLISHING` → `FAILED` (on error)

**Manual Transitions** (by Human):
- `WAITING_APPROVAL` → `APPROVED` (after reviewing draft)
- `WAITING_APPROVAL` → `TODO` (if draft needs major rework)
- `FAILED` → `TODO` (to retry after fixing issue)
- Any → (delete line) (to cancel/remove task)

**CRITICAL**: Only humans can set status to `APPROVED`. This is a security feature.

## Task Types

### Type 1: GitHub Commit Analysis

Analyze a specific commit and create social media content.

**Format**:
```markdown
- [ ] [TODO] Analyze commit <commit_hash> in repo <owner>/<repo-name>
```

**Required Keywords**:
- `commit` followed by commit hash (7-40 hex characters)
- `repo` followed by repository in `owner/name` format

**Examples**:
```markdown
- [ ] [TODO] Analyze commit abc123 in repo vercel/next.js
- [ ] [TODO] Analyze commit 7f3a9c2e1d in repo facebook/react
- [ ] [TODO] Analyze commit def456 in repo myusername/my-project
```

**What Happens**:
1. Pipeline calls Reader Agent to analyze commit
2. Summary saved to `data/context/{commit}_summary.md`
3. Pipeline calls Writer Agent to create social content
4. Draft saved to `data/drafts/{commit}_draft.md`
5. Status updated to `WAITING_APPROVAL`

**Variations**:
```markdown
- [ ] [TODO] Create social post for commit xyz789 in repo user/project
- [ ] [TODO] Write about commit abc123 from repo owner/name
```
(Pipeline recognizes these patterns too)

---

### Type 2: From Existing Summary

Create social content from an already-existing technical summary.

**Format**:
```markdown
- [ ] [TODO] Create social post from summary: <path/to/summary.md>
```

**Required Keywords**:
- `summary:` followed by file path (must end in `.md`)

**Examples**:
```markdown
- [ ] [TODO] Create social post from summary: data/context/feature_summary.md
- [ ] [TODO] Write thread from summary: data/context/bug_fix_analysis.md
```

**What Happens**:
1. Pipeline verifies summary file exists
2. Pipeline calls Writer Agent with summary path
3. Draft saved to `data/drafts/{timestamp}_draft.md`
4. Status updated to `WAITING_APPROVAL`

**Note**: Skips Reader Agent since summary already exists.

---

### Type 3: Free-Form Topic

Create social content about a general topic (no specific commit).

**Format**:
```markdown
- [ ] [TODO] Write about: <topic description>
```

**Required Keywords**:
- `Write about:` followed by topic text

**Examples**:
```markdown
- [ ] [TODO] Write about: implementing dark mode with CSS variables
- [ ] [TODO] Write about: why we chose PostgreSQL over MongoDB
- [ ] [TODO] Write about: lessons learned from our first product launch
```

**What Happens**:
1. Pipeline calls Writer Agent with topic text
2. Writer Agent may research topic (web search) if needed
3. Draft saved to `data/drafts/{timestamp}_draft.md`
4. Status updated to `WAITING_APPROVAL`

**Note**: No Reader Agent involved, goes straight to Writer.

---

## Metadata Format

Metadata provides additional context and state information.

### Basic Format
```markdown
| key1: value1, key2: value2, key3: value3
```

### Common Metadata Keys

#### `draft:`
Path to the draft file created by Writer Agent.

**Example**:
```markdown
- [ ] [WAITING_APPROVAL] Analyze commit abc123 | draft: data/drafts/abc123_draft.md
```

**Set by**: Pipeline Manager (Writer Agent completion)

---

#### `published:`
Typefully URL where content was published.

**Example**:
```markdown
- [ ] [DONE] Feature launch post | published: https://typefully.com/t/xyz789abc
```

**Set by**: Pipeline Manager (Publisher Agent completion)

---

#### `error:`
Error message if task failed.

**Example**:
```markdown
- [ ] [FAILED] Analyze commit xyz | error: Commit not found in repository
```

**Set by**: Pipeline Manager (on failure)

---

#### `started:`
ISO timestamp when processing began.

**Example**:
```markdown
- [ ] [PROCESSING] Analyze commit abc | started: 2024-01-10T10:30:00Z
```

**Set by**: Pipeline Manager (optional, for tracking)

---

#### `priority:`
Task priority (high, medium, low).

**Example**:
```markdown
- [ ] [TODO] URGENT bug fix post | priority: high
```

**Set by**: Human (optional)

**Used by**: Pipeline Manager to order tasks (future feature)

---

### Multiple Metadata Values

Combine multiple metadata keys with commas:
```markdown
- [ ] [DONE] Commit abc123 | draft: data/drafts/abc_draft.md, published: https://typefully.com/t/xyz, completed: 2024-01-10T11:00:00Z
```

Or use multiple `|` separators:
```markdown
- [ ] [DONE] Commit abc123 | draft: data/drafts/abc_draft.md | published: https://typefully.com/t/xyz
```

(Both formats are valid)

---

## File Structure

### Complete tasks.md Example

```markdown
# Media Agent Tasks

This file tracks all social media content tasks. The Pipeline Manager reads this file to determine what work needs to be done.

## Status Guide
- TODO: New task, needs processing
- PROCESSING: Currently being worked on
- WAITING_APPROVAL: Draft created, needs human review
- APPROVED: Human approved, ready to publish
- PUBLISHING: Currently publishing to Typefully
- DONE: Successfully published
- FAILED: Error occurred, needs attention

---

## Active Tasks

- [ ] [TODO] Analyze commit 7f3a9c2 in repo vercel/next.js
- [ ] [TODO] Write about: implementing dark mode with CSS variables
- [ ] [PROCESSING] Analyze commit abc123 in repo user/project | started: 2024-01-10T10:30:00Z
- [ ] [WAITING_APPROVAL] Feature launch post | draft: data/drafts/feature_draft.md
- [ ] [WAITING_APPROVAL] Bug fix explanation | draft: data/drafts/bugfix_draft.md
- [ ] [APPROVED] API optimization thread | draft: data/drafts/api_draft.md

## Completed Tasks

- [ ] [DONE] Authentication refactor post | published: https://typefully.com/t/xyz789
- [ ] [DONE] Performance improvements | published: https://typefully.com/t/abc123
- [ ] [DONE] Q4 roadmap update | published: https://typefully.com/t/def456

## Failed Tasks

- [ ] [FAILED] Invalid task | error: Missing repository name
- [ ] [FAILED] Old commit analysis | error: Commit not found (repo may be private)

---

## Notes

To add a new task:
1. Add a line with [TODO] status
2. Use one of the supported formats (see documentation)
3. Run: codex "use the pipeline-manager skill to process all tasks"

To approve a draft:
1. Review the draft file listed in metadata
2. Make any necessary edits
3. Change status from [WAITING_APPROVAL] to [APPROVED]
4. Run pipeline again to publish

---

_Last updated: 2024-01-10_
```

---

## Best Practices

### Organization

**Group by Status**:
```markdown
## Active Tasks
[TODO, PROCESSING, WAITING_APPROVAL, APPROVED, PUBLISHING tasks here]

## Completed Tasks
[DONE tasks here]

## Failed Tasks
[FAILED tasks here]
```

This makes it easy to see what needs attention.

---

### Descriptive Task Names

❌ **Bad** (vague):
```markdown
- [ ] [TODO] Analyze commit abc123
- [ ] [TODO] Write post
```

✅ **Good** (descriptive):
```markdown
- [ ] [TODO] Analyze commit abc123 in repo vercel/next.js - dark mode feature
- [ ] [TODO] Write about: switching from REST to GraphQL - lessons learned
```

Include enough context so you remember what the task is about later.

---

### Inline Comments

Use Markdown comments to add notes:
```markdown
<!-- Priority task - launch is this Friday -->
- [ ] [TODO] Analyze commit xyz789 in repo user/project

<!-- Waiting for legal approval before publishing -->
- [ ] [WAITING_APPROVAL] New pricing announcement | draft: data/drafts/pricing.md
```

Comments are ignored by the Pipeline Manager.

---

### Archiving Old Tasks

Keep tasks.md manageable by archiving completed tasks:

**Option 1**: Move DONE tasks to a separate file
```markdown
## Completed Tasks
(See completed_tasks_archive.md for older completed tasks)

[Only recent DONE tasks here]
```

**Option 2**: Use dated sections
```markdown
## Completed - January 2024
[January tasks]

## Completed - December 2023
[December tasks]
```

**Option 3**: Delete very old DONE tasks
(They're in Git history anyway)

---

### Task Identifiers

Include identifiers for easy reference:
```markdown
- [ ] [TODO] [TASK-101] Analyze commit abc123 in repo user/project
- [ ] [TODO] [TASK-102] Write about: GraphQL migration
```

Makes it easier to discuss specific tasks in team communication.

---

## Advanced Patterns

### Dependent Tasks

Show dependencies with inline comments:
```markdown
<!-- Depends on TASK-101 completing -->
- [ ] [TODO] [TASK-102] Write about: How we optimized the database | depends: TASK-101
```

**Note**: Pipeline Manager doesn't automatically handle dependencies yet (processes sequentially).

---

### Batch Tasks

Group related tasks:
```markdown
## Sprint 5 - Auth Improvements
- [ ] [TODO] Analyze commit abc123 - OAuth implementation
- [ ] [TODO] Analyze commit def456 - JWT token refresh
- [ ] [TODO] Analyze commit ghi789 - 2FA support
```

---

### Recurring Tasks

For regular content:
```markdown
## Weekly Updates
- [ ] [TODO] Write about: Week of Jan 8-12 progress update
- [ ] [DONE] Write about: Week of Jan 1-5 progress update | published: https://...

(Add new week, mark old week as DONE)
```

---

### Media Notes

Note media requirements in the description:
```markdown
- [ ] [TODO] Analyze commit abc123 - dark mode UI [NEEDS SCREENSHOTS]
- [ ] [TODO] Write about: Performance optimization [INCLUDE GRAPHS]
```

Writer Agent will see these and include media placeholders.

---

## Validation Rules

The Pipeline Manager validates tasks:

### ✅ Valid Tasks

```markdown
- [ ] [TODO] Analyze commit abc123 in repo user/project
- [ ] [WAITING_APPROVAL] Post draft | draft: data/drafts/file.md
- [ ] [DONE] Published post | published: https://typefully.com/t/xyz
```

### ❌ Invalid Tasks

```markdown
- [ ] [] Missing status
- [x] [TODO] Checkbox marked (should always be [ ])
- [ ] [UNKNOWN_STATUS] Unrecognized status
- [ ] [TODO] Analyze commit abc123 (missing repo)
- [ ] [APPROVED] Ready to publish (missing draft path in metadata)
```

**What Happens**:
- Invalid tasks are skipped
- Warning logged
- Task may be marked `[FAILED]` with error

---

## Git Integration

### Committing tasks.md

**Do commit**:
- Task history (transparency)
- Status updates (show progress)
- Metadata (draft paths, URLs)

**Don't commit** (use .gitignore):
- Temporary processing files
- Lock files
- Backup files (*.tmp, *.bak)

### Branching

Can use branches for different content pipelines:
```bash
main - Production content
feature/q1-launch - Special campaign
experiment/new-format - Testing new content style
```

Each branch has its own `data/tasks.md`.

---

## Troubleshooting

### Task Not Processing

**Check**:
1. Status is exactly `[TODO]` (case-sensitive)
2. Format matches one of the three types
3. Required keywords present (commit + repo, summary:, or Write about:)
4. File paths in metadata exist
5. No typos in status value

### Task Stuck in PROCESSING

**Reasons**:
- Pipeline Manager crashed mid-execution
- Long-running operation timed out
- Manual intervention needed

**Fix**:
- Check logs: `logs/pipeline_manager_YYYYMMDD.log`
- If safe, change back to `[TODO]` to retry
- Or mark `[FAILED]` with error note

### Duplicate Tasks

**Avoid**:
```markdown
- [ ] [TODO] Analyze commit abc123 in repo user/project
- [ ] [TODO] Analyze commit abc123 in repo user/project (duplicate!)
```

**Solution**:
- Pipeline processes both (creates duplicate drafts)
- Remove duplicates manually
- Use unique task identifiers to prevent

---

## Quick Reference

### Task Type Templates

```markdown
# GitHub Commit Analysis
- [ ] [TODO] Analyze commit <hash> in repo <owner>/<name>

# From Summary
- [ ] [TODO] Create social post from summary: <path/to/summary.md>

# Free-Form Topic
- [ ] [TODO] Write about: <topic description>
```

### Status Flow
```
TODO → PROCESSING → WAITING_APPROVAL → (human approval) → APPROVED → PUBLISHING → DONE
                 ↓                                              ↓
              FAILED ←-----------← (retry) ←-------------------┘
```

### Common Metadata
```markdown
| draft: data/drafts/file.md
| published: https://typefully.com/t/xyz
| error: Error message here
| priority: high
| started: 2024-01-10T10:30:00Z
```

---

## FAQ

**Q: Can I edit tasks while the pipeline is running?**
A: Not recommended. May cause race conditions. Wait for pipeline to complete.

**Q: Can I have multiple tasks with same commit hash?**
A: Yes, but they'll create separate drafts. Usually not desired.

**Q: What if I want to cancel a task?**
A: Delete the line or change status to `[FAILED] | error: Cancelled by user`

**Q: Can I manually move a task to DONE without publishing?**
A: Yes, but it won't have a Typefully URL. Better to let pipeline handle it.

**Q: Do I need to keep DONE tasks forever?**
A: No, archive or delete old DONE tasks to keep file manageable.

**Q: Can the pipeline process tasks in parallel?**
A: Not currently. Tasks are processed sequentially (one at a time).

**Q: What happens if two people edit tasks.md simultaneously?**
A: Git merge conflict. Resolve manually. Use locking or coordination to avoid.

---

**Remember**: `data/tasks.md` is your workflow. Shape it to fit your needs while following the basic syntax rules.

---
id: TKT-000-TEMPLATE
status: template
source: system
project: ""
type: ""
platforms: []
priority: medium
created: ""
approved: ""
published: ""
typefully_draft_id: ""
locked_by: ""
locked_at: ""
error: ""
retry_count: 0
---

# [Ticket Title]

## Rationale
Why this content should be created.

## Suggested Angle
Content direction and key points to cover.

## Reference
- Commits: []
- Files: []
- Links: []

---

## Field Reference

**status values:**
- `proposed` - AI or user created, awaiting approval
- `approved` - Ready for Writer to process  
- `drafting` - Writer is generating content
- `ready` - Draft created, sent to Typefully
- `publishing` - Publisher is sending to Typefully
- `published` - Successfully published
- `rejected` - Will not be published
- `failed` - Error occurred, see error field

**type values:**
- `introduction` - First post about a project
- `feature` - New feature announcement
- `update` - Improvements, optimizations
- `bugfix` - Bug fix story
- `milestone` - Progress update, achievements
- `deepdive` - Technical deep dive

**source values:**
- `ai` - Created by Analyst agent
- `user` - Created by you manually

**priority values:**
- `high` - Should be processed soon
- `medium` - Normal priority
- `low` - When there's time

**lock fields (for concurrency control):**
- `locked_by` - Agent currently processing (writer/publisher)
- `locked_at` - ISO timestamp when lock was acquired
- Lock expires after 10 minutes (stale lock protection)

**error handling:**
- `error` - Error message if status is failed
- `retry_count` - Number of retry attempts

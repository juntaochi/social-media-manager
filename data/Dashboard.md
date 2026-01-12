# Content Pipeline Dashboard

## Tickets by Status

### 🟡 Proposed (Awaiting Approval)
```dataview
TABLE type, project, priority, created
FROM "data/tickets"
WHERE status = "proposed"
SORT priority DESC, created ASC
```

### 🟢 Approved (Ready for Writing)
```dataview
TABLE type, project, priority
FROM "data/tickets"
WHERE status = "approved"
SORT created ASC
```

### 📝 Drafting
```dataview
TABLE type, project
FROM "data/tickets"
WHERE status = "drafting"
```

### ✅ Ready (Pending Publish)
```dataview
TABLE type, project
FROM "data/tickets"
WHERE status = "ready"
```

### 🚀 Recently Published
```dataview
TABLE type, project, published
FROM "data/tickets"
WHERE status = "published"
SORT published DESC
LIMIT 10
```

---

## Quick Actions

To approve a ticket:
1. Open the ticket file
2. Change `status: proposed` → `status: approved`
3. Run `./scripts/run_pipeline.sh write`

To reject a ticket:
1. Open the ticket file  
2. Change `status: proposed` → `status: rejected`

---

## Projects

```dataview
TABLE stage, introduced, last_post
FROM "data/projects"
```

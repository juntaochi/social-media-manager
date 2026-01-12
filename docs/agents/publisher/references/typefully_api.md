# Typefully API Reference

## Overview

Typefully is a writing and scheduling tool for Twitter/X and LinkedIn. This document covers the API endpoints used by the Publisher Agent.

**Base URL**: `https://api.typefully.com/v1/`

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer your_api_key_here
```

## API Key Setup

1. Log into Typefully: https://typefully.com
2. Go to Settings → API
3. Generate an API key
4. Add to `.env` file:
```bash
TYPEFULLY_API_KEY=tf_your_key_here
```

## Endpoints Used

### 1. Create Draft

**Endpoint**: `POST /drafts`

**Purpose**: Create a new draft post (thread or single post)

**Request Body**:
```json
{
  "content": ["Tweet 1 text", "Tweet 2 text", "Tweet 3 text"],
  "media_ids": ["media_id_1", "media_id_2"],
  "share": {
    "twitter": true,
    "linkedin": false
  },
  "schedule_date": null
}
```

**Parameters**:
- `content` (array, required): Array of strings, each element is one tweet/post
- `media_ids` (array, optional): Array of media IDs from upload endpoint
- `share` (object, optional): Which platforms to share to (default: twitter only)
- `schedule_date` (string, optional): ISO 8601 timestamp for scheduled posting (null = draft only)

**Response**:
```json
{
  "id": "draft_abc123def456",
  "url": "https://typefully.com/t/abc123",
  "status": "draft",
  "created_at": "2024-01-10T10:30:00Z",
  "share": {
    "twitter": true,
    "linkedin": false
  }
}
```

**Character Limits**:
- Twitter/X: 280 characters per tweet
- LinkedIn: 3,000 characters per post

**Example**:
```bash
curl -X POST https://api.typefully.com/v1/drafts \
  -H "Authorization: Bearer $TYPEFULLY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": [
      "Just shipped a new feature 🚀",
      "Here'\''s what it does...",
      "Try it out: https://example.com"
    ],
    "share": {
      "twitter": true
    }
  }'
```

---

### 2. Upload Media

**Endpoint**: `POST /media`

**Purpose**: Upload an image or video to attach to a post

**Request**: `multipart/form-data`

**Form Data**:
- `file` (binary, required): The media file

**Supported Formats**:
- Images: PNG, JPG, JPEG, GIF, WEBP
- Videos: MP4, MOV
- Max size: 50MB

**Response**:
```json
{
  "id": "media_abc123def456",
  "url": "https://cdn.typefully.com/uploads/...",
  "type": "image",
  "width": 1200,
  "height": 630,
  "size": 245680
}
```

**Example**:
```bash
curl -X POST https://api.typefully.com/v1/media \
  -H "Authorization: Bearer $TYPEFULLY_API_KEY" \
  -F "file=@/path/to/image.png"
```

**Note**: The media ID returned must be used in the `create_draft` call's `media_ids` array.

---

### 3. Get Draft

**Endpoint**: `GET /drafts/:id`

**Purpose**: Retrieve details of a specific draft

**Response**:
```json
{
  "id": "draft_abc123",
  "content": ["Tweet 1", "Tweet 2"],
  "media_ids": ["media_xyz"],
  "status": "draft",
  "schedule_date": null,
  "created_at": "2024-01-10T10:30:00Z",
  "updated_at": "2024-01-10T10:35:00Z"
}
```

---

### 4. List Drafts

**Endpoint**: `GET /drafts`

**Purpose**: List all drafts in your account

**Query Parameters**:
- `limit` (int, optional): Number of results (default: 20, max: 100)
- `offset` (int, optional): Pagination offset

**Response**:
```json
{
  "drafts": [
    { "id": "draft_1", "content": [...], ... },
    { "id": "draft_2", "content": [...], ... }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

---

### 5. Schedule Post

**Endpoint**: `PATCH /drafts/:id/schedule`

**Purpose**: Schedule a draft for future publishing

**Request Body**:
```json
{
  "schedule_date": "2024-01-15T14:00:00Z"
}
```

**Response**:
```json
{
  "id": "draft_abc123",
  "status": "scheduled",
  "schedule_date": "2024-01-15T14:00:00Z"
}
```

---

### 6. Publish Now

**Endpoint**: `POST /drafts/:id/publish`

**Purpose**: Immediately publish a draft

**Response**:
```json
{
  "id": "draft_abc123",
  "status": "published",
  "published_at": "2024-01-10T10:45:00Z",
  "tweet_ids": {
    "twitter": ["1234567890123456789", "9876543210987654321"]
  }
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "invalid_token",
  "message": "The provided API key is invalid or expired"
}
```

**Fix**: Check TYPEFULLY_API_KEY environment variable

---

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Content exceeds character limit",
  "details": {
    "tweet_index": 2,
    "characters": 315,
    "limit": 280
  }
}
```

**Fix**: Shorten the tweet content or split into more tweets

---

### 413 Payload Too Large
```json
{
  "error": "file_too_large",
  "message": "Media file exceeds 50MB limit",
  "details": {
    "size": 62914560,
    "limit": 52428800
  }
}
```

**Fix**: Compress or resize the media file

---

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

**Fix**: Wait for `retry_after` seconds before retrying

---

### 415 Unsupported Media Type
```json
{
  "error": "unsupported_media",
  "message": "File type not supported",
  "details": {
    "type": "application/pdf",
    "supported": ["image/png", "image/jpeg", "video/mp4", ...]
  }
}
```

**Fix**: Convert to a supported format

---

## Rate Limits

**Standard Plan**:
- 100 requests per hour
- 1,000 requests per day

**Pro Plan**:
- 500 requests per hour
- 10,000 requests per day

**Headers included in response**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1704888000
```

If rate limited, wait until the `X-RateLimit-Reset` timestamp (Unix timestamp).

---

## Media Upload Workflow

The complete media workflow using the bridge script:

### Step 1: Upload Media
```bash
python3 skills/publisher-agent/scripts/bridge_typefully.py upload --file assets/screenshot.png
```

**Response**:
```json
{
  "media_id": "media_abc123",
  "url": "https://cdn.typefully.com/...",
  "type": "image"
}
```

### Step 2: Create Draft with Media
Using MCP tool or API:
```json
{
  "content": ["Check out this new feature!", "Screenshot below 👇"],
  "media_ids": ["media_abc123"]
}
```

**Note**: Media is attached to the FIRST tweet by default in Typefully.

---

## Best Practices

### Threading
- Each array element in `content` becomes one tweet
- Maintain logical flow between tweets
- Use thread continuation markers if needed: "→" or "(cont.)"

### Media
- Upload media BEFORE creating draft
- Media IDs expire after 24 hours if unused
- One media per tweet (attach to specific tweet by position)
- For multiple media, upload each separately

### Character Counting
- URLs count as 23 characters on Twitter (after shortening)
- @mentions and #hashtags count as full length
- Emojis count as 1-2 characters
- Line breaks count as 1 character

### Scheduling
- Use ISO 8601 format: `2024-01-15T14:00:00Z`
- Timezone: Always UTC (append `Z`)
- Minimum: 10 minutes in future
- Maximum: 1 year in future

### Error Handling
- Always check response status codes
- Log errors with full details
- Retry on 429 (rate limit) after waiting
- Don't retry on 400 (bad request) - fix the data
- Retry on 500 (server error) with exponential backoff

---

## Typefully MCP Server Notes

The community Typefully MCP server provides these tools:

### Available MCP Tools

**create_draft**
- Input: content (array), media_ids (array), platform (string)
- Output: draft_id, url
- Maps to: `POST /drafts`

**get_draft**
- Input: draft_id (string)
- Output: draft details
- Maps to: `GET /drafts/:id`

**list_drafts**
- Input: limit (number), offset (number)
- Output: array of drafts
- Maps to: `GET /drafts`

### MCP Limitations

Current limitations in the MCP implementation:
- Media upload not directly supported (use bridge script)
- Scheduling requires separate call
- No bulk operations
- Limited error details

This is why we use the `bridge_typefully.py` script for media uploads.

---

## Testing

### Test with cURL

```bash
# Test API key
curl -X GET https://api.typefully.com/v1/drafts \
  -H "Authorization: Bearer $TYPEFULLY_API_KEY"

# Create test draft
curl -X POST https://api.typefully.com/v1/drafts \
  -H "Authorization: Bearer $TYPEFULLY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": ["Test tweet from API"],
    "share": {"twitter": true}
  }'
```

### Test with Python

```python
import requests
import os

API_KEY = os.environ.get('TYPEFULLY_API_KEY')
BASE_URL = 'https://api.typefully.com/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Create draft
response = requests.post(
    f'{BASE_URL}/drafts',
    headers=headers,
    json={
        'content': ['Test tweet'],
        'share': {'twitter': True}
    }
)

print(response.json())
```

---

## Additional Resources

- **Typefully Docs**: https://docs.typefully.com/api
- **API Status**: https://status.typefully.com
- **Support**: support@typefully.com
- **Community**: https://twitter.com/typefully

---

## Quick Reference

| Action | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| Create draft | `/drafts` | POST | Yes |
| Get draft | `/drafts/:id` | GET | Yes |
| List drafts | `/drafts` | GET | Yes |
| Upload media | `/media` | POST | Yes |
| Schedule | `/drafts/:id/schedule` | PATCH | Yes |
| Publish | `/drafts/:id/publish` | POST | Yes |

**Remember**: Always upload media first, then create draft with media_ids.

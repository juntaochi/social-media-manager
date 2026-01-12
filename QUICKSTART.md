# Quick Start Guide

Get your Media Agent system up and running in 5 minutes!

## Prerequisites Check

```bash
# Check if OpenCode is installed
opencode --version

# Check Python version (need 3.8+)
python3 --version

# Check Node.js (need 18+)
node --version
```

If any are missing, install them first:
- OpenCode: https://opencode.ai/docs/install
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

## 1. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Add your API keys:
```bash
GITHUB_TOKEN=ghp_your_github_token_here
TYPEFULLY_KEY=your_typefully_api_key_here
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### Get API Keys

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: `repo` (full control)
4. Copy the token to your .env file

**Typefully API Key:**
1. Go to https://typefully.com/settings/api
2. Generate a new API key
3. Copy to your .env file

**Notion Token & Database ID:**
1. Create a new integration at https://www.notion.so/my-integrations
2. Copy the "Internal Integration Token"
3. Create a Notion database with properties: `Task ID` (Title), `Status` (Select), `Content` (Rich Text), `Type` (Select), `Draft Content` (Rich Text).
4. Share the database with your integration.
5. Copy the Database ID from the URL (the part between the workspace name and the `?v=`).

## 2. Load Environment

```bash
# Load environment variables into your shell
export $(cat .env | grep -v '^#' | xargs)

# Verify they're loaded
echo $GITHUB_TOKEN  # Should show your token
```

**TIP:** For persistent loading, add to your shell profile or use `direnv`:
```bash
echo 'export $(cat .env | grep -v "^#" | xargs)' > .envrc
direnv allow
```

## 3. Install Dependencies

```bash
# Install Python dependencies
pip3 install requests

# MCP servers will auto-install via npx on first run
```

## 4. Test the System

### Test 1: Verify Environment

```bash
python3 << 'EOF'
import os
import sys

checks = {
    'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN'),
    'TYPEFULLY_KEY': os.getenv('TYPEFULLY_KEY')
}

print("Environment Check:")
print("-" * 40)
for key, value in checks.items():
    status = "✓" if value else "✗"
    display = f"{value[:10]}..." if value else "NOT SET"
    print(f"{status} {key}: {display}")

all_set = all(checks.values())
print("-" * 40)
print("Result:", "✓ All set!" if all_set else "✗ Missing keys")
sys.exit(0 if all_set else 1)
EOF
```

### Test 2: Test OpenCode CLI

```bash
# Simple test to ensure OpenCode works
opencode "Say 'System ready!' if you can read this."
```

You should see: "System ready!" in the output.

## 5. Run Your First Task

The system uses a Ticket-centric workflow. You can manage tickets via Notion or directly in the `data/tickets/` directory.

### Step 1: Sync with Notion (Optional)

If you're using Notion, start by syncing your local tickets:

```bash
python3 scripts/bridge_tickets.py
```

### Step 2: Propose Content

Run the **Analyst Agent** to scan your projects and propose new content:

```bash
# Propose content based on recent activity
opencode @analyst-agent "Scan projects and propose new tickets"
```

This will create new tickets in `data/tickets/` with status `proposed`.

### Step 3: Approve Tickets

1. Open your Notion Dashboard (or edit the Markdown files in `data/tickets/`).
2. Change the status of a ticket from `proposed` to `approved`.
3. If using Notion, sync back to local:
   ```bash
   python3 scripts/bridge_tickets.py
   ```

### Step 4: Run the Pipeline

Invoke the **Manager Agent** to process all approved tickets:

```bash
# The manager will dispatch to Writer and Publisher agents
opencode @manager-agent "Process all approved tickets"
```

### Manual Ticket Flow (CLI Only)

1. **Create a Ticket**:
   ```bash
   cp data/tickets/_TEMPLATE.md data/tickets/TKT-003.md
   # Edit TKT-003.md and set status: approved
   ```

2. **Run Writer Agent**:
   ```bash
   opencode @writer-agent "Process ticket TKT-003"
   # Status changes to 'ready', draft created in data/drafts/
   ```

3. **Run Publisher Agent**:
   ```bash
   opencode @publisher-agent "Publish ticket TKT-003"
   # Status changes to 'published', Typefully URL added to ticket
   ```

## Status Values

| Status | Description |
|--------|-------------|
| `proposed` | Awaiting human approval |
| `approved` | Ready to be written |
| `drafting` | Writer agent is working |
| `ready` | Draft created, ready to publish |
| `publishing` | Publisher agent is working |
| `published` | Successfully sent to Typefully |
| `failed` | Error occurred |

## Common Issues

### "OpenCode not found"

```bash
# Install OpenCode
npm install -g opencode
# or
brew install opencode
```

### "GITHUB_TOKEN not set"

```bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Verify
echo $GITHUB_TOKEN
```

### "Permission denied" when running scripts

```bash
# Make scripts executable
chmod +x scripts/agents/*/*.py
chmod +x scripts/*.py
```

## Next Steps

1. **Customize agents**: Edit `.opencode/agent/*.md` to change agent behavior
2. **Add media**: Place images in `assets/` and reference them in drafts
3. **Track history**: Commit your `data/tasks.md` to Git

## Tips for Success

1. **Start small**: Test with one commit before automating everything
2. **Review everything**: Always check drafts before approving
3. **Iterate on prompts**: Tweak agent definitions to match your style
4. **Use Git**: Version control your configuration and task history
5. **Monitor logs**: Check `logs/` if something goes wrong

---

**Ready to automate your Build in Public content? 🚀**

Questions? Check the full [README.md](README.md) or open an issue!

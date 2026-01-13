#!/usr/bin/env python3
"""
Ticket-centric Notion Sync Bridge (API Version 2025-09-03)
直接同步 data/tickets/*.md 文件到 Notion。
"""

import os
import sys
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from notion_client import Client

class TicketNotionSync:
    def __init__(self, notion_token: str, database_id: str, tickets_dir: str):
        self.notion = Client(auth=notion_token, notion_version="2025-09-03")
        self.database_id = database_id
        self.tickets_dir = Path(tickets_dir)
        self._db_response = self.notion.request(method="get", path=f"databases/{self.database_id}")
        self.data_source_id = self._db_response.get("data_sources")[0]["id"]
        
        # Get properties from data_source (new API) or database (old API)
        ds = self.notion.request(method="get", path=f"data_sources/{self.data_source_id}")
        self._db_properties = set(ds.get("properties", {}).keys())
        
        # Fallback: query one page to get properties if still empty
        if not self._db_properties:
            resp = self.notion.request(method="post", path=f"data_sources/{self.data_source_id}/query", body={"page_size": 1})
            if resp.get("results"):
                self._db_properties = set(resp["results"][0]["properties"].keys())

    def _get_db_properties(self) -> set:
        return self._db_properties

    def _parse_ticket(self, file_path: Path) -> Optional[Dict[str, Any]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fm_match = re.search(r'---\s*(.*?)\s*---', content, re.DOTALL)
        if not fm_match:
            return None
            
        fm_text = fm_match.group(1)
        data = {}
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip()] = val.strip().strip('"')
        
        if 'title' not in data:
            title_match = re.search(r'^#\s*(.*)$', content, re.MULTILINE)
            data['title'] = title_match.group(1).strip() if title_match else file_path.stem
        
        if 'tkt_id' not in data and 'id' in data:
            data['tkt_id'] = data['id']
        elif 'tkt_id' not in data:
            data['tkt_id'] = file_path.stem
        
        body_content = content[fm_match.end():].strip()
        data['proposal'] = body_content[:2000] if body_content else ""
        
        if not data.get('project'):
            parent_dir = file_path.parent.name
            if parent_dir != 'tickets':
                data['project'] = parent_dir
            
        data['file_path'] = file_path
        return data

    def _update_ticket_field(self, file_path: Path, field: str, value: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if re.search(f'^{field}:', content, re.MULTILINE):
            new_content = re.sub(f'^{field}:.*$', f'{field}: "{value}"', content, flags=re.MULTILINE)
        else:
            new_content = re.sub(r'---', f'---\n{field}: "{value}"', content, count=1)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def _read_draft_content(self, tkt_id: str) -> str:
        draft_path = Path(f"data/drafts/{tkt_id}_draft.md")
        if draft_path.exists():
            with open(draft_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content[:1990]
        return ""

    def sync(self):
        local_tickets = {}
        # Changed: Use rglob to recursively find tickets in subdirectories
        for f in self.tickets_dir.rglob("TKT-*.md"):
            data = self._parse_ticket(f)
            if data:
                local_tickets[data['tkt_id']] = data

        results = []
        has_more = True
        cursor = None
        while has_more:
            params = {"page_size": 100}
            if cursor: params["start_cursor"] = cursor
            resp = self.notion.request(method="post", path=f"data_sources/{self.data_source_id}/query", body=params)
            results.extend(resp.get("results", []))
            has_more = resp.get("has_more", False)
            cursor = resp.get("next_cursor")

        notion_tasks = {}
        for page in results:
            properties = page['properties']
            title_props = properties.get('Title', {}).get('title', [])
            if not title_props:
                title_props = properties.get('Task ID', {}).get('title', [])
            
            notion_title = title_props[0]['text']['content'] if title_props else None
            
            tkt_id_rich_text = properties.get('TKT ID', {}).get('rich_text', [])
            if not tkt_id_rich_text:
                 tkt_id_rich_text = properties.get('Task ID', {}).get('rich_text', [])
            
            tkt_id = tkt_id_rich_text[0]['text']['content'] if tkt_id_rich_text else notion_title
            
            if tkt_id:
                notion_tasks[tkt_id] = page

        for tkt_id, page in notion_tasks.items():
            if tkt_id in local_tickets:
                ticket = local_tickets[tkt_id]
                notion_status = page['properties']['Status']['select']['name']
                if notion_status.upper() != ticket.get('status', '').upper():
                    print(f"🔄 Updating local status {tkt_id}: {ticket.get('status')} -> {notion_status}")
                    self._update_ticket_field(ticket['file_path'], 'status', notion_status.lower())

        for tkt_id, ticket in local_tickets.items():
            title_val = ticket.get('title', tkt_id)[:2000]
            
            props = {
                "Status": {"select": {"name": ticket.get('status', 'proposed').upper()}},
            }
            
            if "Title" in self._get_db_properties():
                props["Title"] = {"title": [{"text": {"content": title_val}}]}
            else:
                props["Task ID"] = {"title": [{"text": {"content": tkt_id}}]}
                props["Content"] = {"rich_text": [{"text": {"content": title_val}}]}
            
            db_props = self._get_db_properties()
            
            if "TKT ID" in db_props:
                props["TKT ID"] = {"rich_text": [{"text": {"content": tkt_id}}]}
            
            if ticket.get('type') and "Type" in db_props:
                props["Type"] = {"select": {"name": ticket['type']}}
            
            if ticket.get('project'):
                if "Project" in db_props:
                    props["Project"] = {"rich_text": [{"text": {"content": ticket['project']}}]}
                elif "Repo" in db_props:
                    props["Repo"] = {"rich_text": [{"text": {"content": ticket['project']}}]}
            
            if ticket.get('priority') and "Priority" in db_props:
                props["Priority"] = {"select": {"name": ticket['priority']}}
            
            if ticket.get('commit') and "Commit" in db_props:
                props["Commit"] = {"rich_text": [{"text": {"content": ticket['commit']}}]}


            if ticket.get('proposal') and "Proposal" in db_props:
                props["Proposal"] = {"rich_text": [{"text": {"content": ticket['proposal'][:2000]}}]}
            
            pub_url = ticket.get('published_url') or ticket.get('typefully_url')
            if pub_url and "Published URL" in db_props:
                props["Published URL"] = {"url": pub_url if pub_url.startswith('http') else None}
            
            if ticket.get('error') and "Error" in db_props:
                props["Error"] = {"rich_text": [{"text": {"content": ticket['error'][:2000]}}]}
            
            draft = ticket.get('draft_content') or self._read_draft_content(tkt_id)
            if draft and "Draft Content" in db_props:
                props["Draft Content"] = {"rich_text": [{"text": {"content": draft[:2000]}}]}

            if tkt_id in notion_tasks:
                self.notion.pages.update(page_id=notion_tasks[tkt_id]['id'], properties=props)
            else:
                print(f"✨ Creating new Ticket in Notion: {tkt_id}")
                self.notion.pages.create(
                    parent={"type": "data_source_id", "data_source_id": self.data_source_id},
                    properties=props
                )


def main():
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if not token or not db_id:
        print("Error: Set NOTION_TOKEN and NOTION_DATABASE_ID")
        return

    syncer = TicketNotionSync(token, db_id, "data/tickets")
    
    if "--watch" in sys.argv:
        interval = int(sys.argv[sys.argv.index("--interval") + 1]) if "--interval" in sys.argv else 300
        print(f"Watching for changes every {interval}s...")
        while True:
            try:
                syncer.sync()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sync complete.")
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(interval)
    elif "--pull-only" in sys.argv:
        print("Pulling from Notion...")
        syncer.sync()
    elif "--push-only" in sys.argv:
        print("Pushing to Notion...")
        syncer.sync()
    else:
        syncer.sync()
        print("Sync complete.")

if __name__ == "__main__":
    main()

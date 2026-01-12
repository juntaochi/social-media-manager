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
from typing import List, Dict, Any
from datetime import datetime
from notion_client import Client

class TicketNotionSync:
    def __init__(self, notion_token: str, database_id: str, tickets_dir: str):
        self.notion = Client(auth=notion_token, notion_version="2025-09-03")
        self.database_id = database_id
        self.tickets_dir = Path(tickets_dir)
        self.data_source_id = self._get_data_source_id()

    def _get_data_source_id(self):
        response = self.notion.request(method="get", path=f"databases/{self.database_id}")
        return response.get("data_sources")[0]["id"]

    def _parse_ticket(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 Frontmatter
        fm_match = re.search(r'---\s*(.*?)\s*---', content, re.DOTALL)
        if not fm_match:
            return None
            
        fm_text = fm_match.group(1)
        data = {}
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip()] = val.strip().strip('"')
        
        # 解析标题
        title_match = re.search(r'^#\s*(.*)$', content, re.MULTILINE)
        data['title'] = title_match.group(1).strip() if title_match else file_path.stem
        data['file_path'] = file_path
        
        return data

    def _update_ticket_status(self, file_path: Path, new_status: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换 status
        new_content = re.sub(r'status:\s*\w+', f'status: {new_status}', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def _read_draft_content(self, ticket_id: str) -> str:
        draft_path = Path(f"data/drafts/{ticket_id}_draft.md")
        if draft_path.exists():
            with open(draft_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content[:1990] # Notion limit
        return ""

    def sync(self):
        # 1. 获取本地 Tickets
        local_tickets = {}
        for f in self.tickets_dir.glob("TKT-*.md"):
            data = self._parse_ticket(f)
            if data:
                local_tickets[data['id']] = data

        # 2. 获取 Notion 页面
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
            task_id = page['properties']['Task ID']['title'][0]['text']['content'] if page['properties']['Task ID']['title'] else None
            if task_id:
                notion_tasks[task_id] = page

        # 3. 双向同步
        # A. Notion -> 本地 (状态更新)
        for task_id, page in notion_tasks.items():
            if task_id in local_tickets:
                notion_status = page['properties']['Status']['select']['name']
                if notion_status.upper() != local_tickets[task_id]['status'].upper():
                    print(f"🔄 更新本地 {task_id}: {local_tickets[task_id]['status']} -> {notion_status}")
                    self._update_ticket_status(local_tickets[task_id]['file_path'], notion_status.lower())

        # B. 本地 -> Notion (新建或更新详细内容)
        for task_id, ticket in local_tickets.items():
            props = {
                "Task ID": {"title": [{"text": {"content": task_id}}]},
                "Status": {"select": {"name": ticket['status'].upper()}},
                "Content": {"rich_text": [{"text": {"content": ticket['title']}}]},
                "Type": {"select": {"name": "ticket_process"}}
            }
            
            # 附加草稿内容
            draft = self._read_draft_content(task_id)
            if draft:
                props["Draft Content"] = {"rich_text": [{"text": {"content": draft}}]}

            if task_id in notion_tasks:
                # 更新
                self.notion.pages.update(page_id=notion_tasks[task_id]['id'], properties=props)
            else:
                # 新建
                print(f"✨ 在 Notion 中创建新 Ticket: {task_id}")
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
    else:
        syncer.sync()
        print("Sync complete.")

if __name__ == "__main__":
    main()

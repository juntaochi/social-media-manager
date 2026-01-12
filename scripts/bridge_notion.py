#!/usr/bin/env python3
"""
Notion Sync Bridge (API Version 2025-09-03)

双向同步 data/tasks.md 和 Notion Database。
保持文件系统为单一真相源，Notion 作为移动端友好的视图层。

支持 Notion API 2025-09-03 版本（使用 data_source_id）

Usage:
    # 单次同步
    python3 scripts/bridge_notion.py --sync
    
    # 持续监听模式（每 5 分钟同步一次）
    python3 scripts/bridge_notion.py --watch --interval 300
    
    # 仅从 Notion 拉取更新
    python3 scripts/bridge_notion.py --pull-only
    
    # 仅推送到 Notion
    python3 scripts/bridge_notion.py --push-only
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Notion SDK
try:
    from notion_client import Client
except ImportError:
    print("ERROR: notion-client not installed. Run: pip install notion-client")
    sys.exit(1)


class NotionTaskSync:
    """双向同步 tasks.md 和 Notion Database (API 2025-09-03)"""
    
    def __init__(self, notion_token: str, database_id: str, tasks_file: Path):
        # 使用最新 API 版本
        self.notion = Client(auth=notion_token, notion_version="2025-09-03")
        self.database_id = database_id
        self.tasks_file = Path(tasks_file)  # Ensure it's always a Path object
        self.data_source_id = None  # 将在初始化时获取
        self.task_counter = 0  # 用于生成递增 ID
        
        # 导入任务解析器
        sys.path.insert(0, str(Path(__file__).parent / 'agents' / 'manager'))
        from parse_tasks import parse_tasks
        self.parse_tasks = parse_tasks
        
        # 获取 data source ID
        self._initialize_data_source()
    
    def _initialize_data_source(self):
        """获取 database 的第一个 data source ID"""
        try:
            # 在 2025-09-03 版本中，需要使用 request 方法
            response = self.notion.request(
                method="get",
                path=f"databases/{self.database_id}"
            )
            
            data_sources = response.get("data_sources", [])
            if not data_sources:
                raise ValueError(
                    f"Database {self.database_id} 没有 data sources。"
                    "请在 Notion 中检查 database 配置。"
                )
            
            # 使用第一个 data source
            self.data_source_id = data_sources[0]["id"]
            print(f"✓ 已连接到 Data Source: {data_sources[0].get('name', 'Unnamed')}")
            print(f"  Data Source ID: {self.data_source_id}")
            
            # 获取现有的最大 TASK-XXX 编号
            self._initialize_task_counter()
            
        except Exception as e:
            raise ValueError(
                f"无法获取 data source ID: {e}\n"
                f"请确认 Database ID 正确且有访问权限。"
            )
    
    def _initialize_task_counter(self):
        """从现有任务中获取最大的 TASK-XXX 编号"""
        try:
            pages = self._get_all_notion_pages()
            max_num = 0
            for page in pages:
                task_id = self._get_task_id_from_page(page)
                # 匹配 TASK-001 格式
                match = re.match(r'TASK-(\d+)', task_id)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
            self.task_counter = max_num
        except Exception:
            self.task_counter = 0
    
    def generate_task_id(self, task: Dict[str, Any]) -> str:
        """生成友好的 Task ID"""
        # 优先：如果任务来自 ticket，提取 TKT-XXX
        if task.get("content"):
            # 匹配 "ticket: data/tickets/TKT-001.md" 格式
            ticket_match = re.search(r'ticket:\s*data/tickets/(TKT-\d+)\.md', task["content"])
            if ticket_match:
                return ticket_match.group(1)
            
            # 匹配 "from ticket: data/tickets/TKT-001.md" 格式
            ticket_match2 = re.search(r'from ticket:\s*data/tickets/(TKT-\d+)\.md', task["content"])
            if ticket_match2:
                return ticket_match2.group(1)
        
        # 其他情况：生成递增的 TASK-XXX
        self.task_counter += 1
        return f"TASK-{self.task_counter:03d}"
    
    def _get_task_id_from_page(self, page: Dict) -> str:
        """从 Notion page 提取 Task ID（安全方法）"""
        try:
            task_id_property = page.get("properties", {}).get("Task ID", {})
            title_array = task_id_property.get("title", [])
            if title_array and len(title_array) > 0:
                return title_array[0].get("plain_text", "")
            return ""
        except (KeyError, IndexError, TypeError):
            return ""
    
    def _read_draft_content(self, draft_path: str) -> str:
        """读取草稿文件内容（截取前 1990 字符）"""
        try:
            # 构建完整路径
            full_path = self.tasks_file.parent.parent / draft_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Notion rich_text 限制 2000 字符，留点余量
                    if len(content) > 1990:
                        return content[:1990] + "..."
                    return content
            return ""
        except Exception as e:
            print(f"Warning: Could not read draft {draft_path}: {e}")
            return ""
    
    def sync_to_notion(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将 tasks.md 的任务推送到 Notion"""
        stats = {"created": 0, "updated": 0, "errors": 0}
        
        # 获取 Notion 现有的所有页面（用于匹配）
        existing_pages = self._get_all_notion_pages()
        existing_by_id = {}
        for page in existing_pages:
            task_id = self._get_task_id_from_page(page)
            if task_id:
                existing_by_id[task_id] = page
        
        # 为了保证 Task ID 的唯一性和一致性，先生成所有 Task ID
        task_id_map = {}  # 映射：task index -> task_id
        
        for idx, task in enumerate(tasks):
            # 尝试从现有 Notion 记录中找到匹配的任务
            # 先用内容哈希匹配（向后兼容旧的哈希 ID）
            import hashlib
            content_hash = hashlib.md5(f"{task['status']}:{task['content']}".encode()).hexdigest()[:8]
            
            # 检查是否有哈希 ID 的旧记录
            if content_hash in existing_by_id:
                task_id = content_hash  # 保留旧 ID，避免重复创建
            else:
                # 检查是否已经有对应的 TKT ID
                task_id = self.generate_task_id(task)
                # 如果这个 ID 已经存在，就直接用它（避免重复）
                if task_id not in existing_by_id:
                    # 新任务，使用生成的 ID
                    pass
            
            task_id_map[idx] = task_id
        
        for idx, task in enumerate(tasks):
            task_id = task_id_map[idx]
            
            try:
                notion_properties = self._task_to_notion_properties(task, task_id)
                
                if task_id in existing_by_id:
                    # 更新现有页面
                    page_id = existing_by_id[task_id]["id"]
                    self.notion.pages.update(page_id=page_id, properties=notion_properties)
                    stats["updated"] += 1
                else:
                    # 创建新页面 - 使用 data_source_id 作为 parent
                    self.notion.pages.create(
                        parent={"type": "data_source_id", "data_source_id": self.data_source_id},
                        properties=notion_properties
                    )
                    stats["created"] += 1
                    
            except Exception as e:
                print(f"Error syncing task {task_id}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def sync_from_notion(self) -> Dict[str, Any]:
        """从 Notion 拉取状态变更并更新 tasks.md"""
        stats = {"updated": 0, "created": 0, "errors": 0}
        
        # 读取本地任务
        tasks, lines = self.parse_tasks(self.tasks_file)
        
        # 获取 Notion 数据库中的所有页面
        notion_pages = self._get_all_notion_pages()
        
        # 创建映射：使用内容匹配而不是 Task ID
        # 因为本地任务可能还没有同步过，没有 Task ID
        local_tasks_by_content = {}
        for task in tasks:
            # 使用内容作为 key
            content_key = f"{task['status']}:{task['content']}"
            local_tasks_by_content[content_key] = task
        
        # Track tasks to add to local file
        new_tasks = []
        
        # 检查 Notion 中是否有状态变更
        for page in notion_pages:
            try:
                task_id = self._get_task_id_from_page(page)
                if not task_id:
                    continue
                
                # 获取 Notion 中的 Content
                content_prop = page.get("properties", {}).get("Content", {})
                content_array = content_prop.get("rich_text", [])
                notion_content = content_array[0].get("plain_text", "") if content_array else ""
                
                # 提取 Notion 中的状态
                status_property = page.get("properties", {}).get("Status", {})
                notion_status = status_property.get("select", {}).get("name", "") if status_property else ""
                
                if not notion_status or not notion_content:
                    continue
                
                # 尝试匹配本地任务
                matched_task = None
                for content_key, task in local_tasks_by_content.items():
                    if task["content"] in notion_content or notion_content in task["content"]:
                        matched_task = task
                        break
                
                if matched_task:
                    # Update existing task if status changed
                    if notion_status != matched_task["status"]:
                        self._update_task_status_in_file(lines, matched_task, notion_status)
                        stats["updated"] += 1
                else:
                    # New task from Notion - add to local file
                    new_tasks.append({
                        "task_id": task_id,
                        "status": notion_status,
                        "content": notion_content
                    })
                    stats["created"] += 1
                    
            except Exception as e:
                print(f"Error syncing from Notion: {e}")
                stats["errors"] += 1
        
        # Add new tasks to the file
        if new_tasks:
            # Find the line with "<!-- Your tasks go here -->"
            insert_index = None
            for i, line in enumerate(lines):
                if "<!-- Your tasks go here -->" in line:
                    insert_index = i + 1
                    break
            
            if insert_index is not None:
                for task in new_tasks:
                    new_line = f"- [ ] [{task['status']}] {task['content']}\n"
                    lines.insert(insert_index, new_line)
                    insert_index += 1
        
        # 写回文件
        if stats["updated"] > 0 or stats["created"] > 0:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        return stats
    
    def _get_all_notion_pages(self) -> List[Dict]:
        """获取 Data Source 中的所有页面（使用 2025-09-03 API）"""
        results = []
        has_more = True
        start_cursor = None
        
        try:
            while has_more:
                # 使用新的 data_sources query API
                query_params = {"page_size": 100}
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                response = self.notion.request(
                    method="post",
                    path=f"data_sources/{self.data_source_id}/query",
                    body=query_params
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
        except Exception as e:
            print(f"Warning: Could not fetch existing pages: {e}")
            # 如果查询失败（例如空 database），返回空列表
            return []
        
        return results
    
    def _task_to_notion_properties(self, task: Dict[str, Any], task_id: str) -> Dict:
        """将本地任务转换为 Notion Properties 格式"""
        properties = {
            "Task ID": {
                "title": [{"text": {"content": task_id}}]
            },
            # Status 字段使用 'select' 类型
            "Status": {
                "select": {"name": task["status"]}
            },
            "Content": {
                "rich_text": [{"text": {"content": task["content"][:2000]}}]  # Notion 限制
            },
            "Type": {
                "select": {"name": task.get("type", "unknown")}
            }
        }
        
        # 如果有草稿路径，读取草稿内容
        if "draft_path" in task:
            draft_content = self._read_draft_content(task["draft_path"])
            if draft_content:
                properties["Draft Content"] = {
                    "rich_text": [{"text": {"content": draft_content}}]
                }
            
            # 保留 Draft Path（虽然手机上打不开，但在电脑上有用）
            properties["Draft Path"] = {
                "url": f"file://{self.tasks_file.parent.parent.absolute() / task['draft_path']}"
            }
        
        if "published_url" in task:
            properties["Published URL"] = {"url": task["published_url"]}
        
        if "error" in task:
            properties["Error"] = {
                "rich_text": [{"text": {"content": task["error"][:2000]}}]
            }
        
        if "repo" in task:
            properties["Repo"] = {
                "rich_text": [{"text": {"content": task["repo"]}}]
            }
        
        if "commit" in task:
            properties["Commit"] = {
                "rich_text": [{"text": {"content": task["commit"]}}]
            }
        
        return properties
    
    def _update_task_status_in_file(self, lines: List[str], task: Dict, new_status: str):
        """在文件中更新任务状态"""
        line_idx = task["line_idx"]
        old_line = lines[line_idx]
        
        # 替换状态标记
        new_line = old_line.replace(f"[{task['status']}]", f"[{new_status}]", 1)
        lines[line_idx] = new_line
        
        print(f"Updated task at line {task['line_number']}: {task['status']} -> {new_status}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Notion <-> tasks.md 双向同步工具 (API 2025-09-03)")
    parser.add_argument("--sync", action="store_true", help="执行双向同步")
    parser.add_argument("--push-only", action="store_true", help="仅推送到 Notion")
    parser.add_argument("--pull-only", action="store_true", help="仅从 Notion 拉取")
    parser.add_argument("--watch", action="store_true", help="持续监听模式")
    parser.add_argument("--interval", type=int, default=300, help="监听间隔（秒）")
    parser.add_argument("--tasks-file", default="data/tasks.md", help="tasks.md 路径")
    
    args = parser.parse_args()
    
    # 获取环境变量
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_token:
        print("ERROR: NOTION_TOKEN 环境变量未设置")
        print("请在 .env 中添加: NOTION_TOKEN=your_integration_token")
        return 1
    
    if not database_id:
        print("ERROR: NOTION_DATABASE_ID 环境变量未设置")
        print("请在 .env 中添加: NOTION_DATABASE_ID=your_database_id")
        return 1
    
    tasks_file = Path(args.tasks_file)
    if not tasks_file.exists():
        print(f"ERROR: 任务文件不存在: {tasks_file}")
        return 1
    
    # 初始化同步器
    try:
        syncer = NotionTaskSync(notion_token, database_id, tasks_file)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    
    def do_sync():
        """执行同步操作"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] 开始同步...")
        
        if args.pull_only:
            # 仅拉取
            stats = syncer.sync_from_notion()
            print(f"✓ 从 Notion 拉取完成: {stats['created']} 新建, {stats['updated']} 更新")
        elif args.push_only:
            # 仅推送
            tasks, _ = syncer.parse_tasks(tasks_file)
            stats = syncer.sync_to_notion(tasks)
            print(f"✓ 推送到 Notion 完成: {stats['created']} 新建, {stats['updated']} 更新")
        else:
            # 双向同步
            # 1. 先从 Notion 拉取状态变更
            pull_stats = syncer.sync_from_notion()
            
            # 2. 重新解析（因为可能有变更）
            tasks, _ = syncer.parse_tasks(tasks_file)
            
            # 3. 推送到 Notion
            push_stats = syncer.sync_to_notion(tasks)
            
            print(f"✓ 双向同步完成:")
            print(f"  - Notion -> 本地: {pull_stats['created']} 新建, {pull_stats['updated']} 更新")
            print(f"  - 本地 -> Notion: {push_stats['created']} 新建, {push_stats['updated']} 更新")
    
    # 执行同步
    if args.watch:
        print(f"进入监听模式，每 {args.interval} 秒同步一次 (Ctrl+C 退出)")
        try:
            while True:
                do_sync()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n监听已停止")
            return 0
    else:
        do_sync()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

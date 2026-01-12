#!/usr/bin/env python3
"""
Quick Add Task - 快速添加任务到 Notion

Usage:
    # 交互式添加
    python3 scripts/quick_add_task.py
    
    # 命令行添加
    python3 scripts/quick_add_task.py "写一个关于新功能的帖子"
"""

import os
import sys
from notion_client import Client

def quick_add_task(content: str):
    """快速添加任务到 Notion"""
    
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_token or not database_id:
        print("ERROR: 请先配置 NOTION_TOKEN 和 NOTION_DATABASE_ID")
        return False
    
    try:
        notion = Client(auth=notion_token, notion_version="2025-09-03")
        
        # 获取 data source ID
        db_response = notion.request(method="get", path=f"databases/{database_id}")
        data_source_id = db_response.get("data_sources")[0]["id"]
        
        # 获取现有任务数量，生成新 ID
        query_response = notion.request(
            method="post",
            path=f"data_sources/{data_source_id}/query",
            body={"page_size": 1}
        )
        
        # 简单的 ID 生成（基于时间戳）
        import time
        task_id = f"TASK-{int(time.time()) % 10000:04d}"
        
        # 创建任务
        notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": data_source_id},
            properties={
                "Task ID": {
                    "title": [{"text": {"content": task_id}}]
                },
                "Status": {
                    "select": {"name": "TODO"}
                },
                "Content": {
                    "rich_text": [{"text": {"content": content}}]
                },
                "Type": {
                    "select": {"name": "free_form"}
                }
            }
        )
        
        print(f"✅ 任务已创建: {task_id}")
        print(f"📝 内容: {content}")
        print(f"🔄 状态: TODO")
        print(f"\n打开 Notion app 查看！")
        return True
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        # 命令行模式
        content = " ".join(sys.argv[1:])
        quick_add_task(content)
    else:
        # 交互式模式
        print("=== 快速添加任务 ===")
        print("提示：直接输入任务描述（一句话即可）\n")
        content = input("📝 任务内容: ").strip()
        
        if content:
            quick_add_task(content)
        else:
            print("❌ 内容不能为空")


if __name__ == "__main__":
    main()

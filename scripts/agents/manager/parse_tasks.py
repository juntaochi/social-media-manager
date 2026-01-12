#!/usr/bin/env python3
"""
Task Parser Utility for Pipeline Manager

Parses tasks.md file and extracts structured task information.
Can be called from Claude via bash tool or used standalone.

Usage:
    python3 parse_tasks.py [--file data/tasks.md] [--format json|text]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def parse_tasks(file_path: Path) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse tasks.md file into structured data.

    Returns:
        tuple: (list of task dicts, list of all lines)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    tasks = []

    # Pattern: - [ ] [STATUS] Content | metadata
    task_pattern = re.compile(r'^- \[ \] \[(.*?)\] (.*?)(?:\s*\|\s*(.*))?$')

    for line_idx, line in enumerate(lines):
        match = task_pattern.match(line.strip())
        if match:
            status = match.group(1).strip()
            content = match.group(2).strip()
            metadata = match.group(3).strip() if match.group(3) else ""

            task = {
                'line_idx': line_idx,
                'line_number': line_idx + 1,  # Human-readable line number
                'status': status,
                'content': content,
                'metadata': metadata,
                'raw': line.rstrip()
            }

            # Extract common metadata patterns
            if 'draft:' in metadata:
                draft_match = re.search(r'draft:\s*(\S+)', metadata)
                if draft_match:
                    task['draft_path'] = draft_match.group(1)

            if 'published:' in metadata:
                url_match = re.search(r'published:\s*(\S+)', metadata)
                if url_match:
                    task['published_url'] = url_match.group(1)

            if 'error:' in metadata:
                error_match = re.search(r'error:\s*(.+)', metadata)
                if error_match:
                    task['error'] = error_match.group(1)

            # Extract task type patterns from content
            commit_match = re.search(r'commit\s+([a-f0-9]+)', content, re.IGNORECASE)
            repo_match = re.search(r'repo\s+([\w\-]+/[\w\-]+)', content, re.IGNORECASE)
            summary_match = re.search(r'summary:\s*(.+\.md)', content)
            topic_match = re.search(r'Write about:\s*(.+)', content, re.IGNORECASE)
            ticket_match = re.search(r'ticket:\s*(data/tickets/.+\.md)', content, re.IGNORECASE)

            if commit_match and repo_match:
                task['type'] = 'github_commit'
                task['commit'] = commit_match.group(1)
                task['repo'] = repo_match.group(1)
            elif summary_match:
                task['type'] = 'from_summary'
                task['summary_path'] = summary_match.group(1)
            elif topic_match:
                task['type'] = 'free_form'
                task['topic'] = topic_match.group(1)
            elif ticket_match:
                task['type'] = 'ticket_process'
                task['ticket_path'] = ticket_match.group(1)
            else:
                task['type'] = 'unknown'

            tasks.append(task)

    return tasks, lines


def format_tasks_text(tasks: List[Dict[str, Any]]) -> str:
    """Format tasks as human-readable text."""
    if not tasks:
        return "No tasks found."

    output = []
    output.append(f"Total tasks: {len(tasks)}\n")

    # Group by status
    status_groups = {}
    for task in tasks:
        status = task['status']
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(task)

    # Display by status
    for status in ['TODO', 'PROCESSING', 'WAITING_APPROVAL', 'APPROVED', 'PUBLISHING', 'DONE', 'FAILED']:
        if status in status_groups:
            tasks_in_status = status_groups[status]
            output.append(f"\n{status}: {len(tasks_in_status)} tasks")
            for task in tasks_in_status:
                output.append(f"  Line {task['line_number']}: {task['content'][:60]}...")
                if task['type'] != 'unknown':
                    output.append(f"    Type: {task['type']}")
                if 'draft_path' in task:
                    output.append(f"    Draft: {task['draft_path']}")
                if 'published_url' in task:
                    output.append(f"    Published: {task['published_url']}")
                if 'error' in task:
                    output.append(f"    Error: {task['error']}")

    # Display unknown status tasks
    for status, tasks_in_status in status_groups.items():
        if status not in ['TODO', 'PROCESSING', 'WAITING_APPROVAL', 'APPROVED', 'PUBLISHING', 'DONE', 'FAILED']:
            output.append(f"\n{status}: {len(tasks_in_status)} tasks (unknown status)")
            for task in tasks_in_status:
                output.append(f"  Line {task['line_number']}: {task['content'][:60]}...")

    return '\n'.join(output)


def format_tasks_json(tasks: List[Dict[str, Any]]) -> str:
    """Format tasks as JSON."""
    return json.dumps(tasks, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Parse tasks.md file')
    parser.add_argument('--file', default='data/tasks.md', help='Path to tasks.md file')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--type', help='Filter by type (github_commit, from_summary, free_form)')

    args = parser.parse_args()

    try:
        # Parse tasks
        file_path = Path(args.file)
        tasks, lines = parse_tasks(file_path)

        # Apply filters
        if args.status:
            tasks = [t for t in tasks if t['status'].upper() == args.status.upper()]

        if args.type:
            tasks = [t for t in tasks if t['type'] == args.type]

        # Format output
        if args.format == 'json':
            print(format_tasks_json(tasks))
        else:
            print(format_tasks_text(tasks))

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

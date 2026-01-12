#!/usr/bin/env python3
"""
Task Status Updater Utility for Pipeline Manager

Updates task status in tasks.md file safely and atomically.
Can be called from Claude via bash tool or used standalone.

Usage:
    python3 update_status.py --file data/tasks.md --line 5 --status DONE
    python3 update_status.py --file data/tasks.md --identifier abc123 --status WAITING_APPROVAL --metadata "draft: data/drafts/abc123_draft.md"
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, List


def find_task_line(lines: List[str], identifier: str) -> Optional[int]:
    """
    Find the line number of a task by identifier (commit hash, keyword, etc.).

    Args:
        lines: List of file lines
        identifier: String to search for in task content

    Returns:
        Line index (0-based) or None if not found
    """
    task_pattern = re.compile(r'^- \[ \] \[(.*?)\] (.*?)(?:\s*\|\s*(.*))?$')

    for line_idx, line in enumerate(lines):
        match = task_pattern.match(line.strip())
        if match:
            content = match.group(2).strip()
            if identifier.lower() in content.lower():
                return line_idx

    return None


def update_task_status(
    file_path: Path,
    line_idx: int,
    new_status: str,
    metadata: Optional[str] = None
) -> bool:
    """
    Update the status of a task and optionally add/update metadata.

    Args:
        file_path: Path to tasks.md file
        line_idx: Line index (0-based) to update
        new_status: New status string (e.g., "DONE", "FAILED")
        metadata: Optional metadata to append/update (e.g., "draft: path/to/file.md")

    Returns:
        bool: True if successful, False otherwise
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False

    # Read all lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if line_idx < 0 or line_idx >= len(lines):
        print(f"Error: Line index {line_idx} out of range (file has {len(lines)} lines)", file=sys.stderr)
        return False

    current_line = lines[line_idx].rstrip()

    # Parse current line
    task_pattern = re.compile(r'^- \[ \] \[(.*?)\] (.*?)(?:\s*\|\s*(.*))?$')
    match = task_pattern.match(current_line)

    if not match:
        print(f"Error: Line {line_idx + 1} is not a valid task line", file=sys.stderr)
        print(f"Content: {current_line}", file=sys.stderr)
        return False

    old_status = match.group(1).strip()
    content = match.group(2).strip()
    old_metadata = match.group(3).strip() if match.group(3) else ""

    # Build new line
    new_line = f"- [ ] [{new_status}] {content}"

    if metadata:
        # If metadata provided, use it (replace old metadata)
        new_line += f" | {metadata}"
    elif old_metadata:
        # If no new metadata but old metadata exists, keep it
        new_line += f" | {old_metadata}"

    new_line += '\n'

    # Update the line
    lines[line_idx] = new_line

    # Write back atomically
    try:
        # Write to temp file first
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        # Move temp file to original (atomic on most systems)
        temp_path.replace(file_path)

        print(f"Updated line {line_idx + 1}:")
        print(f"  Old: [{old_status}] {content[:50]}...")
        print(f"  New: [{new_status}] {content[:50]}...")
        if metadata:
            print(f"  Metadata: {metadata}")

        return True

    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        if temp_path.exists():
            temp_path.unlink()  # Clean up temp file
        return False


def append_metadata(existing: str, new: str) -> str:
    """
    Append new metadata to existing metadata.

    Args:
        existing: Existing metadata string
        new: New metadata to append

    Returns:
        Combined metadata string
    """
    if not existing:
        return new
    if not new:
        return existing

    # Combine with comma separator
    return f"{existing}, {new}"


def main():
    parser = argparse.ArgumentParser(description='Update task status in tasks.md')
    parser.add_argument('--file', required=True, help='Path to tasks.md file')
    parser.add_argument('--line', type=int, help='Line number to update (1-based)')
    parser.add_argument('--identifier', help='Identifier to search for (alternative to --line)')
    parser.add_argument('--status', required=True, help='New status (e.g., DONE, FAILED)')
    parser.add_argument('--metadata', help='Metadata to add/update (e.g., "draft: path/to/file.md")')
    parser.add_argument('--append-metadata', action='store_true',
                       help='Append to existing metadata instead of replacing')

    args = parser.parse_args()

    file_path = Path(args.file)

    # Determine line index
    if args.line is not None:
        line_idx = args.line - 1  # Convert 1-based to 0-based
    elif args.identifier:
        # Read file to find identifier
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        line_idx = find_task_line(lines, args.identifier)
        if line_idx is None:
            print(f"Error: Task with identifier '{args.identifier}' not found", file=sys.stderr)
            return 1
        print(f"Found task at line {line_idx + 1}")
    else:
        print("Error: Either --line or --identifier must be provided", file=sys.stderr)
        parser.print_help()
        return 1

    # Handle metadata
    metadata = args.metadata
    if args.append_metadata and metadata:
        # Read current metadata and append
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        task_pattern = re.compile(r'^- \[ \] \[(.*?)\] (.*?)(?:\s*\|\s*(.*))?$')
        match = task_pattern.match(lines[line_idx].strip())
        if match and match.group(3):
            existing_metadata = match.group(3).strip()
            metadata = append_metadata(existing_metadata, metadata)

    # Update status
    success = update_task_status(file_path, line_idx, args.status, metadata)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

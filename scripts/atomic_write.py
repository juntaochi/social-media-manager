#!/usr/bin/env python3
"""
Atomic file write utility for the content pipeline.

Ensures file writes are atomic to prevent corruption during concurrent access.
Uses write-to-temp + rename pattern which is atomic on POSIX systems.

Usage:
    # As a module
    from atomic_write import atomic_write, atomic_update_yaml_field
    
    atomic_write('data/tickets/TKT-001.md', content)
    atomic_update_yaml_field('data/tickets/TKT-001.md', 'status', 'ready')
    
    # As CLI
    echo "content" | python scripts/atomic_write.py data/file.md
    python scripts/atomic_write.py data/file.md --field status --value ready
"""

import os
import sys
import tempfile
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone


def atomic_write(filepath: str, content: str) -> None:
    """
    Write content to file atomically.
    
    Uses write-to-temp-then-rename pattern:
    1. Write to temporary file in same directory
    2. Sync to disk (fsync)
    3. Rename temp file to target (atomic on POSIX)
    
    Args:
        filepath: Target file path
        content: Content to write
    """
    filepath = Path(filepath).resolve()
    parent = filepath.parent
    
    # Ensure parent directory exists
    parent.mkdir(parents=True, exist_ok=True)
    
    # Create temp file in same directory (required for atomic rename)
    fd, temp_path = tempfile.mkstemp(
        dir=parent,
        prefix=f'.{filepath.name}.',
        suffix='.tmp'
    )
    
    try:
        # Write content
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.rename(temp_path, filepath)
        
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def parse_yaml_frontmatter(content: str) -> tuple[dict, str, int, int]:
    """
    Parse YAML frontmatter from markdown content.
    
    Returns:
        Tuple of (frontmatter_dict, body, start_line, end_line)
    """
    lines = content.split('\n')
    
    if not lines or lines[0].strip() != '---':
        return {}, content, 0, 0
    
    # Find closing ---
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_idx = i
            break
    
    if end_idx is None:
        return {}, content, 0, 0
    
    # Parse frontmatter (simple key: value parsing)
    frontmatter = {}
    frontmatter_lines = lines[1:end_idx]
    
    for line in frontmatter_lines:
        if ':' in line and not line.strip().startswith('-'):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Handle quoted strings
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # Handle numbers
            elif value.isdigit():
                value = int(value)
            # Handle empty strings
            elif value == '""' or value == "''":
                value = ""
                
            frontmatter[key] = value
    
    body = '\n'.join(lines[end_idx + 1:])
    return frontmatter, body, 0, end_idx


def update_yaml_field(content: str, field: str, value: str) -> str:
    """
    Update a single field in YAML frontmatter.
    
    Args:
        content: Full file content with frontmatter
        field: Field name to update
        value: New value (will be quoted if string)
    
    Returns:
        Updated content
    """
    lines = content.split('\n')
    
    if not lines or lines[0].strip() != '---':
        raise ValueError("No YAML frontmatter found")
    
    # Find closing ---
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_idx = i
            break
    
    if end_idx is None:
        raise ValueError("Unclosed YAML frontmatter")
    
    # Format value
    if isinstance(value, str):
        if value == "":
            formatted_value = '""'
        elif ' ' in value or ':' in value or value in ('true', 'false', 'null'):
            formatted_value = f'"{value}"'
        else:
            formatted_value = value
    elif isinstance(value, int):
        formatted_value = str(value)
    elif isinstance(value, bool):
        formatted_value = 'true' if value else 'false'
    else:
        formatted_value = f'"{value}"'
    
    # Find and update field
    field_found = False
    for i in range(1, end_idx):
        line = lines[i]
        if line.startswith(f'{field}:') or line.startswith(f'{field} :'):
            # Preserve indentation
            indent = len(line) - len(line.lstrip())
            lines[i] = f'{" " * indent}{field}: {formatted_value}'
            field_found = True
            break
    
    if not field_found:
        # Add field before closing ---
        lines.insert(end_idx, f'{field}: {formatted_value}')
    
    return '\n'.join(lines)


def atomic_update_yaml_field(filepath: str, field: str, value: str) -> None:
    """
    Atomically update a single YAML frontmatter field.
    
    Args:
        filepath: Path to markdown file with frontmatter
        field: Field name to update
        value: New value
    """
    filepath = Path(filepath).resolve()
    
    # Read current content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update field
    updated = update_yaml_field(content, field, value)
    
    # Write atomically
    atomic_write(str(filepath), updated)


def acquire_lock(filepath: str, agent: str, timeout_minutes: int = 10) -> bool:
    """
    Attempt to acquire lock on a ticket file.
    
    Args:
        filepath: Path to ticket file
        agent: Agent name acquiring lock (e.g., 'writer', 'publisher')
        timeout_minutes: Lock timeout in minutes (default 10)
    
    Returns:
        True if lock acquired, False if already locked (non-stale)
    """
    filepath = Path(filepath).resolve()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter, _, _, _ = parse_yaml_frontmatter(content)
    
    locked_by = frontmatter.get('locked_by', '')
    locked_at = frontmatter.get('locked_at', '')
    
    # Check if locked
    if locked_by and locked_at:
        try:
            lock_time = datetime.fromisoformat(locked_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_minutes = (now - lock_time).total_seconds() / 60
            
            if age_minutes < timeout_minutes:
                # Lock is still valid
                return False
            # Lock is stale, will be overwritten
        except (ValueError, TypeError):
            # Invalid timestamp, proceed with acquiring lock
            pass
    
    # Acquire lock
    now_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    content = update_yaml_field(content, 'locked_by', agent)
    content = update_yaml_field(content, 'locked_at', now_iso)
    
    atomic_write(str(filepath), content)
    return True


def release_lock(filepath: str) -> None:
    """
    Release lock on a ticket file.
    
    Args:
        filepath: Path to ticket file
    """
    filepath = Path(filepath).resolve()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = update_yaml_field(content, 'locked_by', '')
    content = update_yaml_field(content, 'locked_at', '')
    
    atomic_write(str(filepath), content)


def mark_failed(filepath: str, error: str) -> None:
    """
    Mark ticket as failed with error message.
    
    Args:
        filepath: Path to ticket file
        error: Error message
    """
    filepath = Path(filepath).resolve()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter, _, _, _ = parse_yaml_frontmatter(content)
    retry_count = frontmatter.get('retry_count', 0)
    if isinstance(retry_count, str):
        retry_count = int(retry_count) if retry_count.isdigit() else 0
    
    content = update_yaml_field(content, 'status', 'failed')
    content = update_yaml_field(content, 'error', error)
    content = update_yaml_field(content, 'retry_count', str(retry_count + 1))
    content = update_yaml_field(content, 'locked_by', '')
    content = update_yaml_field(content, 'locked_at', '')
    
    atomic_write(str(filepath), content)


def main():
    parser = argparse.ArgumentParser(
        description='Atomic file write utility for content pipeline'
    )
    parser.add_argument('filepath', help='Target file path')
    parser.add_argument('--field', '-f', help='YAML field to update')
    parser.add_argument('--value', '-v', help='New value for field')
    parser.add_argument('--lock', action='store_true', help='Acquire lock')
    parser.add_argument('--unlock', action='store_true', help='Release lock')
    parser.add_argument('--agent', default='cli', help='Agent name for lock')
    parser.add_argument('--fail', help='Mark as failed with error message')
    
    args = parser.parse_args()
    
    try:
        if args.lock:
            success = acquire_lock(args.filepath, args.agent)
            if success:
                print(f"Lock acquired by {args.agent}")
            else:
                print("Lock already held by another agent", file=sys.stderr)
                sys.exit(1)
        
        elif args.unlock:
            release_lock(args.filepath)
            print("Lock released")
        
        elif args.fail:
            mark_failed(args.filepath, args.fail)
            print(f"Marked as failed: {args.fail}")
        
        elif args.field and args.value is not None:
            atomic_update_yaml_field(args.filepath, args.field, args.value)
            print(f"Updated {args.field} = {args.value}")
        
        elif not sys.stdin.isatty():
            # Read content from stdin
            content = sys.stdin.read()
            atomic_write(args.filepath, content)
            print(f"Wrote {len(content)} bytes to {args.filepath}")
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

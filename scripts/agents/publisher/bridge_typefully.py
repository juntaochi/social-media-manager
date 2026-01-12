#!/usr/bin/env python3
"""
Typefully Media Upload Bridge

This script handles media file uploads to Typefully API.
It can be called as a standalone CLI tool or run as an MCP server.

The Typefully MCP server currently has limited media upload support,
so this bridge provides direct API integration for media handling.
"""

import requests
import sys
import os
import json
import argparse
from pathlib import Path


class TypefullyMediaUploader:
    """
    Handles media uploads to Typefully API v2
    """

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("TYPEFULLY_API_KEY not provided")

        self.api_key = api_key
        self.base_url = "https://api.typefully.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def upload_media(self, file_path):
        """
        Upload a media file to Typefully.

        Args:
            file_path: Path to the media file

        Returns:
            dict: Response containing media_id and other metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        # Validate file type
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.webp']
        if file_path.suffix.lower() not in valid_extensions:
            return {
                "success": False,
                "error": f"Invalid file type. Supported: {', '.join(valid_extensions)}"
            }

        # Check file size (most APIs have limits around 10-50MB)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        max_size_mb = 50

        if file_size_mb > max_size_mb:
            return {
                "success": False,
                "error": f"File too large ({file_size_mb:.1f}MB). Max: {max_size_mb}MB"
            }

        try:
            # Step 1: Request upload URL (if Typefully uses signed URLs)
            # Note: The exact endpoint may vary - check Typefully API docs
            # This is a common pattern for media upload APIs

            # For direct upload (adjust based on actual Typefully API):
            upload_url = f"{self.base_url}/media"

            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path.name, f, self._get_mime_type(file_path))
                }

                # Remove Content-Type from headers for multipart/form-data
                upload_headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }

                response = requests.post(
                    upload_url,
                    headers=upload_headers,
                    files=files,
                    timeout=60
                )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "media_id": data.get('id') or data.get('media_id'),
                    "url": data.get('url'),
                    "filename": file_path.name,
                    "size_mb": round(file_size_mb, 2)
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code} - {response.text}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def _get_mime_type(self, file_path):
        """
        Get MIME type for a file based on extension
        """
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime'
        }
        return mime_types.get(file_path.suffix.lower(), 'application/octet-stream')

    def create_draft(self, content, media_ids=None, schedule_date=None):
        """
        Create a draft on Typefully with optional media.

        Args:
            content: The text content (can be a thread with --- separators)
            media_ids: List of media IDs to attach
            schedule_date: Optional ISO format date to schedule

        Returns:
            dict: Response with draft ID and URL
        """
        try:
            endpoint = f"{self.base_url}/drafts"

            payload = {
                "content": content
            }

            if media_ids:
                payload["media_ids"] = media_ids if isinstance(media_ids, list) else [media_ids]

            if schedule_date:
                payload["schedule_date"] = schedule_date

            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "draft_id": data.get('id'),
                    "url": data.get('url') or f"https://typefully.com/drafts/{data.get('id')}",
                    "share_url": data.get('share_url')
                }
            else:
                return {
                    "success": False,
                    "error": f"Draft creation failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating draft: {str(e)}"
            }


def cli_mode(args):
    """
    Run in CLI mode for direct file uploads
    """
    api_key = os.environ.get('TYPEFULLY_API_KEY') or args.api_key

    if not api_key:
        print(json.dumps({
            "success": False,
            "error": "TYPEFULLY_API_KEY environment variable not set"
        }))
        return 1

    uploader = TypefullyMediaUploader(api_key)

    if args.action == 'upload':
        if not args.file:
            print(json.dumps({
                "success": False,
                "error": "No file specified. Use --file <path>"
            }))
            return 1

        result = uploader.upload_media(args.file)
        print(json.dumps(result, indent=2))
        return 0 if result.get('success') else 1

    elif args.action == 'draft':
        if not args.content:
            print(json.dumps({
                "success": False,
                "error": "No content specified. Use --content <text>"
            }))
            return 1

        media_ids = args.media_ids.split(',') if args.media_ids else None
        result = uploader.create_draft(args.content, media_ids, args.schedule)
        print(json.dumps(result, indent=2))
        return 0 if result.get('success') else 1


def server_mode():
    """
    Run as an MCP server (for future implementation)
    """
    print("MCP Server mode not yet implemented.", file=sys.stderr)
    print("Use CLI mode for now: python bridge_typefully.py upload --file <path>", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Typefully Media Upload Bridge - CLI tool and MCP server for media uploads"
    )

    parser.add_argument(
        '--server-mode',
        action='store_true',
        help='Run as MCP server (future implementation)'
    )

    parser.add_argument(
        'action',
        nargs='?',
        choices=['upload', 'draft'],
        help='Action to perform: upload (media file) or draft (create draft)'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Path to media file to upload'
    )

    parser.add_argument(
        '--content',
        type=str,
        help='Content for draft creation'
    )

    parser.add_argument(
        '--media-ids',
        type=str,
        help='Comma-separated media IDs to attach to draft'
    )

    parser.add_argument(
        '--schedule',
        type=str,
        help='ISO format date to schedule the draft'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='Typefully API key (can also use TYPEFULLY_API_KEY env var)'
    )

    args = parser.parse_args()

    if args.server_mode:
        return server_mode()
    elif args.action:
        return cli_mode(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), file=sys.stderr)
        sys.exit(1)

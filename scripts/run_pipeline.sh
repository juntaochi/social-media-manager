#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

show_help() {
    cat <<EOF
Social Media Manager - Content Pipeline

Usage: ./scripts/run_pipeline.sh [command]

Commands:
    write       Process TODO tasks and generate drafts
    publish     Publish APPROVED tasks to Typefully
    full        Run full pipeline (write + publish)
    help        Show this help message

Examples:
    ./scripts/run_pipeline.sh write
    ./scripts/run_pipeline.sh full

Environment:
    Requires .env file with:
    - GITHUB_TOKEN
    - TYPEFULLY_KEY
    - NOTION_TOKEN (optional)
EOF
}

check_env() {
    if [ -z "$TYPEFULLY_KEY" ]; then
        echo "Error: TYPEFULLY_KEY not set. Check your .env file."
        exit 1
    fi
}

run_manager_agent() {
    local prompt="$1"
    echo "Running Manager Agent..."
    echo "Command: $prompt"
    echo "---"
    
    opencode run --agent manager-agent "$prompt"
}

cmd_write() {
    echo "=== Processing Tasks → Generating Drafts ==="
    run_manager_agent "Process approved tickets to generate drafts"
}

cmd_publish() {
    check_env
    echo "=== Publishing Approved Drafts ==="
    run_manager_agent "Publish ready drafts to Typefully"
}

cmd_full() {
    check_env
    echo "=== Full Pipeline: Write + Publish ==="
    run_manager_agent "Run the complete content pipeline (analyze -> write -> publish)"
}

cmd_analyze() {
    echo "=== Analyzing Projects for New Content ==="
    run_manager_agent "Analyze all projects for new content opportunities"
}

cmd_status() {
    echo "=== Current Pipeline Status ==="
    run_manager_agent "Show pipeline status"
}

case "${1:-help}" in
    write)
        cmd_write
        ;;
    publish)
        cmd_publish
        ;;
    full)
        cmd_full
        ;;
    analyze)
        cmd_analyze
        ;;
    status)
        cmd_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

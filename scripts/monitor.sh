#!/bin/bash
# 监控 Social Media Manager 运行状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

clear
echo "========================================="
echo "  Social Media Manager - 实时监控"
echo "========================================="
echo ""

while true; do
    # 时间戳
    echo -e "\n⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    echo "----------------------------------------"
    
    # 1. 同步服务状态
    echo "📡 Notion 同步服务:"
    if [ -f logs/notion_sync.pid ]; then
        PID=$(cat logs/notion_sync.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "   ✅ 运行中 (PID: $PID)"
            # 最后一次同步时间
            if [ -f logs/notion_sync.log ]; then
                LAST_SYNC=$(tail -1 logs/notion_sync.log 2>/dev/null | grep -o '\[.*\]' | head -1)
                echo "   📅 最后同步: $LAST_SYNC"
            fi
        else
            echo "   ❌ 已停止"
        fi
    else
        echo "   ⚠️  未运行"
    fi
    
    # 2. Pipeline进程
    echo ""
    echo "🔄 Pipeline 进程:"
    PIPELINE_PROCS=$(ps aux | grep -E "run_pipeline|opencode.*manager-agent" | grep -v grep | wc -l)
    if [ $PIPELINE_PROCS -gt 0 ]; then
        echo "   ✅ 运行中 ($PIPELINE_PROCS 个进程)"
        ps aux | grep -E "run_pipeline|opencode.*manager-agent" | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%"}'
    else
        echo "   ⏸️  空闲"
    fi
    
    echo ""
    echo "📋 任务状态 (data/tickets/):"
    if [ -d data/tickets ]; then
        PROPOSED=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?proposed"?' {} \; 2>/dev/null | wc -l)
        PROCESSING=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?processing"?' {} \; 2>/dev/null | wc -l)
        WAITING=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?waiting_approval"?' {} \; 2>/dev/null | wc -l)
        APPROVED=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?approved"?' {} \; 2>/dev/null | wc -l)
        PUBLISHING=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?publishing"?' {} \; 2>/dev/null | wc -l)
        PUBLISHED=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?published"?' {} \; 2>/dev/null | wc -l)
        FAILED=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?failed"?' {} \; 2>/dev/null | wc -l)
        REJECTED=$(find data/tickets -name "TKT-*.md" -exec grep -lE 'status:\s*"?rejected"?' {} \; 2>/dev/null | wc -l)
        
        echo "   🟡 Proposed: $PROPOSED"
        echo "   ⚙️  Processing: $PROCESSING"
        echo "   ⏳ Waiting Approval: $WAITING"
        echo "   🟢 Approved: $APPROVED"
        echo "   📤 Publishing: $PUBLISHING"
        echo "   🚀 Published: $PUBLISHED"
        if [ $FAILED -gt 0 ]; then
            echo "   ❌ Failed: $FAILED"
        fi
        if [ $REJECTED -gt 0 ]; then
            echo "   🚫 Rejected: $REJECTED"
        fi
    fi
    

    
    # 4. Drafts数量
    echo ""
    echo "📝 Drafts:"
    DRAFT_COUNT=$(ls -1 data/drafts/*.md 2>/dev/null | wc -l)
    echo "   总计: $DRAFT_COUNT 个文件"
    if [ $DRAFT_COUNT -gt 0 ]; then
        echo "   最新:"
        ls -t data/drafts/*.md | head -3 | while read file; do
            basename=$(basename "$file")
            size=$(ls -lh "$file" | awk '{print $5}')
            echo "     • $basename ($size)"
        done
    fi
    
    # 5. 最新日志
    echo ""
    echo "📄 最新日志 (pipeline_test.log):"
    if [ -f logs/pipeline_test.log ]; then
        tail -3 logs/pipeline_test.log | sed 's/^/   /'
    else
        echo "   (无)"
    fi
    
    echo ""
    echo "========================================="
    echo "按 Ctrl+C 退出监控 | 每 5 秒刷新"
    
    sleep 5
    clear
done

#!/bin/bash
# 주간 보고 자동 실행 스크립트 (crontab용)
# config.yaml에서 assignee를 파싱하고, 프롬프트 템플릿의 플레이스홀더를 치환하여 실행

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/cron/weekly_report.log"
CONFIG_FILE="$PROJECT_DIR/config.yaml"
PROMPT_TEMPLATE="$PROJECT_DIR/cron/weekly_report_prompt.md"

# PATH 자동 탐지: nvm node가 있으면 추가
if [ -d "$HOME/.nvm" ]; then
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi
export PATH="$HOME/.nvm/versions/node/$(ls "$HOME/.nvm/versions/node/" 2>/dev/null | tail -1)/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

CLAUDE_BIN="$(which claude)"

# config.yaml에서 board_url의 assignee 파라미터와 project_key 추출
BOARD_URL=$(grep 'board_url' "$CONFIG_FILE" | sed 's/.*board_url: *"\(.*\)"/\1/')
ASSIGNEE=$(echo "$BOARD_URL" | sed 's/.*assignee=\([^&"]*\).*/\1/')
PROJECT_KEY=$(echo "$BOARD_URL" | sed 's|.*/projects/\([^/]*\)/.*|\1|')

# config.yaml에서 cloud_id 추출
CLOUD_ID=$(grep 'cloud_id' "$CONFIG_FILE" | sed 's/.*cloud_id: *"\(.*\)"/\1/')

# 프롬프트 템플릿에서 플레이스홀더 치환
PROMPT=$(sed -e "s|{{ASSIGNEE}}|${ASSIGNEE}|g" \
             -e "s|{{PROJECT_DIR}}|${PROJECT_DIR}|g" \
             -e "s|{{PROJECT_KEY}}|${PROJECT_KEY}|g" \
             -e "s|{{CLOUD_ID}}|${CLOUD_ID}|g" \
             "$PROMPT_TEMPLATE")

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 주간 보고 시작 ===" >> "$LOG_FILE"

echo "$PROMPT" | "$CLAUDE_BIN" --print --dangerously-skip-permissions --allowedTools "mcp__atlassian__searchJiraIssuesUsingJql,mcp__atlassian__getJiraIssue,Bash" \
  >> "$LOG_FILE" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 주간 보고 완료 ===" >> "$LOG_FILE"

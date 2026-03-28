#!/bin/bash
# weekly_report_bot.sh
# 주간 보고 자동화 설정 스크립트
# 사용법: bash weekly_report_bot.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.weekly-report-bot.scheduler"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
CONFIG_FILE="$PROJECT_DIR/config.yaml"
ENV_FILE="$PROJECT_DIR/.env"

echo "============================================"
echo "  주간 보고 자동화 설정 (Weekly Report Bot)"
echo "============================================"
echo ""

# ── 1. Python 확인 ──
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python이 설치되어 있지 않습니다."
    exit 1
fi
echo "✅ Python: $($PYTHON_CMD --version)"
echo ""

# ── 2. 의존성 설치 ──
echo "📦 의존성 설치 중..."
$PYTHON_CMD -m pip install -r "$PROJECT_DIR/requirements.txt" -q
echo "✅ 의존성 설치 완료"
echo ""

# ── 3. 환경 변수 설정 (.env) ──
echo "🔐 환경 변수 설정"
echo "   (이미 설정된 값이 있으면 Enter로 건너뛸 수 있습니다)"
echo ""

CURRENT_SLACK_TOKEN=""

if [ -f "$ENV_FILE" ]; then
    CURRENT_SLACK_TOKEN=$(grep -E "^SLACK_BOT_TOKEN=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
fi

read -p "Slack Bot Token (xoxb-...) [${CURRENT_SLACK_TOKEN:+현재값 유지}]: " INPUT_SLACK_TOKEN
SLACK_TOKEN="${INPUT_SLACK_TOKEN:-$CURRENT_SLACK_TOKEN}"

cat > "$ENV_FILE" <<EOF
SLACK_BOT_TOKEN=${SLACK_TOKEN}
EOF
echo "✅ .env 저장 완료"
echo ""

# ── 4. config.yaml 설정 ──
echo "⚙️  프로젝트 설정 (config.yaml)"
echo ""

CURRENT_BOARD_URL=""
CURRENT_SLACK_UID=""

if [ -f "$CONFIG_FILE" ]; then
    CURRENT_BOARD_URL=$(grep "board_url:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*board_url: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | xargs)
    CURRENT_SLACK_UID=$(grep "user_id:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | xargs)
fi

echo "   Jira 보드 URL을 입력해주세요."
echo "   예: https://your-domain.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=..."
echo ""
read -p "Jira 보드 URL [${CURRENT_BOARD_URL:+현재값 유지}]: " INPUT_BOARD_URL
BOARD_URL="${INPUT_BOARD_URL:-$CURRENT_BOARD_URL}"

read -p "Slack User ID (U로 시작) [${CURRENT_SLACK_UID:+현재값 유지}]: " INPUT_SUID
SLACK_UID="${INPUT_SUID:-$CURRENT_SLACK_UID}"

cat > "$CONFIG_FILE" <<EOF
jira:
  board_url: "${BOARD_URL}"

slack:
  user_id: "${SLACK_UID}"

schedule:
  day: "thursday"
  time: "17:00"
  timezone: "Asia/Seoul"
EOF
echo "✅ config.yaml 저장 완료"
echo ""

# ── 5. launchd 스케줄 설정 ──
echo "⏰ 스케줄 설정"
echo "   crontab 형식으로 입력해주세요."
echo "   예시:"
echo "     매주 목요일 17:00  →  0 17 * * 4"
echo "     매주 금요일 09:00  →  0 9 * * 5"
echo "     매일 18:00         →  0 18 * * *"
echo ""
read -p "crontab 수식 [0 17 * * 4]: " INPUT_CRON
CRON_EXPR="${INPUT_CRON:-0 17 * * 4}"

# crontab 파싱: 분 시 일 월 요일
CRON_MIN=$(echo "$CRON_EXPR" | awk '{print $1}')
CRON_HOUR=$(echo "$CRON_EXPR" | awk '{print $2}')
CRON_DAY=$(echo "$CRON_EXPR" | awk '{print $3}')
CRON_MONTH=$(echo "$CRON_EXPR" | awk '{print $4}')
CRON_WEEKDAY=$(echo "$CRON_EXPR" | awk '{print $5}')

# launchd plist의 StartCalendarInterval 생성
CAL_INTERVAL="        <dict>"
if [ "$CRON_MIN" != "*" ]; then
    CAL_INTERVAL="$CAL_INTERVAL
            <key>Minute</key>
            <integer>$CRON_MIN</integer>"
fi
if [ "$CRON_HOUR" != "*" ]; then
    CAL_INTERVAL="$CAL_INTERVAL
            <key>Hour</key>
            <integer>$CRON_HOUR</integer>"
fi
if [ "$CRON_DAY" != "*" ]; then
    CAL_INTERVAL="$CAL_INTERVAL
            <key>Day</key>
            <integer>$CRON_DAY</integer>"
fi
if [ "$CRON_MONTH" != "*" ]; then
    CAL_INTERVAL="$CAL_INTERVAL
            <key>Month</key>
            <integer>$CRON_MONTH</integer>"
fi
if [ "$CRON_WEEKDAY" != "*" ]; then
    CAL_INTERVAL="$CAL_INTERVAL
            <key>Weekday</key>
            <integer>$CRON_WEEKDAY</integer>"
fi
CAL_INTERVAL="$CAL_INTERVAL
        </dict>"

PYTHON_FULL_PATH="$(which $PYTHON_CMD)"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# 기존 plist 언로드
if launchctl list | grep -q "$PLIST_NAME" 2>/dev/null; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_FULL_PATH}</string>
        <string>-m</string>
        <string>src.run_report</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>StartCalendarInterval</key>
${CAL_INTERVAL}
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/weekly_report.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/weekly_report_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>SLACK_BOT_TOKEN</key>
        <string>${SLACK_TOKEN}</string>
    </dict>
</dict>
</plist>
EOF

# launchd 등록
launchctl load "$PLIST_PATH"

echo ""
echo "============================================"
echo "  ✅ 설정 완료!"
echo "============================================"
echo ""
echo "  스케줄: ${CRON_EXPR}"
echo "  plist:  ${PLIST_PATH}"
echo "  로그:   ${LOG_DIR}/weekly_report.log"
echo ""
echo "  유용한 명령어:"
echo "    상태 확인:  launchctl list | grep ${PLIST_NAME}"
echo "    즉시 실행:  launchctl start ${PLIST_NAME}"
echo "    중지:       launchctl unload ${PLIST_PATH}"
echo "    로그 확인:  tail -f ${LOG_DIR}/weekly_report.log"
echo ""

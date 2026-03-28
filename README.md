# 주간 보고 자동화 시스템 (Claude Code + MCP)

Claude Code에서 MCP(Model Context Protocol)를 활용하여 Jira 티켓을 자동 수집하고, Claude(LLM)가 자연어로 작업 내용을 요약한 뒤, Slack 앱 메시지 탭(봇과의 1:1 대화)으로 주간 보고를 전송하는 자동화 시스템입니다.

## 동작 방식

1. crontab이 매주 수요일 15:00에 Claude CLI 실행
2. Claude가 Jira MCP Server를 통해 이번 주 담당 티켓 조회
3. Claude(LLM)가 각 티켓의 댓글/상태를 분석하여 자연어 요약 생성
4. Python 스크립트(`Slack_Message_Sender`)가 Slack 앱 메시지 탭으로 보고 전송

## 사전 요구사항

- Python 3.9 이상
- Claude Code CLI (`claude` 명령어 사용 가능해야 함)
- Atlassian MCP 연결 설정 완료
- Slack App Bot Token (팀 관리자에게 전달받기)

## 빠른 설치 (권장)

```bash
git clone <repo-url>
cd weekly_report_bot
pip install -r requirements.txt
```

그 다음 Claude Code에서 아래 한 줄이면 끝:

```
setup_prompt.md 읽고 실행해줘
```

Jira 보드 URL, Slack User ID, Slack Bot Token을 입력하면 `config.yaml` 생성부터 crontab 등록까지 자동으로 완료됩니다.

## 수동 설치

### 1. 클론 및 의존성 설치

```bash
git clone <repo-url>
cd weekly_report_bot
pip install -r requirements.txt
```

### 2. config.yaml 생성

```bash
cp config.yaml.example config.yaml
```

각 필드를 환경에 맞게 수정합니다:

```yaml
jira:
  board_url: ""       # Jira 보드 URL (브라우저에서 복사, assignee 파라미터 포함)

slack:
  user_id: ""         # Slack User ID
  bot_token: ""       # Slack Bot Token (팀 관리자에게 전달받기)

schedule:
  day: "wednesday"
  time: "15:00"
  timezone: "Asia/Seoul"
```

프로젝트 키, 보드 ID, assignee는 URL에서 자동 파싱됩니다.

### 3. Slack User ID 확인 방법

1. Slack 데스크톱/웹 앱에서 본인 프로필 사진 클릭
2. **프로필 보기** 선택
3. 프로필 패널에서 **⋮** (더보기) 버튼 클릭
4. **멤버 ID 복사** 선택 (`U`로 시작하는 ID)

### 4. crontab 등록

```bash
chmod +x cron/run_weekly_report.sh
(crontab -l 2>/dev/null | grep -v 'run_weekly_report.sh'; echo "0 15 * * 3 $(pwd)/cron/run_weekly_report.sh") | crontab -
```

## 테스트 실행

```bash
pip install -r requirements-dev.txt
pytest
```

## 프로젝트 구조

```
├── src/
│   ├── config_manager.py      # 설정 관리 (config.yaml)
│   ├── models.py              # 데이터 모델 (TicketSummary, WeeklyReport)
│   ├── slack_message_sender.py # Slack 앱 메시지 전송
│   └── utils.py               # 유틸리티 (날짜 범위, 포맷팅)
├── tests/
│   ├── unit/                  # 단위 테스트
│   ├── property/              # 속성 기반 테스트 (hypothesis)
│   └── integration/           # 통합 테스트
├── cron/
│   └── run_weekly_report.sh   # crontab 실행 스크립트
├── setup_prompt.md            # Claude Code 자동 셋업 프롬프트
├── config.yaml.example        # 설정 파일 템플릿
├── requirements.txt           # 런타임 의존성
└── requirements-dev.txt       # 개발/테스트 의존성
```

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

Jira 보드 URL, Slack User ID, Slack Bot Token을 입력하면 `config.yaml` 생성부터 crontab 등록까지 자동으로 완료됩니다. 별도로 crontab을 수동 등록할 필요 없이, 셋업 프롬프트가 모든 과정을 처리합니다.

## 테스트 실행

```bash
pip install -r requirements-dev.txt
pytest
```

## 프롬프트 커스터마이징

`cron/weekly_report_prompt.md` 파일을 수정하면 보고서 생성 방식을 자유롭게 변경할 수 있습니다.

- 요약 형식 변경 (예: 영어로 요약, 글머리 기호 스타일 변경)
- 요약 길이 조절 (기본 50자 이내 → 원하는 길이로)
- 추가 정보 포함 (예: 우선순위, 라벨 등)
- JQL 쿼리 수정 (조회 범위 변경)

`{{ASSIGNEE}}`와 `{{PROJECT_DIR}}`는 실행 시 자동 치환되는 플레이스홀더이므로 그대로 유지해주세요.

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
│   ├── run_weekly_report.sh   # crontab 실행 스크립트
│   └── weekly_report_prompt.md # 보고서 생성 프롬프트 (커스터마이징 가능)
├── setup_prompt.md            # Claude Code 자동 셋업 프롬프트
├── config.yaml.example        # 설정 파일 템플릿
├── requirements.txt           # 런타임 의존성
└── requirements-dev.txt       # 개발/테스트 의존성
```

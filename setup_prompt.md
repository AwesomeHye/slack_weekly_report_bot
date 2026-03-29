# 주간 보고 봇 셋업 가이드

이 파일을 Claude Code에서 읽고 실행하면 자동으로 세팅됩니다.
사용법: Claude Code에서 `setup_prompt.md 읽고 실행해줘` 입력

---

## 셋업 지시사항 (Claude가 실행)

아래 단계를 순서대로 수행해줘.

### 1단계: 사용자 정보 입력받기

사용자에게 다음 네 가지를 물어봐:

- **Jira 스프린트 보드 URL**: 브라우저에서 본인 Jira 보드를 열고 URL을 복사해서 붙여넣기. assignee 파라미터가 포함된 URL이어야 함.
  - 예시: `https://your-domain.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=000000:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Slack User ID**: Slack에서 본인 프로필 > 더보기(⋯) > 멤버 ID 복사
  - 예시: `Uxxxxxxxxxx`
- **Slack Bot Token**: 팀 관리자에게 전달받은 봇 토큰
  - 예시: `xoxb-xxxx-xxxx-xxxx`
- **실행 스케줄**: 주간 보고를 언제 실행할지 입력. 자연어 또는 크론 표현식 모두 가능.
  - 자연어 예시: `매주 수요일 오후 3시`, `매주 목요일 17시`, `매일 오전 9시`
  - 크론 표현식 예시: `0 15 * * 3` (매주 수요일 15:00)

### 2단계: 스케줄 파싱 및 검증

입력받은 스케줄을 `src/schedule_parser.py`의 `ScheduleParser`로 파싱해:

```python
from src.schedule_parser import ScheduleParser

parser = ScheduleParser()
try:
    result = parser.parse("<입력받은 스케줄>")
    print(f"크론 표현식: {result.cron_expression}")
    print(f"설명: {result.description}")
except ValueError as e:
    print(f"스케줄 파싱 실패: {e}")
    # 에러 메시지에 입력 예시가 포함되어 있으므로 사용자에게 보여주고 재입력 요청
```

파싱 실패 시 에러 메시지를 보여주고 다시 입력받아.

### 3단계: config.yaml 생성

입력받은 값과 파싱된 스케줄로 프로젝트 루트에 `config.yaml`을 생성해:

```yaml
jira:
  board_url: "<입력받은 Jira 보드 URL>"

slack:
  user_id: "<입력받은 Slack User ID>"
  bot_token: "<입력받은 Slack Bot Token>"

schedule:
  timezone: "Asia/Seoul"
  cron_expression: "<파싱된 크론 표현식>"
  original_input: "<사용자가 입력한 원본 스케줄>"
```

### 4단계: 실행 권한 부여

```bash
chmod +x cron/run_weekly_report.sh
```

### 5단계: crontab 등록

기존에 `run_weekly_report.sh`가 등록되어 있으면 제거하고, 파싱된 크론 표현식으로 새로 등록해:

```bash
(crontab -l 2>/dev/null | grep -v 'run_weekly_report.sh'; echo "<파싱된 크론 표현식> $(pwd)/cron/run_weekly_report.sh") | crontab -
```

예를 들어 크론 표현식이 `0 15 * * 3`이면:
```bash
(crontab -l 2>/dev/null | grep -v 'run_weekly_report.sh'; echo "0 15 * * 3 $(pwd)/cron/run_weekly_report.sh") | crontab -
```

등록 후 `crontab -l`로 확인해서 결과를 보여줘.

### 6단계: 설정 검증

프로젝트 루트에서 실행:

```bash
python3 -c "
from src.config_manager import ConfigManager
config = ConfigManager('config.yaml').load()
print(f'Jira 보드: {config.jira_board_url}')
print(f'Slack User: {config.slack_user_id}')
print(f'스케줄: {config.schedule_cron_expression}')
print('설정 검증 완료!')
"
```

검증 성공하면 "셋업 완료! <파싱된 설명>에 주간 보고가 Slack으로 전송됩니다." 라고 안내해.
예: "셋업 완료! 매주 수요일 15:00에 주간 보고가 Slack으로 전송됩니다."

검증 실패하면 에러 내용을 보여주고 해결 방법을 안내해.

# 주간 보고 봇 셋업 가이드

이 파일을 Claude Code에서 읽고 실행하면 자동으로 세팅됩니다.
사용법: Claude Code에서 `setup_prompt.md 읽고 실행해줘` 입력

---

## 셋업 지시사항 (Claude가 실행)

아래 단계를 순서대로 수행해줘.

### 1단계: 사용자 정보 입력받기

사용자에게 다음 세 가지를 물어봐:

- **Jira 스프린트 보드 URL**: 브라우저에서 본인 Jira 보드를 열고 URL을 복사해서 붙여넣기. assignee 파라미터가 포함된 URL이어야 함.
  - 예시: `https://your-domain.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=000000:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Slack User ID**: Slack에서 본인 프로필 > 더보기(⋯) > 멤버 ID 복사
  - 예시: `Uxxxxxxxxxx`
- **Slack Bot Token**: 팀 관리자에게 전달받은 봇 토큰
  - 예시: `xoxb-xxxx-xxxx-xxxx`

### 2단계: config.yaml 생성

입력받은 값으로 프로젝트 루트에 `config.yaml`을 생성해:

```yaml
jira:
  board_url: "<입력받은 Jira 보드 URL>"

slack:
  user_id: "<입력받은 Slack User ID>"
  bot_token: "<입력받은 Slack Bot Token>"

schedule:
  day: "wednesday"
  time: "15:00"
  timezone: "Asia/Seoul"
```

### 3단계: 실행 권한 부여

```bash
chmod +x cron/run_weekly_report.sh
```

### 4단계: crontab 등록

기존에 `run_weekly_report.sh`가 등록되어 있으면 제거하고 새로 등록해:

```bash
(crontab -l 2>/dev/null | grep -v 'run_weekly_report.sh'; echo "0 15 * * 3 $(pwd)/cron/run_weekly_report.sh") | crontab -
```

등록 후 `crontab -l`로 확인해서 결과를 보여줘.

### 5단계: 설정 검증

프로젝트 루트에서 실행:

```bash
python3 -c "
from src.config_manager import ConfigManager
config = ConfigManager('config.yaml').load()
print(f'프로젝트: {config.jira_project_key}')
print(f'Assignee: {config.assignee_account_id}')
print(f'Slack User: {config.slack_user_id}')
print('설정 검증 완료!')
"
```

검증 성공하면 "셋업 완료! 매주 수요일 15:00에 주간 보고가 Slack으로 전송됩니다." 라고 안내해.
검증 실패하면 에러 내용을 보여주고 해결 방법을 안내해.

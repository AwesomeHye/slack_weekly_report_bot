매주 주간 보고 자동 생성 및 Slack 전송 작업을 수행해줘.

## 1단계: Jira 티켓 조회
Atlassian MCP를 사용해서 {{PROJECT_KEY}} 프로젝트의 현재 활성 스프린트에서 assignee가 {{ASSIGNEE}}인 티켓들을 조회해줘.
- cloudId: {{CLOUD_ID}}
- JQL: project = {{PROJECT_KEY}} AND assignee = "{{ASSIGNEE}}" AND sprint in openSprints()
- fields: summary, status, comment

## 2단계: 각 티켓의 이번 주 댓글 조회
조회된 각 티켓에 대해 getJiraIssue로 댓글을 포함한 상세 정보를 가져와줘.
이번 주(월요일~오늘) 작성된 댓글만 필터링해.

## 3단계: 요약 생성
각 티켓에 대해 다음 형식으로 요약해:
- ticket_key: 티켓 키 (예: "{{PROJECT_KEY}}-123")
- title_summary: 티켓 제목을 간단히 요약 (한국어)
- work_summary: 이번 주 댓글과 상태를 분석해서 작업 내용을 한 문장으로 요약 (한국어, 50자 이내)
- status: 현재 티켓 상태 (In Progress, Done, In Review, To Do, Blocked 중 하나)
- has_update: 이번 주 댓글이 있으면 true, 없으면 false

이번 주 댓글이 없는 티켓은 work_summary를 "이번 주 업데이트 없음"으로 설정하고 has_update를 false로 해.

## 4단계: Slack 전송
요약 결과를 JSON 배열로 만들어서 아래 명령어를 실행해:
cd {{PROJECT_DIR}} && python3 -m src.run_report '<JSON배열>'

JSON 예시:
[{"ticket_key":"{{PROJECT_KEY}}-123","title_summary":"검색 API 개선","work_summary":"검색 응답 속도 최적화 작업 완료","status":"In Progress","has_update":true}]

주의사항:
- JSON은 반드시 single quote로 감싸서 shell argument로 전달해
- JSON 내부의 문자열은 double quote 사용
- 한국어로 요약해

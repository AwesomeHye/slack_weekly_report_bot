"""공통 테스트 fixture 모듈.

TicketSummary 생성, AppConfig mock, 환경 변수 mock fixture를 제공한다.
"""

import pytest

from src.models import TicketSummary
from src.config_manager import AppConfig


@pytest.fixture
def sample_ticket_summary():
    """단일 TicketSummary 인스턴스를 반환한다."""
    return TicketSummary(
        ticket_key="EXAMPLE-123",
        title_summary="검색 API 성능 개선",
        work_summary="캐시 레이어 추가 및 응답 시간 30% 단축",
        status="In Progress",
        has_update=True,
    )


@pytest.fixture
def sample_ticket_summaries():
    """다양한 상태를 가진 TicketSummary 목록을 반환한다."""
    return [
        TicketSummary(
            ticket_key="EXAMPLE-101",
            title_summary="검색 API 성능 개선",
            work_summary="캐시 레이어 추가 및 응답 시간 30% 단축",
            status="In Progress",
            has_update=True,
        ),
        TicketSummary(
            ticket_key="EXAMPLE-102",
            title_summary="인덱싱 파이프라인 리팩토링",
            work_summary="배치 처리 로직 분리 완료",
            status="In Progress",
            has_update=True,
        ),
        TicketSummary(
            ticket_key="EXAMPLE-103",
            title_summary="검색 결과 정렬 버그 수정",
            work_summary="한글 정렬 이슈 해결 및 배포 완료",
            status="Done",
            has_update=True,
        ),
        TicketSummary(
            ticket_key="EXAMPLE-104",
            title_summary="검색 필터 UI 개선",
            work_summary="업데이트 없음",
            status="To Do",
            has_update=False,
        ),
    ]


@pytest.fixture
def mock_app_config():
    """모든 필드가 채워진 AppConfig 인스턴스를 반환한다."""
    return AppConfig(
        jira_board_url="https://example.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=000000:test-account-id",
        jira_project_key="EXAMPLE",
        jira_board_id=123,
        assignee_account_id="000000:test-account-id",
        slack_user_id="U0123456789",
        schedule_day="thursday",
        schedule_time="17:00",
        timezone="Asia/Seoul",
        slack_bot_token="xoxb-test-token",
    )


@pytest.fixture
def mock_env_vars(monkeypatch):
    """SLACK_BOT_TOKEN 환경 변수를 설정한다."""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

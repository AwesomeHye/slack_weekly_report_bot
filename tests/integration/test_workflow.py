"""전체 워크플로우 통합 테스트.

설정 로드 → TicketSummary 목록 생성 → format_message → Slack 앱 메시지 전송
전체 흐름을 검증한다. Slack API는 responses 라이브러리로 mock 처리한다.

Validates: Requirements 7.6
"""

import json
import logging
import os
import tempfile
from unittest.mock import patch

import pytest
import responses
import yaml

from src.config_manager import ConfigManager, AppConfig
from src.models import TicketSummary
from src.slack_message_sender import SlackMessageSender
from src.utils import get_week_range, format_week_range

SLACK_API_URL = "https://slack.com/api/chat.postMessage"


@pytest.fixture
def config_yaml_data():
    """유효한 config.yaml 데이터를 반환한다."""
    return {
        "jira": {
            "board_url": "https://example.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=000000:test-account-id",
        },
        "slack": {
            "user_id": "U0123456789",
            "bot_token": "xoxb-test-token",
        },
        "schedule": {
            "day": "thursday",
            "time": "17:00",
            "timezone": "Asia/Seoul",
        },
    }


@pytest.fixture
def config_file(config_yaml_data):
    """임시 config.yaml 파일을 생성하고 경로를 반환한다."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_yaml_data, f)
        path = f.name
    yield path
    os.unlink(path)


class TestFullWorkflow:
    """정상 흐름: 설정 로드 → TicketSummary 목록 → format_message → send_report 성공 검증."""

    @responses.activate
    def test_end_to_end_report_success(self, config_file, mock_env_vars):
        """설정 로드부터 Slack 전송까지 전체 워크플로우가 성공한다."""
        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        # 1. 설정 로드
        config = ConfigManager(config_path=config_file).load()
        assert config.jira_project_key == "EXAMPLE"
        assert config.slack_user_id == "U0123456789"

        # 2. TicketSummary 목록 생성 (Kiro LLM 요약 결과 시뮬레이션)
        summaries = [
            TicketSummary(
                ticket_key="EXAMPLE-101",
                title_summary="검색 API 성능 개선",
                work_summary="캐시 레이어 추가 및 응답 시간 30% 단축",
                status="In Progress",
                has_update=True,
            ),
            TicketSummary(
                ticket_key="EXAMPLE-102",
                title_summary="검색 결과 정렬 버그 수정",
                work_summary="한글 정렬 이슈 해결 및 배포 완료",
                status="Done",
                has_update=True,
            ),
        ]

        # 3. SlackMessageSender 생성 및 메시지 포맷팅
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )
        week_range = "2024.01.15 ~ 2024.01.21"
        message = sender.format_message(summaries, week_range)

        assert "📋 주간 보고" in message
        assert week_range in message
        assert "검색 API 성능 개선" in message
        assert "총 2건" in message

        # 4. Slack 전송
        result = sender.send_report(summaries, week_range)
        assert result is True

        # 5. API 호출 검증
        assert len(responses.calls) == 1
        body = json.loads(responses.calls[0].request.body)
        assert body["channel"] == "U0123456789"
        assert "📋 주간 보고" in body["text"]

    @responses.activate
    def test_workflow_with_week_range_utils(self, config_file, mock_env_vars):
        """utils의 get_week_range, format_week_range와 함께 전체 흐름이 동작한다."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        config = ConfigManager(config_path=config_file).load()

        dt = datetime(2024, 1, 18, 14, 0, tzinfo=ZoneInfo("Asia/Seoul"))
        week_start, week_end = get_week_range(dt)
        week_range = format_week_range(week_start, week_end)

        summaries = [
            TicketSummary(
                ticket_key="EXAMPLE-200",
                title_summary="인덱싱 파이프라인 리팩토링",
                work_summary="배치 처리 로직 분리 완료",
                status="In Progress",
                has_update=True,
            ),
        ]

        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )
        result = sender.send_report(summaries, week_range)

        assert result is True
        body = json.loads(responses.calls[0].request.body)
        assert "2024.01.15 ~ 2024.01.21" in body["text"]


class TestEmptyTicketWorkflow:
    """빈 티켓: 빈 목록 → '업데이트 없음' 메시지 전송 검증."""

    @responses.activate
    def test_empty_ticket_list_sends_no_update_message(
        self, config_file, mock_env_vars
    ):
        """티켓이 0건이면 '이번 주 업데이트된 티켓이 없습니다' 메시지를 전송한다."""
        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        config = ConfigManager(config_path=config_file).load()
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )

        result = sender.send_report([], "2024.01.15 ~ 2024.01.21")

        assert result is True
        body = json.loads(responses.calls[0].request.body)
        assert "이번 주 업데이트된 티켓이 없습니다" in body["text"]
        assert "2024.01.15 ~ 2024.01.21" in body["text"]


class TestSlackFailureWorkflow:
    """Slack 실패: API 실패 → 재시도 3회 → 최종 실패 로그 검증."""

    @responses.activate
    @patch("time.sleep")
    def test_slack_api_failure_retries_and_fails(
        self, mock_sleep, config_file, mock_env_vars, caplog
    ):
        """Slack API가 3회 모두 실패하면 False를 반환하고 최종 실패 로그를 기록한다."""
        for _ in range(3):
            responses.add(
                responses.POST,
                SLACK_API_URL,
                json={"ok": False, "error": "internal_error"},
                status=200,
            )

        config = ConfigManager(config_path=config_file).load()
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )

        summaries = [
            TicketSummary(
                ticket_key="EXAMPLE-300",
                title_summary="테스트 티켓",
                work_summary="테스트 작업",
                status="In Progress",
                has_update=True,
            ),
        ]

        with caplog.at_level(logging.ERROR):
            result = sender.send_report(summaries, "2024.01.15 ~ 2024.01.21")

        assert result is False
        assert len(responses.calls) == 3
        assert mock_sleep.call_count == 2
        assert "최종 실패" in caplog.text

    @responses.activate
    @patch("time.sleep")
    def test_slack_api_recovers_on_retry(
        self, mock_sleep, config_file, mock_env_vars
    ):
        """첫 번째 실패 후 두 번째 시도에서 성공하면 True를 반환한다."""
        responses.add(
            responses.POST,
            SLACK_API_URL,
            json={"ok": False, "error": "timeout"},
            status=200,
        )
        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        config = ConfigManager(config_path=config_file).load()
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )

        summaries = [
            TicketSummary(
                ticket_key="EXAMPLE-301",
                title_summary="테스트 티켓",
                work_summary="테스트 작업",
                status="Done",
                has_update=True,
            ),
        ]

        result = sender.send_report(summaries, "2024.01.15 ~ 2024.01.21")

        assert result is True
        assert len(responses.calls) == 2


class TestErrorNotificationWorkflow:
    """에러 알림: 에러 발생 → send_error_notification 전송 검증."""

    @responses.activate
    def test_error_notification_sent_on_failure(
        self, config_file, mock_env_vars
    ):
        """에러 발생 시 send_error_notification으로 에러 알림을 전송한다."""
        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        config = ConfigManager(config_path=config_file).load()
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )

        error_msg = "Jira MCP 호출 실패: 연결 시간 초과"
        result = sender.send_error_notification(error_msg)

        assert result is True
        body = json.loads(responses.calls[0].request.body)
        assert body["channel"] == config.slack_user_id
        assert "⚠️" in body["text"]
        assert "Jira MCP 호출 실패" in body["text"]

    @responses.activate
    def test_error_notification_workflow_simulates_jira_failure(
        self, config_file, mock_env_vars
    ):
        """Jira 조회 실패 시나리오: 에러 캐치 → 에러 알림 전송 전체 흐름."""
        responses.add(
            responses.POST, SLACK_API_URL, json={"ok": True}, status=200
        )

        config = ConfigManager(config_path=config_file).load()
        sender = SlackMessageSender(
            bot_token=config.slack_bot_token, user_id=config.slack_user_id
        )

        # Jira MCP 호출 실패 시뮬레이션
        try:
            raise ConnectionError("Jira MCP Server 연결 실패")
        except ConnectionError as e:
            result = sender.send_error_notification(str(e))

        assert result is True
        body = json.loads(responses.calls[0].request.body)
        assert "Jira MCP Server 연결 실패" in body["text"]

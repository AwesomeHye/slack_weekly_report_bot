"""Slack_Message_Sender 단위 테스트.

앱 메시지 전송 성공/실패, 메시지 포맷 검증, 재시도 로직 검증, Bot Token 인증 검증.
Slack API 호출은 responses 라이브러리로 mock 처리한다.
Validates: Requirements 7.2, 7.5
"""

import json
from unittest.mock import patch

import pytest
import responses

from src.models import TicketSummary
from src.slack_message_sender import SlackMessageSender

SLACK_API_URL = "https://slack.com/api/chat.postMessage"
BOT_TOKEN = "xoxb-test-bot-token"
USER_ID = "U0123456789"


@pytest.fixture
def sender():
    """SlackMessageSender 인스턴스를 반환한다."""
    return SlackMessageSender(bot_token=BOT_TOKEN, user_id=USER_ID)


class TestSendReportSuccess:
    """앱 메시지 전송 성공 시 True 반환 검증."""

    @responses.activate
    def test_send_report_returns_true_on_success(self, sender, sample_ticket_summaries):
        responses.add(
            responses.POST,
            SLACK_API_URL,
            json={"ok": True},
            status=200,
        )

        result = sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert result is True

    @responses.activate
    def test_send_report_calls_slack_api_once_on_success(self, sender, sample_ticket_summaries):
        responses.add(
            responses.POST,
            SLACK_API_URL,
            json={"ok": True},
            status=200,
        )

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert len(responses.calls) == 1


class TestSendReportRetry:
    """앱 메시지 전송 실패 시 최대 3회 재시도 검증."""

    @responses.activate
    @patch("time.sleep")
    def test_retries_on_api_error_up_to_3_times(self, mock_sleep, sender, sample_ticket_summaries):
        """Slack API가 ok=false를 반환하면 최대 3회 재시도한다."""
        responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "too_many_requests"}, status=200)
        responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "too_many_requests"}, status=200)
        responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "too_many_requests"}, status=200)

        result = sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert result is False
        assert len(responses.calls) == 3

    @responses.activate
    @patch("time.sleep")
    def test_returns_false_after_all_retries_exhausted(self, mock_sleep, sender, sample_ticket_summaries):
        for _ in range(3):
            responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "internal_error"}, status=200)

        result = sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert result is False

    @responses.activate
    @patch("time.sleep")
    def test_succeeds_on_second_attempt(self, mock_sleep, sender, sample_ticket_summaries):
        """첫 번째 실패 후 두 번째 시도에서 성공하면 True를 반환한다."""
        responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "timeout"}, status=200)
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        result = sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert result is True
        assert len(responses.calls) == 2

    @responses.activate
    @patch("time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep, sender, sample_ticket_summaries):
        """재시도 시 지수 백오프(1초→2초) 딜레이가 적용된다."""
        for _ in range(3):
            responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "error"}, status=200)

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

    @responses.activate
    @patch("time.sleep")
    def test_retries_on_connection_exception(self, mock_sleep, sender, sample_ticket_summaries):
        """네트워크 예외 발생 시에도 재시도한다."""
        responses.add(responses.POST, SLACK_API_URL, body=ConnectionError("connection refused"))
        responses.add(responses.POST, SLACK_API_URL, body=ConnectionError("connection refused"))
        responses.add(responses.POST, SLACK_API_URL, body=ConnectionError("connection refused"))

        result = sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        assert result is False
        assert len(responses.calls) == 3


class TestBotTokenAuth:
    """Bot Token 인증 헤더(Authorization: Bearer) 올바르게 설정 검증."""

    @responses.activate
    def test_authorization_header_contains_bearer_token(self, sender, sample_ticket_summaries):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        request = responses.calls[0].request
        assert request.headers["Authorization"] == f"Bearer {BOT_TOKEN}"

    @responses.activate
    def test_content_type_is_json(self, sender, sample_ticket_summaries):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        request = responses.calls[0].request
        assert "application/json" in request.headers["Content-Type"]


class TestChannelParameter:
    """channel 파라미터에 User ID 올바르게 지정 검증."""

    @responses.activate
    def test_channel_is_user_id(self, sender, sample_ticket_summaries):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        request = responses.calls[0].request
        body = json.loads(request.body)
        assert body["channel"] == USER_ID

    @responses.activate
    def test_text_field_present_in_body(self, sender, sample_ticket_summaries):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_report(sample_ticket_summaries, "2024.01.15 ~ 2024.01.21")

        request = responses.calls[0].request
        body = json.loads(request.body)
        assert "text" in body
        assert len(body["text"]) > 0


class TestEmptyTicketMessage:
    """빈 티켓 목록 시 '업데이트된 티켓이 없습니다' 메시지 포맷 검증."""

    def test_format_message_empty_list(self, sender):
        message = sender.format_message([], "2024.01.15 ~ 2024.01.21")

        assert "이번 주 업데이트된 티켓이 없습니다" in message
        assert "2024.01.15 ~ 2024.01.21" in message

    @responses.activate
    def test_send_report_empty_list_sends_no_update_message(self, sender):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        result = sender.send_report([], "2024.01.15 ~ 2024.01.21")

        assert result is True
        body = json.loads(responses.calls[0].request.body)
        assert "이번 주 업데이트된 티켓이 없습니다" in body["text"]


class TestErrorNotification:
    """에러 알림 메시지 전송 검증."""

    @responses.activate
    def test_send_error_notification_returns_true_on_success(self, sender):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        result = sender.send_error_notification("Jira MCP 호출 실패")

        assert result is True

    @responses.activate
    def test_error_notification_contains_error_message(self, sender):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_error_notification("Jira MCP 호출 실패")

        body = json.loads(responses.calls[0].request.body)
        assert "Jira MCP 호출 실패" in body["text"]
        assert "⚠️" in body["text"]

    @responses.activate
    def test_error_notification_sends_to_user_id(self, sender):
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        sender.send_error_notification("에러 발생")

        body = json.loads(responses.calls[0].request.body)
        assert body["channel"] == USER_ID

    @responses.activate
    @patch("time.sleep")
    def test_error_notification_retries_on_failure(self, mock_sleep, sender):
        """에러 알림도 실패 시 재시도한다."""
        responses.add(responses.POST, SLACK_API_URL, json={"ok": False, "error": "error"}, status=200)
        responses.add(responses.POST, SLACK_API_URL, json={"ok": True}, status=200)

        result = sender.send_error_notification("에러 발생")

        assert result is True
        assert len(responses.calls) == 2

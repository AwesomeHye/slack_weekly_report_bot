import time
import logging
import requests
from typing import List

from src.models import TicketSummary

logger = logging.getLogger(__name__)


class SlackMessageSender:
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    SLACK_API_URL = "https://slack.com/api/chat.postMessage"

    def __init__(self, bot_token: str, user_id: str):
        """
        Slack 앱 메시지 전송 클라이언트를 초기화한다.

        Args:
            bot_token: Slack Bot Token (xoxb-...)
            user_id: Slack User ID (U로 시작)
        """
        self.bot_token = bot_token
        self.user_id = user_id

    def send_report(self, summaries: List[TicketSummary], week_range: str) -> bool:
        """주간 보고 메시지를 Slack 앱 메시지 탭으로 전송한다."""
        message = self.format_message(summaries, week_range)
        return self._send_with_retry(message)

    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 메시지를 앱 메시지 탭으로 전송한다."""
        message = f"⚠️ 주간 보고 생성 중 오류 발생:\n{error_message}"
        return self._send_with_retry(message)

    def format_message(self, summaries: List[TicketSummary], week_range: str) -> str:
        """요약 목록을 Slack 메시지 형식으로 포맷팅한다."""
        if not summaries:
            return f"📋 주간 보고 ({week_range})\n\n이번 주 업데이트된 티켓이 없습니다."

        groups: dict[str, list] = {}
        for s in summaries:
            groups.setdefault(s.status, []).append(s)

        lines = [f"📋 주간 보고 ({week_range})", ""]
        for status, items in groups.items():
            lines.append(f"[{status}]")
            for item in items:
                lines.append(f"• {item.title_summary} : {item.work_summary}")
            lines.append("")

        lines.append(f"총 {len(summaries)}건")
        return "\n".join(lines)

    def _send_with_retry(self, message: str) -> bool:
        """재시도 로직이 포함된 메시지 전송. 지수 백오프(1초→2초→4초) 최대 3회."""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    self.SLACK_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "channel": self.user_id,
                        "text": message,
                    },
                    timeout=10,
                )
                data = response.json()
                if data.get("ok"):
                    logger.info("Slack 앱 메시지 전송 성공")
                    return True
                else:
                    logger.error(f"Slack API 에러: {data.get('error')}")
            except Exception as e:
                logger.error(f"Slack 전송 실패 (시도 {attempt + 1}/{self.MAX_RETRIES}): {e}")

            if attempt < self.MAX_RETRIES - 1:
                delay = self.BASE_DELAY * (2 ** attempt)
                time.sleep(delay)

        logger.error("Slack 앱 메시지 전송 최종 실패")
        return False

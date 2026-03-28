"""주간 보고 실행 엔트리포인트.

설정을 로드하고 Slack 앱 메시지 탭으로 주간 보고를 전송한다.

Jira 티켓 조회 및 LLM 요약은 Claude(MCP)가 수행하며,
요약 결과를 JSON 인자로 전달받아 Slack 전송만 수행한다.

사용법:
    python3 -m src.run_report '<JSON>'
    python3 -m src.run_report  # 인자 없으면 "업데이트 없음" 메시지 전송
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config_manager import ConfigManager
from src.models import TicketSummary
from src.slack_message_sender import SlackMessageSender
from src.utils import get_week_range, format_week_range, KST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    try:
        config = ConfigManager(
            config_path=str(Path(project_root) / "config.yaml")
        ).load()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"설정 로드 실패: {e}")
        sys.exit(1)

    sender = SlackMessageSender(
        bot_token=config.slack_bot_token,
        user_id=config.slack_user_id,
    )

    now = datetime.now(KST)
    week_start, week_end = get_week_range(now)
    week_range = format_week_range(week_start, week_end)

    # Claude가 JSON 인자로 요약 결과를 전달하면 파싱, 없으면 빈 목록
    summaries = []
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            summaries = [TicketSummary(**item) for item in data]
            logger.info(f"요약 데이터 {len(summaries)}건 수신")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"JSON 파싱 실패: {e}")
            sys.exit(1)

    logger.info(f"주간 보고 전송 시작: {week_range}")
    success = sender.send_report(summaries, week_range)

    if success:
        logger.info("주간 보고 전송 완료")
    else:
        logger.error("주간 보고 전송 실패")
        sender.send_error_notification("Slack 메시지 전송에 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()

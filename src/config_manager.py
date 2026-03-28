"""설정 관리 모듈.

config.yaml + 환경 변수를 통합 관리한다.
Jira 보드 URL에서 프로젝트 키, 보드 ID, assignee를 자동 파싱한다.
"""

import re
import yaml
import logging
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """애플리케이션 설정 데이터 클래스."""

    # Jira 설정 (보드 URL에서 파싱)
    jira_board_url: str            # 전체 보드 URL
    jira_project_key: str          # URL에서 파싱: "EXAMPLE"
    jira_board_id: int             # URL에서 파싱: 123
    assignee_account_id: str       # URL 쿼리에서 파싱: "712020:..."
    # Slack 설정
    slack_user_id: str             # "U..." (앱 메시지 전송 대상)
    # 스케줄 설정
    schedule_day: str              # "thursday"
    schedule_time: str             # "17:00"
    timezone: str                  # "Asia/Seoul"
    slack_bot_token: str           # xoxb-...


REQUIRED_CONFIG_FIELDS = [
    "jira.board_url",
    "slack.user_id",
    "slack.bot_token",
]

REQUIRED_ENV_VARS = []


def parse_board_url(url: str) -> dict:
    """Jira 보드 URL에서 project_key, board_id, assignee_account_id를 파싱한다.

    지원 URL 형식:
      https://<domain>/jira/software/c/projects/<KEY>/boards/<ID>?assignee=<ACCOUNT_ID>
    """
    parsed = urlparse(url)
    path = parsed.path

    # /projects/<KEY>/boards/<ID> 패턴 매칭
    match = re.search(r"/projects/([^/]+)/boards/(\d+)", path)
    if not match:
        raise ValueError(
            f"Jira 보드 URL 형식이 올바르지 않습니다: {url}\n"
            "예시: https://your-domain.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=..."
        )

    project_key = match.group(1)
    board_id = int(match.group(2))

    # 쿼리 파라미터에서 assignee 추출
    query_params = parse_qs(parsed.query)
    assignee = query_params.get("assignee", [""])[0]

    return {
        "project_key": project_key,
        "board_id": board_id,
        "assignee_account_id": assignee,
    }


class ConfigManager:
    """config.yaml + 환경 변수를 통합 관리하는 설정 매니저."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path

    def load(self) -> AppConfig:
        """config.yaml + 환경 변수를 읽어 AppConfig를 반환한다."""
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        self._validate_config(data)
        self._validate_env_vars()

        board_url = data["jira"]["board_url"]
        parsed = parse_board_url(board_url)

        return AppConfig(
            jira_board_url=board_url,
            jira_project_key=parsed["project_key"],
            jira_board_id=parsed["board_id"],
            assignee_account_id=parsed["assignee_account_id"],
            slack_user_id=data["slack"]["user_id"],
            schedule_day=data.get("schedule", {}).get("day", "thursday"),
            schedule_time=data.get("schedule", {}).get("time", "17:00"),
            timezone=data.get("schedule", {}).get("timezone", "Asia/Seoul"),
            slack_bot_token=data["slack"]["bot_token"],
        )

    def _validate_config(self, data: dict) -> None:
        """필수 설정값 누락 시 에러를 발생시킨다."""
        missing = []
        for field_path in REQUIRED_CONFIG_FIELDS:
            keys = field_path.split(".")
            value = data
            for key in keys:
                if not isinstance(value, dict) or key not in value:
                    missing.append(field_path)
                    break
                value = value[key]
            else:
                if value is None or value == "":
                    missing.append(field_path)
        if missing:
            raise ValueError(f"필수 설정값 누락: {', '.join(missing)}")

    def _validate_env_vars(self) -> None:
        """필수 환경 변수 누락 시 에러를 발생시킨다."""
        missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
        if missing:
            raise ValueError(f"필수 환경 변수 누락: {', '.join(missing)}")

    @staticmethod
    def serialize_config(config: AppConfig) -> dict:
        """AppConfig를 YAML 직렬화 가능한 dict로 변환한다."""
        return {
            "jira": {
                "board_url": config.jira_board_url,
            },
            "slack": {
                "user_id": config.slack_user_id,
                "bot_token": config.slack_bot_token,
            },
            "schedule": {
                "day": config.schedule_day,
                "time": config.schedule_time,
                "timezone": config.timezone,
            },
        }

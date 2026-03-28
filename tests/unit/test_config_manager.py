"""Config_Manager 단위 테스트.

config.yaml 로드, 보드 URL 파싱, 환경 변수 로드, 필수값 누락 검증을 테스트한다.
Validates: Requirements 7.3
"""

import pytest
import yaml

from src.config_manager import ConfigManager, AppConfig, parse_board_url


BOARD_URL = "https://example.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=000000:test-account-id"

VALID_CONFIG_DATA = {
    "jira": {
        "board_url": BOARD_URL,
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


def _write_config(tmp_path, data):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(data, allow_unicode=True))
    return str(config_file)


class TestParseBoardUrl:
    """보드 URL 파싱 검증."""

    def test_parses_project_key(self):
        result = parse_board_url(BOARD_URL)
        assert result["project_key"] == "EXAMPLE"

    def test_parses_board_id(self):
        result = parse_board_url(BOARD_URL)
        assert result["board_id"] == 123

    def test_parses_assignee(self):
        result = parse_board_url(BOARD_URL)
        assert result["assignee_account_id"] == "000000:test-account-id"

    def test_no_assignee_returns_empty(self):
        url = "https://example.atlassian.net/jira/software/c/projects/TEST/boards/100"
        result = parse_board_url(url)
        assert result["assignee_account_id"] == ""

    def test_invalid_url_raises_error(self):
        with pytest.raises(ValueError, match="형식이 올바르지 않습니다"):
            parse_board_url("https://example.com/not-a-board")


class TestConfigManagerLoadSuccess:
    """config.yaml 로드 성공 및 AppConfig 필드 매핑 검증."""

    def test_load_returns_app_config(self, tmp_path):
        config_path = _write_config(tmp_path, VALID_CONFIG_DATA)
        config = ConfigManager(config_path).load()
        assert isinstance(config, AppConfig)

    def test_jira_fields_parsed_from_url(self, tmp_path):
        config_path = _write_config(tmp_path, VALID_CONFIG_DATA)
        config = ConfigManager(config_path).load()
        assert config.jira_project_key == "EXAMPLE"
        assert config.jira_board_id == 123
        assert config.assignee_account_id == "000000:test-account-id"
        assert config.jira_board_url == BOARD_URL

    def test_slack_fields_mapped(self, tmp_path):
        config_path = _write_config(tmp_path, VALID_CONFIG_DATA)
        config = ConfigManager(config_path).load()
        assert config.slack_user_id == "U0123456789"

    def test_schedule_defaults_when_missing(self, tmp_path):
        data = {"jira": VALID_CONFIG_DATA["jira"], "slack": VALID_CONFIG_DATA["slack"]}
        config_path = _write_config(tmp_path, data)
        config = ConfigManager(config_path).load()
        assert config.schedule_day == "thursday"
        assert config.schedule_time == "17:00"
        assert config.timezone == "Asia/Seoul"


class TestConfigManagerBotToken:
    """bot_token 로드 검증."""

    def test_bot_token_loaded_from_config(self, tmp_path):
        config_path = _write_config(tmp_path, VALID_CONFIG_DATA)
        config = ConfigManager(config_path).load()
        assert config.slack_bot_token == "xoxb-test-token"


class TestConfigManagerMissingConfigFields:
    """필수 설정값 누락 시 ValueError 발생 검증."""

    def test_missing_board_url(self, tmp_path):
        data = {"jira": {}, "slack": {"user_id": "U123", "bot_token": "xoxb-test"}}
        config_path = _write_config(tmp_path, data)
        with pytest.raises(ValueError, match="jira.board_url"):
            ConfigManager(config_path).load()

    def test_missing_slack_user_id(self, tmp_path):
        data = {"jira": {"board_url": BOARD_URL}, "slack": {"bot_token": "xoxb-test"}}
        config_path = _write_config(tmp_path, data)
        with pytest.raises(ValueError, match="slack.user_id"):
            ConfigManager(config_path).load()

    def test_missing_slack_bot_token(self, tmp_path):
        data = {"jira": {"board_url": BOARD_URL}, "slack": {"user_id": "U123"}}
        config_path = _write_config(tmp_path, data)
        with pytest.raises(ValueError, match="slack.bot_token"):
            ConfigManager(config_path).load()

    def test_empty_board_url(self, tmp_path):
        data = {"jira": {"board_url": ""}, "slack": {"user_id": "U123", "bot_token": "xoxb-test"}}
        config_path = _write_config(tmp_path, data)
        with pytest.raises(ValueError, match="jira.board_url"):
            ConfigManager(config_path).load()

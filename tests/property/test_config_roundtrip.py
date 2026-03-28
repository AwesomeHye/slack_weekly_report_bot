"""Property 5: 설정 파일 라운드트립 속성 기반 테스트.

임의의 AppConfig → serialize_config → YAML 직렬화 → 로드 → 원본 일치 검증.

Feature: weekly-report-slack-bot, Property 5: 설정 파일 라운드트립

Validates: Requirements 5.3
"""

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from string import printable

from src.config_manager import AppConfig, ConfigManager

printable_text = st.text(alphabet=printable, min_size=1, max_size=50)
board_id_strategy = st.integers(min_value=1, max_value=99999)

# 유효한 보드 URL 생성 전략
board_url_strategy = st.builds(
    lambda key, bid, aid: f"https://example.atlassian.net/jira/software/c/projects/{key}/boards/{bid}?assignee={aid}",
    key=st.from_regex(r"[A-Z]{2,6}", fullmatch=True),
    bid=board_id_strategy,
    aid=printable_text,
)

app_config_strategy = st.builds(
    AppConfig,
    jira_board_url=board_url_strategy,
    jira_project_key=st.from_regex(r"[A-Z]{2,6}", fullmatch=True),
    jira_board_id=board_id_strategy,
    assignee_account_id=printable_text,
    slack_user_id=printable_text,
    schedule_day=printable_text,
    schedule_time=printable_text,
    timezone=printable_text,
    slack_bot_token=printable_text,
)


@settings(max_examples=100)
@given(config=app_config_strategy)
def test_serialize_yaml_roundtrip(config):
    """serialize_config → YAML dump → YAML load 라운드트립이 동일한 dict를 복원해야 한다."""
    serialized = ConfigManager.serialize_config(config)
    yaml_str = yaml.dump(serialized)
    loaded = yaml.safe_load(yaml_str)
    assert loaded == serialized


@settings(max_examples=100)
@given(config=app_config_strategy)
def test_roundtrip_preserves_board_url(config):
    """라운드트립 후 board_url이 원본과 일치해야 한다."""
    serialized = ConfigManager.serialize_config(config)
    yaml_str = yaml.dump(serialized)
    loaded = yaml.safe_load(yaml_str)
    assert loaded["jira"]["board_url"] == config.jira_board_url


@settings(max_examples=100)
@given(config=app_config_strategy)
def test_roundtrip_preserves_slack_user_id(config):
    """라운드트립 후 slack_user_id가 원본과 일치해야 한다."""
    serialized = ConfigManager.serialize_config(config)
    yaml_str = yaml.dump(serialized)
    loaded = yaml.safe_load(yaml_str)
    assert loaded["slack"]["user_id"] == config.slack_user_id

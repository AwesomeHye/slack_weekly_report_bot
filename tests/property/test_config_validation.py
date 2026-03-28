"""Property 6: 필수 설정값 누락 검증 속성 기반 테스트.

임의의 필수 필드 제거 → _validate_config → ValueError 발생 + 필드명 포함 검증.

Feature: weekly-report-slack-bot, Property 6: 필수 설정값 누락 검증

Validates: Requirements 5.4
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.config_manager import ConfigManager, REQUIRED_CONFIG_FIELDS


def _build_valid_config() -> dict:
    """모든 필수 필드가 포함된 유효한 config dict를 생성한다."""
    return {
        "jira": {
            "board_url": "https://example.atlassian.net/jira/software/c/projects/EXAMPLE/boards/123?assignee=test",
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


def _remove_field(data: dict, field_path: str) -> dict:
    """중첩 dict에서 dot-notation 경로의 필드를 제거한다."""
    keys = field_path.split(".")
    current = data
    for key in keys[:-1]:
        current = current[key]
    del current[keys[-1]]
    return data


# 생성 전략: 필수 필드 서브셋 전략
fields_to_remove_strategy = st.sets(
    st.sampled_from(REQUIRED_CONFIG_FIELDS), min_size=1
)


@settings(max_examples=100)
@given(fields_to_remove=fields_to_remove_strategy)
def test_missing_required_fields_raises_value_error(fields_to_remove):
    """필수 필드를 하나 이상 제거하면 _validate_config가 ValueError를 발생시켜야 한다.

    **Validates: Requirements 5.4**
    """
    config = _build_valid_config()
    for field_path in fields_to_remove:
        _remove_field(config, field_path)

    manager = ConfigManager()

    with pytest.raises(ValueError):
        manager._validate_config(config)


@settings(max_examples=100)
@given(fields_to_remove=fields_to_remove_strategy)
def test_missing_fields_error_message_contains_field_name(fields_to_remove):
    """ValueError 메시지에 누락된 필드 경로가 하나 이상 포함되어야 한다.

    **Validates: Requirements 5.4**
    """
    config = _build_valid_config()
    for field_path in fields_to_remove:
        _remove_field(config, field_path)

    manager = ConfigManager()

    with pytest.raises(ValueError) as exc_info:
        manager._validate_config(config)

    error_message = str(exc_info.value)
    assert any(
        field in error_message for field in fields_to_remove
    ), f"에러 메시지에 누락 필드가 포함되지 않음: {error_message}, 제거된 필드: {fields_to_remove}"

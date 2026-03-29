"""Property 9: 크론 표현식 유효성 검증

임의의 유효/무효 크론 필드 값 → validate_cron → 범위 내 통과, 범위 밖 거부 검증

Validates: Requirements 8.2, 8.9
"""
import pytest
from hypothesis import given, strategies as st, assume

from src.schedule_parser import ScheduleParser, CRON_FIELD_RANGES


# 유효한 크론 필드 값 생성 전략
valid_minute = st.integers(min_value=0, max_value=59)
valid_hour = st.integers(min_value=0, max_value=23)
valid_day_of_month = st.integers(min_value=1, max_value=31)
valid_month = st.integers(min_value=1, max_value=12)
valid_day_of_week = st.integers(min_value=0, max_value=7)

# 무효한 크론 필드 값 생성 전략 (범위 밖, 양수만)
invalid_minute = st.integers(min_value=60, max_value=999)
invalid_hour = st.integers(min_value=24, max_value=999)
invalid_day_of_month = st.one_of(
    st.integers(min_value=0, max_value=0),  # 0은 무효
    st.integers(min_value=32, max_value=999)
)
invalid_month = st.one_of(
    st.integers(min_value=0, max_value=0),  # 0은 무효
    st.integers(min_value=13, max_value=999)
)
invalid_day_of_week = st.integers(min_value=8, max_value=999)


class TestCronValidationProperty:
    """Property 9: 크론 표현식 유효성 검증 속성 테스트"""

    @given(
        minute=valid_minute,
        hour=valid_hour,
        day_of_month=valid_day_of_month,
        month=valid_month,
        day_of_week=valid_day_of_week,
    )
    def test_valid_cron_fields_pass_validation(
        self, minute, hour, day_of_month, month, day_of_week
    ):
        """유효한 범위 내 필드 값은 검증 통과"""
        cron = f"{minute} {hour} {day_of_month} {month} {day_of_week}"
        
        # 에러 없이 통과해야 함
        ScheduleParser.validate_cron(cron)

    @given(minute=invalid_minute)
    def test_invalid_minute_fails_validation(self, minute):
        """분 필드 범위 초과 값은 검증 실패"""
        cron = f"{minute} 12 1 1 1"
        
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron(cron)
        
        assert "minute" in str(exc_info.value) or "범위" in str(exc_info.value)

    @given(hour=invalid_hour)
    def test_invalid_hour_fails_validation(self, hour):
        """시 필드 범위 초과 값은 검증 실패"""
        cron = f"0 {hour} 1 1 1"
        
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron(cron)
        
        assert "hour" in str(exc_info.value) or "범위" in str(exc_info.value)

    @given(day_of_month=invalid_day_of_month)
    def test_invalid_day_of_month_fails_validation(self, day_of_month):
        """일 필드 범위 밖 값은 검증 실패"""
        cron = f"0 12 {day_of_month} 1 1"
        
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron(cron)
        
        assert "day_of_month" in str(exc_info.value) or "범위" in str(exc_info.value)

    @given(month=invalid_month)
    def test_invalid_month_fails_validation(self, month):
        """월 필드 범위 밖 값은 검증 실패"""
        cron = f"0 12 1 {month} 1"
        
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron(cron)
        
        assert "month" in str(exc_info.value) or "범위" in str(exc_info.value)

    @given(day_of_week=invalid_day_of_week)
    def test_invalid_day_of_week_fails_validation(self, day_of_week):
        """요일 필드 범위 초과 값은 검증 실패"""
        cron = f"0 12 1 1 {day_of_week}"
        
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron(cron)
        
        assert "day_of_week" in str(exc_info.value) or "범위" in str(exc_info.value)

    @given(
        minute=valid_minute,
        hour=valid_hour,
        day_of_week=valid_day_of_week,
    )
    def test_wildcard_fields_with_valid_values_pass(self, minute, hour, day_of_week):
        """와일드카드와 유효한 값 조합은 검증 통과"""
        cron = f"{minute} {hour} * * {day_of_week}"
        
        # 에러 없이 통과해야 함
        ScheduleParser.validate_cron(cron)

    @given(
        minute=valid_minute,
        hour=valid_hour,
    )
    def test_all_wildcards_except_time_pass(self, minute, hour):
        """시간만 지정하고 나머지 와일드카드인 경우 통과"""
        cron = f"{minute} {hour} * * *"
        
        ScheduleParser.validate_cron(cron)

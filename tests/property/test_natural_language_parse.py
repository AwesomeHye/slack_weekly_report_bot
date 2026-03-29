"""Property 10: 자연어 파싱 결과 유효성

임의의 한국어 자연어 패턴 조합 → parse → 결과가 유효한 크론 표현식인지 검증

Validates: Requirements 8.3, 8.4
"""
import pytest
from hypothesis import given, strategies as st, assume, settings

from src.schedule_parser import ScheduleParser, DAY_MAP


# 한국어 요일 전략
korean_days = st.sampled_from(list(DAY_MAP.keys()))

# 시간 전략 (1-12시)
hour_12 = st.integers(min_value=1, max_value=12)

# 시간 전략 (0-23시)
hour_24 = st.integers(min_value=0, max_value=23)

# 분 전략 (0-59분)
minute = st.integers(min_value=0, max_value=59)

# 오전/오후 전략
ampm = st.sampled_from(["오전", "오후"])


@st.composite
def korean_ampm_time(draw):
    """오전/오후 시간 패턴 생성 (예: "오후 3시", "오전 9시 30분")"""
    ap = draw(ampm)
    h = draw(hour_12)
    m = draw(st.one_of(st.none(), minute))
    
    if m is not None and m > 0:
        return f"{ap} {h}시 {m}분"
    return f"{ap} {h}시"


@st.composite
def korean_24hour_time(draw):
    """24시간 형식 시간 패턴 생성 (예: "17시", "9시 30분")"""
    h = draw(hour_24)
    m = draw(st.one_of(st.none(), minute))
    
    if m is not None and m > 0:
        return f"{h}시 {m}분"
    return f"{h}시"


@st.composite
def korean_colon_time(draw):
    """콜론 형식 시간 패턴 생성 (예: "17:00", "9:30")"""
    h = draw(hour_24)
    m = draw(minute)
    return f"{h}:{m:02d}"


@st.composite
def korean_weekly_schedule(draw):
    """매주 요일+시간 패턴 생성 (예: "매주 수요일 오후 3시")"""
    day = draw(korean_days)
    time_pattern = draw(st.one_of(
        korean_ampm_time(),
        korean_24hour_time(),
        korean_colon_time(),
    ))
    return f"매주 {day} {time_pattern}"


@st.composite
def korean_daily_schedule(draw):
    """매일 시간 패턴 생성 (예: "매일 오전 9시")"""
    time_pattern = draw(st.one_of(
        korean_ampm_time(),
        korean_24hour_time(),
        korean_colon_time(),
    ))
    return f"매일 {time_pattern}"


class TestNaturalLanguageParseProperty:
    """Property 10: 자연어 파싱 결과 유효성 속성 테스트"""

    @given(schedule=korean_weekly_schedule())
    @settings(max_examples=100)
    def test_weekly_schedule_produces_valid_cron(self, schedule):
        """매주 요일+시간 패턴은 유효한 크론 표현식 생성"""
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        # 결과가 유효한 크론 표현식인지 검증
        ScheduleParser.validate_cron(result.cron_expression)
        
        # 5개 필드인지 확인
        parts = result.cron_expression.split()
        assert len(parts) == 5
        
        # 요일 필드가 와일드카드가 아닌지 확인 (요일 지정됨)
        assert parts[4] != "*"

    @given(schedule=korean_daily_schedule())
    @settings(max_examples=100)
    def test_daily_schedule_produces_valid_cron(self, schedule):
        """매일 시간 패턴은 유효한 크론 표현식 생성"""
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        # 결과가 유효한 크론 표현식인지 검증
        ScheduleParser.validate_cron(result.cron_expression)
        
        # 5개 필드인지 확인
        parts = result.cron_expression.split()
        assert len(parts) == 5
        
        # 요일 필드가 와일드카드인지 확인 (매일)
        assert parts[4] == "*"

    @given(time_pattern=korean_ampm_time())
    @settings(max_examples=50)
    def test_ampm_time_produces_valid_hour(self, time_pattern):
        """오전/오후 시간 패턴은 유효한 시간 값 생성"""
        parser = ScheduleParser()
        schedule = f"매일 {time_pattern}"
        result = parser.parse(schedule)
        
        parts = result.cron_expression.split()
        hour = int(parts[1])
        
        # 시간이 0-23 범위인지 확인
        assert 0 <= hour <= 23

    @given(time_pattern=korean_24hour_time())
    @settings(max_examples=50)
    def test_24hour_time_produces_valid_hour(self, time_pattern):
        """24시간 형식 시간 패턴은 유효한 시간 값 생성"""
        parser = ScheduleParser()
        schedule = f"매일 {time_pattern}"
        result = parser.parse(schedule)
        
        parts = result.cron_expression.split()
        hour = int(parts[1])
        minute = int(parts[0])
        
        # 시간과 분이 유효 범위인지 확인
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59

    @given(day=korean_days)
    def test_all_korean_days_map_to_valid_cron_day(self, day):
        """모든 한국어 요일이 유효한 크론 요일 값으로 매핑"""
        parser = ScheduleParser()
        schedule = f"매주 {day} 12시"
        result = parser.parse(schedule)
        
        parts = result.cron_expression.split()
        day_of_week = int(parts[4])
        
        # 요일이 0-6 범위인지 확인 (일요일=0, 토요일=6)
        assert 0 <= day_of_week <= 6

    @given(schedule=korean_weekly_schedule())
    @settings(max_examples=50)
    def test_parse_result_contains_original_input(self, schedule):
        """파싱 결과에 원본 입력이 보존됨"""
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        assert result.original_input == schedule

    @given(schedule=korean_weekly_schedule())
    @settings(max_examples=50)
    def test_parse_result_has_description(self, schedule):
        """파싱 결과에 설명이 포함됨"""
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        assert result.description is not None
        assert len(result.description) > 0

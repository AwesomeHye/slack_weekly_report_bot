"""Property 12: 자연어 → 크론 → 설명 라운드트립

임의의 자연어 입력 → parse → describe_cron → 요일/시간 정보 보존 검증

Validates: Requirements 8.10, 8.8
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.schedule_parser import ScheduleParser, DAY_MAP, CRON_TO_DAY


# 한국어 요일 전략
korean_days = st.sampled_from(list(DAY_MAP.keys()))

# 시간 전략 (0-23시)
hour_24 = st.integers(min_value=0, max_value=23)

# 분 전략 (0-59분)
minute = st.integers(min_value=0, max_value=59)


@st.composite
def simple_weekly_schedule(draw):
    """단순 매주 요일+시간 패턴 생성 (라운드트립 검증용)"""
    day = draw(korean_days)
    hour = draw(hour_24)
    min_val = draw(minute)
    
    if min_val > 0:
        schedule = f"매주 {day} {hour}시 {min_val}분"
    else:
        schedule = f"매주 {day} {hour}시"
    
    return schedule, day, hour, min_val


@st.composite
def simple_daily_schedule(draw):
    """단순 매일 시간 패턴 생성 (라운드트립 검증용)"""
    hour = draw(hour_24)
    min_val = draw(minute)
    
    if min_val > 0:
        schedule = f"매일 {hour}시 {min_val}분"
    else:
        schedule = f"매일 {hour}시"
    
    return schedule, hour, min_val


class TestScheduleRoundtripProperty:
    """Property 12: 자연어 → 크론 → 설명 라운드트립 속성 테스트"""

    @given(data=simple_weekly_schedule())
    @settings(max_examples=100)
    def test_weekly_schedule_preserves_day(self, data):
        """매주 스케줄의 요일 정보가 라운드트립에서 보존됨"""
        schedule, expected_day, expected_hour, expected_minute = data
        
        parser = ScheduleParser()
        result = parser.parse(schedule)
        description = result.description
        
        # 설명에 요일이 포함되어야 함
        assert expected_day in description, f"'{expected_day}' not in '{description}'"

    @given(data=simple_weekly_schedule())
    @settings(max_examples=100)
    def test_weekly_schedule_preserves_time(self, data):
        """매주 스케줄의 시간 정보가 라운드트립에서 보존됨"""
        schedule, expected_day, expected_hour, expected_minute = data
        
        parser = ScheduleParser()
        result = parser.parse(schedule)
        description = result.description
        
        # 설명에 시간이 포함되어야 함 (HH:MM 형식)
        expected_time = f"{expected_hour:02d}:{expected_minute:02d}"
        assert expected_time in description, f"'{expected_time}' not in '{description}'"

    @given(data=simple_daily_schedule())
    @settings(max_examples=100)
    def test_daily_schedule_preserves_time(self, data):
        """매일 스케줄의 시간 정보가 라운드트립에서 보존됨"""
        schedule, expected_hour, expected_minute = data
        
        parser = ScheduleParser()
        result = parser.parse(schedule)
        description = result.description
        
        # 설명에 시간이 포함되어야 함
        expected_time = f"{expected_hour:02d}:{expected_minute:02d}"
        assert expected_time in description, f"'{expected_time}' not in '{description}'"
        
        # 매일 스케줄은 "매일" 포함
        assert "매일" in description

    @given(data=simple_weekly_schedule())
    @settings(max_examples=50)
    def test_cron_to_description_matches_original_day(self, data):
        """크론 표현식에서 생성된 설명의 요일이 원본과 일치"""
        schedule, expected_day, expected_hour, expected_minute = data
        
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        # 크론에서 요일 추출
        parts = result.cron_expression.split()
        cron_day = parts[4]
        
        # 크론 요일 값이 원본 요일과 매핑되는지 확인
        expected_cron_day = str(DAY_MAP[expected_day])
        assert cron_day == expected_cron_day

    @given(data=simple_weekly_schedule())
    @settings(max_examples=50)
    def test_cron_to_description_matches_original_time(self, data):
        """크론 표현식에서 생성된 설명의 시간이 원본과 일치"""
        schedule, expected_day, expected_hour, expected_minute = data
        
        parser = ScheduleParser()
        result = parser.parse(schedule)
        
        # 크론에서 시간 추출
        parts = result.cron_expression.split()
        cron_minute = int(parts[0])
        cron_hour = int(parts[1])
        
        # 크론 시간 값이 원본과 일치하는지 확인
        assert cron_hour == expected_hour
        assert cron_minute == expected_minute

    @given(day=korean_days, hour=hour_24, min_val=minute)
    @settings(max_examples=50)
    def test_describe_cron_inverse_of_parse(self, day, hour, min_val):
        """describe_cron이 parse의 역함수 역할을 함"""
        parser = ScheduleParser()
        
        # 자연어 → 크론
        if min_val > 0:
            schedule = f"매주 {day} {hour}시 {min_val}분"
        else:
            schedule = f"매주 {day} {hour}시"
        
        result = parser.parse(schedule)
        
        # 크론 → 설명
        description = ScheduleParser.describe_cron(result.cron_expression)
        
        # 설명에 원본 정보가 보존되어야 함
        assert day in description
        assert f"{hour:02d}:" in description

    @given(hour=hour_24, min_val=minute)
    @settings(max_examples=50)
    def test_daily_cron_roundtrip(self, hour, min_val):
        """매일 스케줄의 크론 라운드트립"""
        parser = ScheduleParser()
        
        if min_val > 0:
            schedule = f"매일 {hour}시 {min_val}분"
        else:
            schedule = f"매일 {hour}시"
        
        result = parser.parse(schedule)
        
        # 크론 형식 확인
        parts = result.cron_expression.split()
        assert parts[4] == "*"  # 매일이므로 요일은 와일드카드
        assert int(parts[0]) == min_val
        assert int(parts[1]) == hour
        
        # 설명에 "매일" 포함
        assert "매일" in result.description

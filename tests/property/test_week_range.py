"""Property 1: 주간 날짜 범위 계산 속성 기반 테스트.

임의의 datetime에 대해 get_week_range가 항상 올바른
월요일~일요일 범위를 반환하는지 검증한다.

Feature: weekly-report-slack-bot, Property 1: 주간 날짜 범위 계산

Validates: Requirements 1.2
"""

from datetime import time

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils import KST, get_week_range


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_start_is_monday(dt):
    """get_week_range의 시작일은 항상 월요일(weekday=0)이어야 한다.

    **Validates: Requirements 1.2**
    """
    start, _ = get_week_range(dt)
    assert start.weekday() == 0, f"시작일이 월요일이 아님: {start} (weekday={start.weekday()})"


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_end_is_sunday(dt):
    """get_week_range의 종료일은 항상 일요일(weekday=6)이어야 한다.

    **Validates: Requirements 1.2**
    """
    _, end = get_week_range(dt)
    assert end.weekday() == 6, f"종료일이 일요일이 아님: {end} (weekday={end.weekday()})"


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_contains_input(dt):
    """입력 datetime은 항상 반환된 주간 범위 내에 포함되어야 한다.

    **Validates: Requirements 1.2**
    """
    start, end = get_week_range(dt)
    assert start <= dt <= end, f"입력 {dt}가 범위 [{start}, {end}]에 포함되지 않음"


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_start_time_is_midnight(dt):
    """get_week_range의 시작일 시각은 항상 00:00:00이어야 한다.

    **Validates: Requirements 1.2**
    """
    start, _ = get_week_range(dt)
    assert start.time() == time(0, 0, 0), f"시작일 시각이 00:00:00이 아님: {start.time()}"


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_end_time_is_end_of_day(dt):
    """get_week_range의 종료일 시각은 항상 23:59:59여야 한다.

    **Validates: Requirements 1.2**
    """
    _, end = get_week_range(dt)
    assert end.hour == 23, f"종료일 시간이 23이 아님: {end.hour}"
    assert end.minute == 59, f"종료일 분이 59가 아님: {end.minute}"
    assert end.second == 59, f"종료일 초가 59가 아님: {end.second}"


@settings(max_examples=100)
@given(dt=st.datetimes(timezones=st.just(KST)))
def test_week_range_span_is_seven_days(dt):
    """get_week_range의 시작일과 종료일은 정확히 6일 차이여야 한다 (월~일 = 7일간).

    **Validates: Requirements 1.2**
    """
    start, end = get_week_range(dt)
    diff = end.date() - start.date()
    assert diff.days == 6, f"시작일과 종료일 차이가 6일이 아님: {diff.days}일"

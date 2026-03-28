"""유틸리티 함수 단위 테스트.

get_week_range, format_week_range, filter_comments_by_week,
format_summary_line, parse_summary_line, truncate 함수를 검증한다.
Validates: Requirements 7.4
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.utils import (
    KST,
    get_week_range,
    format_week_range,
    filter_comments_by_week,
    format_summary_line,
    parse_summary_line,
    truncate,
)


class TestGetWeekRangeWednesday:
    """수요일 입력 시 해당 주 월요일~일요일 범위를 반환한다."""

    def test_wednesday_returns_monday_to_sunday(self):
        # 2024-01-17 = 수요일
        wed = datetime(2024, 1, 17, 14, 30, 0, tzinfo=KST)
        start, end = get_week_range(wed)

        assert start == datetime(2024, 1, 15, 0, 0, 0, 0, tzinfo=KST)
        assert start.weekday() == 0  # 월요일
        assert end.weekday() == 6    # 일요일
        assert end.year == 2024
        assert end.month == 1
        assert end.day == 21


class TestGetWeekRangeMonday:
    """월요일 입력 시 해당 주 월요일~일요일 범위를 반환한다."""

    def test_monday_returns_same_week(self):
        # 2024-01-15 = 월요일
        mon = datetime(2024, 1, 15, 9, 0, 0, tzinfo=KST)
        start, end = get_week_range(mon)

        assert start == datetime(2024, 1, 15, 0, 0, 0, 0, tzinfo=KST)
        assert start.weekday() == 0
        assert end.day == 21
        assert end.weekday() == 6


class TestGetWeekRangeSunday:
    """일요일 입력 시 해당 주 월요일~일요일 범위를 반환한다."""

    def test_sunday_returns_same_week(self):
        # 2024-01-21 = 일요일
        sun = datetime(2024, 1, 21, 23, 0, 0, tzinfo=KST)
        start, end = get_week_range(sun)

        assert start == datetime(2024, 1, 15, 0, 0, 0, 0, tzinfo=KST)
        assert start.weekday() == 0
        assert end.day == 21
        assert end.weekday() == 6


class TestGetWeekRangeNaiveDatetime:
    """naive datetime 입력 시 KST를 자동 부여한다."""

    def test_naive_datetime_gets_kst(self):
        naive = datetime(2024, 1, 17, 10, 0, 0)
        start, end = get_week_range(naive)

        assert start.tzinfo == KST
        assert end.tzinfo == KST
        assert start.weekday() == 0
        assert end.weekday() == 6


class TestFormatWeekRange:
    """format_week_range가 올바른 포맷 문자열을 반환한다."""

    def test_format_correct(self):
        start = datetime(2024, 1, 15, 0, 0, 0, tzinfo=KST)
        end = datetime(2024, 1, 21, 23, 59, 59, tzinfo=KST)

        result = format_week_range(start, end)

        assert result == "2024.01.15 ~ 2024.01.21"


class TestFilterCommentsByWeek:
    """filter_comments_by_week가 범위 내 댓글만 반환한다."""

    def test_includes_in_range_excludes_out_of_range(self):
        week_start = datetime(2024, 1, 15, 0, 0, 0, tzinfo=KST)
        week_end = datetime(2024, 1, 21, 23, 59, 59, 999999, tzinfo=KST)

        comments = [
            {"id": 1, "created": datetime(2024, 1, 16, 10, 0, 0, tzinfo=KST)},  # in range
            {"id": 2, "created": datetime(2024, 1, 14, 23, 59, 59, tzinfo=KST)},  # before
            {"id": 3, "created": datetime(2024, 1, 22, 0, 0, 1, tzinfo=KST)},  # after
            {"id": 4, "created": datetime(2024, 1, 15, 0, 0, 0, tzinfo=KST)},  # exact start
            {"id": 5, "created": datetime(2024, 1, 21, 23, 59, 59, 999999, tzinfo=KST)},  # exact end
        ]

        result = filter_comments_by_week(comments, week_start, week_end)

        ids = [c["id"] for c in result]
        assert ids == [1, 4, 5]

    def test_empty_list_returns_empty(self):
        week_start = datetime(2024, 1, 15, 0, 0, 0, tzinfo=KST)
        week_end = datetime(2024, 1, 21, 23, 59, 59, 999999, tzinfo=KST)

        result = filter_comments_by_week([], week_start, week_end)

        assert result == []


class TestFormatSummaryLine:
    """format_summary_line이 올바른 형식을 반환한다."""

    def test_format_correct(self):
        result = format_summary_line("검색 API 성능 개선", "캐시 레이어 추가")

        assert result == "검색 API 성능 개선 : 캐시 레이어 추가"


class TestParseSummaryLine:
    """parse_summary_line이 올바르게 파싱한다."""

    def test_parse_correct(self):
        title, work = parse_summary_line("검색 API 성능 개선 : 캐시 레이어 추가")

        assert title == "검색 API 성능 개선"
        assert work == "캐시 레이어 추가"

    def test_invalid_format_raises_value_error(self):
        with pytest.raises(ValueError, match="잘못된 요약 형식"):
            parse_summary_line("구분자가 없는 문자열")


class TestTruncate:
    """truncate가 텍스트를 올바르게 자른다."""

    def test_short_text_unchanged(self):
        assert truncate("짧은 텍스트", 50) == "짧은 텍스트"

    def test_long_text_truncated(self):
        long_text = "a" * 100
        result = truncate(long_text, 50)

        assert len(result) == 50
        assert result == "a" * 50

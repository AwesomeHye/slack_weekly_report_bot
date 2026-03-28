"""Property 3: 요약 포맷/파싱 라운드트립 속성 기반 테스트.

임의의 title_summary(` : ` 미포함)와 work_summary에 대해
format_summary_line → parse_summary_line 라운드트립이
원본을 정확히 복원하는지 검증한다.

Feature: weekly-report-slack-bot, Property 3: 요약 포맷/파싱 라운드트립

Validates: Requirements 2.5, 6.2, 7.7
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils import format_summary_line, parse_summary_line

# 생성 전략: " : " 구분자를 포함하지 않는 비어있지 않은 문자열
title_strategy = st.text().filter(lambda s: " : " not in s and len(s) > 0)
work_strategy = st.text(min_size=1)


@settings(max_examples=100)
@given(title=title_strategy, work=work_strategy)
def test_roundtrip_restores_title(title, work):
    """format_summary_line → parse_summary_line 후 title_summary가 원본과 일치해야 한다.

    **Validates: Requirements 2.5, 6.2, 7.7**
    """
    line = format_summary_line(title, work)
    parsed_title, _ = parse_summary_line(line)
    assert parsed_title == title, (
        f"title 불일치: 원본={title!r}, 파싱={parsed_title!r}"
    )


@settings(max_examples=100)
@given(title=title_strategy, work=work_strategy)
def test_roundtrip_restores_work(title, work):
    """format_summary_line → parse_summary_line 후 work_summary가 원본과 일치해야 한다.

    **Validates: Requirements 2.5, 6.2, 7.7**
    """
    line = format_summary_line(title, work)
    _, parsed_work = parse_summary_line(line)
    assert parsed_work == work, (
        f"work 불일치: 원본={work!r}, 파싱={parsed_work!r}"
    )


@settings(max_examples=100)
@given(title=title_strategy, work=work_strategy)
def test_roundtrip_full_restoration(title, work):
    """format_summary_line → parse_summary_line 라운드트립이 원본 (title, work) 튜플을 정확히 복원해야 한다.

    **Validates: Requirements 2.5, 6.2, 7.7**
    """
    line = format_summary_line(title, work)
    parsed_title, parsed_work = parse_summary_line(line)
    assert (parsed_title, parsed_work) == (title, work), (
        f"라운드트립 실패: 원본=({title!r}, {work!r}), 파싱=({parsed_title!r}, {parsed_work!r})"
    )

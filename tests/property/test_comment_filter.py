"""Property 2: 댓글 주간 범위 필터링 속성 기반 테스트.

임의의 댓글 목록과 주간 범위에 대해 filter_comments_by_week가
범위 내 댓글만 정확히 반환하는지 검증한다.

Feature: weekly-report-slack-bot, Property 2: 댓글 주간 범위 필터링

Validates: Requirements 2.1
"""

from datetime import datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils import KST, filter_comments_by_week, get_week_range


# 커스텀 댓글 전략: created 필드가 있는 dict 리스트
comment_datetimes = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
    timezones=st.just(KST),
)


def make_comment(created: datetime) -> dict:
    """created 필드를 가진 댓글 dict를 생성한다."""
    return {"created": created, "body": "test comment"}


comment_strategy = comment_datetimes.map(make_comment)
comment_list_strategy = st.lists(comment_strategy, min_size=0, max_size=30)

# 주간 범위 생성을 위한 기준 datetime 전략
base_datetime_strategy = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
    timezones=st.just(KST),
)


@settings(max_examples=100)
@given(comments=comment_list_strategy, base_dt=base_datetime_strategy)
def test_filtered_comments_are_within_range(comments, base_dt):
    """필터링된 모든 댓글의 created는 [week_start, week_end] 범위 내에 있어야 한다.

    **Validates: Requirements 2.1**
    """
    week_start, week_end = get_week_range(base_dt)
    result = filter_comments_by_week(comments, week_start, week_end)

    for c in result:
        assert week_start <= c["created"] <= week_end, (
            f"범위 밖 댓글 포함: {c['created']} not in [{week_start}, {week_end}]"
        )


@settings(max_examples=100)
@given(comments=comment_list_strategy, base_dt=base_datetime_strategy)
def test_no_in_range_comments_excluded(comments, base_dt):
    """범위 내 댓글이 결과에서 누락되지 않아야 한다.

    **Validates: Requirements 2.1**
    """
    week_start, week_end = get_week_range(base_dt)
    result = filter_comments_by_week(comments, week_start, week_end)

    in_range = [c for c in comments if week_start <= c["created"] <= week_end]
    assert len(result) == len(in_range), (
        f"범위 내 댓글 수 불일치: 결과={len(result)}, 기대={len(in_range)}"
    )


@settings(max_examples=100)
@given(comments=comment_list_strategy, base_dt=base_datetime_strategy)
def test_result_is_subset_of_input(comments, base_dt):
    """필터링 결과는 입력 댓글 목록의 부분집합이어야 한다.

    **Validates: Requirements 2.1**
    """
    week_start, week_end = get_week_range(base_dt)
    result = filter_comments_by_week(comments, week_start, week_end)

    for c in result:
        assert c in comments, f"결과에 입력에 없는 댓글 포함: {c}"


@settings(max_examples=100)
@given(comments=comment_list_strategy, base_dt=base_datetime_strategy)
def test_out_of_range_comments_not_included(comments, base_dt):
    """범위 밖 댓글은 결과에 포함되지 않아야 한다.

    **Validates: Requirements 2.1**
    """
    week_start, week_end = get_week_range(base_dt)
    result = filter_comments_by_week(comments, week_start, week_end)
    result_set = [id(c) for c in result]

    for c in comments:
        if not (week_start <= c["created"] <= week_end):
            assert id(c) not in result_set, (
                f"범위 밖 댓글이 결과에 포함됨: {c['created']}"
            )

"""Property 4: 메시지 포맷 필수 요소 포함 + Property 7: 상태별 그룹화 속성 기반 테스트.

임의의 TicketSummary 목록에 대해 format_message가 필수 요소(날짜 헤더,
불릿 포인트, 총 건수)를 포함하고, 같은 상태의 티켓이 연속 블록으로
그룹화되는지 검증한다.

Feature: weekly-report-slack-bot, Property 4: 메시지 포맷 필수 요소 포함
Feature: weekly-report-slack-bot, Property 7: 상태별 그룹화

Validates: Requirements 3.2, 6.3, 6.4
"""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from src.models import TicketSummary
from src.slack_message_sender import SlackMessageSender

# 커스텀 TicketSummary 전략
STATUSES = ["In Progress", "Done", "In Review", "To Do", "Blocked"]

ticket_summary_strategy = st.builds(
    TicketSummary,
    ticket_key=st.from_regex(r"EXAMPLE-[1-9][0-9]{0,3}", fullmatch=True),
    title_summary=st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
    work_summary=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    status=st.sampled_from(STATUSES),
    has_update=st.booleans(),
)

week_range_strategy = st.from_regex(
    r"20[2-3][0-9]\.[01][0-9]\.[0-3][0-9] ~ 20[2-3][0-9]\.[01][0-9]\.[0-3][0-9]",
    fullmatch=True,
)


def _make_sender() -> SlackMessageSender:
    """format_message 테스트용 더미 SlackMessageSender 인스턴스를 생성한다."""
    return SlackMessageSender(bot_token="xoxb-dummy", user_id="U0000000000")


# ---------------------------------------------------------------------------
# Property 4: 메시지 포맷 필수 요소 포함
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    summaries=st.lists(ticket_summary_strategy, min_size=1, max_size=20),
    week_range=week_range_strategy,
)
def test_message_contains_date_header(summaries, week_range):
    """format_message 결과에 week_range가 날짜 헤더로 포함되어야 한다.

    **Validates: Requirements 3.2**

    Feature: weekly-report-slack-bot, Property 4: 메시지 포맷 필수 요소 포함
    """
    sender = _make_sender()
    message = sender.format_message(summaries, week_range)
    assert week_range in message, f"날짜 헤더 '{week_range}'가 메시지에 없음"


@settings(max_examples=100)
@given(
    summaries=st.lists(ticket_summary_strategy, min_size=1, max_size=20),
    week_range=week_range_strategy,
)
def test_message_contains_bullet_points(summaries, week_range):
    """format_message 결과에 각 요약에 대한 불릿 포인트(•)가 포함되어야 한다.

    **Validates: Requirements 6.3**

    Feature: weekly-report-slack-bot, Property 4: 메시지 포맷 필수 요소 포함
    """
    sender = _make_sender()
    message = sender.format_message(summaries, week_range)
    bullet_count = message.count("•")
    assert bullet_count == len(summaries), (
        f"불릿 포인트 수({bullet_count})가 요약 수({len(summaries)})와 다름"
    )


@settings(max_examples=100)
@given(
    summaries=st.lists(ticket_summary_strategy, min_size=1, max_size=20),
    week_range=week_range_strategy,
)
def test_message_contains_total_count(summaries, week_range):
    """format_message 결과에 총 티켓 수가 포함되어야 한다.

    **Validates: Requirements 3.2**

    Feature: weekly-report-slack-bot, Property 4: 메시지 포맷 필수 요소 포함
    """
    sender = _make_sender()
    message = sender.format_message(summaries, week_range)
    expected = f"총 {len(summaries)}건"
    assert expected in message, f"'{expected}'가 메시지에 없음"


# ---------------------------------------------------------------------------
# Property 7: 상태별 그룹화
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    summaries=st.lists(ticket_summary_strategy, min_size=2, max_size=20).filter(
        lambda lst: len({s.status for s in lst}) >= 2
    ),
    week_range=week_range_strategy,
)
def test_same_status_tickets_are_contiguous(summaries, week_range):
    """같은 상태의 티켓은 연속된 블록으로 그룹화되어야 하며,
    동일 상태의 티켓 사이에 다른 상태의 티켓이 끼어들지 않아야 한다.

    **Validates: Requirements 6.4**

    Feature: weekly-report-slack-bot, Property 7: 상태별 그룹화
    """
    sender = _make_sender()
    message = sender.format_message(summaries, week_range)

    # 메시지에서 [status] 헤더와 불릿 라인을 순서대로 추출
    lines = message.split("\n")
    bullet_statuses = []
    current_status = None

    for line in lines:
        header_match = re.match(r"^\[(.+)\]$", line)
        if header_match:
            current_status = header_match.group(1)
        elif line.startswith("•") and current_status is not None:
            bullet_statuses.append(current_status)

    # 같은 상태가 연속 블록인지 검증: 한 번 떠난 상태가 다시 나타나면 안 됨
    seen_statuses = set()
    prev_status = None
    for status in bullet_statuses:
        if status != prev_status:
            assert status not in seen_statuses, (
                f"상태 '{status}'가 비연속적으로 나타남 (그룹화 위반)"
            )
            if prev_status is not None:
                seen_statuses.add(prev_status)
            prev_status = status

"""유틸리티 함수 모듈.

주간 날짜 범위 계산, 댓글 필터링, 요약 포맷팅/파싱 등
공통 유틸리티 함수를 제공한다.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple

KST = ZoneInfo("Asia/Seoul")


def get_week_range(dt: datetime) -> Tuple[datetime, datetime]:
    """주어진 날짜가 속한 주의 월요일 00:00:00 ~ 일요일 23:59:59 (KST) 범위를 반환한다."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    monday = dt - timedelta(days=dt.weekday())
    week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = (week_start + timedelta(days=6)).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    return week_start, week_end


def format_week_range(week_start: datetime, week_end: datetime) -> str:
    """주간 범위를 'YYYY.MM.DD ~ YYYY.MM.DD' 형식으로 포맷팅한다."""
    return f"{week_start.strftime('%Y.%m.%d')} ~ {week_end.strftime('%Y.%m.%d')}"


def filter_comments_by_week(
    comments: list, week_start: datetime, week_end: datetime
) -> list:
    """주간 범위 내에 작성된 댓글만 필터링한다."""
    return [c for c in comments if week_start <= c["created"] <= week_end]


def format_summary_line(title_summary: str, work_summary: str) -> str:
    """위키 형식으로 요약 라인을 포맷팅한다."""
    return f"{title_summary} : {work_summary}"


def parse_summary_line(line: str) -> Tuple[str, str]:
    """위키 형식 요약 라인을 파싱하여 (title_summary, work_summary)를 반환한다."""
    parts = line.split(" : ", 1)
    if len(parts) != 2:
        raise ValueError(f"잘못된 요약 형식: {line}")
    return parts[0], parts[1]


def truncate(text: str, max_length: int = 50) -> str:
    """텍스트를 max_length 이하로 잘라낸다."""
    if len(text) <= max_length:
        return text
    return text[:max_length]

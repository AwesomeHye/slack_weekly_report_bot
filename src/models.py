from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TicketStatus(Enum):
    """Jira 티켓 상태를 나타내는 Enum"""
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    IN_REVIEW = "In Review"
    TO_DO = "To Do"
    BLOCKED = "Blocked"


@dataclass
class TicketSummary:
    """Kiro(LLM)가 생성한 티켓 요약 결과"""
    ticket_key: str               # "EXAMPLE-123"
    title_summary: str            # 티켓 제목 간단 요약
    work_summary: str             # 이번 주 작업 한 문장 요약 (50자 이내)
    status: str                   # TicketStatus 값
    has_update: bool              # 업데이트 유무


@dataclass
class WeeklyReport:
    """주간 보고 전체 데이터"""
    week_start: datetime
    week_end: datetime
    summaries: List[TicketSummary] = field(default_factory=list)
    total_count: int = 0
    generated_at: Optional[datetime] = None

"""Schedule Parser 모듈

사용자가 입력한 한국어 자연어 스케줄 표현 또는 크론 표현식을 파싱하여
유효한 crontab 스케줄로 변환한다.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 요일 매핑 (한국어 → 크론 값)
DAY_MAP = {
    "월요일": 1,
    "화요일": 2,
    "수요일": 3,
    "목요일": 4,
    "금요일": 5,
    "토요일": 6,
    "일요일": 0,
}

# 크론 값 → 한국어 요일 역매핑
CRON_TO_DAY = {
    "0": "일요일",
    "7": "일요일",
    "1": "월요일",
    "2": "화요일",
    "3": "수요일",
    "4": "목요일",
    "5": "금요일",
    "6": "토요일",
}

# 크론 필드 범위 정의
CRON_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),  # 0과 7 모두 일요일
}


@dataclass
class ParseResult:
    """스케줄 파싱 결과"""
    cron_expression: str       # "0 15 * * 3"
    original_input: str        # 사용자 원본 입력
    description: str           # "매주 수요일 15:00"


class ScheduleParser:
    """한국어 자연어 또는 크론 표현식을 파싱하여 crontab 스케줄로 변환한다."""

    def parse(self, user_input: str) -> ParseResult:
        """사용자 입력을 파싱하여 ParseResult를 반환한다.

        Args:
            user_input: 크론 표현식 또는 한국어 자연어 스케줄

        Returns:
            ParseResult: 파싱된 크론 표현식, 원본 입력, 사람이 읽을 수 있는 설명

        Raises:
            ValueError: 유효한 크론 표현식도 아니고 파싱 가능한 자연어도 아닌 경우
        """
        stripped = user_input.strip()

        # 1) 크론 표현식인지 먼저 확인
        if self._is_cron_expression(stripped):
            self.validate_cron(stripped)
            return ParseResult(
                cron_expression=stripped,
                original_input=user_input,
                description=self.describe_cron(stripped),
            )

        # 2) 한국어 자연어 파싱 시도
        result = self._parse_korean(stripped)
        if result is not None:
            hour, minute, day_of_week = result
            cron = self._build_cron(minute, hour, day_of_week)
            return ParseResult(
                cron_expression=cron,
                original_input=user_input,
                description=self.describe_cron(cron),
            )

        # 3) 둘 다 아니면 에러
        raise ValueError(
            f"스케줄을 파싱할 수 없습니다: '{user_input}'\n"
            "입력 예시:\n"
            "  - 크론 표현식: 0 15 * * 3\n"
            "  - 한국어: 매주 수요일 오후 3시, 매주 목요일 17시, 매일 오전 9시"
        )

    @staticmethod
    def _is_cron_expression(text: str) -> bool:
        """5개 필드로 구성된 크론 표현식 형태인지 확인한다."""
        parts = text.split()
        return len(parts) == 5 and all(
            re.match(r'^[\d\*,/\-]+$', p) for p in parts
        )

    @staticmethod
    def validate_cron(expression: str) -> None:
        """크론 표현식의 각 필드 범위를 검증한다.

        Args:
            expression: 5필드 크론 표현식 (예: "0 15 * * 3")

        Raises:
            ValueError: 필드 수가 5개가 아니거나 범위를 벗어나는 경우
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"크론 표현식은 5개 필드여야 합니다: '{expression}'")

        field_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        for i, (part, name) in enumerate(zip(parts, field_names)):
            if part == "*":
                continue
            min_val, max_val = CRON_FIELD_RANGES[name]
            # 쉼표로 구분된 값, 범위(-), 간격(/) 처리
            for segment in part.split(","):
                if "/" in segment:
                    base, step = segment.split("/", 1)
                    if base != "*":
                        val = int(base)
                        if not (min_val <= val <= max_val):
                            raise ValueError(
                                f"크론 필드 '{name}' 값 {val}이 범위({min_val}-{max_val})를 벗어납니다"
                            )
                elif "-" in segment:
                    low, high = segment.split("-", 1)
                    low_val, high_val = int(low), int(high)
                    if not (min_val <= low_val <= max_val):
                        raise ValueError(
                            f"크론 필드 '{name}' 값 {low_val}이 범위({min_val}-{max_val})를 벗어납니다"
                        )
                    if not (min_val <= high_val <= max_val):
                        raise ValueError(
                            f"크론 필드 '{name}' 값 {high_val}이 범위({min_val}-{max_val})를 벗어납니다"
                        )
                else:
                    val = int(segment)
                    if not (min_val <= val <= max_val):
                        raise ValueError(
                            f"크론 필드 '{name}' 값 {val}이 범위({min_val}-{max_val})를 벗어납니다"
                        )


    def _parse_korean(self, text: str) -> Optional[Tuple[int, int, Optional[int]]]:
        """한국어 자연어를 파싱하여 (hour, minute, day_of_week)를 반환한다.

        Returns:
            (hour, minute, day_of_week) 튜플. day_of_week이 None이면 매일.
            파싱 실패 시 None.
        """
        # 요일 추출
        day_of_week = None
        for day_name, cron_val in DAY_MAP.items():
            if day_name in text:
                day_of_week = cron_val
                break

        # 시간 추출
        hour, minute = None, 0

        # 패턴 1: "오후 3시 30분", "오전 9시"
        ampm_match = re.search(r'(오전|오후)\s*(\d{1,2})시(?:\s*(\d{1,2})분)?', text)
        if ampm_match:
            ampm, h, m = ampm_match.group(1), int(ampm_match.group(2)), ampm_match.group(3)
            if ampm == "오전":
                hour = 0 if h == 12 else h
            else:  # 오후
                hour = h if h == 12 else h + 12
            minute = int(m) if m else 0

        # 패턴 2: "17시", "9시 30분"
        if hour is None:
            h24_match = re.search(r'(\d{1,2})시(?:\s*(\d{1,2})분)?', text)
            if h24_match:
                hour = int(h24_match.group(1))
                minute = int(h24_match.group(2)) if h24_match.group(2) else 0

        # 패턴 3: "17:00", "9:30"
        if hour is None:
            colon_match = re.search(r'(\d{1,2}):(\d{2})', text)
            if colon_match:
                hour = int(colon_match.group(1))
                minute = int(colon_match.group(2))

        if hour is None:
            return None

        return hour, minute, day_of_week

    @staticmethod
    def _build_cron(minute: int, hour: int, day_of_week: Optional[int]) -> str:
        """파싱된 값으로 크론 표현식을 생성한다."""
        dow = str(day_of_week) if day_of_week is not None else "*"
        return f"{minute} {hour} * * {dow}"

    @staticmethod
    def describe_cron(expression: str) -> str:
        """크론 표현식을 사람이 읽을 수 있는 한국어 설명으로 변환한다.

        Args:
            expression: 5필드 크론 표현식

        Returns:
            한국어 설명 문자열 (예: "매주 수요일 15:00")
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            return expression

        minute, hour, dom, month, dow = parts

        # 시간 문자열 - 단순 숫자만 처리 (범위/간격 등은 원본 반환)
        time_str = ""
        try:
            if hour != "*" and minute != "*":
                time_str = f"{int(hour):02d}:{int(minute):02d}"
            elif hour != "*":
                time_str = f"{int(hour):02d}:00"
        except ValueError:
            # 범위(9-17), 간격(*/15) 등 복잡한 표현식은 원본 반환
            return expression

        # 요일 문자열 - 단순 숫자만 처리
        day_str = ""
        if dow != "*":
            if dow in CRON_TO_DAY:
                day_str = CRON_TO_DAY.get(dow, f"요일({dow})")
            else:
                # 범위(1-5), 쉼표(1,3,5) 등 복잡한 표현식은 원본 반환
                return expression

        if day_str and time_str:
            return f"매주 {day_str} {time_str}"
        elif day_str:
            return f"매주 {day_str}"
        elif time_str:
            return f"매일 {time_str}"
        else:
            return expression

"""Property 11: 무효 입력 거부

임의의 무효 문자열 → parse → ValueError 발생 + 에러 메시지에 입력 예시 포함 검증

Validates: Requirements 8.5
"""
import pytest
import re
from hypothesis import given, strategies as st, assume, settings

from src.schedule_parser import ScheduleParser, DAY_MAP


def is_potentially_valid_input(text: str) -> bool:
    """입력이 유효한 크론 표현식이거나 파싱 가능한 한국어인지 확인"""
    stripped = text.strip()
    
    # 빈 문자열은 무효
    if not stripped:
        return False
    
    # 크론 표현식 형태 확인 (5개 필드, 숫자/*/,/-/ 포함)
    parts = stripped.split()
    if len(parts) == 5 and all(re.match(r'^[\d\*,/\-]+$', p) for p in parts):
        return True
    
    # 한국어 시간 패턴 확인
    has_time = bool(
        re.search(r'(오전|오후)\s*\d{1,2}시', stripped) or
        re.search(r'\d{1,2}시', stripped) or
        re.search(r'\d{1,2}:\d{2}', stripped)
    )
    
    return has_time


# 무효 입력 생성 전략
@st.composite
def invalid_text(draw):
    """파싱 불가능한 무효 텍스트 생성"""
    # 다양한 무효 패턴
    patterns = [
        # 숫자만
        st.from_regex(r'^[0-9]+$', fullmatch=True),
        # 영문자만
        st.from_regex(r'^[a-zA-Z]+$', fullmatch=True),
        # 특수문자만
        st.from_regex(r'^[!@#$%^&*()]+$', fullmatch=True),
        # 한글이지만 시간 패턴 없음
        st.sampled_from([
            "안녕하세요",
            "테스트",
            "무효입력",
            "가나다라",
            "매주",  # 요일/시간 없음
            "수요일",  # 시간 없음
            "오후",  # 시간 값 없음
        ]),
        # 잘못된 크론 형식 (필드 수 불일치)
        st.sampled_from([
            "0 15 * *",  # 4개 필드
            "0 15 * * * *",  # 6개 필드
            "0 15",  # 2개 필드
        ]),
    ]
    
    text = draw(st.one_of(*patterns))
    assume(not is_potentially_valid_input(text))
    return text


class TestInvalidInputRejectProperty:
    """Property 11: 무효 입력 거부 속성 테스트"""

    @given(text=invalid_text())
    @settings(max_examples=100)
    def test_invalid_input_raises_value_error(self, text):
        """무효 입력은 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse(text)

    @given(text=invalid_text())
    @settings(max_examples=50)
    def test_error_message_contains_examples(self, text):
        """에러 메시지에 입력 예시 포함"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse(text)
        
        error_msg = str(exc_info.value)
        assert "입력 예시" in error_msg or "예시" in error_msg

    @given(text=st.text(min_size=0, max_size=5).filter(lambda x: x.strip() == ""))
    def test_empty_or_whitespace_raises_error(self, text):
        """빈 문자열 또는 공백만 있는 입력은 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse(text)

    @given(
        num1=st.integers(min_value=0, max_value=100),
        num2=st.integers(min_value=0, max_value=100),
    )
    def test_random_numbers_not_cron_format_raises_error(self, num1, num2):
        """크론 형식이 아닌 숫자 조합은 ValueError 발생"""
        text = f"{num1} {num2}"  # 2개 필드만
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse(text)

    @given(day=st.sampled_from(list(DAY_MAP.keys())))
    def test_day_without_time_raises_error(self, day):
        """요일만 있고 시간이 없는 입력은 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse(f"매주 {day}")

    @given(text=st.from_regex(r'^[a-zA-Z]{5,20}$', fullmatch=True))
    def test_english_text_raises_error(self, text):
        """영문 텍스트는 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse(text)

    def test_partial_cron_raises_error(self):
        """불완전한 크론 표현식은 ValueError 발생"""
        parser = ScheduleParser()
        
        invalid_crons = [
            "0 15 * *",      # 4개 필드
            "0 15",          # 2개 필드
            "* * *",         # 3개 필드
            "0 15 * * * *",  # 6개 필드
        ]
        
        for cron in invalid_crons:
            with pytest.raises(ValueError):
                parser.parse(cron)

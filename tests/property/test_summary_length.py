"""Property 8: 요약 길이 제한 속성 기반 테스트.

임의의 긴 문자열에 대해 truncate(50)이 항상 길이 50 이하의
결과를 반환하는지 검증한다.

Feature: weekly-report-slack-bot, Property 8: 요약 길이 제한

Validates: Requirements 2.2
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils import truncate


@settings(max_examples=100)
@given(text=st.text(min_size=1))
def test_truncate_result_length_within_limit(text):
    """truncate(text, 50)의 결과 길이는 항상 50 이하여야 한다.

    **Validates: Requirements 2.2**
    """
    result = truncate(text, 50)
    assert len(result) <= 50, f"결과 길이가 50을 초과: {len(result)}"


@settings(max_examples=100)
@given(text=st.text(min_size=1, max_size=50))
def test_truncate_short_text_unchanged(text):
    """길이가 50 이하인 텍스트는 truncate 후에도 원본과 동일해야 한다.

    **Validates: Requirements 2.2**
    """
    result = truncate(text, 50)
    assert result == text, f"50자 이하 텍스트가 변경됨: '{text}' → '{result}'"


@settings(max_examples=100)
@given(text=st.text(min_size=51))
def test_truncate_long_text_sliced(text):
    """길이가 50을 초과하는 텍스트는 truncate 후 text[:50]과 동일해야 한다.

    **Validates: Requirements 2.2**
    """
    result = truncate(text, 50)
    assert result == text[:50], f"잘린 결과가 text[:50]과 다름: '{result}' != '{text[:50]}'"

"""Schedule_Parser 단위 테스트

Requirements: 8.2, 8.3, 8.4, 8.5, 8.8, 8.9
"""
import pytest
from src.schedule_parser import ScheduleParser, ParseResult


class TestScheduleParserCronExpression:
    """크론 표현식 입력 테스트"""

    def test_valid_cron_expression_returns_as_is(self):
        """유효한 크론 표현식 입력 시 그대로 반환"""
        parser = ScheduleParser()
        result = parser.parse("0 15 * * 3")
        
        assert result.cron_expression == "0 15 * * 3"
        assert result.original_input == "0 15 * * 3"
        assert "수요일" in result.description
        assert "15:00" in result.description

    def test_cron_with_all_wildcards(self):
        """모든 필드가 와일드카드인 크론 표현식"""
        parser = ScheduleParser()
        result = parser.parse("* * * * *")
        
        assert result.cron_expression == "* * * * *"

    def test_cron_with_ranges(self):
        """범위가 포함된 크론 표현식 - 파싱 및 검증 통과"""
        parser = ScheduleParser()
        result = parser.parse("0 9-17 * * 1-5")
        
        assert result.cron_expression == "0 9-17 * * 1-5"
        # describe_cron은 복잡한 범위 표현식에서 원본 반환 가능
        assert result.description is not None

    def test_cron_with_intervals(self):
        """간격이 포함된 크론 표현식"""
        parser = ScheduleParser()
        result = parser.parse("*/15 * * * *")
        
        assert result.cron_expression == "*/15 * * * *"


class TestScheduleParserKoreanNaturalLanguage:
    """한국어 자연어 파싱 테스트"""

    def test_weekly_wednesday_afternoon(self):
        """매주 수요일 오후 3시"""
        parser = ScheduleParser()
        result = parser.parse("매주 수요일 오후 3시")
        
        assert result.cron_expression == "0 15 * * 3"
        assert result.original_input == "매주 수요일 오후 3시"

    def test_weekly_thursday_24hour(self):
        """매주 목요일 17시"""
        parser = ScheduleParser()
        result = parser.parse("매주 목요일 17시")
        
        assert result.cron_expression == "0 17 * * 4"

    def test_daily_morning(self):
        """매일 오전 9시"""
        parser = ScheduleParser()
        result = parser.parse("매일 오전 9시")
        
        assert result.cron_expression == "0 9 * * *"

    def test_weekly_friday_with_minutes(self):
        """매주 금요일 9:30"""
        parser = ScheduleParser()
        result = parser.parse("매주 금요일 9:30")
        
        assert result.cron_expression == "30 9 * * 5"

    def test_weekly_monday_afternoon_with_minutes(self):
        """매주 월요일 오후 2시 30분"""
        parser = ScheduleParser()
        result = parser.parse("매주 월요일 오후 2시 30분")
        
        assert result.cron_expression == "30 14 * * 1"

    def test_sunday_schedule(self):
        """매주 일요일 오전 10시"""
        parser = ScheduleParser()
        result = parser.parse("매주 일요일 오전 10시")
        
        assert result.cron_expression == "0 10 * * 0"

    def test_saturday_evening(self):
        """매주 토요일 오후 6시"""
        parser = ScheduleParser()
        result = parser.parse("매주 토요일 오후 6시")
        
        assert result.cron_expression == "0 18 * * 6"

    def test_midnight_am(self):
        """오전 12시 (자정)"""
        parser = ScheduleParser()
        result = parser.parse("매일 오전 12시")
        
        assert result.cron_expression == "0 0 * * *"

    def test_noon_pm(self):
        """오후 12시 (정오)"""
        parser = ScheduleParser()
        result = parser.parse("매일 오후 12시")
        
        assert result.cron_expression == "0 12 * * *"


class TestScheduleParserInvalidInput:
    """무효 입력 테스트"""

    def test_invalid_input_raises_value_error(self):
        """파싱 불가능한 입력 시 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("잘못된 입력")
        
        assert "스케줄을 파싱할 수 없습니다" in str(exc_info.value)

    def test_error_message_contains_examples(self):
        """에러 메시지에 입력 예시 포함"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("abc123")
        
        error_msg = str(exc_info.value)
        assert "입력 예시" in error_msg
        assert "크론 표현식" in error_msg
        assert "한국어" in error_msg

    def test_empty_input_raises_error(self):
        """빈 입력 시 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse("")

    def test_whitespace_only_raises_error(self):
        """공백만 있는 입력 시 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse("   ")

    def test_partial_time_without_hour_raises_error(self):
        """시간 정보 없이 요일만 있는 경우 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse("매주 수요일")


class TestCronValidation:
    """크론 필드 범위 검증 테스트"""

    def test_invalid_minute_raises_error(self):
        """분 필드 범위 초과 (60분)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("60 15 * * 3")
        
        assert "minute" in str(exc_info.value)
        assert "범위" in str(exc_info.value)

    def test_invalid_hour_raises_error(self):
        """시 필드 범위 초과 (25시)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("0 25 * * 3")
        
        assert "hour" in str(exc_info.value)

    def test_invalid_day_of_week_raises_error(self):
        """요일 필드 범위 초과 (8)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("0 15 * * 8")
        
        assert "day_of_week" in str(exc_info.value)

    def test_invalid_day_of_month_raises_error(self):
        """일 필드 범위 초과 (32)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("0 15 32 * *")
        
        assert "day_of_month" in str(exc_info.value)

    def test_invalid_month_raises_error(self):
        """월 필드 범위 초과 (13)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse("0 15 * 13 *")
        
        assert "month" in str(exc_info.value)

    def test_multiple_invalid_fields(self):
        """여러 필드 범위 초과 (첫 번째 오류에서 중단)"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse("60 25 * * 8")

    def test_negative_value_raises_error(self):
        """음수 값 시 ValueError 발생"""
        parser = ScheduleParser()
        
        with pytest.raises(ValueError):
            parser.parse("-1 15 * * 3")

    def test_wrong_field_count_raises_error(self):
        """필드 수가 5개가 아닌 경우"""
        with pytest.raises(ValueError) as exc_info:
            ScheduleParser.validate_cron("0 15 * *")
        
        assert "5개 필드" in str(exc_info.value)


class TestDescribeCron:
    """크론 → 한국어 설명 변환 테스트"""

    def test_describe_weekly_schedule(self):
        """요일+시간 크론 → 한국어 설명"""
        description = ScheduleParser.describe_cron("0 15 * * 3")
        
        assert "수요일" in description
        assert "15:00" in description
        assert "매주" in description

    def test_describe_daily_schedule(self):
        """매일 실행 크론 → 한국어 설명"""
        description = ScheduleParser.describe_cron("0 9 * * *")
        
        assert "매일" in description
        assert "09:00" in description

    def test_describe_sunday(self):
        """일요일 크론 → 한국어 설명"""
        description = ScheduleParser.describe_cron("30 10 * * 0")
        
        assert "일요일" in description
        assert "10:30" in description

    def test_describe_sunday_as_7(self):
        """일요일(7) 크론 → 한국어 설명"""
        description = ScheduleParser.describe_cron("0 8 * * 7")
        
        assert "일요일" in description

    def test_describe_all_weekdays(self):
        """모든 요일 변환 확인"""
        day_map = {
            "1": "월요일",
            "2": "화요일",
            "3": "수요일",
            "4": "목요일",
            "5": "금요일",
            "6": "토요일",
            "0": "일요일",
        }
        for cron_val, korean_day in day_map.items():
            description = ScheduleParser.describe_cron(f"0 12 * * {cron_val}")
            assert korean_day in description

    def test_describe_invalid_cron_returns_original(self):
        """잘못된 크론 형식은 원본 반환"""
        invalid_cron = "invalid"
        description = ScheduleParser.describe_cron(invalid_cron)
        
        assert description == invalid_cron


class TestParseResult:
    """ParseResult 필드 검증 테스트"""

    def test_parse_result_has_all_fields_for_cron(self):
        """크론 입력 시 모든 필드 포함"""
        parser = ScheduleParser()
        result = parser.parse("0 15 * * 3")
        
        assert result.cron_expression == "0 15 * * 3"
        assert result.original_input == "0 15 * * 3"
        assert result.description is not None
        assert len(result.description) > 0

    def test_parse_result_has_all_fields_for_korean(self):
        """한국어 입력 시 모든 필드 포함"""
        parser = ScheduleParser()
        result = parser.parse("매주 수요일 오후 3시")
        
        assert result.cron_expression == "0 15 * * 3"
        assert result.original_input == "매주 수요일 오후 3시"
        assert "수요일" in result.description
        assert "15:00" in result.description

    def test_original_input_preserved_with_whitespace(self):
        """원본 입력 공백 포함 보존"""
        parser = ScheduleParser()
        result = parser.parse("  매주 목요일 17시  ")
        
        assert result.original_input == "  매주 목요일 17시  "
        assert result.cron_expression == "0 17 * * 4"

    def test_parse_result_is_dataclass(self):
        """ParseResult가 dataclass인지 확인"""
        parser = ScheduleParser()
        result = parser.parse("0 9 * * 1")
        
        # dataclass 필드 접근 가능 확인
        assert hasattr(result, 'cron_expression')
        assert hasattr(result, 'original_input')
        assert hasattr(result, 'description')

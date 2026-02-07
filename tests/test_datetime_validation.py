"""Test datetime validation for API key rotation."""

import pytest
from datetime import datetime, timezone
from app.core.config import _parse_iso_datetime


class TestParseISODatetime:
    """Test ISO datetime parsing with validation."""

    def test_valid_basic_iso_datetime(self):
        """Test parsing valid basic ISO datetime."""
        result = _parse_iso_datetime("2024-01-31T12:34:56")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 31
        assert result.hour == 12
        assert result.minute == 34
        assert result.second == 56
        assert result.tzinfo == timezone.utc

    def test_valid_iso_datetime_with_utc(self):
        """Test parsing ISO datetime with Z suffix."""
        result = _parse_iso_datetime("2024-01-31T12:34:56Z")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_valid_iso_datetime_with_timezone(self):
        """Test parsing ISO datetime with timezone offset."""
        result = _parse_iso_datetime("2024-01-31T12:34:56+02:00")
        assert result is not None
        # The timezone should be preserved (not converted to UTC)
        assert result.hour == 12
        assert str(result.tzinfo) == "UTC+02:00"

    def test_valid_compact_iso_datetime(self):
        """Test parsing compact ISO datetime."""
        result = _parse_iso_datetime("20240131T123456")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 31

    def test_valid_iso_datetime_with_milliseconds(self):
        """Test parsing ISO datetime with milliseconds."""
        result = _parse_iso_datetime("2024-01-31T12:34:56.789")
        assert result is not None
        assert result.microsecond == 789000

    def test_valid_iso_datetime_with_milliseconds_z(self):
        """Test parsing ISO datetime with milliseconds and Z."""
        result = _parse_iso_datetime("2024-01-31T12:34:56.789Z")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_none_input(self):
        """Test that None input returns None."""
        result = _parse_iso_datetime(None)
        assert result is None

    def test_empty_string(self):
        """Test that empty string returns None."""
        result = _parse_iso_datetime("")
        assert result is None

    def test_non_string_input(self):
        """Test that non-string input returns None."""
        result = _parse_iso_datetime(12345)
        assert result is None

    def test_too_short_string(self):
        """Test that too short string returns None."""
        result = _parse_iso_datetime("2024-01-31")
        assert result is None

    def test_too_long_string(self):
        """Test that too long string returns None."""
        result = _parse_iso_datetime("2024-01-31T12:34:56.1234567890123456789012345678901234567890")
        assert result is None

    def test_invalid_format_slashes(self):
        """Test that slash format is rejected."""
        result = _parse_iso_datetime("2024/01/31T12:34:56")
        assert result is None

    def test_invalid_format_space(self):
        """Test that space format is rejected."""
        result = _parse_iso_datetime("2024-01-31 12:34:56")
        assert result is None

    def test_invalid_date_february_30(self):
        """Test that invalid date (Feb 30) is rejected."""
        result = _parse_iso_datetime("2024-02-30T12:34:56")
        assert result is None

    def test_invalid_date_april_31(self):
        """Test that invalid date (Apr 31) is rejected."""
        result = _parse_iso_datetime("2024-04-31T12:34:56")
        assert result is None

    def test_invalid_time(self):
        """Test that invalid time is rejected."""
        result = _parse_iso_datetime("2024-01-31T25:34:56")
        assert result is None

    def test_invalid_minute(self):
        """Test that invalid minute is rejected."""
        result = _parse_iso_datetime("2024-01-31T12:60:56")
        assert result is None

    def test_invalid_second(self):
        """Test that invalid second is rejected."""
        result = _parse_iso_datetime("2024-01-31T12:34:60")
        assert result is None

    def test_too_old_date(self):
        """Test that dates more than 10 years in past are rejected."""
        # Create a date 11 years in the past
        old_date = "2013-01-31T12:34:56"
        result = _parse_iso_datetime(old_date)
        assert result is None

    def test_too_future_date(self):
        """Test that dates more than 10 years in future are rejected."""
        # Create a date 11 years in the future
        future_date = "2035-01-31T12:34:56"
        result = _parse_iso_datetime(future_date)
        assert result is None

    def test_edge_case_exactly_10_years_past(self):
        """Test that exactly 10 years in past is accepted."""
        # This should work (exact boundary)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        past_date = now.replace(year=now.year - 10).strftime("%Y-%m-%dT%H:%M:%S")
        result = _parse_iso_datetime(past_date)
        assert result is not None

    def test_edge_case_exactly_10_years_future(self):
        """Test that exactly 10 years in future is accepted."""
        # This should work (exact boundary)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        future_date = now.replace(year=now.year + 10).strftime("%Y-%m-%dT%H:%M:%S")
        result = _parse_iso_datetime(future_date)
        assert result is not None

    def test_random_string(self):
        """Test that random string is rejected."""
        result = _parse_iso_datetime("not_a_date_at_all")
        assert result is None

    def test_partial_iso_format(self):
        """Test that partial ISO format is rejected."""
        result = _parse_iso_datetime("2024-01-31T12:34")
        assert result is None

    def test_malformed_iso_format(self):
        """Test that malformed ISO format is rejected."""
        result = _parse_iso_datetime("2024-13-31T12:34:56")  # Invalid month
        assert result is None

    def test_leap_year_feb_29(self):
        """Test that valid leap year date is accepted."""
        result = _parse_iso_datetime("2024-02-29T12:34:56")  # 2024 is a leap year
        assert result is not None
        assert result.month == 2
        assert result.day == 29

    def test_non_leap_year_feb_29(self):
        """Test that Feb 29 in non-leap year is rejected."""
        result = _parse_iso_datetime("2023-02-29T12:34:56")  # 2023 is not a leap year
        assert result is None

    def test_timezone_negative_offset(self):
        """Test parsing with negative timezone offset."""
        result = _parse_iso_datetime("2024-01-31T12:34:56-05:00")
        assert result is not None
        # The timezone should be preserved
        assert result.hour == 12
        assert "-05:00" in str(result.tzinfo)

    def test_timezone_large_offset(self):
        """Test parsing with large timezone offset."""
        result = _parse_iso_datetime("2024-01-31T12:34:56+14:00")  # Maximum reasonable offset
        assert result is not None
        # The timezone should be preserved
        assert result.hour == 12
        assert "+14:00" in str(result.tzinfo)

    def test_microseconds_precision(self):
        """Test parsing with microseconds precision."""
        result = _parse_iso_datetime("2024-01-31T12:34:56.123456")
        assert result is not None
        assert result.microsecond == 123456

    def test_leading_and_trailing_spaces(self):
        """Test that leading/trailing spaces are handled."""
        result = _parse_iso_datetime(" 2024-01-31T12:34:56 ")
        assert result is None  # Should fail due to spaces

    def test_newline_characters(self):
        """Test that newline characters are rejected."""
        result = _parse_iso_datetime("2024-01-31T12:34:56\n")
        assert result is None

    def test_tab_characters(self):
        """Test that tab characters are rejected."""
        result = _parse_iso_datetime("2024-01-31T12:34:56\t")
        assert result is None

    def test_uppercase_z(self):
        """Test that uppercase Z is accepted."""
        result = _parse_iso_datetime("2024-01-31T12:34:56Z")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_lowercase_z(self):
        """Test that lowercase z is rejected (invalid)."""
        result = _parse_iso_datetime("2024-01-31T12:34:56z")
        assert result is None

    def test_special_characters_in_middle(self):
        """Test that special characters in date are rejected."""
        result = _parse_iso_datetime("2024-01-31T12:34:56@invalid")
        assert result is None

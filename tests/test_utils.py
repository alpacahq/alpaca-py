import pytest
from datetime import datetime
from alpaca.common.utils import (
    iso_to_unix,
)  # Adjust this import based on the actual project structure


def test_valid_iso_timestamp_with_z():
    """Test valid ISO 8601 timestamp conversion with 'Z' for UTC"""
    assert (
        iso_to_unix("2025-02-17T10:00:00Z") == 1739786400000
    )  # Adjust expected value based on your desired timestamp


def test_valid_iso_timestamp_without_z():
    """Test valid ISO 8601 timestamp without 'Z' (assuming UTC)"""
    assert (
        iso_to_unix("2025-02-17T10:00:00") == 1739782800000
    )  # Adjust expected value based on your desired timestamp


def test_invalid_iso_timestamp():
    """Test invalid timestamp format raises ValueError"""
    with pytest.raises(ValueError, match="Invalid timestamp format: invalid_timestamp"):
        iso_to_unix("invalid_timestamp")


def test_empty_string():
    """Test empty string input raises ValueError"""
    with pytest.raises(ValueError, match="Invalid timestamp format: "):
        iso_to_unix("")


def test_iso_with_timezone_offset():
    """Test ISO 8601 timestamp with a timezone offset"""
    assert (
        iso_to_unix("2025-02-17T10:00:00+01:00") == 1739782800000
    )  # Adjust expected value based on the correct conversion


def test_iso_with_negative_offset():
    """Test ISO 8601 timestamp with a negative timezone offset (-05:00)"""
    assert (
        iso_to_unix("2025-02-17T10:00:00-05:00") == 1739804400000
    )  # Adjust the expected value


def test_leap_year():
    """Test leap year (February 29th)"""
    # Leap year (2024)
    assert (
        iso_to_unix("2024-02-29T00:00:00Z") == 1709164800000
    )  # Adjust the expected value


def test_daylight_saving_time():
    """Test daylight saving time transition (March 8th, 2025)"""
    # For example, 2 AM on March 8th, 2025 in a region with daylight saving time
    assert (
        iso_to_unix("2025-03-08T02:00:00-05:00") == 1741417200000
    )  # Adjust the expected value


def test_midnight_timestamp():
    """Test timestamp at midnight, January 1st, 1970 (Unix epoch start)"""
    assert (
        iso_to_unix("1970-01-01T00:00:00Z") == 0
    )  # Unix epoch start, timestamp should be 0


def test_large_timestamp():
    """Test very large timestamp (e.g., year 9999)"""
    assert (
        iso_to_unix("9999-12-31T23:59:59Z") == 253402300799000
    )  # Adjust the expected value


def test_small_timestamp():
    """Test very small timestamp (e.g., year 0001)"""
    assert (
        iso_to_unix("0001-01-01T00:00:00Z") == -62135596800000
    )  # Adjust the expected value

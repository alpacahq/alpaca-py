from alpaca.common.models import Clock, Calendar
from datetime import datetime, date


def test_clock_timestamps():
    """Tests whether timestamp string is successfully parsed into datetime"""
    clock = Clock(
        timestamp="2022-04-28T14:07:04.451420928-04:00",
        is_open=True,
        next_open="2022-04-29T09:30:00-04:00",
        next_close="2022-04-28T16:00:00-04:00",
    )

    assert type(clock.timestamp) is datetime

    assert clock.timestamp.day == 28


def test_calendar_timestamps():
    """Tests whether the timestamp strings are successfully parsed into datetime"""
    calendar = Calendar(date="2021-03-02", open="09:30", close="4:00")

    assert type(calendar.date) is date
    assert type(calendar.open) is datetime
    assert type(calendar.close) is datetime

    assert calendar.open.minute == 30

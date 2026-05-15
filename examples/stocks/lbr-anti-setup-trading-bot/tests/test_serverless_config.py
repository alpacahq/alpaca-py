from pathlib import Path


def test_schedule_uses_timezone_aware_eventbridge_scheduler():
    serverless = Path("serverless.yml").read_text()

    assert "method: scheduler" in serverless
    assert "timezone: America/New_York" in serverless
    assert "rate: cron(30 9 ? * MON-FRI *)" in serverless
    assert "cron(30 14 ? * MON-FRI *)" not in serverless

from alpaca.trading.enums import ActivityType


def test_activity_type_is_trade_activity():
    """This seems like an overly simple test right now but will probably be more useful in the future"""

    assert ActivityType.FILL.is_trade_activity()
    assert not ActivityType.ACATC.is_trade_activity()

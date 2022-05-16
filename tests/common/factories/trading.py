from alpaca.common.models import Asset


def create_dummy_asset() -> Asset:
    """
    Creates an Asset object for testing

    Returns:
        Asset: An example asset
    """

    asset_data = {
        "id": "904837e3-3b76-47ec-b432-046db621571b",
        "class": "us_equity",
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "status": "active",
        "tradable": True,
        "marginable": True,
        "shortable": True,
        "easy_to_borrow": True,
        "fractionable": True,
    }

    return Asset(**asset_data)

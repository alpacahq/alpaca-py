from urllib.parse import parse_qs, urlparse

from alpaca.data.historical.logo import LogoClient

_PNG = b"\x89PNG\r\n\x1a\nlogo"


def test_get_logo_returns_png_bytes(reqmock, logo_client: LogoClient):
    reqmock.get("https://data.alpaca.markets/v1beta1/logos/AAPL", content=_PNG)

    image = logo_client.get_logo("AAPL")

    assert image == _PNG
    assert isinstance(image, bytes)
    assert urlparse(reqmock.request_history[0].url).path == "/v1beta1/logos/AAPL"
    assert "placeholder" not in parse_qs(urlparse(reqmock.request_history[0].url).query)


def test_get_logo_sends_placeholder(reqmock, logo_client: LogoClient):
    reqmock.get("https://data.alpaca.markets/v1beta1/logos/MSFT", content=_PNG)

    image = logo_client.get_logo("MSFT", placeholder=False)

    assert image == _PNG
    assert urlparse(reqmock.request_history[0].url).path == "/v1beta1/logos/MSFT"
    assert parse_qs(urlparse(reqmock.request_history[0].url).query)["placeholder"] == [
        "false"
    ]

import urllib.parse
from datetime import datetime, timezone

from alpaca.data.historical import NewsClient
from alpaca.data.models.news import NewsSet
from alpaca.data.requests import NewsRequest


def test_get_news(reqmock, news_client: NewsClient):
    # Test single symbol request

    symbols = "AAPL"
    next_page_token = "MTcyNDAwMjIyNDAwMDAwMDAwMHw0MDQzMTg4MQ=="
    _next_page_token_in_url = urllib.parse.quote_plus(next_page_token)

    start = datetime(2022, 2, 1)
    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/news?symbols={symbols}&start={_start_in_url}&page_token={_next_page_token_in_url}",
        text="""
{
  "news": [
    {
      "author": "John",
      "content": "",
      "created_at": "2024-08-18T20:15:44Z",
      "headline": "headline",
      "id": 40432158,
      "images": [
        {
          "size": "large",
          "url": "https://"
        },
        {
          "size": "small",
          "url": "https://"
        },
        {
          "size": "thumb",
          "url": "https://"
        }
      ],
      "source": "source",
      "summary": "summary",
      "symbols": [
        "AAPL",
        "QCOM"
      ],
      "updated_at": "2024-08-18T20:15:44Z",
      "url": "https://"
    }
  ],
  "next_page_token": "MTcyNDAwMjIyNDAwMDAwMDAwMHw0MDQzMTg4MQ=="
}
        """,
    )
    request = NewsRequest(
        symbols=symbols,
        start=start,
        page_token=next_page_token,
    )
    newsset = news_client.get_news(request_params=request)

    assert isinstance(newsset, NewsSet)

    assert newsset["news"][0].id == 40432158

    assert newsset.df.index.nlevels == 1

    assert reqmock.called_once

from datetime import datetime
from typing import Optional, List

from pydantic import ConfigDict

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data import NewsImageSize
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class NewsImage(BaseModel):
    """
    images (URLs) related to given article

    Attributes:
        size (NewsImageSize): Possible values for size are thumb, small and large.
        url (str): url to image from news article.
    """

    size: NewsImageSize
    url: str

    model_config = ConfigDict(protected_namespaces=tuple())


class News(BaseModel):
    """
    News article object

    Attributes:
        id (str): News article ID
        headline (str): Headline or title of the article
        source (str): Source where the news originated from (e.g. Benzinga)
        url (Optional[str]): URL of article (if applicable)
        summary (str): Summary text for the article (may be first sentence of content)
        created_at (datetime): Date article was created (RFC 3339)
        updated_at (datetime): Date article was updated (RFC 3339)
        symbols (List[str]): List of related or mentioned symbols
        content (str): Content of the news article (might contain HTML)
        author (str): Original author of news article
        images (List[NewsImage]): List of images (URLs) related to given article (may be empty)
    """

    id: float
    headline: str
    source: str
    url: Optional[str]
    summary: str
    created_at: datetime
    updated_at: datetime
    symbols: List[str]
    author: str
    content: str
    images: Optional[List[NewsImage]]  # Not in WS response

    model_config = ConfigDict(protected_namespaces=tuple())

    def __init__(self, symbols: List[str], raw_data: RawData) -> None:
        """Instantiates a news article

        Args:
            symbols (List[str]): List of related or mentioned symbols
            raw_data (RawData): Raw unparsed news data from API.
        """
        # Mapping not needed since all keys are the same
        super().__init__(symbol=symbols, **raw_data)


class NewsSet(BaseDataSet, TimeSeriesMixin):
    """
    A collection of News articles.

    Attributes:
        news (List[News]): Array of news objects
        next_page_token (Optional[str]): Pagination token for next page
    """

    news: List[News]
    next_page_token: Optional[str]

    def __init__(self, raw_data: RawData) -> None:
        """A collection of News articles.

        Args:
            raw_data (RawData): The collection of raw news data from API.
        """
        parsed_news = []

        raw_news = raw_data

        for symbol, news in raw_news.items():
            parsed_news[symbol] = [News(symbol, news) for news in news]

        super().__init__(**parsed_news)

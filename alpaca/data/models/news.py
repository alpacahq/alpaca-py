from datetime import datetime
from typing import List, Optional

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

    id: int
    headline: str
    source: str
    url: Optional[str]
    summary: str
    created_at: datetime
    updated_at: datetime
    symbols: List[str]
    author: str
    content: str
    images: Optional[List[NewsImage]] = None  # only in historical

    def __init__(self, raw_data: RawData) -> None:
        """Instantiates a news article

        Args:
            raw_data (RawData): Raw unparsed news data from API.
        """

        super().__init__(**raw_data)


class NewsSet(BaseDataSet, TimeSeriesMixin):
    """
    A collection of News articles.

    Attributes:
        data (Dict[str, List[News]]): The collection of News articles.
        next_page_token (Optional[str]): The token to get the next page of data.
    """

    next_page_token: Optional[str]

    def __init__(self, raw_data: RawData) -> None:
        """A collection of News articles.

        Args:
            raw_data (RawData): The collection of raw news data from API.
        """
        parsed_news = {}
        articles = []

        for article in raw_data.get("news", []):
            news = News(raw_data=article)
            articles.append(news)

        parsed_news["news"] = articles
        next_page_token = raw_data.get("next_page_token")

        super().__init__(data=parsed_news, next_page_token=next_page_token)

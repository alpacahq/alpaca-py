from datetime import datetime
from typing import Optional, List
from alpaca.data.mappings import NEWS_MAPPING
from pydantic import ConfigDict

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data import NewsImageSize


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
        author (str): Original author of news article
        created_at (datetime): Date article was created (RFC 3339)
        updated_at (datetime): Date article was updated (RFC 3339)
        summary (str): Summary text for the article (may be first sentence of content)
        content (str): Content of the news article (might contain HTML)
        url (Optional[str]): URL of article (if applicable)
        images (List[NewsImage]): List of images (URLs) related to given article (may be empty)
        symbols (List[str]): List of related or mentioned symbols
        source (str): Source where the news originated from (e.g. Benzinga)
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
    images: Optional[List[NewsImage]] = None # Not in WS response

    model_config = ConfigDict(protected_namespaces=tuple())

    def __init__(self, symbols: List[str], raw_data: RawData) -> None:
        """Instantiates a news article

        Args:
            symbols (List[str]): List of related or mentioned symbols
            raw_data (RawData): Raw unparsed news data from API.
        """
        mapped_news = {
            NEWS_MAPPING[key]: val
            for key, val in raw_data.items()
            if key in NEWS_MAPPING
        }

        super().__init__(symbol=symbols[0], **mapped_news)


class NewsSet(BaseModel):
    """
    A collection of News articles.

    Attributes:
        news (List[News]): Array of news objects
        next_page_token (Optional[str]): Pagination token for next page
    """

    news: List[News]
    next_page_token: Optional[str]

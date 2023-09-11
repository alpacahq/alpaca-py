from datetime import datetime
from typing import Optional, List

from alpaca.common.models import ValidateBaseModel as BaseModel
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
    images (URLs) related to given article

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
        symbols (str): List of related or mentioned symbols
        source (str): Source where the news originated from (e.g. Benzinga)
    """

    id: float
    headline: str
    author: str
    created_at: datetime
    updated_at: datetime
    summary: str
    content: str
    url: Optional[str]
    images: List[NewsImage]
    symbols: List[str]
    source: str


class NewsSet(BaseModel):
    """
    images (URLs) related to given article

    Attributes:
        news (List[News]): Array of news objects
        next_page_token (Optional[str]): Pagination token for next page
    """

    news: List[News]
    next_page_token: Optional[str]

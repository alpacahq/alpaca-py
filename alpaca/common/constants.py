from typing import TypeVar

DATA_V2_MAX_LIMIT = 10000  # max items per api call

ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE = 100

BROKER_DOCUMENT_UPLOAD_LIMIT = 10

PageItem = TypeVar("PageItem")  # Generic type for an item from a paginated request.

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_WAIT_SECONDS = 3
DEFAULT_RETRY_EXCEPTION_CODES = [429, 504]

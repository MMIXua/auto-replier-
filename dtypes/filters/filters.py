
from typing import Type

from dtypes.source_type import BaseSourceType
from . import BaseFilter


class SearchFilter(BaseFilter):
    name = "search_filter"
    source_type: Type[BaseSourceType]


class SendFilter(BaseFilter):
    name = "send_filter"
    source_type: Type[BaseSourceType]

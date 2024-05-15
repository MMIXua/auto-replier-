
from typing import Type

from dtypes.source_type import BaseSourceType
from utils.jsonify import Jsonified


class BaseFilter(Jsonified):
    name = "filter"
    source_type: Type[BaseSourceType]

    def __init__(self, source_type: Type[BaseSourceType]):
        self.name = self.name
        self.source_type = source_type

        self.fields = ["source_type"]


from .filters import SearchFilter, SendFilter

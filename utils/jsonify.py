
from typing import Any
import json


class BaseJsonifed:
    fields = []

    def to_dict(self):
        pass

    def to_json(self):
        return json.dumps(self.to_dict())


class JsonifiedProperty(BaseJsonifed):
    field = "base"

    def to_dict(self):
        if self.field not in self.__dict__:
            raise KeyError(f"Cant find field with name: {self.field} in object: {self}")

        return self.__dict__[self.field]


class Jsonified(BaseJsonifed):
    fields: list[str | JsonifiedProperty] = []

    def to_dict(self) -> dict:
        export = {}

        for field in self.fields:

            if isinstance(field, str):
                if field not in self.__dict__:
                    raise KeyError(f"Cant find field with name: {field} in object: {self}")

                obj = self.__dict__[field]

            else:
                obj = field

            if isinstance(obj, list):
                data = {
                    field: [i.to_dict() if isinstance(i, Jsonified) else i for i in obj]
                }

            elif not issubclass(obj.__class__, BaseJsonifed):
                data = {
                    field: obj
                }

            elif issubclass(obj.__class__, BaseJsonifed):
                data = {
                    obj.name: obj.to_dict()
                }

            export.update(data)

        return export

    def update(self, key: str, value: Any) -> None:
        if key not in self.__dict__:
            return

        elif isinstance(self.__dict__[key], list):
            self.__dict__[key].append(value)

        else:
            self.__dict__.update({key: value})

    def to_str(self):
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            indent=4
        )

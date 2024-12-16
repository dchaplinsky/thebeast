from typing import Optional, List, Any
from collections import namedtuple

DEFAULT_META_FIELDS: List[str] = [
    "locale",
    "transformation",
    "date",
    "record_no",
    "input_uri",
]
meta_cls: Optional[type] = None


def get_meta_cls(meta_fields: List[str] = DEFAULT_META_FIELDS) -> type:
    global meta_cls

    if meta_cls is None:
        # That's a bloody black magic
        class meta_cls(
            namedtuple("meta_cls", meta_fields, defaults=[None for _ in meta_fields])
        ):
            def set_field(self, name: str, value: Any):
                if name in self._fields:
                    return self._replace(**{name: value})

                return self

    return meta_cls


__all__ = ["get_meta_cls"]

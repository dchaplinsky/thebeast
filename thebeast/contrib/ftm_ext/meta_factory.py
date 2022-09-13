from typing import Optional, List
from collections import namedtuple

DEFAULT_META_FIELDS: List[str] = ["locale", "transformation", "date"]
meta_cls: Optional[type] = None


def get_meta_cls(meta_fields: List[str] = DEFAULT_META_FIELDS) -> type:
    global meta_cls

    if meta_cls is None:
        meta_cls = namedtuple("Meta", meta_fields, defaults=[None for _ in meta_fields])

    return meta_cls


__all__ = ["get_meta_cls"]

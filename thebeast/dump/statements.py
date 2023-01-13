from hashlib import sha1

try:
    from functools import cache
except ImportError:
    from functools import lru_cache

    def cache(user_function, /):
        'Simple lightweight unbounded cache.  Sometimes called "memoize".'
        return lru_cache(maxsize=None)(user_function)


from typing import Dict, Union, List, Iterable, Any
from csv import DictWriter

from followthemoney import model as ftm

from thebeast.types import RedGreenEntity
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from .abstract import AbstractStatementsWriter
from thebeast.contrib.ftm_ext.meta_factory import get_meta_cls

ID_PROP: str = "id"
# meta fields o use for statement_id generation by default
DEFAULT_META_FOR_ID: List[str] = ["locale", "transformation", "date"]


@cache
def resolve_schema_propery_type(schema: str, property_name: str) -> str:
    return ftm.schemata[schema].properties[property_name].type.name


def stmt_key(
    entity_id: str, prop: str, value: Union[StrProxy, str], id_use_meta: List[str] = DEFAULT_META_FOR_ID
) -> str:
    """Hash the key properties of a statement record to make a unique ID."""

    if not isinstance(value, StrProxy):
        key = f"thebeast.{entity_id}.{prop}.{value}.no_meta"
        return sha1(key.encode("utf-8")).hexdigest()

    # i really dont know what i am doing
    # hope this works

    # filter entity meta based on given properties list
    filtered_meta = {}
    for x in id_use_meta:
        filtered_meta[x] = getattr(value._meta, x)

    # and create a new meta object to keep filtered values
    meta_cls = get_meta_cls()
    meta = meta_cls(**filtered_meta)

    key = f"thebeast.{entity_id}.{prop}.{value}.{meta}"
    return sha1(key.encode("utf-8")).hexdigest()


class StatementsCSVWriter(AbstractStatementsWriter):
    def __init__(
        self,
        output_uri: str,
        meta_fields: List[str],
        error_uri: str = "/dev/null",
        id_use_meta: List[str] = DEFAULT_META_FOR_ID,
    ) -> None:
        super().__init__(output_uri, meta_fields, error_uri)
        self.id_use_meta = id_use_meta

        fieldnames: List[str] = [
            "id",
            "entity_id",
            "prop",
            "prop_type",
            "schema",
            "value",
        ] + [f"meta:{f}" for f in meta_fields]

        self.csv_writer = DictWriter(
            self.output_fh,
            fieldnames=fieldnames,
        )

        self.csv_writer.writeheader()

        if self.output_uri != self.error_uri:
            self.csv_error_writer = DictWriter(
                self.error_fh,
                fieldnames=fieldnames,
            )

            self.csv_error_writer.writeheader()
        else:
            self.csv_error_writer = self.csv_writer

    def write_entities(self, entities: Iterable[RedGreenEntity], flush: bool = True) -> None:
        for entity in entities:
            rows = []

            rec: Dict[str, Any] = {
                "id": stmt_key(
                    entity_id=entity.payload["id"],
                    prop=ID_PROP,
                    value=entity.payload["id"],
                    id_use_meta=self.id_use_meta,
                ),
                "entity_id": entity.payload["id"],
                "prop": ID_PROP,
                "prop_type": ID_PROP,
                "schema": entity.payload["schema"],
                "value": entity.payload["id"],
            }

            rows.append(rec)

            for prop, values in entity.payload["properties"].items():
                for value in values:
                    rec = {
                        "id": stmt_key(
                            entity_id=entity.payload["id"], prop=prop, value=value, id_use_meta=self.id_use_meta
                        ),
                        "entity_id": entity.payload["id"],
                        "prop": prop,
                        "prop_type": resolve_schema_propery_type(schema=entity.payload["schema"], property_name=prop),
                        "schema": entity.payload["schema"],
                        "value": value,
                    }

                    rec.update({f"meta:{f}": v for f, v in value._meta._asdict().items()})
                    rows.append(rec)

            if entity.valid:
                self.csv_writer.writerows(rows)
            else:
                self.csv_error_writer.writerows(rows)

        if flush:
            self.output_fh.flush()

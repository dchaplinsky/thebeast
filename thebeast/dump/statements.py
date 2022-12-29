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
from followthemoney.schema import Schema  # type: ignore

from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from .abstract import AbstractStatementsWriter

ID_PROP: str = "id"


@cache
def resolve_schema_propery_type(schema: str, property_name: str) -> str:
    return ftm.schemata[schema].properties[property_name].type.name


def stmt_key(
    entity_id: str,
    prop: str,
    value: Union[StrProxy, str],
) -> str:
    """Hash the key properties of a statement record to make a unique ID."""

    if isinstance(value, StrProxy):
        key = f"thebeast.{entity_id}.{prop}.{value}.{value._meta}"
    else:
        key = f"thebeast.{entity_id}.{prop}.{value}.no_meta"

    return sha1(key.encode("utf-8")).hexdigest()


class StatementsCSVWriter(AbstractStatementsWriter):
    def __init__(self, output_uri: str, meta_fields: List[str]) -> None:
        super().__init__(output_uri, meta_fields)

        self.csv_writer = DictWriter(
            self.output,
            fieldnames=[
                "id",
                "entity_id",
                "prop",
                "prop_type",
                "schema",
                "value",
            ]
            + [f"meta:{f}" for f in meta_fields],
        )

        self.csv_writer.writeheader()

    def write_entities(self, entities: Iterable[Schema], flush: bool = True) -> None:
        for entity in entities:
            rows = []

            rec: Dict[str, Any] = {
                "id": stmt_key(entity_id=entity["id"], prop=ID_PROP, value=entity["id"]),
                "entity_id": entity["id"],
                "prop": ID_PROP,
                "prop_type": ID_PROP,
                "schema": entity["schema"],
                "value": entity["id"],
            }

            rows.append(rec)

            for prop, values in entity["properties"].items():
                for value in values:
                    rec = {
                        "id": stmt_key(entity_id=entity["id"], prop=prop, value=value),
                        "entity_id": entity["id"],
                        "prop": prop,
                        "prop_type": resolve_schema_propery_type(schema=entity["schema"], property_name=prop),
                        "schema": entity["schema"],
                        "value": value,
                    }

                    rec.update({f"meta:{f}": v for f, v in value._meta._asdict().items()})
                    rows.append(rec)

            self.csv_writer.writerows(rows)

        if flush:
            self.output.flush()

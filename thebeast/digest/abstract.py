from typing import List, Dict, Generator, Iterable, Callable, Optional, Any, Union, Tuple

from followthemoney.schema import Schema  # type: ignore

from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy
from thebeast.types import Record

from .utils import (
    generate_pseudo_id,
    make_entity,
    jmespath_results_as_array,
    resolve_entity_refs,
    ensure_list,
    resolve_callable,
    deflate_entity,
    ENTITY_TYPE
)
from .resolvers import resolve_property_values, resolve_constant_meta_values, resolve_collection_meta_values


def make_entities(
    record: Union[List, Dict],
    entities_config: Dict,
    statements_meta: Dict[str, str],
    parent_context_entities_map: Dict[str, Schema],
) -> Tuple[List[Schema], Dict[str, Schema]]:
    """
    Takes the list/dict of records and a config for collection and produces entites
    """

    context_entities_map: Dict[str, str] = parent_context_entities_map.copy()
    context_entities: List[Schema] = []

    for entity_name, entity_config in entities_config.items():
        entity = make_entity(entity_config["schema"], key_prefix=entity_name)
        key_values: List[str] = []
        variables: Dict[str, List[StrProxy]] = {}

        for property_name, property_configs in entity_config["properties"].items():
            if not isinstance(property_configs, list):
                property_configs = [property_configs]

            property_values: List[StrProxy] = resolve_property_values(
                property_configs=property_configs,
                record=record,
                entity=entity,
                statements_meta=statements_meta,
                variables=variables,
            )

            if property_name.startswith("$"):
                variables[property_name] = property_values
            else:
                entity.add(
                    property_name,
                    property_values,
                )

        # Some bizarre parsing of values here, so we can construct an id for the entity from both
        # existing entity fields and records (after jmespathing it)
        for key in entity_config["keys"]:
            key_type, key_path = key.split(".", 1)
            if key_type == "entity":
                properties_to_use: List[str] = []

                if key_path == "*":
                    properties_to_use = sorted(entity.properties)
                else:
                    properties_to_use = [key_path]

                for property_name in properties_to_use:
                    prop = entity.schema.properties[property_name]

                    if prop.type == ENTITY_TYPE:
                        for val in entity.get(property_name):
                            key_values += context_entities_map[val]
                    else:
                        key_values += entity.get(property_name)

            elif key_type == "variable":
                key_values += variables.get(key_path)
            elif key_type == "record":
                key_values += jmespath_results_as_array(key_path, record)

        entity.make_id(*key_values)

        context_entities_map[generate_pseudo_id(entity.key_prefix)] = entity.id
        context_entities.append(entity)

    return list(resolve_entity_refs(context_entities, context_entities_map)), context_entities_map


def main_cog(
    data: Record,
    config: Dict,
    parent_context_entities_map: Dict[str, Schema],
    statements_meta: Dict[str, str],
    # TODO: inject parent record as __parent or something
    parent_record: Optional[Any],
) -> Generator[Schema, None, None]:
    for collection_name, collection_config in config.get("collections", {}).items():
        # Applying optional record level transformer
        record_transformer: Callable = (
            resolve_callable(collection_config["record_transformer"])
            if "record_transformer" in collection_config
            else lambda x: x
        )

        for record in record_transformer(jmespath_results_as_array(collection_config["path"], data.payload)):
            # Retrieving some record-level meta
            local_statements_meta: Dict[str, str] = {"record_no": data.record_no, "input_uri": data.input_uri}

            if "meta" in collection_config:
                local_statements_meta.update(
                    {
                        statement_meta_name: "\n".join(
                            resolve_collection_meta_values(
                                property_configs=ensure_list(statement_meta_config),
                                record=record,
                                statements_meta=statements_meta,
                            ),
                        )
                        for statement_meta_name, statement_meta_config in collection_config.get("meta", {}).items()
                    }
                )

            # Updating local copy of a parent meta with a local statements meta
            # TODO: https://docs.python.org/3/library/collections.html#collections.ChainMap
            combined_statements_meta: Dict[str, str] = statements_meta.copy()
            combined_statements_meta.update(local_statements_meta)

            local_context_entities, combined_context_entites_map = make_entities(
                record,
                collection_config["entities"],
                statements_meta=combined_statements_meta,
                parent_context_entities_map=parent_context_entities_map,
            )

            for entity in local_context_entities:
                # We are converting entities from Schema to Dict here to overcome
                # an issue with circular references during pickling (also it'll reduce)
                # the amount of data needs to be transfered between processed, since
                # each process now has it's own FTM model and you don't need to
                # carry a copy around with each entity
                yield deflate_entity(entity)

            if "collections" in collection_config:
                for entity in main_cog(
                    data=Record(payload=record, record_no=data.record_no, input_uri=data.input_uri),
                    config=collection_config,
                    parent_context_entities_map=combined_context_entites_map,
                    statements_meta=statements_meta,
                    parent_record=None,
                ):
                    yield entity


class AbstractDigestor:
    """
    TODO: review an architecture once it works
    """

    def __init__(self, mapping_config: Dict, meta_fields: List[str]) -> None:
        self.mapping_config: Dict = mapping_config
        self.meta_fields: List[str] = meta_fields

    def extract(self, records: Iterable[Record]) -> Generator[Dict, None, None]:
        # First let's get some global level meta values for our statements
        statements_meta: Dict[str, str] = {
            statement_meta_name: "\n".join(resolve_constant_meta_values(ensure_list(statement_meta_config)))
            for statement_meta_name, statement_meta_config in self.mapping_config.get("meta", {}).items()
        }

        # constant statements will have dummy values for the record_no and input_uri
        statements_meta.update(
            {
                "record_no": 0,
                "input_uri": "__mapping__",
            }
        )

        # Then let's yield constant entities
        context_entities, context_entities_map = make_entities(
            record={},
            entities_config=self.mapping_config.get("constant_entities", {}),
            statements_meta=statements_meta,
            parent_context_entities_map={},
        )

        for entity in context_entities:
            yield deflate_entity(entity)

        for entity in self.run_the_cog(
            records=records, parent_context_entities_map=context_entities_map, statements_meta=statements_meta
        ):
            yield entity

    def run_the_cog(
        self,
        records: Iterable[Record],
        parent_context_entities_map: Dict[str, str],
        statements_meta: Dict[str, str],
    ) -> Generator[Schema, None, None]:
        raise NotImplementedError("You have to redefine it")

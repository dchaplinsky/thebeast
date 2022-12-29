from typing import Union, List, Dict, Generator, Iterable, Callable, Optional, Any

from followthemoney.schema import Schema  # type: ignore

from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy

from .utils import (
    generate_pseudo_id,
    make_entity,
    jmespath_results_as_array,
    resolve_entity_refs,
    ensure_list,
    resolve_callable,
    inflate_entity,
    deflate_entity,
)
from .resolvers import resolve_property_values, resolve_constant_meta_values, resolve_collection_meta_values


def make_entities(
    record: Union[List, Dict], entities_config: Dict, statements_meta: Dict[str, str]
) -> Generator[Schema, None, None]:
    """
    Takes the list/dict of records and a config for collection and produces entites
    """

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
                key_values += entity.get(key_path)
            elif key_type == "record":
                key_values += jmespath_results_as_array(key_path, record)

        entity.make_id(*key_values)

        yield entity


def main_cog(
    data: Union[List, Dict],
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

        for record in record_transformer(jmespath_results_as_array(collection_config["path"], data)):
            # Retrieving some record-level meta
            local_statements_meta: Dict[str, str] = {}

            if "meta" in collection_config:
                local_statements_meta = {
                    statement_meta_name: "\n".join(
                        resolve_collection_meta_values(
                            property_configs=ensure_list(statement_meta_config),
                            record=record,
                            statements_meta=statements_meta,
                        ),
                    )
                    for statement_meta_name, statement_meta_config in collection_config.get("meta", {}).items()
                }

            # Updating local copy of a parent meta with a local statements meta
            combined_statements_meta: Dict[str, str] = statements_meta.copy()
            combined_statements_meta.update(local_statements_meta)

            local_context_entities: Dict[str, Schema] = {}
            for entity in make_entities(record, collection_config["entities"], combined_statements_meta):
                local_context_entities[generate_pseudo_id(entity.key_prefix)] = entity

            combined_context_entites_map: Dict[str, Schema] = parent_context_entities_map.copy()
            combined_context_entites_map.update({k: v.id for k, v in local_context_entities.items()})

            for entity in resolve_entity_refs(local_context_entities.values(), combined_context_entites_map):
                yield deflate_entity(entity)

            if "collections" in collection_config:
                for entity in main_cog(
                    data=record,
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

    def extract(self, records: Iterable[Union[List, Dict]]) -> Generator[Schema, None, None]:
        # First let's get some global level meta values for our statements
        statements_meta: Dict[str, str] = {
            statement_meta_name: "\n".join(resolve_constant_meta_values(ensure_list(statement_meta_config)))
            for statement_meta_name, statement_meta_config in self.mapping_config.get("meta", {}).items()
        }

        # Then let's yield constant entities
        context_entities_map: Dict[str, str] = {}
        context_entities: List[Schema] = []

        # TODO: use a dedicated function to make constant entities maybe?
        for entity in make_entities(
            record={}, entities_config=self.mapping_config.get("constant_entities", {}), statements_meta=statements_meta
        ):
            context_entities_map[generate_pseudo_id(entity.key_prefix)] = entity.id
            context_entities.append(entity)

        # And resolve entity refererence in constant entities (i.e one constant entity is referencing
        # another in the property)
        for entity in resolve_entity_refs(context_entities, context_entities_map):
            yield entity

        for entity in self.run_the_cog(
            records=records, parent_context_entities_map=context_entities_map, statements_meta=statements_meta
        ):
            yield entity

    def run_the_cog(
        self,
        records: Iterable[Union[List, Dict]],
        parent_context_entities_map: Dict[str, str],
        statements_meta: Dict[str, str],
    ) -> Generator[Schema, None, None]:
        raise NotImplementedError("You have to redefine it")

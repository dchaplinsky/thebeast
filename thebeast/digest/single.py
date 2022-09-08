from typing import Union, List, Dict, Generator, Iterable

from followthemoney.schema import Schema  # type: ignore

from .utils import generate_pseudo_id, make_entity, jmespath_results_as_array, resolve_entity_refs, ensure_list

from .resolvers import resolve_entity, resolve_constant_statement_meta


def make_entities(
    record: Union[List, Dict], entities_config: Dict, statements_meta: Dict[str, str]
) -> Generator[Schema, None, None]:
    """
    Takes the list/dict of records and a config for collection and produces entites
    """

    for entity_name, entity_config in entities_config.items():
        entity = make_entity(entity_config["schema"], key_prefix=entity_name)
        key_values: List[str] = []

        for property_name, property_configs in entity_config["properties"].items():
            if not isinstance(property_configs, list):
                property_configs = [property_configs]

            entity.add(
                property_name,
                resolve_entity(
                    property_configs=property_configs, record=record, entity=entity, statements_meta=statements_meta
                ),
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
    parent_context_entities: Dict[str, Schema],
    statements_meta: Dict[str, str],
) -> Generator[Schema, None, None]:
    for collection_name, collection_config in config.get("collections", {}).items():
        for record in jmespath_results_as_array(collection_config["path"], data):
            local_context_entities: Dict[str, Schema] = {}
            for entity in make_entities(record, collection_config["entities"], statements_meta):
                local_context_entities[generate_pseudo_id(entity.key_prefix)] = entity

            combined_context_entites: Dict[str, Schema] = parent_context_entities.copy()
            combined_context_entites.update(local_context_entities)

            for entity in resolve_entity_refs(local_context_entities.values(), combined_context_entites):
                yield entity


class SingleThreadedDigestor:
    """
    TODO: review an architecture once it works
    """

    def __init__(self, mapping_config: Dict) -> None:
        self.mapping_config = mapping_config

    def extract(self, records: Iterable[Union[List, Dict]]) -> Generator[Schema, None, None]:
        # First let's get some global level meta values for our statements
        statements_meta: Dict[str, str] = {
            statement_meta_name: "\n".join(resolve_constant_statement_meta(ensure_list(statement_meta_config)))
            for statement_meta_name, statement_meta_config in self.mapping_config.get(
                "statement_meta_values", {}
            ).items()
        }

        # Then let's yield constant entities
        context_entities: Dict[str, Schema] = {}

        # TODO: use a dedicated function to make constant entities maybe?
        for entity in make_entities(
            record={}, entities_config=self.mapping_config.get("constant_entities", {}), statements_meta=statements_meta
        ):
            context_entities[generate_pseudo_id(entity.key_prefix)] = entity

        # And resolve entity refererence in constant entities (i.e one constant entity is referencing
        # another in the property)
        for entity in resolve_entity_refs(context_entities.values(), context_entities):
            yield entity

        # Now for the fun part: real entities
        for record in records:
            for entity in main_cog(
                data=record,
                config=self.mapping_config,
                parent_context_entities=context_entities,
                statements_meta=statements_meta,
            ):
                # TODO: green/red sorting for valid records/exceptions here?
                yield entity

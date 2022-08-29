from typing import Union, List, Dict, Generator, Iterable, Any, Callable

import jmespath  # type: ignore
import regex as re  # type: ignore
from jinja2 import Environment, BaseLoader, select_autoescape

from followthemoney.schema import Schema  # type: ignore

# We are utilizing here the fact that Model is a singletone and set up
# in the thebeast.conf.mapping
from followthemoney import model as ftm  # type: ignore
from followthemoney.types import registry  # type: ignore
from followthemoney.util import make_entity_id  # type: ignore

from thebeast.conf.utils import import_string


# TODO: expose jmespath to templates as a filter?
jinja_env = Environment(loader=BaseLoader(), autoescape=select_autoescape())

ENTITY_TYPE = registry.get("entity")
CALLABLE_CACHE: Dict[str, Callable] = {}

# TODO: move to utils?


def resolve_callable(fqfn: str) -> Callable:
    if fqfn in CALLABLE_CACHE:
        return CALLABLE_CACHE[fqfn]

    func = import_string(fqfn)
    CALLABLE_CACHE[fqfn] = func

    return func


def jmespath_results_as_array(path: str, record: Union[List, Dict]) -> List[Any]:
    """
    Extracts the values from the record according to the path, wraps everything into array
    """
    values = jmespath.search(path, record) or []
    if not isinstance(values, list):
        values = [values]

    return values


def generate_pseudo_id(temporary_entity_id: str):
    return make_entity_id(temporary_entity_id, key_prefix="thebeast_temporary_entity_id")


def resolve_entity_refs(
    entities: Iterable[Schema], context_entities: Dict[str, Schema]
) -> Generator[Schema, None, None]:
    for entity in entities:
        for prop in entity.iterprops():
            if prop.type == ENTITY_TYPE:
                resolved_properties = []

                # TODO: errors (probably red/green sorting) for the properties that cannot be resolved
                for prop_val in entity.get(prop):
                    resolved_properties = context_entities.get(prop_val, prop_val)

                entity.set(prop, resolved_properties)

        yield entity


def make_entities(record: Union[List, Dict], entities_config: Dict) -> Generator[Schema, None, None]:
    """
    Takes the list/dict of records and a config for collection and produces entites
    """

    for entity_name, entity_config in entities_config.items():
        entity = ftm.make_entity(entity_config["schema"], key_prefix=entity_name)
        key_values: List[str] = []

        for property_name, property_configs in entity_config["properties"].items():
            if not isinstance(property_configs, list):
                property_configs = [property_configs]

            property_values = []
            for property_config in property_configs:
                for command, command_config in property_config.items():
                    if command == "literal":
                        # `literal` is simply a string or number constant used for FTM entity field
                        property_values.append(command_config)
                    elif command == "entity":
                        # `entity` is a named reference to another entity available in the current context
                        # i.e as a constant entity or entity of the current collection and its parents
                        # For now we just adding the reference to the another entity and we'll resolve it later
                        # TODO: green/red validate if the property allows to reference to another entity
                        # i.e entity.schema.properties[property_name].type == entity
                        # TODO: we probably want to preserve the list of property names to resolve later on

                        # To fool the FTM we supply something that looks like entity ID which we can
                        # resolve later
                        property_values.append(generate_pseudo_id(command_config))
                    elif command == "column":
                        # `column` is a jmespath applied at the current level of the doc
                        # to collect all the needed values for the field from it
                        property_values += jmespath_results_as_array(command_config, record)

                    elif command == "regex_split":
                        # `regex_split` is an optional regex splitter to extract multiple
                        # values for the entity field from the single string.

                        new_property_values: List[str] = []

                        for property_value in property_values:
                            new_property_values += re.split(command_config, str(property_value), flags=re.V1)

                        property_values = new_property_values

                    elif command == "regex":
                        # `regex` is an optional regex **matcher** to match the part of the extracted string
                        # and set it as a value for the entity field. It is being applied after the (optional)
                        # regex_split

                        extracted_property_values: List[Any] = []

                        for property_value in property_values:
                            if not property_value:
                                continue

                            m = re.search(command_config, str(property_value), flags=re.V1)
                            if m:
                                if m.groups():
                                    # We support both, groups
                                    extracted_property_values.append(m.group(1))
                                else:
                                    # And full match
                                    extracted_property_values.append(m.group(0))

                        property_values = extracted_property_values

                    elif command == "transformer":
                        # `transformer` is a python function which (currently) accepts only a list of values
                        # applies some transform to it and returns the modified list. That list will be
                        # added to the entity instead of the original values
                        property_values = resolve_callable(command_config)(property_values)

                    elif command == "augmentor":
                        # `augmentor` is a similar concept to the `transformer`, but modified list is added
                        # to the original values
                        property_values += resolve_callable(command_config)(property_values)
                    elif command == "template":
                        # `template` is a jinja template str that will be rendered using the context
                        # which contains current half-finished entity and original
                        template = jinja_env.from_string(command_config)
                        property_values.append(template.render(entity=entity.properties, record=record))

            entity.add(property_name, property_values)

        for key in entity_config["keys"]:
            key_type, key_path = key.split(".", 1)
            if key_type == "entity":
                key_values += entity.get(key_path)
            elif key_type == "record":
                key_values += jmespath_results_as_array(key_path, record)

        entity.make_id(*key_values)

        yield entity


def main_cog(
    data: Union[List, Dict], config: Dict, parent_context_entities: Dict[str, Schema]
) -> Generator[Schema, None, None]:
    for collection_name, collection_config in config.get("collections", {}).items():
        for record in jmespath_results_as_array(collection_config["path"], data):
            local_context_entities: Dict[str, Schema] = {}
            for entity in make_entities(record, collection_config["entities"]):
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
        # First let's yield constant entities
        context_entities: Dict[str, Schema] = {}
        for entity in make_entities({}, self.mapping_config.get("constant_entities", {})):
            context_entities[generate_pseudo_id(entity.key_prefix)] = entity

        for entity in resolve_entity_refs(context_entities.values(), context_entities):
            yield entity

        for record in records:
            for entity in main_cog(data=record, config=self.mapping_config, parent_context_entities=context_entities):
                # TODO: green/red sorting for valid records/exceptions here?
                yield entity

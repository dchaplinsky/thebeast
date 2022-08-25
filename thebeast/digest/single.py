from typing import Union, List, Dict, Generator, Iterable, Any

import jmespath  # type: ignore
import re
from thebeast.conf import SourceMapping
from jinja2 import Environment, BaseLoader, select_autoescape

from followthemoney.schema import Schema  # type: ignore

# We are utilizing here the fact that Model is a singletone and set up 
# in the thebeast.conf.mapping
from followthemoney import model as ftm  # type: ignore


jinja_env = Environment(loader=BaseLoader(), autoescape=select_autoescape())


def make_entities(record: Union[List, Dict], entities_config: Dict) -> Generator[Schema, None, None]:
    for entity_name, entity_config in entities_config.items():
        entity = ftm.make_entity(entity_config["schema"], key_prefix=entity_name)
        key_values: List[str] = []

        for property_name, property_configs in entity_config["properties"].items():
            if not isinstance(property_configs, list):
                property_configs = [property_configs]
            for property_config in property_configs:
                if "literal" in property_config:
                    entity.add(property_name, property_config["literal"])
                elif "column" in property_config:
                    property_values = jmespath.search(property_config["column"], record) or []
                    
                    if "regex" in property_config:
                        extracted_property_values: List[Any] = []

                        if not isinstance(property_values, list):
                            property_values = [property_values]

                        for property_value in property_values:
                            if not property_value:
                                continue

                            m = re.search(property_config["regex"], str(property_value))
                            if m:
                                if m.groups():
                                    # We support both, groups
                                    extracted_property_values.append(m.group(1))
                                else:
                                    # And full match
                                    extracted_property_values.append(m.group(0))

                        entity.add(property_name, extracted_property_values)
                    else:
                        entity.add(property_name, property_values)

        # Templates are resolved after all other extractors
        for property_name, property_configs in entity_config["properties"].items():
            if not isinstance(property_configs, list):
                property_configs = [property_configs]

            for property_config in property_configs:
                if "template" in property_config:
                    template = jinja_env.from_string(property_config["template"])
                    entity.add(property_name, template.render(
                        entity=entity.properties,
                        record=record
                    ))

        for key in entity_config["keys"]:
            key_values += entity.get(key)

        entity.make_id(*key_values)

        yield entity


def main_cog(data: Union[List, Dict], config: Dict) -> Generator[Schema, None, None]:
    """
    TODO: Do we really need a function?
    """
    for collection_name, collection_config in config.get("collections", {}).items():
        for record in jmespath.search(collection_config["path"], data) or []:
            for entity in make_entities(record, collection_config["entities"]):
                yield entity

    for entity in make_entities({}, config.get("constant_entities", {})):
        yield entity


class SingleThreadedDigestor:
    """
    TODO: review an architecture once it works
    """

    def __init__(self, mapping_config: Dict) -> None:
        self.mapping_config = mapping_config

    def extract(self, records: Iterable[Union[List, Dict]]) -> Generator[Schema, None, None]:
        for record in records:
            for entity in main_cog(record, self.mapping_config):
                # TODO: green/red sorting for valid records/exceptions here?
                yield entity

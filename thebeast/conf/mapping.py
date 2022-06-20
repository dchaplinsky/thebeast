from pathlib import Path
from typing import Union, Callable, Dict, Any
import yaml
import json

import fastjsonschema  # type: ignore
from .exc import InvalidMappingException, InvalidOverridesException
from .utils import import_string


class SourceMapping:
    """
    A class to load a mapping, validate it, load the ftm ontology and rock-n-roll
    """

    def __init__(
        self, mapping_file: Path, schema_file: Union[Path, None] = None,
        ingest_overrides: Union[Dict[str, Any], None] = None,
        dump_overrides: Union[Dict[str, Any], None] = None
    ):
        """
        You might provide an alternative jsonschema file for the validation (for example, to bypass it)
        """

        if ingest_overrides is None:
            ingest_overrides = {}
        if dump_overrides is None:
            dump_overrides = {}

        curr_dir: Path = Path(__file__).parent
        if schema_file is None:
            schema_file = Path(curr_dir / "mapping_validator.json")

        with schema_file.open("r") as fp:
            schema: Callable = fastjsonschema.compile(json.load(fp))

        with mapping_file.open("r") as fp:
            mapping: dict = yaml.safe_load(fp)

        # First validate the mapping loaded from the file
        try:
            schema(mapping)
        except fastjsonschema.exceptions.JsonSchemaValueException as e:
            raise InvalidMappingException(e)

        # Now validate the overrided values
        ingest_params: dict = mapping["ingest"].get("params", {})
        ingest_params.update(ingest_overrides)
        mapping["ingest"]["params"] = ingest_params
        # dump_params: dict = mapping["dump"].get("params", {})
        # dump_params.update(dump_overrides)
        # mapping["dump"]["params"] = dump_params

        try:
            mapping = schema(mapping)
        except fastjsonschema.exceptions.JsonSchemaValueException as e:
            raise InvalidOverridesException(e)
        
        self.ingestor = import_string(mapping["ingest"]["extractor"])(**mapping["ingest"].get("params", {}))

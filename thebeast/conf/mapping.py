import os
from pathlib import Path
from typing import Union, Callable, Dict, Any, List
import json


import fastjsonschema  # type: ignore
from .exc import InvalidMappingException, InvalidOverridesException
from .utils import import_string, ordered_load
from thebeast.contrib.ftm_ext.meta_factory import get_meta_cls, DEFAULT_META_FIELDS


class SourceMapping:
    """
    A class to load a mapping, validate it, load the ftm ontology and rock-n-roll
    """

    def __init__(
        self,
        mapping_file: Path,
        schema_file: Union[Path, None] = None,
        ingest_overrides: Union[Dict[str, Any], None] = None,
        dump_overrides: Union[Dict[str, Any], None] = None,
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
            mapping: dict = ordered_load(fp)

        # First validate the mapping loaded from the file
        try:
            schema(mapping)
        except fastjsonschema.exceptions.JsonSchemaValueException as e:
            raise InvalidMappingException(e)

        # Now validate the overrided values
        ingest_params: dict = mapping["ingest"].get("params", {})
        ingest_params.update(ingest_overrides)
        mapping["ingest"]["params"] = ingest_params
        dump_params: dict = mapping["dump"].get("params", {})
        dump_params.update(dump_overrides)
        mapping["dump"]["params"] = dump_params

        try:
            mapping = schema(mapping)
        except fastjsonschema.exceptions.JsonSchemaValueException as e:
            raise InvalidOverridesException(e)

        # TODO: validate entity names and availability of the refs in the context

        # Overriding ftm ontology with a custom one if needed
        if mapping.get("ftm_ontology", None) is not None:
            os.environ["FTM_MODEL_PATH"] = mapping["ftm_ontology"]

        # ftm model is a singleton instantiated on the import, we should be careful here
        from followthemoney import model as ftm  # type: ignore

        meta_fields: List[str] = DEFAULT_META_FIELDS
        if mapping.get("meta", None) is not None:
            # Setting meta singletone for statements meta
            meta_fields = mapping["meta"]
            get_meta_cls(mapping["meta"])

        self.ftm = ftm
        # self.ingestor = import_string(mapping["ingest"]["cls"])(**mapping["ingest"].get("params", {}))
        self.digestor = import_string(mapping["digest"]["cls"])(
            mapping_config=mapping["digest"], **mapping["digest"].get("params", {})
        )

        # self.dumper = import_string(mapping["dump"]["cls"])(
        #     **mapping["dump"].get("params", {}), meta_fields=meta_fields
        # )

        # Just in case, the list of jmespathes to extract some jmespathes.
        # digest.collections.*.path
        # digest.collections.*.entities[].*.keys[][]
        # digest.collections.*.entities[].*.properties.*.column[][]

from typing import Any, List, Dict, Union, Iterable, Callable, Generator, Optional
from itertools import islice, chain
import jmespath  # type: ignore


# We are utilizing here the fact that Model is a singletone and set up
# in the thebeast.conf.mapping
from followthemoney import model as ftm  # type: ignore
from followthemoney.types import registry  # type: ignore
from followthemoney.util import make_entity_id  # type: ignore
from followthemoney.schema import Schema  # type: ignore
from followthemoney.exc import InvalidData

from thebeast.contrib.ftm_ext.rigged_entity_proxy import RiggedEntityProxy
from thebeast.conf.utils import import_string
from thebeast.types import RedGreenEntity


ENTITY_TYPE = registry.get("entity")
CALLABLE_CACHE: Dict[str, Callable] = {}


def ensure_list(values: Any) -> List[Any]:
    """
    Wrap the value into the list if needed
    """
    if not isinstance(values, list):
        return [values]
    return values


def generate_pseudo_id(temporary_entity_id: str):
    """
    Generates pseudo id for the entity to fool FTM, which is going to be resolved later
    """
    return make_entity_id(temporary_entity_id, key_prefix="thebeast_temporary_entity_id")


def jmespath_results_as_array(path: str, record: Union[List, Dict]) -> List[Any]:
    """
    Extracts the values from the record according to the path, wraps everything into array
    """
    return ensure_list(jmespath.search(path, record) or [])


def resolve_entity_refs(entities: Iterable[Schema], context_entities: Dict[str, str]) -> Generator[Schema, None, None]:
    for entity in entities:
        for prop in entity.iterprops():
            if prop.type == ENTITY_TYPE:
                resolved_properties = []

                # TODO: errors (probably red/green sorting) for the properties that cannot be resolved
                for prop_val in entity.get(prop):
                    resolved_properties.append(prop_val.inject_meta_to_str(context_entities.get(prop_val)))

                entity.set(prop, resolved_properties)

        yield entity


def make_entity(schema: Union[str, Schema], key_prefix: Optional[str] = None) -> RiggedEntityProxy:
    """Instantiate an empty entity proxy of the given schema type."""

    return RiggedEntityProxy(ftm, {"schema": schema}, key_prefix=key_prefix)


def resolve_callable(fqfn: str) -> Callable:
    """
    Caching callables, resolved by fully qualified function name (fqfn)
    """
    if fqfn in CALLABLE_CACHE:
        return CALLABLE_CACHE[fqfn]

    func = import_string(fqfn)
    CALLABLE_CACHE[fqfn] = func

    return func


def chunks(iterable: Iterable, size: int) -> Iterable:
    """Generate adjacent chunks of data"""
    it = iter(iterable)
    return iter(lambda: tuple(islice(it, size)), ())


def flatten(list_of_lists: Iterable[Iterable]) -> Iterable:
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)


def inflate_entity(entity_dict: Dict) -> RiggedEntityProxy:
    return RiggedEntityProxy.from_dict(ftm, entity_dict)


def deflate_entity(entity: RiggedEntityProxy) -> RedGreenEntity:
    asdict: Dict = entity.to_dict()
    valid: bool = True

    if entity.id is None:
        valid = False
    else:
        try:
            entity.schema.validate(asdict)
        except InvalidData:
            valid = False

    return RedGreenEntity(payload=asdict, valid=valid)

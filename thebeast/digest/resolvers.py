import regex as re  # type: ignore
from typing import Optional, List, Dict, Union, Any, Callable, NewType
from dataclasses import dataclass


from jinja2 import Environment, BaseLoader, select_autoescape
from followthemoney.schema import Schema  # type: ignore
from thebeast.contrib.ftm_ext.rigged_entity_proxy import StrProxy

from .utils import (
    generate_pseudo_id,
    jmespath_results_as_array,
    resolve_callable,
    ensure_list,
)

# TODO: expose jmespath to templates as a filter?
jinja_env = Environment(loader=BaseLoader(), autoescape=select_autoescape())


@dataclass
class ResolveContext:
    record: Optional[Union[List, Dict]]
    property_values: List[StrProxy]
    entity: Optional[Schema]
    statements_meta: Optional[Dict[str, str]]
    variables: Optional[Dict[str, List[StrProxy]]]


CommandConfig = NewType("CommandConfig", Union[str, dict])


def _resolve_literal(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `literal` is simply a string or number constant used for FTM entity field
    """
    return context.property_values + [
        StrProxy(command_config, meta=context.statements_meta)
    ]


def _resolve_entity(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `entity` is a named reference to another entity available in the current context
    i.e as a constant entity or entity of the current collection and its parents
    For now we just adding the reference to the another entity and we'll resolve it later
    TODO: green/red validate if the property allows to reference to another entity
    i.e entity.schema.properties[property_name].type == entity
    TODO: we probably want to preserve the list of property names to resolve later on

    To fool the FTM we supply something that looks like entity ID which we can resolve later
    """

    return context.property_values + [
        StrProxy(generate_pseudo_id(command_config), meta=context.statements_meta)
    ]


def _resolve_column(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `column` is a jmespath applied at the current level of the doc
    to collect all the needed values for the field from it
    """

    return context.property_values + [
        StrProxy(val, meta=context.statements_meta)
        for val in jmespath_results_as_array(command_config, context.record)
    ]


def _resolve_regex_split(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `regex_split` is an optional regex splitter to extract multiple
    values for the entity field from the single string.
    """
    new_property_values: List[StrProxy] = []

    for property_value in context.property_values:
        new_property_values += [
            property_value.inject_meta_to_str(val)
            for val in re.split(command_config, str(property_value), flags=re.V1)
        ]

    return new_property_values


def _resolve_regex_first(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `regex_first` is an optional regex **matcher** to match the part of the extracted string
    and set it as a value for the entity field. It returns the first match
    """

    extracted_property_values: List[Any] = []

    for property_value in context.property_values:
        if not property_value:
            continue

        m = re.search(command_config, property_value, flags=re.V1)
        if m:
            if m.groups():
                # We support both, groups
                extracted_property_values.append(
                    property_value.inject_meta_to_str(m.group(1))
                )
            else:
                # And full match
                extracted_property_values.append(
                    property_value.inject_meta_to_str(m.group(0))
                )

    return extracted_property_values


def _resolve_regex(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `regex` is an optional regex **matcher** to match the part of the extracted string
    and set it as a value for the entity field. It returns the first match
    """

    extracted_property_values: List[Any] = []

    for property_value in context.property_values:
        if not property_value:
            continue

        extracted_property_values += [
            property_value.inject_meta_to_str(v)
            for v in re.findall(command_config, property_value, flags=re.V1)
        ]

    return extracted_property_values


def regex_replace_multiple(
    regex_list: list, replace_list: list, property_values: list
) -> List[StrProxy]:
    """
    `regex_list` is a list of regex expression to apply to input.
    `replace list` is a list of replacement strings, it MUST have length equal to `regex_list`.
    """

    extracted_property_values: List[Any] = []

    for property_value in property_values:
        if not property_value:
            continue

        string = property_value

        for regex, replace in zip(regex_list, replace_list):
            string = property_value.inject_meta_to_str(
                re.sub(regex, replace, string, flags=re.V1)
            )

        extracted_property_values += [string]

    return extracted_property_values


def _resolve_regex_replace(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `regex_replace` is an optional regex **replacer** to replace content of extracted string.

    It accepts a single regex or regex list, and a single replace value or list of replaces for each given regex.
    In case of single value, all regexes will be replaced with it. In other case, length of `replace` list must
    be equal to length of `regex` list, or ValueError will be thrown.

    fixme: can/should we validate both lengths in mapping_validator or keep it there?
    """

    extracted_property_values: List[Any] = []
    regex_list = command_config["regex"]
    replace = command_config["replace"]

    if not isinstance(regex_list, list):
        regex_list = [regex_list]

    if isinstance(replace, list):
        if len(replace) != len(regex_list):
            raise ValueError(
                "If 'replace' is an array, it must have same length as 'regex'"
            )
        else:
            return regex_replace_multiple(regex_list, replace, context.property_values)

    for property_value in context.property_values:
        if not property_value:
            continue

        for regex in regex_list:
            property_value = property_value.inject_meta_to_str(
                re.sub(regex, replace, property_value, flags=re.V1)
            )

        extracted_property_values += [property_value]

    return extracted_property_values


def _resolve_transformer(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `transformer` is a python function which (currently) accepts only a list of values
    applies some transform to it and returns the modified list. That list will be
    added to the entity instead of the original values
    """

    if isinstance(command_config, dict):
        fcfn: str = command_config["name"]
        params: dict = command_config.get("params", {})
    else:
        fcfn = command_config
        params = {}

    params_as_args = ", ".join(
        f"{param_name}={param_value}" for param_name, param_value in params.items()
    )

    transformer_signature = f"{fcfn}({params_as_args})"
    property_values = resolve_callable(fcfn)(context.property_values, **params)
    for property_value in property_values:
        property_value._meta = property_value._meta.set_field(
            "transformation", transformer_signature
        )

    return property_values


def _resolve_augmentor(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `augmentor` is a similar concept to the `transformer`, but modified list is added
    to the original values
    """

    return context.property_values + _resolve_transformer(command_config, context)


def _resolve_template(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `template` is a jinja template str that will be rendered using the context
    which contains current half-finished entity and original
    """
    template = jinja_env.from_string(command_config)
    return [
        StrProxy(
            template.render(
                entity=context.entity.properties,
                record=context.record,
                meta=context.statements_meta,
                property_value=property_value,
                variables=context.variables,
            ),
            meta=context.statements_meta,
        )
        for property_value in context.property_values or [StrProxy("")]
    ]


def _resolve_property(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `property` gets the property value from the current entity or $variable
    """

    if command_config.startswith("$") and context.variables is not None:
        return context.property_values + context.variables.get(command_config, [])
    elif context.entity is not None:
        return context.property_values + context.entity.get(command_config)


def _resolve_meta(
    command_config: CommandConfig, context: ResolveContext
) -> List[StrProxy]:
    """
    `meta` collects the meta information and sets it for the current property values
    """

    # TODO: DRY with "meta" in collection_config
    local_statements_meta: Dict[str, str] = {
        meta_name: "\n".join(
            resolve_meta_values(
                ensure_list(meta_config),
                record=context.record,
                statements_meta=context.statements_meta,
                entity=context.entity,
            )
        )
        for meta_name, meta_config in command_config.items()
    }

    for property_value in context.property_values:
        property_value._meta = property_value._meta._replace(**local_statements_meta)

    return context.property_values


def _resolve_configs(
    property_configs: List, commands_mapping: Dict[str, Callable], **kwargs
) -> List[StrProxy]:
    """
    A general function that applies all the command from the config to the kwargs
    """

    property_values: List[StrProxy] = []
    ctx = ResolveContext(property_values=property_values, **kwargs)

    for property_config in property_configs:
        curr_property_values: List[StrProxy] = []
        for command, command_config in property_config.items():
            if command in commands_mapping:
                ctx.property_values = curr_property_values
                curr_property_values = commands_mapping[command](
                    command_config=command_config, context=ctx
                )
            else:
                pass
                # TODO: signal to show our disrespect?

        property_values += curr_property_values

    return property_values


def resolve_property_values(
    property_configs: List,
    record: Union[List, Dict],
    entity: Schema,
    statements_meta: Dict[str, str],
    variables: List[StrProxy],
) -> List[StrProxy]:
    """
    A wrapper for _resolve_configs for the entity (all commands are supported)
    """
    return _resolve_configs(
        property_configs=property_configs,
        commands_mapping={
            "literal": _resolve_literal,
            "entity": _resolve_entity,
            "column": _resolve_column,
            "regex_split": _resolve_regex_split,
            "regex": _resolve_regex,
            "regex_first": _resolve_regex_first,
            "regex_replace": _resolve_regex_replace,
            "transformer": _resolve_transformer,
            "augmentor": _resolve_augmentor,
            "template": _resolve_template,
            "property": _resolve_property,
            "meta": _resolve_meta,
        },
        record=record,
        entity=entity,
        statements_meta=statements_meta,
        variables=variables,
    )


def resolve_meta_values(
    property_configs: List,
    record: Union[List, Dict],
    statements_meta: Dict[str, str],
    entity: Optional[Schema],
) -> List[StrProxy]:
    """
    A wrapper for _resolve_configs for the meta values on property level (everything except meta is allowed)
    """
    return _resolve_configs(
        property_configs=property_configs,
        commands_mapping={
            "literal": _resolve_literal,
            "column": _resolve_column,
            "regex_split": _resolve_regex_split,
            "regex": _resolve_regex,
            "regex_first": _resolve_regex_first,
            "regex_replace": _resolve_regex_replace,
            "transformer": _resolve_transformer,
            "augmentor": _resolve_augmentor,
            "property": _resolve_property,
            "template": _resolve_template,
        },
        record=record,
        statements_meta=statements_meta,
        entity=entity,
        variables=None,
    )


def resolve_collection_meta_values(
    property_configs: List, record: Union[List, Dict], statements_meta: Dict[str, str]
) -> List[StrProxy]:
    """
    A wrapper for _resolve_configs for the meta values on collection level
    (everything except meta and property is allowed)
    """
    return _resolve_configs(
        property_configs=property_configs,
        commands_mapping={
            "literal": _resolve_literal,
            "column": _resolve_column,
            "regex_split": _resolve_regex_split,
            "regex": _resolve_regex,
            "regex_first": _resolve_regex_first,
            "transformer": _resolve_transformer,
            "augmentor": _resolve_augmentor,
            "template": _resolve_template,
        },
        record=record,
        statements_meta=statements_meta,
        entity=None,
        variables=None,
    )


def resolve_constant_meta_values(property_configs: List) -> List[StrProxy]:
    """
    A wrapper to resolve meta values for statements on a dataset level (supports `literal` only)
    """
    return _resolve_configs(
        property_configs=property_configs,
        commands_mapping={
            "literal": _resolve_literal,
        },
        record=None,
        entity=None,
        statements_meta=None,
        variables=None,
    )

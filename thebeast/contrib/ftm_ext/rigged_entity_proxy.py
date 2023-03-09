from typing import Optional, Dict, Any, Union, NamedTuple, Mapping

from followthemoney.proxy import EntityProxy, P  # type: ignore
from followthemoney.util import value_list  # type: ignore
from copy import copy

from .meta_factory import get_meta_cls


class StrProxy(str):
    """
    Oh, that's truly a bread and butter class of everything. Or even a dough for the
    bread and milk for the butter.
    """

    def __new__(cls, content: Union[str, Any], meta: Optional[Union[Dict, NamedTuple]] = None):
        meta_cls = get_meta_cls()
        if isinstance(content, StrProxy):
            result = copy(content)
        else:
            result = str.__new__(cls, content)
            result._meta = meta_cls()

        if meta is not None:
            if isinstance(meta, Mapping):
                # TODO: quickly validate that all the meta provided is in the meta fields declared
                filtered_meta: Dict = {k: v for k, v in meta.items() if k in meta_cls._fields}
                result._meta = meta_cls(**filtered_meta)
            else:
                result._meta = meta

        return result

    def inject_meta_to_str(self, content: Optional[str]):
        if content is None:
            return None

        return StrProxy(content, self._meta)


class RiggedEntityProxy(EntityProxy):
    def add(
        self,
        prop: P,
        values: Any,
        cleaned: bool = False,
        quiet: bool = False,
        fuzzy: bool = False,
        format: Optional[str] = None,
    ) -> None:
        if not cleaned:
            prop_name = self._prop_name(prop, quiet=quiet)
            if prop_name is None:
                return None
            resolved_prop = self.schema.properties[prop_name]

            values = [
                StrProxy(value).inject_meta_to_str(
                    resolved_prop.type.clean(value, proxy=self, fuzzy=fuzzy, format=format)
                )
                for value in value_list(values)
            ]
            cleaned = True

        return super().add(prop, values, cleaned, quiet, fuzzy, format)

    def unsafe_add(
        self,
        prop: P,
        value: Optional[str],
        cleaned: bool = False,
        fuzzy: bool = False,
        format: Optional[str] = None,
    ) -> None:
        if not cleaned and value is not None:
            if isinstance(value, str):
                value = StrProxy(value)

            value = value.inject_meta_to_str(prop.type.clean_text(value, fuzzy=fuzzy, format=format, proxy=self))
            cleaned = True

        return super().unsafe_add(prop, value, cleaned, fuzzy, format)

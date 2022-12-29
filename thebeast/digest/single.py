from typing import Union, List, Dict, Generator, Iterable

from followthemoney.schema import Schema  # type: ignore

from .abstract import AbstractDigestor, main_cog


class SingleProcessDigestor(AbstractDigestor):
    """
    TODO: review an architecture once it works
    """

    def run_the_cog(
        self,
        records: Iterable[Union[List, Dict]],
        parent_context_entities_map: Dict[str, str],
        statements_meta: Dict[str, str],
    ) -> Generator[Schema, None, None]:
        for record in records:
            for entity in main_cog(
                data=record,
                config=self.mapping_config,
                parent_context_entities_map=parent_context_entities_map,
                statements_meta=statements_meta,
                parent_record=None,
            ):
                # TODO: green/red sorting for valid records/exceptions here?
                yield entity

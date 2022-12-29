from typing import Union, List, Dict, Generator, Iterable, Any
from multiprocessing import Pool, cpu_count
from followthemoney.schema import Schema  # type: ignore

from .abstract import AbstractDigestor, main_cog

from .utils import flatten, inflate_entity

main_cog_ctx: Dict[str, Any]

# task executed in a worker process
def task(record: Union[Dict, List]) -> List[Schema]:
    # declare global variable
    global main_cog_ctx

    return list(
        main_cog(
            data=record,
            config=main_cog_ctx["mapping_config"],
            parent_context_entities_map=main_cog_ctx["parent_context_entities_map"],
            statements_meta=main_cog_ctx["statements_meta"],
            parent_record=None,
        )
    )


# initialize a worker in the process pool
def worker_init(
    mapping_config: Dict,
    parent_context_entities_map: Dict[str, str],
    statements_meta: Dict[str, str],
    meta_fields: List[str],
) -> None:
    # declare global variable
    global main_cog_ctx
    from thebeast.contrib.ftm_ext.meta_factory import get_meta_cls

    get_meta_cls(meta_fields)

    # assign the global variable
    main_cog_ctx = {
        "mapping_config": mapping_config,
        "parent_context_entities_map": parent_context_entities_map,
        "statements_meta": statements_meta,
    }


class MultiProcessDigestor(AbstractDigestor):
    """
    TODO: review an architecture once it works
    """

    def __init__(self, mapping_config: Dict, meta_fields: List[str], batch_size: int = 1, processes: int = -1) -> None:
        """
        processes: the number of processes to launch in the pool
        batch_size: the number of the records to throw into the pool
        """
        super().__init__(mapping_config=mapping_config, meta_fields=meta_fields)

        self.processes: int = processes

        # TODO: use it or remove it
        self.batch_size: int = batch_size
        if self.processes == -1:
            self.processes = cpu_count()

    def run_the_cog(
        self,
        records: Iterable[Union[List, Dict]],
        parent_context_entities_map: Dict[str, str],
        statements_meta: Dict[str, str],
    ) -> Generator[Schema, None, None]:
        # Now for the really fun part: real entities with multiprocessing
        with Pool(
            self.processes,
            initializer=worker_init,
            initargs=(self.mapping_config, parent_context_entities_map, statements_meta, self.meta_fields),
        ) as da_pool:
            for entity in flatten(da_pool.imap(func=task, iterable=records, chunksize=self.batch_size)):
                yield inflate_entity(entity)

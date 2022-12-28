from typing import Union, List, Dict, Generator, Iterable
from multiprocessing import Pool, cpu_count
from followthemoney.schema import Schema  # type: ignore


from .single import generate_pseudo_id, resolve_entity_refs, ensure_list, make_entities, main_cog

from .utils import chunks
from .resolvers import resolve_constant_meta_values


# # Solution to pass lambdas to multiprocessing
# # https://medium.com/@yasufumy/python-multiprocessing-c6d54107dd55
# _func = None


# def worker_init(func):
#     global _func
#     _func = func


# def worker(x):
#     return _func(x)


# task executed in a worker process
def task(record):
    # declare global variable
    global custom_data
    # report a message with global variable
    print(f"Worker executing with: {custom_data}", flush=True)
    # block for a moment

    for ent in main_cog(
        data=record,
        config=custom_data["mapping_config"],
        parent_context_entities=custom_data["context_entities"],
        statements_meta=custom_data["statements_meta"],
        parent_record=None,
    ):
        yield ent


# initialize a worker in the process pool
def worker_init(
    config,
    parent_context_entities,
    statements_meta,
    parent_record,
):
    # declare global variable
    global custom_data
    # assign the global variable
    custom_data = {
        "config": config,
        "parent_context_entities": parent_context_entities,
        "statements_meta": statements_meta,
        "parent_record": parent_record,
    }
    # report a message
    print(f"Initializing worker with: {custom_data}", flush=True)


class MultiProcessDigestor:
    """
    TODO: review an architecture once it works
    """

    def __init__(self, mapping_config: Dict, batch_size: int = 100, processes: int = -1) -> None:
        """
        processes: the number of processes to launch in the pool
        batch_size: the number of the records to throw into the pool
        """

        self.processes: int = processes
        self.batch_size: int = batch_size
        if self.processes == -1:
            self.processes = cpu_count()

        self.mapping_config: Dict = mapping_config

    def extract(self, records: Iterable[Union[List, Dict]]) -> Generator[Schema, None, None]:
        # Preparation steps are single-threaded

        # First let's get some global level meta values for our statements
        statements_meta: Dict[str, str] = {
            statement_meta_name: "\n".join(resolve_constant_meta_values(ensure_list(statement_meta_config)))
            for statement_meta_name, statement_meta_config in self.mapping_config.get("meta", {}).items()
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

        # Now for the really fun part: real entities with multiprocessing

        with Pool(
            self.processes,
            initializer=worker_init,
            initargs=(
                self.mapping_config,
                context_entities,
                statements_meta,
                None,
            ),
        ) as da_pool:
            for entity in da_pool.imap(func=task, iterable=records, chunksize=self.batch_size):
                # for entity in main_cog(
                #     data=record,
                #     config=self.mapping_config,
                #     parent_context_entities=context_entities,
                #     statements_meta=statements_meta,
                #     parent_record=None,
                # ):
                yield entity

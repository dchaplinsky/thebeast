import yaml
import tempfile
import argparse
from random import random
from collections import Counter, defaultdict
from pathlib import Path

from tqdm import tqdm

from thebeast.conf.mapping import SourceMapping

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sample records from a mapping file and export them as entities"
    )
    parser.add_argument("mapping_file", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument(
        "--fraction", type=float, default=0.001, help="Fraction of records to sample"
    )
    args = parser.parse_args()
    # Read the YAML file
    with args.mapping_file.open("r", encoding="utf-8") as f:
        mapping_data = yaml.safe_load(f)

    # Replace the dump.cls with the desired value
    mapping_data["dump"]["cls"] = "thebeast.dump.FTMLinesWriter"
    if "params" in mapping_data["dump"]:
        if "meta_for_stmt_id" in mapping_data["dump"]["params"]:
            del mapping_data["dump"]["params"]["meta_for_stmt_id"]

    # Save the modified YAML to a temporary file
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=".yaml", mode="wt"
    ) as temp_file:
        yaml.dump(mapping_data, temp_file, allow_unicode=True)
        temp_file.flush()
        temp_mapping_file = Path(temp_file.name)

        mapping = SourceMapping(
            temp_mapping_file,
            dump_overrides={
                "output_uri": str(args.output_file),
            },
        )

    records = tqdm(mapping.ingestor, desc="Records in")
    stats = {
        "entities_count": Counter(),
        "entities_by_schema": Counter(),
        "fields_count": Counter(),
        "total_records": 0,
        "total_entities": 0,
        "field_values": defaultdict(Counter),
    }

    def entity_generator():
        global stats
        for record in filter(lambda x: random() < args.fraction, records):
            stats["total_records"] += 1
            entities = list(mapping.digestor.extract([record]))

            stats["entities_count"].update([len(entities)])

            for entity in entities:
                stats["total_entities"] += 1
                stats["entities_by_schema"].update([entity.payload["schema"]])
                for field in entity.payload["properties"]:
                    stats["fields_count"].update(
                        [f"{entity.payload['schema']}.{field}"]
                    )
                    stats["field_values"][f"{entity.payload['schema']}.{field}"].update(
                        entity.payload["properties"][field]
                    )

                yield entity

    mapping.dumper.write_entities(entity_generator())

    if stats["total_records"]:
        print(f"Total records: {stats['total_records']}")
        print(f"Total entities: {stats['total_entities']}")
        print(
            f"Average entities per record: {stats['total_entities'] / stats['total_records']}"
        )

        print("\n\nEntities count per record:")
        for count, entities in stats["entities_count"].most_common():
            print(f"\t{count} entities: {entities}")

        print("\n\nEntities by schema:")
        for schema, count in stats["entities_by_schema"].most_common():
            print(f"\t{schema}: {count} (per record: {count / stats['total_records']})")

        print("\n\nFields count:")
        for field, count in stats["fields_count"].most_common():
            schema, _ = field.split(".")
            print(
                f"\t{field}: {count} (per entity: {round(count / stats['entities_by_schema'][schema], 2)})"
            )

        print("\n\nField values (top-10):")
        for field, values in stats["field_values"].items():
            print(f"\t{field}: ")
            for value, count in values.most_common(10):
                print(f"\t\t{value}: {count}")
    else:
        print("No records found")

    mapping.dumper.close()

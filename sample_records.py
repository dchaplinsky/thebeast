import yaml
import tempfile
import argparse
from random import random
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

    mapping.dumper.write_entities(
        tqdm(
            mapping.digestor.extract(
                filter(lambda x: random() < args.fraction, records)
            ),
            desc="Entities out",
        )
    )

    mapping.dumper.close()

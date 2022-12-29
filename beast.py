from pathlib import Path
from thebeast.conf.mapping import SourceMapping
from tqdm import tqdm
import sys

if __name__ == "__main__":
    mapping = SourceMapping(Path("thebeast/tests/sample/mappings/ukrainian_mps_multithreaded.yaml"))

    mapping.dumper.write_entities(
        tqdm(mapping.digestor.extract(tqdm(mapping.ingestor, desc="Records in")), desc="Entities out")
    )

    mapping.dumper.close()

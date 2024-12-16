from pathlib import Path
from thebeast.conf.mapping import SourceMapping
from tqdm import tqdm
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No mapping yaml is provided in script arguments")
        sys.exit(0)

    mapping = SourceMapping(Path(sys.argv[1]))

    mapping.dumper.write_entities(
        tqdm(
            mapping.digestor.extract(tqdm(mapping.ingestor, desc="Records in")),
            desc="Entities out",
        )
    )

    mapping.dumper.close()

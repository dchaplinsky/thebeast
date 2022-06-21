from pathlib import Path
from thebeast.conf.mapping import SourceMapping

if __name__ == '__main__':
    mapping = SourceMapping(Path("thebeast/tests/sample/mappings/ukrainian_mps.yaml"))
    mapping.dumper.write_entities(mapping.digestor.extract(mapping.ingestor))

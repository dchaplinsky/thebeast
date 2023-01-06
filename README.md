# The Beast

The beast is an experimental, flexible, declarative-oriented toolkit to read
machinereadable data from the various sources and transform them into follow the money entities.

Do not rely on this one until it is out of alpha. Everything is very volatile 


## More reading
The FTM proposal:
https://github.com/alephdata/followthemoney/issues/717

The sample mapping with tons of comments to make you understand an idea better (beware, it's just an example, format is the subject to change):
https://github.com/dchaplinsky/thebeast/blob/main/thebeast/tests/sample/mappings/ukrainian_mps.yaml

Validator for the mappings in [json schema](https://json-schema.org) format (again, work in progress and tons of comments):
https://github.com/dchaplinsky/thebeast/blob/main/thebeast/conf/mapping_validator.json

First proposal of the mapping (obsolete, but can give you a better idea)
https://gist.github.com/dchaplinsky/8021b530ea7e44c9443afcc3318042fd


## Current status
- [x] Basic ingest for json/jsonlines/csv, both local and remote, compressed or not, singular or multiple files
- [x] Tests for the basic ingest
- [ ] Ingest from databases (mongo, postgres)
- [ ] Tests for the databases ingest
- [x] Mapping reader
- [x] Tests for mapping reader
- [x] Basic digest routines
- [x] Tests for basic digest routines
- [x] Advanced ingest routines: constant entities (think Country or Organization)
- [x] Advanced ingest routines: backreferencing (think talking from subcollections to parent items)
- [x] Advanced ingest routines: nested collections (think parsing involved JSON)
- [x] Advanced ingest routines: templates (think combining fields when setting the entity field)
- [x] Advanced ingest routines: multiple values for the entity property
- [x] Advanced ingest routines: split string into multiple values
- [x] Advanced ingest routines: full entity validation and red/green sorting
- [ ] Advanced ingest routines: regex validation to discard values that do not pass the test?
- [X] Advanced ingest routines: augmentations/transformations
- [X] Advanced ingest routines: records transformations
- [X] Tests for records transformations
- [X] Tests for the individual resolvers
- [ ] Tests for the resolver wrappers
- [X] Tests for digest routines
- [X] Advanced digest routines: multiprocessing
- [X] Tests for advanced digest routines
- [ ] Basic CLI
- [x] Basic dump routines (stdout/files)
- [x] Basic dump routines: statements
- [x] Tests for basic dump routines
- [X] Tests for basic dump routines: statements
- [x] Remove inflate/deflate and pass dicts rather than entities between digest and dump
- [x] Python 3.11 support (https://github.com/dchaplinsky/thebeast/actions/runs/3802499820/jobs/6468041810, https://github.com/ICRAR/ijson/issues/80)

## Running tests

```bash

pip install -r requirements.txt
python -m pytest
```

## Run using Docker

`/bin/` directory contains scripts to run Beast inside Docker container.

Use `/bin/run data/mapping.yaml` to run Beast with selected mapping. 
Note: mapping and source file(s) must be in Beast root (sub-)directory. E.g. `./data/mapping.yaml`
You can't point Beast to a file outside it's root directory.

Use `/bin/tests` to run tests.

Use `/bin/black` to run [black](https://github.com/psf/black) to format source files before contributing a pull request.

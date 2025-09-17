# The Beast

The Beast is an experimental, flexible, declarative-oriented toolkit to read
machine-readable data from the various sources and transform them into follow-the-money entities (FTM).

~~Do not rely on this one until it is out of alpha. Everything is very volatile.~~

The Beast is currently in beta and is quite stable. While we can foresee some changes to the mapping format to allow for better flexibility, we are slow to implement them, and we are cautious.

The Beast is battle-tested. Complete documentation is available [here](docs/README.md).



## More reading
The FTM proposal:
https://github.com/alephdata/followthemoney/issues/717

The sample mapping with tons of comments to make you understand an idea better (beware, it's just an example, format is subject to change):
https://github.com/dchaplinsky/thebeast/blob/main/thebeast/tests/sample/mappings/ukrainian_mps.yaml

Validator for the mappings in [JSON schema](https://json-schema.org) format (again, work in progress and tons of comments):
https://github.com/dchaplinsky/thebeast/blob/main/thebeast/conf/mapping_validator.json

First proposal of the mapping (obsolete, but can give you a better idea)
https://gist.github.com/dchaplinsky/8021b530ea7e44c9443afcc3318042fd


## Current status

### High priority
- [ ] Ingest from databases (mongo, postgres) using SQLAlchemy or PeeWee
- [ ] Tests for the databases ingest
- [ ] Basic CLI
- [ ] Signals on exceptions and policy for the incorrectly parsed entity values (drop, drop all, drop entity, reraise)
- [ ] Tests for the signals
- [ ] Stats collector (number of signals of each type, number of invalid entities, etc)
- [ ] Packaging (partially done in `packaging_and_spark_integration` branch)
- [ ] Documentation (@legless, your notes will be very valuable)


### Low priority
- [ ] Advanced ingest routines: regex validation to discard values that do not pass the test?
- [ ] Tests for the resolver wrappers


Done
- [x] Basic ingest for json/jsonlines/csv, both local and remote, compressed or not, singular or multiple files
- [x] Tests for the basic ingest
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
- [X] Advanced ingest routines: augmentations/transformations
- [X] Advanced ingest routines: record transformations
- [X] Tests for record transformations
- [X] Tests for the individual resolvers
- [X] Tests for digest routines
- [X] Advanced digest routines: multiprocessing
- [X] Tests for advanced digest routines
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

The `/bin/` directory contains scripts to run Beast inside a Docker container.

Use `/bin/run data/mapping.yaml` to run Beast with selected mapping. 
Note: mapping and source file(s) must be in the Beast root (sub-)directory. E.g. `./data/mapping.yaml`
You can't point Beast to a file outside its root directory.

Use `/bin/tests` to run tests.

Use `/bin/black` to run [black](https://github.com/psf/black) to format source files before contributing a pull request.

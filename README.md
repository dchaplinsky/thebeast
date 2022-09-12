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
- [ ] Advanced ingest routines: nested collections (think parsing involved JSON)
- [x] Advanced ingest routines: templates (think combining fields when setting the entity field)
- [x] Advanced ingest routines: multiple values for the entity property
- [x] Advanced ingest routines: split string into multiple values
- [ ] Advanced ingest routines: full entity validation with jsonschema and red/green sorting
- [ ] Advanced ingest routines: regex validation to discard values that do not pass the test?
- [X] Advanced ingest routines: augmentations/transformations
- [X] Advanced ingest routines: records transformations
- [X] Tests for records transformations
- [X] Tests for the individual resolvers
- [ ] Tests for the resolver wrappers
- [ ] Tests for digest routines
- [ ] Advanced ingest routines: multiprocessing
- [ ] Tests for advanced digest routines
- [ ] Basic CLI
- [x] Basic dump routines (stdout)
- [ ] Basic dump routines: statements
- [x] Tests for basic dump routines

## Running tests

```bash

pip install -r requirements.txt
python -m pytest
```

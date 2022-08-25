# The Beast

The beast is an experimental, flexible, declarative-oriented toolkit to read
machinereadable data from the various sources and transform them into follow the money entities.

Do not rely on this one until it is out of alpha. Everything is very volatile 


## More reading
The FTM proposal:
https://github.com/alephdata/followthemoney/issues/717

The sample mapping with tons of comments to make you understand an idea better (beware, it's just an example, format is the subject to change):
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
- [ ] Advanced ingest routines: backreferencing (think talking from subcollections to parent items)
- [ ] Advanced ingest routines: nested collections (think parsing involved JSON)
- [x] Advanced ingest routines: templates (think combining fields when setting the entity field)
- [x] Advanced ingest routines: multiple values for the entity property
- [ ] Advanced ingest routines: multiprocessing
- [ ] Tests for advanced digest routines
- [ ] Basic CLI
- [x] Basic dump routines (stdout)
- [x] Tests for basic dump routines

## Running tests

```bash

pip install -r requirements.txt
python -m pytest
```

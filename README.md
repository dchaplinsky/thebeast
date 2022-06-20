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
- [ ] Mapping reader
- [ ] Tests for mapping reader
- [ ] Basic digest routines
- [ ] Tests for basic digest routines
- [ ] Basic dump routines (stdout)
- [ ] Tests for basic dump routines

## Running tests

```bash

pip install -r requirements.txt
python -m pytest
```

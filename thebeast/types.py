from collections import namedtuple

# A thin wrapper on each record in the input collection. A main transport between ingest and digest
Record: type = namedtuple("Record", ["payload", "record_no", "input_uri"], defaults=[None, None])

# Again, a thin wrapper on top of the serialized entity
# Just like Record is a main transport between ingest and digest, RedGreenEntity is a
# transport between digest and dump
RedGreenEntity: type = namedtuple("RedGreenEntity", ["payload", "valid"])

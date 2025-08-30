# Beast Mapping Format – Comprehensive Guide & Examples

**Version:** 1.0 • **Date:** 2025‑08‑30  • **Audience:** Data engineers & OSINT practitioners using *the beast* to generate FollowTheMoney (FtM) entities and statement streams.

---

## 1) What is a “mapping” in Beast?

A Beast **mapping** is a declarative YAML file that tells the platform how to:

1. **Ingest** source data (CSV/JSON/SQL/etc.).
2. **Digest** the records into FtM **entities** (and relationships) using JMESPath & Jinja, plus optional Python helpers.
3. **Dump** (emit) either *entities* or *statements* (tabular rows describing each property value + its metadata).

Mappings are self‑contained and portable: they specify the extractor, the transformation graph, optional constant entities, and how to export results.

---

## 2) Anatomy of a mapping file

At the top level a mapping has these sections:

```yaml
id: my_dataset_v1            # Optional but recommended
info:                        # Optional provenance for the mapping itself
  author: ACME Lab
  maintainer: ops@acme.example
  created: 2025-08-30
  comments: First import of ACME directors

import:                      # Optional: Python packages or contrib modules to import
  - my_project.contrib.cleaning

ftm_ontology: ./ontology     # Optional path to a custom FtM model directory

meta:                        # Optional whitelist of statement metadata fields permitted in this mapping
  - dataset
  - origin
  - lang
  - first_seen
  - last_seen

ingest:                      # REQUIRED: how to read the source
  cls: my_pkg.ingest.CSVIngestor
  params:
    input_uri: s3://acme-bucket/inputs/companies.csv
    input_encoding: utf-8

digest:                      # REQUIRED: how to turn records into entities/statements
  cls: thebeast.digest.SingleProcessDigestor
  meta:                      # dataset‑level statement metadata applied to all collections
    dataset:
      literal: ACME_COMPANIES
    origin:
      literal: companies.csv

  constant_entities:         # Optional: entities to generate irrespective of the input rows
    acme_org:
      schema: Organization
      keys: ["ACME"]
      properties:
        name: { literal: "ACME, Inc." }
        jurisdiction: { literal: "US" }

  collections:               # REQUIRED: one or more collections
    companies:               # developer-chosen name
      path: records[*]       # JMESPath from the current context
      meta:                  # collection‑level statement metadata
        lang: { literal: "en" }

      # You can nest sub‑collections when the input is hierarchical
      # collections: { ... }

      record_transformer: my_project.contrib.row_fixups.normalize_company_row

      entities:              # REQUIRED: entity blueprints produced for each row
        company:
          schema: Company
          keys: [id, name]   # values must be available from the row after any record_transformer
          properties:
            name:       { column: name }
            alias:      { column: alt_names, split_regex: "[;,]" }
            address:    { column: address }
            incorporationDate: { column: incorporation_date, regex_first: "(\\d{4}-\\d{2}-\\d{2})" }
            jurisdiction: { literal: US }
            # property-level metadata (overrides collection/dataset levels for these statements)
            sourceUrl:
              template: "https://registry.acme.example/company/{{ id }}"
              meta:
                origin: { literal: "acme_registry_link" }

        membership:
          schema: Directorship
          keys: [id, director_name]
          properties:
            organization: { entity: company }
            director:
              template: "{{ director_name }}"
              # demonstrate transformation chaining
              transformer:
                name: my_project.contrib.cleaning.person_name
                params: { allow_suffixes: true }
```

### 2.1 Top‑level fields

* **`id`**: a human/ops identifier for the mapping instance.
* **`info`**: free‑form provenance for the *mapping file* (author, created/modified, comments, maintainer).
* **`import`**: modules that register transformers/augmentors or Jinja helpers.
* **`ftm_ontology`**: filesystem path to a custom FtM model (use when extending or constraining the standard ontology).
* **`meta`**: optional list *whitelisting* metadata keys permitted on statements. If omitted, Beast falls back to its internal default set.

### 2.2 `ingest`

* **`cls` (FQCN)**: the ingestor class (must subclass Beast’s `AbstractIngestor`).
* **`params`**: class‑specific parameters. Common ones:

  * `input_uri`: file path/URL/stream locator
  * `input_encoding`: text encoding for line‑based inputs

### 2.3 `digest`

* **`cls` (FQCN)**: the digestor class. Default is `thebeast.digest.SingleProcessDigestor`.
* **`meta`**: dataset‑level **statement** metadata to apply everywhere (overridden by collection/property meta when present).
* **`constant_entities`**: a map of *always‑present* entities (e.g., a source Organization, Publisher, Dataset). Each item has:

  * `schema`: FtM schema name
  * `keys`: list of key fields (strings or literals)
  * `properties`: a map where each property is either a single `constant_property` or a list of them; use:

    * `literal`: a fixed string/number
    * `entity`: link to another entity defined in the current mapping context
* **`collections`**: one or many sources of records to be mapped into entities.

### 2.4 Collections

**Collections** describe how to traverse an input structure and which entities to make from each element:

| Field                | Purpose                                                                                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `path`               | A **JMESPath** expression selecting an array/iterable of records from the current JSON‑like context.                                                                                             |
| `record_transformer` | Optional Python **FQFN** or `{name, params}` object. Runs once per record to pre‑shape it (e.g., parse semi‑structured text, normalize codes). Use it for logic that exceeds mapping primitives. |
| `meta`               | Constant **statement metadata** that apply to all properties emitted from this collection.                                                                                                       |
| `collections`        | Optional nested collections when a row contains subordinate lists.                                                                                                                               |
| `entities`           | Entity blueprints to emit per record.                                                                                                                                                            |

---

## 3) Defining entities

Each entity includes:

| Field        | Purpose                                                                                                                                   |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `schema`     | FtM schema name (e.g., `Person`, `Company`, `Ownership`, `Membership`).                                                                   |
| `keys`       | A **list of strings** that are combined to form a stable entity ID. Choose enough fields to avoid collisions.                             |
| `properties` | A mapping where *order matters*: each item is a **property pipeline** (one or more steps) that extracts and optionally transforms values. |

> **Key design tip.** Prefer domain identifiers (registration numbers, full names + birthDate) over display names. For event/relationship schemas (e.g., `Ownership`, `Directorship`, `Membership`), keys are usually a product of the participant keys (e.g., `owner_id` + `asset_id`).

---

## 4) Property pipelines (extraction & transformation)

A property definition is an ordered list (or a single step) of **operations** applied to the current record. Valid operations:

| Operation                               | What it does                                                                                    | Typical use                                                                     |                                                                   |                                       |
| --------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------- |
| `column: <jmespath>`                    | Extract values from the current record via JMESPath. Returns a scalar or list.                  | `column: name`, `column: emails[*]`.                                            |                                                                   |                                       |
| `literal: <str\|number>`                                                                                       | Emit a fixed value.                                                             | `jurisdiction: { literal: "UA"}`.                                |                                       |
| `template: <Jinja2>`                    | Render a string using Jinja2. Inputs can reference fields from the current record/context.      | `template: "{{ first }} {{ last }}"`.                                           |                                                                   |                                       |
| `entity: <name>`                        | Link to another entity defined in the **current mapping context**.                              | In `Ownership.asset`, reference the `company` entity created from the same row. |                                                                   |                                       |
| `property: <name>`                      | Re‑use a value already produced for another property of the **current entity** (or a variable). | Re‑emit `name` as `alias` with modifications.                                   |                                                                   |                                       |
| `regex: <re>`                           | Keep **all matches** of the pattern from each extracted value.                                  | Pull dates/IDs embedded in free text.                                           |                                                                   |                                       |
| `regex_first: <re>`                     | Keep the **first match** only.                                                                  | Extract YYYY‑MM‑DD from a messy field.                                          |                                                                   |                                       |
| `regex_replace: { regex: <re>\|[...], replace: <str>\|[...] }`                                                                      | Replace substrings using one or multiple regex→replacement pairs. | Strip prefixes, normalize whitespace. |
| `split_regex: <re>`                     | Split a string into multiple values.                                                            | Turn `"a; b, c"` into `a`, `b`, `c`.                                            |                                                                   |                                       |
| `transformer: <FQFN or {name, params}>` | Apply a Python function **to the list of string values** and replace with the result.           | Name cleanup, ISO‐date parsing.                                                 |                                                                   |                                       |
| `augmentor: <FQFN or {name, params}>`   | Like `transformer`, but **append** its result to the current list instead of replacing it.      | Add derived aliases without losing originals.                                   |                                                                   |                                       |
| `meta: {...}`                           | Attach **statement metadata** for the values emitted by this property.                          | Flag `sourceUrl` statements with a special origin.                              |                                                                   |                                       |

> **Ordering matters.** Steps are executed in the order written. For example, you might `column → regex_replace → split_regex → transformer`.

---

## 5) Statement metadata (provenance & context)

Beast lets you attach metadata to **each emitted value** (statement). Metadata can be set at three levels, with the usual specificity rules:

1. **Dataset‑level**: `digest.meta` – applies everywhere unless overridden.
2. **Collection‑level**: `digest.collections.<name>.meta` – overrides dataset level for that collection.
3. **Property‑level**: `...properties.<prop>.meta` – overrides collection & dataset for those values.

Typical metadata keys: `dataset`, `origin`, `lang`, `first_seen`, `last_seen`, `canonical_id`, etc. The optional top‑level `meta:` list acts as a **whitelist** of allowed metadata keys for this mapping.

---

## 6) Dumping (where results go)

The `dump` section controls the output sink:

```yaml
dump:
  cls: my_pkg.dump.StatementsJSONLDumper   # or another Dumper subclass
  params:
    output_uri: s3://acme-bucket/exports/acme_statements.jsonl
    error_uri:  /dev/null                  # where to write malformed entities/statements
```

Different dumpers may emit FtM **entities** or **statement streams** (JSONL/CSV/DB). Use a statements‑capable dumper when you need per‑value metadata and downstream statement‑based aggregation.

---

## 7) End‑to‑end examples

### 7.1 Minimal: CSV → Persons

**Input (CSV)**

```csv
id,first,last,birth,emails
1,Olena,Shevchenko,1981-05-20,olena@example.org;osh@example.com
2,Andriy,Melnyk,1979-07-01,
```

**Mapping (excerpt)**

```yaml
ingest:
  cls: my_pkg.ingest.CSVIngestor
  params: { input_uri: ./people.csv }

digest:
  cls: thebeast.digest.SingleProcessDigestor
  meta:
    dataset: { literal: PEOPLE_SAMPLE }

  collections:
    persons:
      path: records[*]
      entities:
        person:
          schema: Person
          keys: [id, birth]
          properties:
            name:       { template: "{{ first }} {{ last }}" }
            birthDate:  { column: birth }
            email:      { column: emails, split_regex: "[;,]" }
```

**What gets emitted (statements, conceptual)**

```
entity_id=md5("1|1981-05-20"), schema=Person, prop=name,       value="Olena Shevchenko", dataset=PEOPLE_SAMPLE
entity_id=md5("1|1981-05-20"), schema=Person, prop=birthDate,  value=1981-05-20,        dataset=PEOPLE_SAMPLE
entity_id=md5("1|1981-05-20"), schema=Person, prop=email,      value=olena@example.org, dataset=PEOPLE_SAMPLE
entity_id=md5("1|1981-05-20"), schema=Person, prop=email,      value=osh@example.com,   dataset=PEOPLE_SAMPLE
```

### 7.2 Relationships: Company ↔ Director (Directorship)

**Input (JSON)**

```json
{
  "companies": [
    {"id": "C-101", "name": "Rivne Steel", "director": "Vasyl Popov"},
    {"id": "C-102", "name": "Lviv Electronics", "director": "Olena Shevchenko"}
  ]
}
```

**Mapping (excerpt)**

```yaml
collections:
  companies:
    path: companies[*]
    entities:
      company:
        schema: Company
        keys: [id]
        properties:
          name: { column: name }

      director:
        schema: Person
        keys: [director]
        properties:
          name: { column: director }

      directorship:
        schema: Directorship
        keys: [id, director]
        properties:
          organization: { entity: company }
          director:     { entity: director }
          role:         { literal: director }
```

This produces three entities per row: the `Company`, a `Person`, and a `Directorship` linking them via `entity:` references.

### 7.3 Cleaning & enrichment pipeline

**Goal:** Normalize company names, split aliases, attach a source URL with property‑level metadata, and add a constant publisher entity.

**Mapping (excerpt)**

```yaml
digest:
  meta:
    dataset: { literal: UA_COMPANY_REGISTER }
  constant_entities:
    publisher:
      schema: Organization
      keys: ["UA_STATE_REGISTER"]
      properties:
        name: { literal: "Ukrainian State Register" }
        country: { literal: UA }

  collections:
    companies:
      path: records[*]
      meta: { lang: { literal: "ukr" } }
      record_transformer:
        name: my_project.contrib.rows.parse_dates
        params: { fields: ["incorporationDate"] }

      entities:
        org:
          schema: Company
          keys: [registrationNumber]
          properties:
            name:
              column: name_raw
              regex_replace:
                regex: ["^ТОВ\\s+", "\\s+ЛТД$"]
                replace: ["", ""]
              transformer: my_project.contrib.cleaning.squeeze_whitespace
            alias: { column: alt_names, split_regex: ";|,|\\|" }
            registrationNumber: { column: reg_no }
            sourceUrl:
              template: "https://usr.minjust.gov.ua/company/{{ reg_no }}"
              meta:
                origin: { literal: "minjust" }

        entry:
          schema: Publisher
          keys: ["UA_STATE_REGISTER"]
          properties:
            publisher: { entity: publisher }
            subject:   { entity: org }
```

---

## 8) Record transformers vs. property transformers

* **`record_transformer`** runs **once per row**, returning a modified row used by *all* property pipelines for that row. Use it for heavy logic (parsing, joining, classification).
* **`transformer` / `augmentor`** run inside a **single property pipeline** on the list of values extracted so far.

**Example:**

```yaml
record_transformer: my_project.contrib.rows.parse_person_name
# returns: { first: "Vasyl", last: "Popov", birth: "1979-07-01", ... }

properties:
  name:
    template: "{{ first }} {{ last }}"
  weakAlias:
    property: name
    augmentor: my_project.contrib.name.to_latin_translit
```

---

## 9) Nested collections

If a row has nested arrays, you can descend and emit related entities from a child **collection**.

```yaml
collections:
  filings:
    path: companies[*]
    entities:
      company:
        schema: Company
        keys: [id]
        properties: { name: { column: name } }
    collections:
      events:
        path: filings[*]
        entities:
          filing:
            schema: Ownership
            keys: [parent_id, id]
            properties:
              owner: { entity: company }
              asset: { column: asset_entity_id } # could come from another named entity in this nested context
              role:  { column: role }
```

---

## 10) Statement output (tabular semantics)

When using a statements‑enabled dumper, Beast emits one row **per property value** with columns like:

* `entity_id`, `schema`, `prop`, `prop_type`, `value`, `original_value`, `lang`
* `dataset`, `origin`
* `first_seen`, `last_seen`
* `canonical_id`, `external`

Your mapping controls most of these via entity schemas, property pipelines, and the `meta` layers.

---

## 11) Validation & linting

Beast validates mappings against its JSON Schema before execution. You can also lint a mapping in CI using any JSON Schema validator. Minimal Python example:

```python
from pathlib import Path
import yaml, json
from jsonschema import validate

schema = json.loads(Path("./mapping_validator.json").read_text())
instance = yaml.safe_load(Path("./my_mapping.yaml").read_text())
validate(instance=instance, schema=schema)
print("OK: mapping validates.")
```

**Common validation issues & remedies**

* *Unknown field under `properties`*: use only the operations listed in §4.
* *Missing `path`/`entities` in a collection*: both are required.
* *Wrong FQCN/FQFN pattern*: classes/functions must be fully qualified.

---

## 12) Practical tips & patterns

* **Choose good keys**: combine stable identifiers; for events use participant keys.
* **Normalize early**: simple regex/transformers in the mapping reduce downstream cleaning.
* **Prefer `split_regex` over ad‑hoc splitting** so you can keep it declarative.
* **Use `constant_entities`** for sources/publishers/datasets to keep provenance explicit and re‑linkable.
* **Layer metadata** thoughtfully: dataset → collection → property.
* **Keep transformers pure** (idempotent, no network IO) to ease reproducibility.
* **Test on a slice** of data and inspect emitted statements before full runs.

---

## 13) FAQ

**Q: Can I reference values computed earlier in the same entity?**\
Yes, via `property: <name>`.

**Q: How do I handle multi‑value inputs (e.g., emails)?**\
Extract with `column`, then `split_regex`, then optional `transformer` to clean each value.

**Q: What’s the difference between `transformer` and `augmentor`?**\
`transformer` replaces the current value list; `augmentor` appends to it.

**Q: Can I restrict which metadata keys are allowed?**\
Yes, via the top‑level `meta:` whitelist.

**Q: How do nested collections work with entity references?**\
Entities defined in the parent context are addressable from child collections using `entity:` (emit relationships from child rows to parent entities).

---

## 14) Checklist before running a mapping

* [ ] Mapping validates against the schema.
* [ ] Keys chosen avoid collisions.
* [ ] All transformers/augmentors are importable and deterministic.
* [ ] Metadata layering is intentional and documented.
* [ ] Sample run produces the expected entities/statements.

---

### Appendix A — Property operation quick reference

* `column: <jmespath>`
* `literal: <str|number>`
* `template: <jinja>`
* `entity: <name>`
* `property: <name>`
* `regex: <re>`
* `regex_first: <re>`
* `regex_replace: { regex: <re>|[...], replace: <str>|[...] }`
* `split_regex: <re>`
* `transformer: <FQFN or {name, params}>`
* `augmentor: <FQFN or {name, params}>`
* `meta: { <metakey>: (constant | property pipeline) }`

### Appendix B — Common FtM entities in OSINT/PEP/AML

* **[Person](https://followthemoney.tech/explorer/schemata/Person/) / [LegalEntity](https://followthemoney.tech/explorer/schemata/LegalEntity/) / [Organization](https://followthemoney.tech/explorer/schemata/Organization/)**
* **[Ownership](https://followthemoney.tech/explorer/schemata/Ownership/) / [Directorship](https://followthemoney.tech/explorer/schemata/Directorship/) / [Membership](https://followthemoney.tech/explorer/schemata/Membership/) / [Employment](https://followthemoney.tech/explorer/schemata/Employment/)**
* **[Address](https://followthemoney.tech/explorer/schemata/Address) / [Identification](https://followthemoney.tech/explorer/schemata/Identification/) / [Passport](https://followthemoney.tech/explorer/schemata/Passport/)**
* **[Sanction](https://followthemoney.tech/explorer/schemata/Sanction/) / [Position](https://followthemoney.tech/explorer/schemata/Position/) / [Representation](https://followthemoney.tech/explorer/schemata/Representation/)**

*(Consult [FtM Entity schemata explorer](https://followthemoney.tech/explorer/schemata/) for complete property lists.)*

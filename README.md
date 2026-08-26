# lakeworks-animal-sources

One YAML per shelter data source. Sources are data, not code.

Adding the thirtieth source costs the same as adding the second: a file. The ingestion job is a
generic worker parameterised by a row, Step Functions Distributed Map reads this set as its item
list, and the adapter is the only place a portal dialect exists.

## What a spec carries

| Key | Why it exists |
| --- | --- |
| `adapter` | `socrata`, `opendatasoft`, `arcgis`, `ckan`, `http_file` — five dialects, one interface |
| `discovery` | Dataset ids are resolved from the portal catalog at runtime, never pinned |
| `shape` | `two_feed` or `one_row` — the conflict the conform job reconciles |
| `mapping` | Source column to domain column, so renaming is a YAML edit |
| `watermark` | How incrementality works for this source |
| `notes` | The trap. Read these before trusting a number |

## Why ids are never pinned

Austin has renamed and re-issued its datasets, and Dallas publishes a separate dataset per fiscal
year. A pinned id fails as an *empty result*, not as an error, so the pipeline stays green and the
table stops growing. Every job resolves its dataset by querying the portal's catalog endpoint.

## The notes are part of the data

`austin.yml` records that Austin is the largest no-kill city in the US, so its outcome distribution
is not nationally representative. Any cross-shelter adoption-rate comparison that does not normalise
for intake mix will rank Austin unfairly well.

That belongs with the source rather than in an analysis, because the analysis that needs it is one
nobody has written yet.

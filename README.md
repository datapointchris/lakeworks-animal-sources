# lakeworks-animal-sources

One YAML file per shelter data source, for the `animal` domain of lakeworks. Each file says where a
shelter publishes its feeds and how their columns map onto the domain's event model. The repo is
data. Its one script, `validate_sources.py`, checks the files and does nothing else.

`lakeworks-animal-conform` reads these files and turns every enabled source into intake and outcome
events. This repo declares how each source differs. Conform holds no code that names a source. A
source that does not fit is fixed with a declaration here, never with a branch in conform.

## Starting from scratch

Adding a source is one YAML file and one validator run. The validator needs
[uv](https://docs.astral.sh/uv/), which installs its one dependency, PyYAML, from `uv.lock`.

```bash
git clone https://github.com/datapointchris/lakeworks-animal-sources
cd lakeworks-animal-sources
uv run python validate_sources.py   # one line per spec, then how many are valid

cp sonoma.yml <shelter>.yml         # start from the spec whose shape matches the feed
$EDITOR <shelter>.yml               # source_id becomes animal.<shelter>, to match the file name
uv run python validate_sources.py   # exit 1 names each failing file and what is wrong in it
```

With [Task](https://taskfile.dev) installed, `task test` runs the validator and then the validator's
own tests in `tests/`. `task lint` runs ruff and mypy without writing a file. `task setup` installs
the dev tools and the git hooks.

Copy `austin.yml` for a shelter that publishes intake and outcome as two feeds. Copy `sonoma.yml`
for one that puts both on a single row. The `shape` section below says what each one requires.

The file name is the source's identity. `source_id` must read `animal.<file stem>`, and the
validator refuses any other value. The extension is `.yml`. The validator and conform both read
`*.yml`, so a `.yaml` file is never checked and never conformed.

`enabled: false` lands a spec that conform skips. The validator still checks it.

A green validator is not the whole of adding a source. Conform maps outcome and breed spellings
through the `dim_outcome_type` and `dim_breed` tables, keyed on `source_id` and the raw value. A
new source's spellings each need a row there. Conform's README, under
[`jobs/conform.py`](https://github.com/datapointchris/lakeworks-animal-conform#jobsconformpy--every-source-through-one-path-with-no-branch-that-names-a-source),
says what a spelling with no row becomes and how a run reports it.

CI runs the same validator on every push to `main` and on every pull request.

## A spec declares where a feed lives and how it maps onto events

| Key | Declares | Read by |
| --- | --- | --- |
| `source_id` | `animal.<file stem>`, so `austin.yml` is `animal.austin` | conform, to select the source's bronze rows and its vocabulary rows |
| `domain` | The lakeworks domain, `animal` | the validator, which builds the expected `source_id` from it |
| `enabled` | Whether conform takes the source | conform, which skips a source set to `false` |
| `adapter` | The portal dialect. `ADAPTERS` in `validate_sources.py` holds the accepted values | the validator only |
| `endpoint` | The portal's base URL | the validator only |
| `discovery` | How each feed is found in the portal's catalog. The specs here find feeds `by_title` | the validator only |
| `watermark` | How incrementality works for this source. `WATERMARK_STRATEGIES` holds the strategies | the validator only |
| `schedule` | When the source is fetched, as an EventBridge cron expression | nothing |
| `shape` | `two_feed` or `one_row` | conform, which dispatches on it |
| `join_key` | The domain column a `two_feed` source's feeds join on, so `animal_id` rather than `Animal ID` | conform, after the mapping has renamed the columns |
| `mapping` | Per feed, each domain column and the source column it comes from | conform, which renames and drops every unmapped column |
| `contract` | The path of the feed's contract file, relative to this repo | the validator, which refuses a path that names no file |
| `notes` | What would make a number from this source wrong | people |

The validator requires every key except `schedule`, `join_key`, `contract` and `notes`. It requires
`join_key` for `two_feed` and refuses it for `one_row`.

`adapter`, `endpoint`, `discovery`, `watermark` and `schedule` describe the fetch, for an ingestion
worker configured by one spec and nothing else. No lakeworks repo implements that worker. The
validator checks the first four, and nothing reads `schedule`.

A mapping runs from domain column to source column. `animal_id: "Animal ID"` puts the source's
`Animal ID` into the domain's `animal_id`. Conform drops every source column the mapping does not
name. Every feed must map `animal_id`, because nothing downstream can key a row without it. A source
that renames a column costs one edit to its mapping.

## `shape` is the conflict conform reconciles, declared per source

Shelters lay out intake and outcome in two ways. The domain model is an event model, and both
layouts have to reach it. Neither layout is wrong.

**`two_feed`** is Austin's layout: intake and outcome as separate feeds. The mapping names two
feeds, `intake` and `outcome`. `join_key` names the domain column they join on, and both feeds must
map it. `austin.yml`'s `notes` say why the id alone does not key the join, and what it keys on.

**`one_row`** is Sonoma's layout: one row per animal-visit, carrying both halves. The mapping names
one feed, `combined`. Its columns for the two halves carry an `intake_` or `outcome_` prefix, and
`intake_at` and `outcome_at` are the two timestamps. Conform splits each row into two events.
`sonoma.yml`'s `notes` say what a row with no outcome date yields.

Conform reads feeds by those three names: `intake`, `outcome` and `combined`. A feed under any other
name is never read, and the validator does not check the names.

A third value needs a third layout, not one awkward source. An awkward source is usually a mapping
problem. A third value also needs a branch in conform's shape dispatch. Conform's README, under
[`jobs/conform.py`](https://github.com/datapointchris/lakeworks-animal-conform#jobsconformpy--every-source-through-one-path-with-no-branch-that-names-a-source),
says what a run does with a shape it has no branch for.

## A spec never pins a dataset id

`discovery` names each feed as the portal's catalog lists it. The dataset id is left to be resolved
from the catalog on every fetch. The validator refuses a spec with no `discovery` block.

Portals rename and re-issue datasets, and Austin has done both. Dallas publishes each fiscal year as
its own dataset. A pinned id fails as an empty result, not as an error: the pipeline stays green
while the table stops growing, and nothing reports it.

## `notes` is part of the data, not a comment on it

`notes` records what would make a number from the source wrong. That covers a shelter's intake mix,
a jurisdiction's reporting quirk, and a vocabulary that differs from its neighbors'.

The `notes` in `austin.yml` and `sonoma.yml` are the examples to read: Austin's intake mix, and
Sonoma's outcome vocabulary set against Austin's.

A note travels with its source because the analysis that will need it does not exist to hold it.
Keep notes when tidying a spec, and keep them in the spec rather than in a separate document.

## The validator stops a bad spec before a pipeline meets it

Without it, a malformed spec fails inside a Glue job. It fails minutes into a run, in a CloudWatch
log, as a `KeyError` that names a dictionary rather than a file. Each validator message names the
file and what to fix in it.

Parsing is not the bar. The validator checks:

- `adapter`, `shape` and the watermark strategy against the values it accepts
- `source_id` against the file name
- `join_key` against the shape, and against every feed's mapping
- that a `discovery` block exists
- that a `contract`, where a spec gives one, names a file in this repo
- that every feed's mapping is non-empty and maps `animal_id`

A key added to the spec format gets its check in the same change. The validator ignores a key it
does not know, so `contracts:` written for `contract:` prints `ok` and its path is never opened.

The accepted values live in the script rather than in the shared platform library. They move there
when a second domain needs the same schema.

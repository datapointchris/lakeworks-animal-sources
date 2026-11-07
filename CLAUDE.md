# lakeworks-animal-sources

The README owns what a spec holds and which code reads each key. It also says why dataset ids are
never pinned, why `notes` is part of the data, what the validator checks, and when `shape` earns a
third value. Read it before editing a spec or the validator. This file holds only what the README
does not.

## Sources are data, not code

Adding a source is one YAML file here, plus a row in `dim_outcome_type` and `dim_breed` for each
of its spellings those tables do not hold. `lakeworks-animal-conform` reads every spec and holds no
branch that names a source.

If a source seems to need a code change, look first at the shape it introduced. A per-source branch
anywhere is the failure this layout exists to prevent.

A portal's dialect belongs in its adapter, never in a branch keyed on a source. `ADAPTERS` in
`validate_sources.py` holds the dialects a spec may name.

## Every root `*.yml` is a spec

The validator and conform both read every `*.yml` at the root as a source. A config file added at
the root takes `.yaml`, as `Taskfile.yaml` does. `task test` runs the validator and then `tests/`.

# CLAUDE.md

Guidance for Claude Code working in this repository.

Read the README first. It carries what a spec holds, why dataset ids are never pinned, and why the
`notes` field is part of the data rather than commentary on it.

## Sources are data, not code

Adding a source is one YAML file and nothing else. The ingestion job is a generic worker
parameterised by a row, and the fan-out reads this directory as its item list, so nothing needs
widening when a source arrives.

If a new source seems to need a code change, the shape it introduced is the thing to look at. A
per-source branch anywhere is the failure this layout exists to prevent — the adapter is the only
place a portal dialect may live, and there are five adapters covering every source here.

## Never pin a dataset id

Ids are resolved from the portal's catalog endpoint at runtime. Portals rename and re-issue
datasets, and some publish a separate dataset per fiscal year.

**A pinned id fails as an empty result, not as an error.** The pipeline stays green and the table
simply stops growing, which is the failure mode that survives longest. Any suggestion to pin an id
"for stability" buys nothing and costs the only signal there would have been.

## `notes` is a field, not a comment

It records what would make a number wrong — a shelter's intake mix, a jurisdiction's reporting
quirk, anything that would mislead an analysis nobody has written yet. It travels with the source
because the analysis that needs it does not exist to hold it.

Do not strip these when tidying a spec, and do not move them into a separate document.

## Validation gates the specs

`validate_sources.py` checks every spec, and CI runs it. A spec that parses is not the bar — the
validator is what stops a bad `adapter`, `shape` or `mapping` reaching a pipeline at runtime, where
the failure is expensive and remote.

When adding a key to the spec format, add its check to the validator in the same change. A key the
validator does not know about is one that can be silently misspelled.

## `shape` is the conflict, not a formality

`two_feed` and `one_row` are genuinely different source shapes, and reconciling them is the conform
job's work. Do not add a third value to accommodate one awkward source without establishing that it
is a real third shape rather than a mapping problem.

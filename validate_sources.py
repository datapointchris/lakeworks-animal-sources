"""Validate every source spec before it can break a pipeline at runtime.

Without this, a malformed spec fails inside a Glue job — minutes into a run, in a CloudWatch log,
with a KeyError that names a dictionary rather than a file. Every failure below is one a person can
fix from the message alone.

The schema lives here rather than in the platform library on purpose. It is an in-script table
until there is a second domain that needs it, at which point this is the extraction point.
`repo-structure.md` § "Prefer an in-script table over an external registry" is the rule.
"""

import pathlib
import sys

import yaml

ADAPTERS = {'socrata', 'opendatasoft', 'arcgis', 'ckan', 'http_file', 'api_oauth2'}
SHAPES = {'two_feed', 'one_row'}
WATERMARK_STRATEGIES = {'field', 'full_snapshot', 'manifest'}
REQUIRED = (
    'source_id',
    'domain',
    'adapter',
    'enabled',
    'endpoint',
    'shape',
    'mapping',
    'contract',
)


def check(path: pathlib.Path) -> list[str]:
    """Validate one spec.

    Args:
        path: The YAML file to check.

    Returns:
        Human-readable problems. Empty when the spec is valid.
    """
    try:
        spec = yaml.safe_load(path.read_text())
    except yaml.YAMLError as err:
        return [f'not parseable as YAML: {err}']

    if not isinstance(spec, dict):
        return ['top level is not a mapping']

    problems = [f'missing required key `{key}`' for key in REQUIRED if key not in spec]
    if problems:
        return problems

    if spec['adapter'] not in ADAPTERS:
        problems.append(f'unknown adapter `{spec["adapter"]}` — expected one of {sorted(ADAPTERS)}')

    if spec['shape'] not in SHAPES:
        problems.append(f'unknown shape `{spec["shape"]}` — expected one of {sorted(SHAPES)}')

    if spec['source_id'] != f'{spec["domain"]}.{path.stem}':
        problems.append(f'source_id `{spec["source_id"]}` does not match `{spec["domain"]}.{path.stem}`')

    strategy = spec.get('watermark', {}).get('strategy')
    if strategy not in WATERMARK_STRATEGIES:
        problems.append(f'watermark.strategy `{strategy}` — expected one of {sorted(WATERMARK_STRATEGIES)}')

    # A two-feed source needs a join key, and a one-row source must not carry one. Either mistake
    # produces a cross join or a silently dropped half of the data rather than an error.
    if spec['shape'] == 'two_feed' and 'join_key' not in spec:
        problems.append('shape is two_feed but no join_key is declared')
    if spec['shape'] == 'one_row' and 'join_key' in spec:
        problems.append('shape is one_row but a join_key is declared — it would never be used')

    # Dataset ids resolved at runtime is the rule; a pinned id fails as an empty result rather than
    # an error, so the pipeline stays green while the table stops growing.
    if 'discovery' not in spec:
        problems.append('no discovery block — dataset ids must be resolved at runtime, never pinned')

    for feed, mapping in spec['mapping'].items():
        if not isinstance(mapping, dict) or not mapping:
            problems.append(f'mapping.{feed} is empty')
            continue
        if 'animal_id' not in mapping:
            problems.append(f'mapping.{feed} has no animal_id — nothing downstream can key on it')

    return problems


def main() -> int:
    specs = sorted(pathlib.Path(__file__).parent.glob('*.yml'))
    if not specs:
        print('no source specs found', file=sys.stderr)
        return 1

    failed = 0
    for path in specs:
        if problems := check(path):
            failed += 1
            for problem in problems:
                print(f'{path.name}: {problem}', file=sys.stderr)
        else:
            print(f'{path.name}: ok')

    print(f'\n{len(specs) - failed}/{len(specs)} specs valid')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

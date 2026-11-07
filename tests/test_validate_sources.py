"""The validator refuses each malformed spec on its own branch, and passes every committed spec."""

import copy
import pathlib

import pytest
import yaml

from validate_sources import check

ROOT = pathlib.Path(__file__).parent.parent

VALID = {
    'source_id': 'animal.demo',
    'domain': 'animal',
    'adapter': 'socrata',
    'enabled': True,
    'endpoint': 'https://data.example.org',
    'discovery': {'by_title': {'intake': 'Intakes', 'outcome': 'Outcomes'}},
    'watermark': {'strategy': 'field', 'field': 'DateTime'},
    'shape': 'two_feed',
    'join_key': 'animal_id',
    'mapping': {
        'intake': {'animal_id': 'Animal ID', 'name': 'Name'},
        'outcome': {'animal_id': 'Animal ID', 'event_at': 'DateTime'},
    },
}


def _drop(key):
    return lambda spec: spec.pop(key)


def _set(key, value):
    return lambda spec: spec.__setitem__(key, value)


def _one_row_with_join_key(spec):
    spec['shape'] = 'one_row'
    spec['mapping'] = {'combined': {'animal_id': 'Animal ID'}}


def _no_animal_id(spec):
    spec['join_key'] = 'event_at'
    spec['mapping']['intake'] = {'event_at': 'DateTime'}


# Each mutation breaks one rule, so the spec must come back with exactly one problem, naming the
# key a person edits to fix it.
REFUSALS = [
    pytest.param(_drop('endpoint'), 'endpoint', id='missing-required-key'),
    pytest.param(_set('adapter', 'ftp'), 'adapter', id='unknown-adapter'),
    pytest.param(_set('shape', 'three_feed'), 'shape', id='unknown-shape'),
    pytest.param(_set('source_id', 'animal.other'), 'source_id', id='source-id-mismatch'),
    pytest.param(_drop('watermark'), 'watermark', id='missing-watermark'),
    pytest.param(_set('watermark', 'field'), 'watermark', id='watermark-not-a-block'),
    pytest.param(_set('watermark', {'strategy': 'daily'}), 'watermark.strategy', id='unknown-strategy'),
    pytest.param(_drop('join_key'), 'join_key', id='two-feed-without-join-key'),
    pytest.param(_one_row_with_join_key, 'join_key', id='one-row-with-join-key'),
    pytest.param(_drop('discovery'), 'discovery', id='missing-discovery'),
    pytest.param(_set('contract', 'contracts/missing.yaml'), 'contract', id='contract-names-no-file'),
    pytest.param(_set('join_key', 'name'), 'join_key', id='join-key-not-mapped'),
    pytest.param(lambda spec: spec['mapping'].__setitem__('outcome', {}), 'mapping.outcome', id='empty-mapping'),
    pytest.param(_no_animal_id, 'animal_id', id='no-animal-id'),
]


@pytest.mark.parametrize(('mutate', 'names'), REFUSALS)
def test_refuses_a_broken_spec_once_naming_its_key(tmp_path, mutate, names):
    spec = copy.deepcopy(VALID)
    mutate(spec)
    path = tmp_path / 'demo.yml'
    path.write_text(yaml.safe_dump(spec))

    problems = check(path)

    assert len(problems) == 1, problems
    assert names in problems[0]


@pytest.mark.parametrize('path', sorted(ROOT.glob('*.yml')), ids=lambda p: p.name)
def test_committed_spec_is_valid(path):
    assert check(path) == []

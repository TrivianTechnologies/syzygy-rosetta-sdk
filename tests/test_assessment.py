# SPDX-License-Identifier: MPL-2.0
from itertools import permutations, product
import pytest
from open_rosetta.assessment import Observation, Verdict, PROFILE, SCHEMA, REQUIRED, EvidenceBinding, EVIDENCE_VERSION, assess


BINDING=EvidenceBinding('subject:fixture','scope:fixture','action:fixture','a'*64,EVIDENCE_VERSION,'state:fixture')

def observation(check,value,evidence):
    return Observation(check,value,evidence,BINDING)

def evaluate(items, **kwargs):
    return assess(items, profile=kwargs.get('profile', PROFILE), schema=kwargs.get('schema', SCHEMA),binding=kwargs.get('binding',BINDING))


@pytest.mark.parametrize('values', list(product([True, False, None], repeat=4)))
def test_complete_truth_table(values):
    items = [observation(k, v, 'host:fixture') for k, v in zip(REQUIRED, values)]
    expected = Verdict.FAILS if False in values else Verdict.UNRESOLVED if None in values else Verdict.SURVIVES
    result = evaluate(items)
    assert result.verdict is expected
    assert not result.authorizes_execution
    assert result.observations == tuple(items)


def test_false_dominates_unknown_in_every_order_with_complete_diagnostics():
    items = [observation(REQUIRED[0], False, 'host:1'), observation(REQUIRED[1], None, 'host:2'), observation(REQUIRED[2], True, 'host:3')]
    results = [evaluate(p) for p in permutations(items)]
    assert all(r.verdict is Verdict.FAILS for r in results)
    assert all(r.diagnostics == results[0].diagnostics for r in results)
    assert results[0].diagnostics == ('false:authority_current', 'invalid_or_unknown:consent_current', 'missing:constraints_preserved')


@pytest.mark.parametrize('items', [[], [observation(REQUIRED[0], True, 'host:1')], [observation(k, True, 'host:1') for k in REQUIRED] + [observation(REQUIRED[0], True, 'host:2')]])
def test_coverage_cannot_be_reduced_or_deduplicated(items):
    assert evaluate(items).verdict is Verdict.UNRESOLVED


@pytest.mark.parametrize('value,evidence', [(0,'host:1'),(1,'host:1'),('false','host:1'),(False,''),(True,None)])
def test_invalid_observation_cannot_become_definite(value,evidence):
    assert evaluate([observation(REQUIRED[0], value, evidence)]).verdict is Verdict.UNRESOLVED


@pytest.mark.parametrize('kwargs', [{'profile':'future'}, {'schema':'future'}])
def test_unknown_version_never_authorizes(kwargs):
    result=evaluate([observation(k,False,'host:1') for k in REQUIRED],**kwargs)
    assert result.verdict is Verdict.UNRESOLVED and not result.authorizes_execution


def test_conflicting_duplicate_retains_false_and_all_evidence():
    items=[observation(k,True,'host:1') for k in REQUIRED]+[observation(REQUIRED[0],False,'host:2')]
    result=evaluate(items)
    assert result.verdict is Verdict.FAILS
    assert 'duplicate:authority_current' in result.diagnostics
    assert result.observations == tuple(items)


def test_malformed_object_rejected():
    with pytest.raises(TypeError): evaluate([{}])

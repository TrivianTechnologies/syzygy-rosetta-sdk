# SPDX-License-Identifier: MPL-2.0
"""Integrated correction controls on the normal public API; no enabling override."""
import pytest
import sqlite3
import tria
from open_rosetta import tria_adapter as adapter
from open_rosetta.correction import apply_correction


@pytest.fixture(params=['memory', 'sqlite'])
def correction_world(request, tmp_path):
    store = tria.InMemoryEventStore() if request.param == 'memory' else tria.SQLiteEventStore(tmp_path/'events.sqlite')
    rel = tria.Tria(store).create_relationship(['human:a', 'agent:b'])
    source = rel.register_claim('agent:b', tria.EpistemicType.OBSERVATION, 'source', source_refs=['host:source']).claim_id
    child = rel.register_claim('agent:b', tria.EpistemicType.INFERENCE, 'derived', derived_from=[source]).claim_id
    rel.admin.grant_permission('human:a', 'agent:b', 'truth-integrity:corrections', tria.Capability.ACT)
    binding = adapter.TriaBinding(rel, adapter.ReleasePolicy('agent:b', 'local:effect', 'human:a', 'scope', 'test', 'subject'), (child,))
    correction = tria.CorrectionEvidence('correction:public', source, 'human:a', ('host:new',), tria.CorrectionDisposition.WARRANTED)
    yield store, rel, source, child, binding, correction
    if hasattr(store, 'close'):
        store.close()


def apply(world, snapshot=None):
    _, rel, source, _, binding, correction = world
    return apply_correction(binding, correction, snapshot or tria.snapshot_correction_graph(rel, source), acceptance_ref='host:accepted')


@pytest.mark.parametrize('kind', ['omitted', 'fabricated', 'duplicate'])
def test_public_application_rejects_noncanonical_graph_without_mutation(correction_world, kind):
    _, rel, source, child, _, _ = correction_world
    snapshot = tria.snapshot_correction_graph(rel, source)
    links = {'omitted': (), 'fabricated': (tria.DependencyLink(source, 'missing', tria.DependencyKind.DERIVED_FROM),),
             'duplicate': snapshot.dependencies + snapshot.dependencies}[kind]
    bad = tria.CorrectionGraphSnapshot(source, snapshot.head_hash, links)
    before = tuple(rel.events)
    assert apply(correction_world, bad).backend_receipt.outcome is tria.GovernanceOutcome.BLOCK
    assert tuple(rel.events) == before


def test_public_revocation_during_recording_prevents_partial_application(correction_world, monkeypatch):
    _, rel, source, child, _, _ = correction_world
    original = rel.record_governance_decision
    def revoke(decision, **kwargs):
        event = original(decision, **kwargs)
        rel.admin.revoke_permission('human:a', 'agent:b', 'truth-integrity:corrections', tria.Capability.ACT)
        return event
    monkeypatch.setattr(rel, 'record_governance_decision', revoke)
    assert apply(correction_world).backend_receipt.outcome is tria.GovernanceOutcome.BLOCK
    assert all(rel.state.claims[x].status is tria.ClaimStatus.ACTIVE for x in (source, child))
    assert not any(e.event_type in ('ClaimDisputed', 'CorrectionUptakeApplied') for e in rel.events)


def test_public_batch_failure_rolls_back_and_fresh_attempt_recovers(correction_world, monkeypatch):
    store, rel, source, child, _, _ = correction_world
    if isinstance(store, tria.SQLiteEventStore):
        store._session.conn.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON events WHEN json_extract(NEW.event_json,'$.event_type')='CorrectionUptakeApplied' BEGIN SELECT RAISE(ABORT,'injected'); END")
    else:
        original = tria.RelationalEvent.verify_hash
        def fail(event):
            if event.event_type == 'CorrectionUptakeApplied':
                raise RuntimeError('injected final-event validation failure')
            return original(event)
        monkeypatch.setattr(tria.RelationalEvent, 'verify_hash', fail)
    with pytest.raises((RuntimeError, sqlite3.IntegrityError)):
        apply(correction_world)
    assert all(rel.state.claims[x].status is tria.ClaimStatus.ACTIVE for x in (source, child))
    assert not any(e.event_type in ('ClaimDisputed', 'CorrectionUptakeApplied') for e in rel.events)
    if isinstance(store, tria.SQLiteEventStore):
        store._session.conn.execute('DROP TRIGGER reject_receipt')
    else:
        monkeypatch.setattr(tria.RelationalEvent, 'verify_hash', original)
    assert apply(correction_world).backend_receipt.outcome is tria.GovernanceOutcome.ALLOW
    assert rel.audit()['chain_valid']


@pytest.mark.parametrize('failure', ['unavailable', 'mismatched'])
def test_public_correction_fails_closed_when_backend_changes(correction_world, monkeypatch, failure):
    _, rel, source, _, binding, correction = correction_world
    snapshot = tria.snapshot_correction_graph(rel, source)
    before = tuple(rel.events)
    if failure == 'mismatched':
        monkeypatch.setattr(adapter, 'version', lambda _: 'incompatible')
    else:
        original = adapter.importlib.import_module
        def missing(name, *args, **kwargs):
            if name == 'tria':
                raise ModuleNotFoundError('backend unavailable')
            return original(name, *args, **kwargs)
        monkeypatch.setattr(adapter.importlib, 'import_module', missing)
    with pytest.raises(adapter.BackendUnavailable):
        apply_correction(binding, correction, snapshot, acceptance_ref='host:accepted')
    assert tuple(rel.events) == before

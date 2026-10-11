# SPDX-License-Identifier: MPL-2.0
import pytest
import tria
from open_rosetta.conformance import CorrectionExecutionUnavailable
from open_rosetta.correction import apply_correction
from test_correction_integration import fixture, release


def test_closed_gate_prevents_correction_mutation_and_host_entry(monkeypatch):
    # Retain the closed-gate safety contract when the feature is unavailable.
    monkeypatch.setattr('open_rosetta.conformance._CORRECTION_EXECUTION_ENABLED', False)
    rel, source, child, binding, correction = fixture()
    snapshot = tria.snapshot_correction_graph(rel, source)
    before = tuple(rel.events)
    calls = []
    with pytest.raises(CorrectionExecutionUnavailable):
        apply_correction(binding, correction, snapshot, acceptance_ref='host:accepted')
    with pytest.raises(CorrectionExecutionUnavailable):
        release(binding, calls)
    assert tuple(rel.events) == before
    assert calls == []


def test_candidate_default_uses_public_api_without_gate_override():
    from open_rosetta.conformance import _CORRECTION_EXECUTION_ENABLED
    assert _CORRECTION_EXECUTION_ENABLED is True
    rel, source, child, binding, correction = fixture()
    calls = []
    assert release(binding, calls).host_entered
    snapshot = tria.snapshot_correction_graph(rel, source)
    applied = apply_correction(binding, correction, snapshot, acceptance_ref='host:accepted')
    assert applied.backend_receipt.outcome is tria.GovernanceOutcome.ALLOW
    assert release(binding, calls).disposition == 'CLAIM_CONTEXT_DENIED'
    assert len(calls) == 1

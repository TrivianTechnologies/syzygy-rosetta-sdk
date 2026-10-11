# SPDX-License-Identifier: MPL-2.0
import pytest
import tria
from open_rosetta.conformance import CorrectionExecutionUnavailable
from open_rosetta.correction import apply_correction
from test_correction_integration import fixture, release


def test_default_gate_prevents_correction_mutation_and_host_entry():
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

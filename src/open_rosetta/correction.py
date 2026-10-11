# SPDX-License-Identifier: MPL-2.0
"""Bounded local application; a receipt alone is not substantive uptake evidence."""
from dataclasses import dataclass
from .tria_adapter import TriaBinding, _load_backend
from .conformance import require_correction_conformance


@dataclass(frozen=True)
class CorrectionApplication:
    correction_id: str
    accepted_by: str
    acceptance_ref: str
    authority_event_ref: str | None
    before_head: str
    after_head: str
    backend_receipt: object
    evidence_trust: str = 'host_supplied_not_authenticated'


def apply_correction(binding: TriaBinding, correction, snapshot, *, acceptance_ref: str):
    """Acceptance/application share the bound ACT principal; host assesses truth.

    acceptance_ref attributes the separate host epistemic acceptance. It does not
    authenticate evidence or grant authority. Backend ACT and snapshot guards are
    mandatory; actual downstream consumption must be observed separately.
    """
    tria=_load_backend()
    if type(binding) is not TriaBinding or type(snapshot) is not tria.CorrectionGraphSnapshot:
        raise TypeError('Use a bound backend and its canonical graph snapshot.')
    # Revalidate at use: a reconstructed or modified dataclass must never turn
    # the mandatory snapshot guard into the kernel's optional None sentinel.
    snapshot=tria.CorrectionGraphSnapshot(snapshot.target_ref,snapshot.head_hash,snapshot.dependencies)
    if type(correction) is not tria.CorrectionEvidence or correction.target_ref!=snapshot.target_ref:
        raise ValueError('Correction and snapshot target must match.')
    if type(acceptance_ref) is not str or not acceptance_ref.strip():
        raise ValueError('A host acceptance evidence reference is required.')
    require_correction_conformance()
    rel=binding.relationship; actor=binding.policy.actor
    with rel.execution_guard():
        before=rel.events[-1].event_hash
        authority=rel.state.permissions.get((actor,'truth-integrity:corrections',tria.Capability.ACT))
        receipt=tria.apply_correction_uptake(rel,actor,correction,snapshot.dependencies,expected_head=snapshot.head_hash)
        return CorrectionApplication(correction.correction_id,actor,acceptance_ref,
            authority.grant_event_id if authority else None,before,rel.events[-1].event_hash,receipt)

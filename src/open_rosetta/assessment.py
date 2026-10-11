# SPDX-License-Identifier: MPL-2.0
"""Original local candidate implementing the proposed assessment profile.

No transport, permission cache, executor or authority registry is provided.
The schema identifier names this local Python candidate, not an adopted wire API.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

PROFILE = 'assessment-only/0.1.0-draft.2'
SCHEMA = 'open-rosetta-local-observation/0.1.0-draft.1'
REQUIRED = ('authority_current', 'consent_current', 'scope_valid', 'constraints_preserved')
EVIDENCE_VERSION = 'host-observation/0.1'


@dataclass(frozen=True)
class EvidenceBinding:
    subject: str
    scope: str
    action_id: str
    action_digest: str
    evidence_version: str
    state_context: str

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in vars(self).values()):
            raise ValueError('Binding fields must be exact nonempty strings.')
        if len(self.action_digest) != 64 or any(c not in '0123456789abcdef' for c in self.action_digest):
            raise ValueError('action_digest must be a SHA-256 hex digest.')


class Verdict(str, Enum):
    SURVIVES = 'SURVIVES'
    FAILS = 'FAILS'
    UNRESOLVED = 'UNRESOLVED'


@dataclass(frozen=True)
class Observation:
    check: str
    value: bool | None
    evidence_ref: str
    binding: EvidenceBinding | None = None


@dataclass(frozen=True)
class Assessment:
    verdict: Verdict
    observations: tuple[Observation, ...]
    diagnostics: tuple[str, ...]
    profile: str
    schema: str
    binding: EvidenceBinding | None

    @property
    def authorizes_execution(self) -> bool:
        return False


def assess(observations: Iterable[Observation], *, profile: str, schema: str,
           binding: EvidenceBinding | None = None) -> Assessment:
    """Assess complete profile-owned coverage without creating permission.

    Evidence references are host assertions, not authenticated observations.
    Malformed Python objects raise TypeError; malformed observation fields
    produce retained diagnostics. Only exact bools with evidence count.
    """
    items = tuple(observations)
    if any(type(item) is not Observation for item in items):
        raise TypeError('observations must be Observation instances')
    diagnostics = []
    recognized = type(profile) is str and type(schema) is str and profile == PROFILE and schema == SCHEMA
    if type(profile) is not str:
        diagnostics.append('invalid_profile_type')
    if type(schema) is not str:
        diagnostics.append('invalid_schema_type')
    bound = type(binding) is EvidenceBinding and binding.evidence_version == EVIDENCE_VERSION
    if not bound:
        diagnostics.append('invalid_or_missing_binding')
    definite_false = False
    for item in items:
        if type(item.check) is not str or item.check not in REQUIRED:
            diagnostics.append('unknown_check')
            continue
        matching = bound and type(item.binding) is EvidenceBinding and item.binding == binding
        if not matching:
            diagnostics.append('binding_mismatch:' + item.check)
        valid = (matching and type(item.value) is bool and type(item.evidence_ref) is str
                 and bool(item.evidence_ref.strip()))
        if not valid:
            diagnostics.append('invalid_or_unknown:' + item.check)
        elif item.value is False:
            definite_false = True
            diagnostics.append('false:' + item.check)
    for check in REQUIRED:
        count = sum(type(item.check) is str and item.check == check for item in items)
        if count == 0:
            diagnostics.append('missing:' + check)
        elif count > 1:
            diagnostics.append('duplicate:' + check)
    if not recognized:
        diagnostics.append('unrecognized_profile_or_schema')
        verdict = Verdict.UNRESOLVED
    elif definite_false:
        verdict = Verdict.FAILS
    elif diagnostics:
        verdict = Verdict.UNRESOLVED
    else:
        verdict = Verdict.SURVIVES
    return Assessment(verdict, items, tuple(sorted(diagnostics)), profile, schema, binding)

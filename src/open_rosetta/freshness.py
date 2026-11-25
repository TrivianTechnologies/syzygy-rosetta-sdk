# SPDX-License-Identifier: MPL-2.0
"""Optional reporting companion. Source authentication belongs to the shared verifier."""

from dataclasses import dataclass

from syzygy_freshness import Observation as FreshnessObservation, Verifier, fingerprint
from .assessment import Assessment, EvidenceBinding, assess


def _binding(value):
    if type(value) is not EvidenceBinding:
        raise ValueError("complete evidence binding required")
    return [
        value.subject,
        value.scope,
        value.action_id,
        value.action_digest,
        value.evidence_version,
        value.state_context,
    ]


def assessment_subject(assessment, *, policy_version, policy_digest):
    """Digest a versioned policy and the ordered evidence actually examined by assess()."""
    if type(policy_version) is not str or not policy_version.strip():
        raise ValueError("policy version required")
    if (
        type(policy_digest) is not str
        or len(policy_digest) != 64
        or any(c not in "0123456789abcdef" for c in policy_digest)
    ):
        raise ValueError("expected a SHA-256 policy digest")
    if type(assessment.profile) is not str or type(assessment.schema) is not str:
        raise ValueError("unsupported profile/schema type")
    observations = []
    for item in assessment.observations:
        if (
            type(item.check) is not str
            or type(item.evidence_ref) is not str
            or (item.value is not None and type(item.value) is not bool)
        ):
            raise ValueError("unsupported observation representation")
        observations.append(
            [item.check, item.value, item.evidence_ref, _binding(item.binding)]
        )
    return fingerprint(
        [
            "open-rosetta.assessed-evidence/1",
            policy_version,
            policy_digest,
            assessment.profile,
            assessment.schema,
            _binding(assessment.binding),
            observations,
        ]
    )


@dataclass(frozen=True)
class AssessmentReport:
    assessment: Assessment
    freshness: FreshnessObservation | None
    reason: str

    @property
    def freshness_status(self):
        return self.freshness.status if self.freshness is not None else "unverified"

    @property
    def authorizes_execution(self):
        return False


def assess_with_freshness(
    observations,
    *,
    profile,
    schema,
    binding,
    policy_version,
    policy_digest,
    verifier=None,
    exchange=None,
    preview_max_age_ms=None,
):
    original = assess(observations, profile=profile, schema=schema, binding=binding)
    try:
        subject = assessment_subject(
            original, policy_version=policy_version, policy_digest=policy_digest
        )
    except ValueError:
        return AssessmentReport(original, None, "unbound_evidence_or_policy")
    if type(verifier) is not Verifier:
        return AssessmentReport(original, None, "missing_verifier")
    if preview_max_age_ms is not None:
        if exchange is not None:
            raise ValueError("choose online observation or explicit bounded preview")
        observed = verifier.bounded_preview(subject, max_age_ms=preview_max_age_ms)
    elif exchange is None:
        return AssessmentReport(original, None, "missing_confirmation")
    else:
        observed = verifier.observe(subject, exchange)
    return AssessmentReport(original, observed, observed.reason)

# SPDX-License-Identifier: MPL-2.0
from dataclasses import replace
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from syzygy_freshness import Cursor, Domain, Verifier, ZERO, reply
from open_rosetta.assessment import (
    EvidenceBinding,
    EVIDENCE_VERSION,
    PROFILE,
    SCHEMA,
    REQUIRED,
    Observation,
    assess,
)
from open_rosetta.freshness import assess_with_freshness, assessment_subject

B = EvidenceBinding(
    "agent", "scope", "act", "a" * 64, EVIDENCE_VERSION, "policy-state-1"
)
OBS = tuple(Observation(k, True, "source/" + k, B) for k in REQUIRED)
POLICY = dict(policy_version="p1", policy_digest=sha256(b"policy-1").hexdigest())
ARGS = dict(profile=PROFILE, schema=SCHEMA, binding=B)
ROOT = Cursor(1, "event", "a" * 64, 0, ZERO)
TIP = Cursor(2, "next", "b" * 64, 1, "c" * 64)


def test_identical_input_on_either_side_of_policy_publication(tmp_path):
    key = Ed25519PrivateKey.generate()
    verifier = Verifier(
        tmp_path / "state",
        Domain("issuer", "epoch", "rel", "ledger"),
        key.public_key(),
        ROOT,
        enroll=True,
    )
    original = assess(OBS, **ARGS)
    independent = [assessment_subject(original, **POLICY)]
    generation = [TIP]

    def exchange(q):
        return reply(
            key, q, generation[0], "current" if q.subject == independent[0] else "stale"
        )

    def run(items=OBS, **kw):
        return assess_with_freshness(items, **ARGS, **POLICY, verifier=verifier, **kw)

    before = run(exchange=exchange)
    assert (
        before.assessment == original and before.freshness_status == "current_at_check"
    )
    assert run(preview_max_age_ms=1000).freshness_status == "bounded_as_of"
    independent[0] = assessment_subject(original, **{**POLICY, "policy_version": "p2"})
    generation[0] = replace(TIP, publication=2, publication_hash="e" * 64)
    after = run(exchange=exchange)
    assert after.assessment == original and after.freshness_status == "stale"
    assert run(preview_max_age_ms=1000).freshness_status == "unverified"
    assert not before.authorizes_execution and not after.assessment.authorizes_execution


@pytest.mark.parametrize(
    "change",
    [
        "policy_version",
        "policy_digest",
        "scope",
        "action",
        "evidence",
        "order",
        "value",
    ],
)
def test_each_subject_dimension_is_bound(change):
    items = list(OBS)
    policy = dict(POLICY)
    binding = B
    if change in policy:
        policy[change] = "p2" if change == "policy_version" else "b" * 64
    elif change == "scope":
        binding = replace(B, scope="other")
    elif change == "action":
        binding = replace(B, action_digest="e" * 64)
    elif change == "order":
        items.reverse()
    elif change == "evidence":
        items[0] = replace(items[0], evidence_ref="other")
    else:
        items[0] = replace(items[0], value=False)
    original = assessment_subject(assess(OBS, **ARGS), **POLICY)
    assert (
        assessment_subject(assess(items, **{**ARGS, "binding": binding}), **policy)
        != original
    )


def test_current_failed_constraint_and_missing_confirmation(tmp_path):
    items = (replace(OBS[0], value=False), *OBS[1:])
    key = Ed25519PrivateKey.generate()
    v = Verifier(
        tmp_path / "f",
        Domain("issuer", "epoch", "rel", "scope"),
        key.public_key(),
        ROOT,
        enroll=True,
    )
    report = assess_with_freshness(
        items,
        **ARGS,
        **POLICY,
        verifier=v,
        exchange=lambda q: reply(key, q, TIP, "current"),
    )
    assert (
        report.assessment.verdict.value,
        report.freshness_status,
        report.authorizes_execution,
    ) == ("FAILS", "current_at_check", False)
    assert (
        assess_with_freshness(OBS, **ARGS, **POLICY, verifier=v).reason
        == "missing_confirmation"
    )


def test_missing_binding_retains_original_result():
    args = {**ARGS, "binding": None}
    report = assess_with_freshness(OBS, **args, **POLICY)
    assert report.assessment == assess(OBS, **args)
    assert report.freshness_status == "unverified" and not report.authorizes_execution

# Bounded local correction enablement candidate

Status: **candidate under independent review, not yet supported availability**.
This branch changes the SDK correction gate from false to true. The merged SDK
`6f76a7c605014b2ce13c76e6884f22bbf53094df` remains disabled; use this branch only
for review and local conformance until its exact enabling commit passes review/CI.

## Transition and scope

The exact kernel pin is merged TRIA
`03b8ef764a60c5ba01031ddaf363028e5c49f7d9`, package `0.1.0a7`, correction-safety
surface `0.1`; all Python-source fingerprints are unchanged. The kernel tree is
identical to independently reviewed `69a0b3739457e86f9e481cdfe4fa41e9810461cc`.
No kernel event, projection, authority or normative contract changes accompany
this SDK gate transition. The SDK package remains an unpublished source candidate.

The enabled local path uses `TriaBinding` with declared `claim_refs` and
`apply_correction` with a validated canonical snapshot and attributable host
acceptance. Existing current ACT/READ/consent checks, exact backend fingerprint,
mandatory snapshot continuity and local atomic kernel application remain in force.
A receipt is not substantive uptake: inspect the actual next consumption and
mock consequence. Non-ACTIVE declared claims withhold subsequent local release.

This does not add REVISED/SUPERSEDED lifecycle events or replacement-content
authority. Hosts still declare all semantic dependencies and own authentication,
evidence integrity and external effects. F033 remains unresolved and excluded:
no global revocation freshness, independent-store convergence or distributed
no-resurrection guarantees.

## Evidence and gates

Historical disabled source and override-based tests are retained byte-for-byte in
`evidence/pre-enablement-6f76a7c/`, with a hash manifest. They are not current tests.
The active integration tests no longer patch the feature on. The closed-gate
no-mutation/no-entry regression remains, with the gate explicitly false in that
one negative case. A new default-enabled regression exercises the normal public
API, observes pre-correction entry, applies correction, and observes withheld
post-correction entry without enabling overrides.

`tests/test_correction_public_api.py` adds memory/SQLite public-path checks for
omitted/fabricated/duplicate graphs, revocation during authorization recording,
atomic failure and fresh-snapshot recovery, and unavailable/mismatched backends.
Existing stale/malformed snapshot, next-consumption, evidence and boundary controls
remain. The local Sandbox enabling candidate removes its gate override while
retaining deterministic clocks, identities and explicit simulated-effect labels.

CI builds both wheel and sdist, installs each in a new environment with the exact
merged kernel, then runs tests from outside the repository. Positive paths must
pass without modifying `conformance.py` or a private flag at runtime. A deliberately
closed-gate test remains a negative control, not an enabling workaround.

Required before any supported-availability claim: exact enabling-head independent
review; passing integrated positive/negative controls and installed-artifact tests;
applicable GitHub reviews/CI; and recorded merge disposition. No merge or publication
is implied by preparing this candidate. Sandbox remote publication remains separately
blocked on deployment-trigger inspection.

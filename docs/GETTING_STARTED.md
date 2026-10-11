# Build your first governed local action

Open Rosetta separates an assessment from permission to act. This walkthrough
runs a Python-only simulated action, revokes consent, and observes that the next
attempt never enters the mock executor. No model account, service credentials or
network calls are needed after installation.

## Install the merged sources

Use Python 3.11, 3.12 or 3.13 and Git. Packages are source-installed prereleases;
these commands do not assume a published PyPI distribution. From this checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install \
  'tria-sdk @ git+https://github.com/TrivianTechnologies/tria-sdk.git@03b8ef764a60c5ba01031ddaf363028e5c49f7d9' \
  'open-rosetta-sdk @ git+https://github.com/TrivianTechnologies/syzygy-rosetta-sdk.git@6f76a7c605014b2ce13c76e6884f22bbf53094df'
.venv/bin/python -m pip check
.venv/bin/python examples/quickstart.py
```

On Windows use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
Installation downloads public source and build dependencies. The example itself
is offline and only appends to an in-memory list.

Expected observations:

- Before revocation: `HOST_ENTERED`, one simulated effect.
- After revocation: `TRIA_DENIED`, no second effect.
- `assessment_authorizes` is always `false`.
- External effect observation remains `UNKNOWN` even when the mock reports completion.
- `chain_valid` is `true`.

All `True` evidence values in this example are explicit tutorial fixtures. A host
must provide its own authenticated actors and attributable evidence in a real
integration. The SDK checks represented relationships, not the truth of the world.

## Choose the profile

| Profile | What it does | What it requires |
|---|---|---|
| Assessment | Evaluates required checks, preserving failure and uncertainty | Profile/schema and bound observations; no TRIA installation required for assessment imports |
| Claim-independent local governance | Rechecks current authority and consent at synchronous local handoff | Exact TRIA source, declared scope, current evidence and a local executor |
| Correction-dependent governance | Candidate graph validation, status propagation and atomic correction | Currently disabled by the release gate; offline conformance exercises it in a fixed simulation |

`SURVIVES` is an assessment outcome, not authorization. Missing/ambiguous evidence
remains unresolved. A definite false required check takes precedence over unknowns.
An empty `claim_refs` tuple asserts a host-owned precondition of claim independence;
it must not be used to hide consequential claim dependencies.

## Reproduce the Sandbox

Use the [Open Rosetta Sandbox](https://github.com/TrivianTechnologies/syzygy-rosetta-sandbox)
local candidate and its `docs/REPRODUCE.md`. Its source is presently a review artifact;
the default branch must not be described as containing the new offline runner until
that candidate is merged. The candidate supplies four basic controls and eleven
paired correction controls, with deterministic traces and explicit failure findings.
A browser demo replays those recorded local traces; it does not run Python or make
claims about live external effects.

## Troubleshooting and limits

`BackendUnavailable` means the installed TRIA version or Python sources do not match
the pin. Recreate the environment using the two immutable sources above; do not
remove the fingerprint check. See [compatibility](COMPATIBILITY.md).

`CorrectionExecutionUnavailable` is the intentional release gate, not a missing
credential. There is no supported runtime switch. `ASSESSMENT_DENIED`, `TRIA_DENIED`,
`DEADLINE_DENIED` and `BINDING_CHANGED` identify different failure boundaries.
Do not automatically retry a missing receipt or unknown effect.

The host owns identity, evidence integrity, external effects and deployment controls.
F033 remains unresolved: no global revocation freshness, independent-store
convergence or distributed no-resurrection guarantee. See [security boundaries](SECURITY.md).

## Get implementation help

For integration design, technical questions or implementation assistance, contact
[node@triviantech.com](mailto:node@triviantech.com). Include the source commits,
Python version, expected behavior and a synthetic reproducer. Do not send credentials,
customer records or private data. For investment inquiries use
[invest@triviantech.com](mailto:invest@triviantech.com).

For the separate, not-yet-supported correction-enablement candidate, see
[the explicit transition record](CORRECTION_ENABLEMENT.md). The commands above
continue to install the merged SDK with correction-dependent execution disabled.

# Open Rosetta SDK

**Assess an action. Check current authority. Observe the local result.**

Open Rosetta provides non-authorizing assessment and a bounded TRIA integration
for Python applications. Start with a local action, revoke consent, and see the
next attempt blocked before the mock executor runs.

[**Run the quickstart**](docs/GETTING_STARTED.md) ·
[Compatibility](docs/COMPATIBILITY.md) · [Security boundaries](docs/SECURITY.md)

## Developer path

1. Understand the implemented [Syzygy Rosetta Protocol](https://github.com/TrivianTechnologies/syzygy-rosetta-protocol).
2. Install the exact merged sources using [Getting started](docs/GETTING_STARTED.md).
3. Run [examples/quickstart.py](examples/quickstart.py): assessment, local authority and revocation.
4. Reproduce the [offline Sandbox candidate](https://github.com/TrivianTechnologies/syzygy-rosetta-sandbox) using its review artifact and reproducibility guide. Its new runner is not yet on the default branch.
5. Request implementation assistance at [node@triviantech.com](mailto:node@triviantech.com).

The SDK is an unpublished source-installed prerelease, not a PyPI release. The
quickstart names immutable merged revisions and works without service credentials.

## Profiles and observable behavior

Assessment retains required-check diagnostics and gives definite false evidence
precedence over unknowns. It never grants permission. Local governed execution
binds action, input, subject, principals, scope and state, then asks one exact
TRIA backend for fresh authorization at the synchronous handoff. No cached ALLOW
or alternate-backend fallback is used.

Claim-independent local execution is available. Correction application and
claim-dependent release remain disabled pending their release gates. Fixed offline
fixtures exercise the correction candidate; they are not a runtime opt-in.

Host evidence is attributable input, not independently verified truth. A host
completion report is distinct from an observed external effect. F033 remains
unresolved; global freshness, independent-store convergence and distributed
no-resurrection are excluded. See the technical guides for full boundaries.

## Provenance and license

Originator: Sarasha Elion. Research lineage: Trivian Institute. Engineering home:
Trivian Technologies. Software/tests: MPL-2.0; applicable original documentation:
CC BY-SA 4.0. Preserve contributor notices and historical grants. See
[LICENSE.md](LICENSE.md) and [NOTICE.md](NOTICE.md).

The earlier planned HTTP description in `syzygy-rosetta-sdk.md` is historical
planning, not an adopted SDK API. The Protocol remains canonical for architecture
and normative commitments.

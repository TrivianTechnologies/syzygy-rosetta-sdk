# Open Rosetta SDK — local interoperability candidate

Open Rosetta provides non-authorizing assessment and a bounded public TRIA
integration. It provides no credentials, HTTP service or proprietary implementation.

Install the exact committed TRIA dependency and this source in an isolated environment:

```bash
python -m pip install -e ".[governed]" pytest
python -m pytest -q tests
```

The exact source fingerprint in `src/open_rosetta/_tria_source_pin.json` must match;
package version alone is insufficient. The pin is TRIA commit
`69a0b3739457e86f9e481cdfe4fa41e9810461cc` ([draft PR #61](https://github.com/TrivianTechnologies/tria-sdk/pull/61)); required review and CI remain pending.

Correction application and claim-dependent release are disabled by default pending
G01–G03 conformance and required review. Tests override the private gate only in
scoped offline fixtures; there is no supported runtime opt-in. Assessment and
claim-independent local governance remain available.

`assessment.assess` retains required-check diagnostics, implements false-over-unknown
precedence and never grants permission. Observations bind subject, scope, principals,
action/input identity, evidence version and local state.

`tria_adapter.TriaBinding` fixes one relationship and policy. Explicit `claim_refs`
enable canonical claim-context checking; empty refs retain the host precondition of
claim-independent behavior. Fresh ACT/consent/READ, final handoff, inclusive deadline
and explicit effect uncertainty remain mandatory. Hosts declare dependencies and
authenticate evidence; arbitrary executor semantics are not automatically inferred.

`correction.apply_correction` delegates graph-validated atomic correction to the
pinned kernel. A receipt does not prove uptake. The local Sandbox supplies paired
U01–U11 next-consumption/consequence controls. See [CANDIDATE.txt](CANDIDATE.txt).
Historical failure witnesses under `evidence/` belong to their original kernel;
they are separate from current conformance. F033 remains UNRESOLVED and excluded.

## Provenance and license

Originator: Sarasha Elion. Research lineage: Trivian Institute. Engineering home:
Trivian Technologies. Preserve contributor notices and historical grants.
Rights-to-license authority does not imply copyright assignment. Software/tests:
MPL-2.0; applicable original documentation: CC BY-SA 4.0. See [LICENSE.md](LICENSE.md)
and [NOTICE.md](NOTICE.md).

The earlier planned HTTP description remains in `syzygy-rosetta-sdk.md` as historical
planning, not an adopted API. The public Protocol repository remains canonical for
architecture and normative commitments:
https://github.com/TrivianTechnologies/syzygy-rosetta-protocol

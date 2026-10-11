# Verified source compatibility

The validated source tuple is:

| Component | Exact merged commit | Package/reference version |
|---|---|---|
| Protocol | `f12d85dd8af3dd0ab99f376906810c8e64d70702` | `2.1.0` reference; integration contract remains draft |
| TRIA | `03b8ef764a60c5ba01031ddaf363028e5c49f7d9` | `0.1.0a7` |
| Open Rosetta SDK | `9d784d8cee1aa6efdf5bb0ffe6360b44b4c4f114` | `0.0.0.dev0` |

All three are two-parent merge commits. Their trees are byte-identical to reviewed
PR heads `e679be06a4a9e6c67f468037b05b417148ac29a1`,
`69a0b3739457e86f9e481cdfe4fa41e9810461cc` and
`5e205c1eb1611a1c997526007df57e3724712652`, respectively. Post-merge CI passed.

The merged SDK pins the exact merged TRIA commit and verifies its full Python-source
fingerprint. Do not infer compatibility with another `0.1.0a7` build from its
package version alone.

Python 3.11–3.13 are exercised. Assessment, local handoff, correction simulation,
and packaging are separate evidence scopes. Bounded correction-dependent local
execution is enabled in this exact source tuple following independent review and
passing conformance/CI. A passing simulation does not certify production behavior,
host-supplied evidence or distributed systems. See the
[transition record](CORRECTION_ENABLEMENT.md).

TRIA event schema `0.3`, projection `0.6`, replay bundle `0.1`, operational spec
`0.1.3`, and correction-safety surface `0.1` remain unchanged. No revision or
supersession lifecycle events are added. F033 remains unresolved and excluded.

# Verified source compatibility

The validated source tuple is:

| Component | Exact merged commit | Package/reference version |
|---|---|---|
| Protocol | `f12d85dd8af3dd0ab99f376906810c8e64d70702` | `2.1.0` reference; integration contract remains draft |
| TRIA | `03b8ef764a60c5ba01031ddaf363028e5c49f7d9` | `0.1.0a7` |
| Open Rosetta SDK | `6f76a7c605014b2ce13c76e6884f22bbf53094df` | `0.0.0.dev0` |

All three are two-parent merge commits. Their trees are byte-identical to reviewed
PR heads `e679be06a4a9e6c67f468037b05b417148ac29a1`,
`69a0b3739457e86f9e481cdfe4fa41e9810461cc` and
`0e839497e128d39df235fef78203879bf1418f41`, respectively. Post-merge CI passed.

The merged SDK's source fingerprint references the reviewed TRIA ancestor. The
merged TRIA tree is identical, so its full Python-source fingerprint matches. This
onboarding candidate advances the metadata/dependency reference to the exact merge
commit without changing kernel hashes or runtime behavior. Do not infer compatibility
with another `0.1.0a7` build from its package version alone.

Python 3.11–3.13 are exercised. Assessment, local handoff, correction simulation,
and packaging are separate evidence scopes. A passing simulation does not certify
production behavior or a distributed system. The merged sources above retain the disabled correction gate. This branch prepares
a separate enabling candidate described in [the transition record](CORRECTION_ENABLEMENT.md);
its normal public API and installed artifacts require exact-head review/CI before
supported availability. The original onboarding installation remains pinned to
the merged, disabled SDK.

TRIA event schema `0.3`, projection `0.6`, replay bundle `0.1`, operational spec
`0.1.3`, and correction-safety surface `0.1` remain unchanged. No revision or
supersession lifecycle events are added. F033 remains unresolved and excluded.

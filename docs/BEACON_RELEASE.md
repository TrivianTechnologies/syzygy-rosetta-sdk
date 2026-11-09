# Rosetta Beacon — implementation and release evidence

Prepared 2026-11-08 (America/Los_Angeles). Status: local release candidate;
public deployment NOT performed; live URL NOT assigned. No new spending.

## Focused infrastructure audit

| Source inspected | Revision | Finding and reuse decision |
| --- | --- | --- |
| Open Rosetta SDK | `7ef98c73a49110204851daca8f0b8d0344e23b78` | Existing assessment-only engine, required checks, bindings, diagnostics and false-over-unknown semantics reused unchanged. Added optional host in this repository. |
| Rosetta Protocol | `6a433542851f28934d7c5f301f47c277cbfbf3e5` | Normative architecture and preserved invariants remain canonical; no protocol or invariant edits. This demo does not prove all normative commitments. |
| TRIA SDK | `96f2d35de0577e7a95c5baa4ce59b9d0927b5b20` | Existing machine discovery and read-only diagnostic contract inspected. TRIA separates diagnostics from execution authority. No SDK edits or public execution surface. Original Rosetta tests use their existing exact TRIA dependency `03b8ef764a60c5ba01031ddaf363028e5c49f7d9`. |
| Syzygy Core | Current main inspected through authenticated repository access | Private runtime and separate conversational host; its public/private boundary precludes copying implementation into this public release. Documentation and deployment configuration inspected, not a full Core security audit or new Core suite run. |
| Rosetta Sandbox | `2136b84a0bf8996c9a2b0a7ff13d020f9fc4a4ee` | Historical Flask/GCP deployment includes model-provider integration and content logging unsuitable for this assessment-only beacon. Existing address is explicitly unverified. It was not repurposed. |

No new repository, commercial product, cloud resource or provider account was
created. The optional ASGI host can run behind an existing ingress; actual current
hosting capacity, TLS/DNS, disk, logs and spend controls require account access.

## Implemented surface

- `/`: human landing page, experimental boundaries and developer entry points.
- `/.well-known/rosetta-beacon.json`: versioned custom discovery manifest (not a
  standardized MCP registry or A2A Agent Card).
- `/openapi.json`: generated OpenAPI with strict input/response shapes and bearer scheme.
- `/docs`, `/llms.txt`, `/robots.txt`: publicly readable discovery/documentation.
- `POST /v1/assess`: scoped expiring bearer plus explicit consent, fixed synthetic
  `current`, `revoked`, `unknown` scenarios, actual Rosetta assessment invocation.
- Optional official Python MCP SDK stdio adapter: `discover_beacon` and
  `assess_synthetic_scenario`, forwarding to the same configured HTTP host.

Authorization is deployment-owned bearer possession with explicit scope and
expiry. It is not proof of a real-world actor's identity or legitimate authority.
Fixture `consent_current` is distinct from invocation processing consent. Neither
creates permission for external actions. No executor, private memory, arbitrary
prompt, URL fetching, provider call, registration or administrator endpoint exists.

## Verification

- Full original SDK suite plus beacon checks: **203 passed** on Python 3.12.
  This consists of 178 original SDK tests and 25 new beacon tests.
- Installed wheel exercised over actual loopback HTTP by two separate processes
  with separate random scoped credentials: **both passed all three scenarios**.
- Official MCP client negotiated **2025-11-25**; tool listing, manifest discovery,
  successful invocation and explicit-consent denial passed. This is not a claim
  of compatibility with every MCP protocol revision or client implementation.
- Security witnesses: unauthorized/expired/revoked grants, false consent, strict
  booleans, unknown fields, duplicate JSON keys/headers, invalid JSON, size limit,
  Host/Origin rejection, absent privileged routes, per-token/global limits,
  persistent quota across restart, release cap, and failed storage fail closed.
- Application privacy: quota records inspected for absence of raw credentials,
  IP addresses and body contents. No application request-content logs are enabled.
  Hosting-platform telemetry remains unverified.
- Wheel and source distribution build succeeded. HTML/text assets included.
- Dependency audit of the locked third-party packages: no known vulnerabilities
  in the final report. This is advisory-database coverage, not security certification.
- Browser visual QA remains unverified: local Playwright has no installed Chromium.
  HTTP asset delivery is tested; no screenshot or visual-browser pass is claimed.

[Sanitized two-client evidence](BEACON_CLIENT_EVIDENCE.json) ·
[Dependency audit](BEACON_DEPENDENCY_AUDIT.json) ·
[Exact dependency lock](../deploy/beacon/requirements.lock) ·
[Reproduction and deployment](../deploy/beacon/README.md)

These independently configured protocol clients are scripted test clients, not
independently recruited users or model-driven autonomous agents. They establish
local interoperability. They do not establish autonomous discovery, public
availability, organic adoption, real-world consent correctness, scientific
validity, benefit, production readiness or resolution of F033.

## Costs, operations and remaining gates

Runtime model/API spend: **$0**, with no provider transport. New hosting spend:
**$0 incurred**. Reusing existing paid capacity could have $0 incremental compute
cost, but capacity/persistence/ingress are unverified. A comparison baseline is
approximately $7/month for a small always-on Render web service, plus disk,
bandwidth/taxes and applicable workspace charges, subject to the actual account
quote. Pricing source checked 2026-11-08: https://render.com/pricing .

Durable ceiling: 10000 assessment attempts per ledger; 10 requests per credential
per minute and 120 HTTP requests globally per minute. The application does not
impose a hard hosting-dollar cap. Require host-level billing controls, no scaling,
CPU/memory/ingress limits, persistent owner-only SQLite and blocked runtime egress.
An attacker can exhaust the global quota and deny availability; this intentionally
favors bounded resource use. A host compromise bypasses application assumptions.

Monitor health every five minutes, aggregate counters and errors daily during the
pilot, quota at 80%, storage persistence, TLS expiry and restarts. See deployment
instructions for credential rotation and rollback. Credentials require initial
operator provisioning; no per-request manual introduction or active human session.

Release blockers: verified existing hosting target/access and ingress configuration;
principal approval for that exact public deployment and any added recurring cost;
public TLS/privacy/restart checks and hosted two-client trial. Model-driven agent
trials and independently observed adoption remain separate unmet evidence gates.

# Integration boundaries

Use narrow host APIs that bind identity, resource, purpose, consent principal and
all relevant claim dependencies. An assessment is never a bearer credential.
The local bridge rechecks authority at handoff; it cannot protect delayed work
that a host queues and executes later without a new check.

Host evidence references provide attribution, not independent authentication.
The host is responsible for identity, source integrity, credential custody,
transport, external-effect observation, reconciliation and deployment safeguards.
A completed host report does not establish an independently observed effect.

The SDK is an in-process library, not a hostile-code sandbox. Raw Python access,
custom stores and direct database writes remain trusted infrastructure. Do not
expose relationship administration or the local adapter as a public endpoint.
The offline demo requires no server, secrets, customer data or privileged endpoint.

This enabling candidate exercises correction-dependent execution through the normal
public API without enabling overrides; supported availability still requires its
exact-head review, CI and merge gates. Overrides in preserved historical fixtures
are not an integration API. Preserve failure traces, reconcile unknown effects, and
use fresh authority for any retry. F033 remains unresolved; distributed freshness,
independent-store convergence and global no-resurrection are excluded.

Report technical issues with a synthetic reproducer to node@triviantech.com.
Do not include secrets or customer data in public issues or email examples.

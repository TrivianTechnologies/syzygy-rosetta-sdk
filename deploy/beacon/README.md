# Beacon deployment candidate — approval required

This adds an optional HTTP host to the existing Open Rosetta SDK repository.
It does not replace the sandbox, create a new repository, or import proprietary
Syzygy Core code. No deployment hook, hosting resource or auto-deploy was created.

## Reproduce locally

Use Python 3.12 in a fresh virtual environment from this repository:

```sh
python -m pip install -r deploy/beacon/requirements.lock
python -m pip install --no-deps .
python -m pytest -q beacon_tests
python beacon_tests/run_clients.py
```

The client runner creates temporary scoped grants, starts loopback Uvicorn,
launches two distinct client processes with separate credentials, discovers the
contract, verifies all three scenarios, and shuts everything down. It does not
call a model or any public endpoint. These are protocol clients, not independently
recruited users or autonomous model agents.

To run the original SDK suite as well, install `.[governed]` (the repository's
existing immutable TRIA pin), then `python -m pytest -q tests beacon_tests`.

## Existing-host release procedure

1. Identify the existing approved host and its ingress, deployment branch, budget,
   TLS domain, private process port and persistent disk. None is inferred from an
   old repository deployment address. Do not replace a running application.
2. Review this candidate and approve public deployment to that exact origin.
   Approve incremental hosting cost separately if it is not zero.
3. Install the tested lock and package into an isolated environment on that host.
   The beacon can run as a separate process behind the existing reverse proxy;
   this does not require a new paid platform. Do not mount the private sandbox.
4. Create an owner-only directory (`0700`) and set process umask `077`. Provision
   `ROSETTA_LEDGER` there on persistent local storage (not NFS or an ephemeral
   container filesystem). Back it up with its counters; do not reset it to evade
   the 10000-assessment cap. One host, one worker, no autoscaling.
5. Set `ROSETTA_ORIGIN` to the exact HTTPS origin. Set `ROSETTA_GRANTS` through the
   host secret store to a JSON object mapping SHA-256 token hashes to
   `{"scope":"beacon-synthetic-assessment/1","expires":UNIX_TIMESTAMP}`.
   Generate each raw token with `secrets.token_urlsafe(32)` and distribute through
   a secure invitation channel. Raw tokens must never enter URLs or logs. Maximum
   100 configured grants; expiration is mandatory. Removing a grant and restarting
   revokes it. No live session or per-call human intervention is needed afterward.
6. Run behind the reviewed ingress (example configuration adjacent):

```sh
umask 077
python -m uvicorn open_rosetta.beacon.app:app_from_env --factory \
  --host 127.0.0.1 --port 8766 --workers 1 --limit-concurrency 20 \
  --timeout-keep-alive 5 --no-access-log --log-level critical
```

7. Enforce TLS, ingress connection/body/slow-client limits, disabled access and
   sensitive error logs, process memory/CPU limits, no outbound runtime network
   access and no provider credentials. Check platform logging separately. The
   application itself contains no network client or model provider.
8. Set hosting budget controls and disable autoscaling. Application counters cap
   assessment work, not the provider's bandwidth/compute billing. Do not claim a
   hard dollar ceiling unless the host actually enforces one.
9. Verify restart preserves counters, then run `client_http.py` and `client_mcp.py`
   separately with scoped test credentials against the approved origin. Capture
   sanitized results. Repeat Host/Origin, expiry, quota, consent and deny-path
   checks on staging; do not exhaust the production ledger as a test.
10. Add a link from the existing ecosystem llms.txt and human developer page only
    after the URL is confirmed. Submission to search/MCP registries is separate;
    publishing these documents does not prove indexing, discovery or adoption.

## Monitoring and rollback

Check health every 5 minutes; it consumes the global request budget. Inspect
aggregate verdict and assessment-total counters locally daily during the pilot;
alert at 8000 assessments, disk errors, sustained 429/503, TLS expiry and process
restarts. No public metrics endpoint exists. Aggregate counters have no automatic
export, identity analytics or adoption attribution.

Stop the beacon process or remove its proxy route to disable all invocation.
Remove grants and restart for credential revocation. Preserve quota data and
release evidence. Roll back only to an approved package and lock with the same
quota ledger; never roll back authority or quota to manufacture available access.

## Cost and remaining deployment gates

Model/API cost is $0 by construction. Newly incurred hosting cost is $0 so far.
Incremental existing-host cost may be $0 if capacity, persistence and ingress
already suffice; that has not been verified. As a comparison, Render's pricing
search result checked 2026-11-08 lists $7/month for its smallest paid web service,
plus persistent storage, bandwidth/tax and any workspace charges. This is not a
quote for the user's account or approval to buy a service. Free sleeping services
do not meet an always-available beacon requirement.
Sources: https://render.com/pricing and https://render.com/docs/free .

Pending: exact existing host access/configuration; approval for public deployment;
provider cost cap and privacy/ingress verification; hosted two-client evidence;
separately configured model-agent trials if required for the final adoption gate.

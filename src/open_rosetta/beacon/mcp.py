# SPDX-License-Identifier: MPL-2.0
"""Operator-configured stdio adapter; same HTTP authorization, no local bypass."""
import os
from urllib.parse import urlsplit
import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP('Rosetta Beacon assessment-only')
origin = os.environ['ROSETTA_BEACON_URL']
u = urlsplit(origin)
if u.path or u.query or u.fragment or u.username or u.password or not u.netloc or (u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('127.0.0.1', 'localhost'))):
    raise ValueError('Exact HTTPS or loopback origin required')
token = os.environ['ROSETTA_BEACON_TOKEN']

@server.tool()
def discover_beacon() -> dict:
    """Read the configured beacon manifest. Discovery grants no execution authority."""
    with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
        response = client.get(origin + '/.well-known/rosetta-beacon.json')
        response.raise_for_status()
        return response.json()

@server.tool()
def assess_synthetic_scenario(scenario: str, consent: bool) -> dict:
    """With explicit operator authorization, assess current/revoked/unknown synthetic evidence only."""
    if scenario not in ('current', 'revoked', 'unknown') or consent is not True:
        raise ValueError('Valid scenario and explicit consent required')
    with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
        response = client.post(origin + '/v1/assess', headers={'Authorization': 'Bearer ' + token},
                               json={'scenario': scenario, 'consent': consent})
        if response.status_code != 200:
            raise ValueError('Beacon withheld assessment; HTTP ' + str(response.status_code))
        return response.json()

if __name__ == '__main__':
    server.run(transport='stdio')

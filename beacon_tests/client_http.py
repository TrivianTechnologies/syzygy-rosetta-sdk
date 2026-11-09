# SPDX-License-Identifier: MPL-2.0
"""Independently configured urllib agent-protocol client. No LLM or adoption claim."""
import json
import os
from urllib.request import Request, urlopen

origin = os.environ['ROSETTA_BEACON_URL']
token = os.environ['ROSETTA_BEACON_TOKEN']
def get(path):
    with urlopen(origin + path, timeout=10) as r: return json.load(r)
manifest = get('/.well-known/rosetta-beacon.json')
assert manifest['base_url'] == origin
spec = get('/openapi.json')
path = next(p for p, ops in spec['paths'].items() if ops.get('post',{}).get('operationId') == 'assessSyntheticScenario')
rows = []
for scenario, verdict in [('current','SURVIVES'),('revoked','FAILS'),('unknown','UNRESOLVED')]:
    request = Request(origin + path, data=json.dumps({'scenario':scenario,'consent':True}).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urlopen(request, timeout=10) as r: result=json.load(r)
    assert result['verdict'] == verdict and result['authorizes_execution'] is False
    rows.append({'scenario':scenario,'verdict':result['verdict'],'authorizes_execution':False})
print(json.dumps({'client':'stdlib-urllib','discovery':'manifest + OpenAPI operationId','results':rows}))

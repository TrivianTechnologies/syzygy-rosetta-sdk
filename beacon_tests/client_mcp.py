# SPDX-License-Identifier: MPL-2.0
"""Official MCP ClientSession in a separate process with a distinct credential."""
import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params=StdioServerParameters(command=sys.executable,args=['-m','open_rosetta.beacon.mcp'],
        env={k:os.environ[k] for k in ('ROSETTA_BEACON_URL','ROSETTA_BEACON_TOKEN')})
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as client:
            initialized=await client.initialize()
            tools=await client.list_tools()
            assert {t.name for t in tools.tools} == {'discover_beacon','assess_synthetic_scenario'}
            manifest=await client.call_tool('discover_beacon',{})
            assert not manifest.isError
            parsed=json.loads(manifest.content[0].text)
            assert parsed['base_url'] == os.environ['ROSETTA_BEACON_URL']
            rows=[]
            for scenario,verdict in [('current','SURVIVES'),('revoked','FAILS'),('unknown','UNRESOLVED')]:
                response=await client.call_tool('assess_synthetic_scenario',{'scenario':scenario,'consent':True})
                assert not response.isError
                result=json.loads(response.content[0].text)
                assert result['verdict']==verdict and result['authorizes_execution'] is False
                rows.append({'scenario':scenario,'verdict':result['verdict'],'authorizes_execution':False})
            denied=await client.call_tool('assess_synthetic_scenario',{'scenario':'current','consent':False})
            assert denied.isError
            print(json.dumps({'client':'official-python-mcp','protocol':initialized.protocolVersion,
                              'discovery':'MCP tools/list + discover_beacon','results':rows,'consent_denial':True}))
asyncio.run(main())

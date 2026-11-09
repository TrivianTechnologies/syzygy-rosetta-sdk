# SPDX-License-Identifier: MPL-2.0
"""Explicitly authorized local integration test. Secrets never leave subprocess env."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from open_rosetta.beacon.app import POLICY

here=Path(__file__).parent
with tempfile.TemporaryDirectory() as tmp:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    origin=f'http://127.0.0.1:{port}'
    tokens=[secrets.token_urlsafe(32) for _ in range(2)]
    grants={hashlib.sha256(t.encode()).hexdigest():{'scope':POLICY,'expires':int(time.time())+600} for t in tokens}
    env={**os.environ,'ROSETTA_ORIGIN':origin,'ROSETTA_GRANTS':json.dumps(grants),'ROSETTA_LEDGER':tmp+'/quota.db'}
    process=subprocess.Popen([sys.executable,'-m','uvicorn','open_rosetta.beacon.app:app_from_env','--factory',
        '--host','127.0.0.1','--port',str(port),'--workers','1','--no-access-log','--log-level','error'],env=env)
    try:
        for _ in range(100):
            if process.poll() is not None: raise RuntimeError('server exited')
            try:
                with urlopen(origin+'/healthz',timeout=1): break
            except OSError: time.sleep(.05)
        else: raise RuntimeError('server failed to become ready')
        results=[]
        for script,token in zip(('client_http.py','client_mcp.py'),tokens):
            run=subprocess.run([sys.executable,str(here/script)],env={**os.environ,'ROSETTA_BEACON_URL':origin,'ROSETTA_BEACON_TOKEN':token},
                               capture_output=True,text=True,timeout=40)
            if run.returncode:
                # Subprocesses do not print credentials. Never record their environment.
                raise RuntimeError(script+' failed: '+run.stderr)
            results.append(json.loads(run.stdout))
        print(json.dumps({'scope':'authorized synthetic localhost interoperability; not independent adoption or LLM-agent validation',
            'separate_processes':True,'distinct_credentials':True,'clients':results},indent=2))
    finally:
        process.terminate();process.wait(timeout=10)

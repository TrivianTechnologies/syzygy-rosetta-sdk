# SPDX-License-Identifier: MPL-2.0
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
from fastapi import Security
from pydantic import BaseModel, ConfigDict, StrictBool, Field
from typing import Literal

from open_rosetta.assessment import (
    EvidenceBinding, Observation, PROFILE, SCHEMA, REQUIRED, EVIDENCE_VERSION, assess,
)

CASES = ('current', 'revoked', 'unknown')
POLICY = 'beacon-synthetic-assessment/1'
ASSETS = Path(__file__).parent

class Demo(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    scenario: Literal['current', 'revoked', 'unknown']
    consent: StrictBool

class Result(BaseModel):
    scenario: str
    verdict: str
    authorizes_execution: Literal[False]
    synthetic: Literal[True]
    diagnostics: list[str]
    profile: str
    schema_id: str = Field(alias="schema")
    policy: str
    evidence_kind: str

class Ledger:
    """Bounded durable counters. No IPs, content, or raw credentials retained."""
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS counters (key TEXT PRIMARY KEY, n INTEGER NOT NULL)')
    def connect(self):
        return sqlite3.connect(self.path, timeout=1, isolation_level=None)
    def take(self, key, limit):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            n = db.execute('SELECT n FROM counters WHERE key=?', (key,)).fetchone()
            if n and n[0] >= limit:
                db.rollback()
                return False
            db.execute('INSERT INTO counters VALUES (?,1) ON CONFLICT(key) DO UPDATE SET n=n+1', (key,))
            db.commit()
            return True
    def minute(self, identity, limit):
        # Exactly one counter per finite configured identity, independent of attacker IP.
        minute = int(time.time() // 60)
        key = 'minute:' + identity
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT n FROM counters WHERE key=?', (key,)).fetchone()
            previous, count = divmod(row[0], 1000000) if row else (0, 0)
            count = count if previous == minute else 0
            if count >= limit:
                db.rollback()
                return False
            db.execute('INSERT INTO counters VALUES (?,?) ON CONFLICT(key) DO UPDATE SET n=excluded.n', (key, minute * 1000000 + count + 1))
            db.commit()
            return True


def demonstrate(scenario):
    binding = EvidenceBinding('synthetic:subject', 'synthetic:assessment',
        'synthetic:no-effect', hashlib.sha256(b'no-effect').hexdigest(),
        EVIDENCE_VERSION, 'synthetic:' + scenario)
    values = {k: True for k in REQUIRED}
    if scenario == 'revoked':
        values['consent_current'] = False
    if scenario == 'unknown':
        values['authority_current'] = None
    report = assess([Observation(k, values[k], 'fixture:' + scenario, binding) for k in REQUIRED],
                    profile=PROFILE, schema=SCHEMA, binding=binding)
    return dict(scenario=scenario, verdict=report.verdict.value,
        authorizes_execution=report.authorizes_execution, synthetic=True,
        diagnostics=list(report.diagnostics), profile=report.profile, schema=report.schema,
        policy=POLICY, evidence_kind='fixed host assertions; not real-world verification')


def create_app(origin, grants, ledger_path):
    u = urlsplit(origin)
    if (u.scheme not in ('https', 'http') or not u.netloc or u.path or u.query or u.fragment
        or u.username or u.password or (u.scheme == 'http' and u.hostname not in ('127.0.0.1', 'localhost'))):
        raise ValueError('An exact HTTPS origin (or local loopback HTTP) is required')
    if not isinstance(grants, dict) or not 1 <= len(grants) <= 100:
        raise ValueError('1 to 100 explicit grants required')
    for digest, grant in grants.items():
        if (not re.fullmatch('[0-9a-f]{64}', digest) or not isinstance(grant, dict)
            or set(grant) != {'scope', 'expires'} or grant['scope'] != POLICY
            or type(grant['expires']) is not int or grant['expires'] <= time.time()):
            raise ValueError('Invalid or expired scoped grant')
    ledger = Ledger(ledger_path)
    app = FastAPI(title='Rosetta Beacon', version='0.1.0', docs_url=None, redoc_url=None)
    app.state.ledger = ledger

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({'error': 'invalid_request'}, status_code=422)

    @app.middleware('http')
    async def guard(request: Request, call_next):
        response = None
        singleton_headers = ('host', 'origin', 'authorization', 'content-type', 'content-length')
        if any(len(request.headers.getlist(h)) > 1 for h in singleton_headers):
            response = JSONResponse({'error': 'ambiguous_headers'}, status_code=400)
        elif request.headers.get('host') != u.netloc or request.headers.get('origin', origin) != origin:
            response = JSONResponse({'error': 'origin_or_host_denied'}, status_code=403)
        elif request.url.query:
            response = JSONResponse({'error': 'query_not_supported'}, status_code=400)
        try:
            if response is None and not ledger.minute('global', 120):
                response = JSONResponse({'error': 'rate_limit'}, status_code=429, headers={'Retry-After': '60'})
            if response is None and request.method == 'POST':
                if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                    response = JSONResponse({'error': 'json_required'}, status_code=415)
                else:
                    body = b''
                    async for chunk in request.stream():
                        body += chunk
                        if len(body) > 2048:
                            response = JSONResponse({'error': 'body_limit'}, status_code=413)
                            break
                    if response is None:
                        def pairs(items):
                            result = {}
                            for k, v in items:
                                if k in result: raise ValueError('duplicate')
                                result[k] = v
                            return result
                        try:
                            json.loads(body, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
                        except (ValueError, RecursionError, UnicodeError):
                            response = JSONResponse({'error': 'invalid_json'}, status_code=400)
                        request._body = body
            if response is None:
                response = await call_next(request)
        except Exception:
            # No exception text or submitted content enters logs/responses.
            response = JSONResponse({'error': 'unavailable'}, status_code=503)
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'",
            'Referrer-Policy': 'no-referrer'})
        return response

    async def authorized(request: Request, credentials=Security(HTTPBearer(auto_error=False))):
        if credentials is None or len(credentials.credentials) > 256:
            raise HTTPException(401, 'credential_required', headers={'WWW-Authenticate': 'Bearer'})
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        grant = grants.get(digest)
        if not grant or grant['expires'] <= time.time() or grant['scope'] != POLICY:
            raise HTTPException(403, 'grant_denied')
        if not ledger.minute(digest, 10):
            raise HTTPException(429, 'rate_limit', headers={'Retry-After': '60'})
        return digest

    @app.get('/', response_class=HTMLResponse, include_in_schema=False)
    def landing():
        return (ASSETS / 'index.html').read_text()

    @app.get('/healthz', include_in_schema=False)
    def health():
        return {'status': 'ok', 'mode': 'assessment-only'}

    @app.get('/.well-known/rosetta-beacon.json')
    def manifest():
        return {'schema': 'rosetta-beacon/0.1', 'name': 'Rosetta Beacon', 'base_url': origin,
            'openapi': origin + '/openapi.json', 'documentation': origin + '/docs',
            'assessment': origin + '/v1/assess', 'policy': POLICY, 'scenarios': list(CASES),
            'discovery_authentication': 'none', 'invocation_authentication': 'scoped expiring bearer',
            'credential_request': 'mailto:node@triviantech.com',
            'authorizes_execution': False, 'synthetic_only': True, 'model_calls': False,
            'mcp': {'transport': 'stdio', 'module': 'open_rosetta.beacon.mcp',
                    'remote_transport': None, 'requires_operator_configuration': True},
            'source': 'https://github.com/TrivianTechnologies/syzygy-rosetta-sdk',
            'tria': 'https://github.com/TrivianTechnologies/tria-sdk',
            'adoption_claim': 'none; publication does not establish discovery or adoption'}

    @app.get('/docs', response_class=PlainTextResponse, include_in_schema=False)
    def docs():
        return (ASSETS / 'developer.txt').read_text()

    @app.get('/llms.txt', response_class=PlainTextResponse, include_in_schema=False)
    def llms():
        return '# Rosetta Beacon\nAssessment only; no permission to execute.\n' + '\n'.join(origin+p for p in ('/.well-known/rosetta-beacon.json', '/openapi.json', '/docs'))

    @app.get('/robots.txt', response_class=PlainTextResponse, include_in_schema=False)
    def robots():
        return 'User-agent: *\nAllow: /\nDisallow: /v1/\n'

    @app.post('/v1/assess', response_model=Result, operation_id='assessSyntheticScenario',
              description='Fixed synthetic Rosetta assessment. Never authorizes execution. Explicit processing consent and scoped bearer required.')
    def assessment(body: Demo, identity=Security(authorized)):
        if body.consent is not True:
            raise HTTPException(403, 'consent_required')
        if not ledger.take('assessment_total', 10000):
            raise HTTPException(429, 'release_quota_exhausted')
        result = demonstrate(body.scenario)
        # Only aggregate verdict counts; no subject, token, IP, request or response logs.
        ledger.take('outcome:' + result['verdict'], 10000)
        return result
    return app


def app_from_env():
    return create_app(os.environ['ROSETTA_ORIGIN'], json.loads(os.environ['ROSETTA_GRANTS']),
                      os.environ['ROSETTA_LEDGER'])

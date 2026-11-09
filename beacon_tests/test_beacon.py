# SPDX-License-Identifier: MPL-2.0
import hashlib
import json
import time
import pytest
from fastapi.testclient import TestClient
from open_rosetta.beacon.app import create_app, POLICY

TOKEN = 'synthetic-test-credential-not-for-deployment'
DIGEST = hashlib.sha256(TOKEN.encode()).hexdigest()

@pytest.fixture
def setup(tmp_path):
    grants = {DIGEST: {'scope': POLICY, 'expires': int(time.time()) + 3600}}
    app = create_app('http://127.0.0.1', grants, str(tmp_path / 'ledger.db'))
    return app, TestClient(app, base_url='http://127.0.0.1'), grants


def post(client, body=None, token=TOKEN, **kwargs):
    return client.post('/v1/assess', json=body or {'scenario':'current','consent':True},
        headers={'Authorization':'Bearer '+token}, **kwargs)

@pytest.mark.parametrize('scenario,verdict', [('current','SURVIVES'),('revoked','FAILS'),('unknown','UNRESOLVED')])
def test_real_engine(setup, scenario, verdict):
    app, client, _ = setup
    r = post(client, {'scenario':scenario,'consent':True})
    assert r.status_code == 200
    assert r.json()['verdict'] == verdict
    assert r.json()['authorizes_execution'] is False
    assert r.json()['synthetic'] is True

@pytest.mark.parametrize('path', ['/', '/docs', '/openapi.json', '/llms.txt','/robots.txt','/.well-known/rosetta-beacon.json'])
def test_discovery(setup, path):
    r = setup[1].get(path)
    assert r.status_code == 200
    assert 'nosniff' == r.headers['x-content-type-options']

@pytest.mark.parametrize('body', [ {'scenario':'execute','consent':True}, {'scenario':'current','consent':'true'}, {'scenario':'current','consent':1}, {'scenario':'current','consent':True,'url':'https://example.com'}, {} ])
def test_invalid_fields(setup, body):
    r=setup[1].post('/v1/assess',json=body,headers={'Authorization':'Bearer '+TOKEN})
    assert r.status_code == 422
    assert 'example.com' not in r.text


def test_authority_and_consent(setup):
    app, client, grants = setup
    assert client.post('/v1/assess',json={'scenario':'current','consent':True}).status_code == 401
    assert post(client, token='wrong').status_code == 403
    assert post(client, {'scenario':'current','consent':False}).status_code == 403
    grants[DIGEST]['expires']=0
    assert post(client).status_code == 403
    del grants[DIGEST]
    assert post(client).status_code == 403

@pytest.mark.parametrize('raw', ['{"scenario":"current","scenario":"revoked","consent":true}', '{', '[NaN]', '"'+('x'*2050)+'"'])
def test_bounded_json(setup,raw):
    r=setup[1].post('/v1/assess',content=raw,headers={'Content-Type':'application/json'})
    assert r.status_code in (400,413)


def test_transport_boundaries(setup):
    c=setup[1]
    assert c.get('/',headers={'Host':'evil.example'}).status_code == 403
    assert c.get('/',headers={'Origin':'https://evil.example'}).status_code == 403
    assert c.get('/?token=secret').status_code == 400
    assert c.post('/v1/assess',content='text').status_code == 415
    assert c.get('/v1/assess').status_code == 405
    for p in ('/execute','/memory','/admin','/metrics','/mcp'):
        assert c.get(p).status_code == 404


def test_durable_quotas_and_no_content(setup, monkeypatch):
    now = time.time()
    monkeypatch.setattr("open_rosetta.beacon.app.time.time", lambda: now)
    app, c, _=setup
    for _ in range(10): assert post(c).status_code == 200
    assert post(c).status_code == 429
    ledger=app.state.ledger
    with ledger.connect() as db:
        rows=db.execute('SELECT * FROM counters').fetchall()
    assert TOKEN not in repr(rows) and '127.0.0.1' not in repr(rows)
    assert sum(n for k,n in rows if k=='assessment_total') == 10
    # Reconstructed process shares the quota.
    fresh=create_app('http://127.0.0.1',setup[2],ledger.path)
    assert post(TestClient(fresh,base_url='http://127.0.0.1')).status_code == 429


def test_release_cap_and_storage_failure(setup):
    app,c,_=setup
    with app.state.ledger.connect() as db:
        db.execute('INSERT INTO counters VALUES (?,?)',('assessment_total',10000))
    assert post(c).status_code==429
    app.state.ledger.path='/missing/ledger.db'
    assert post(c).status_code==503


def test_fail_closed_configuration(tmp_path):
    for origin,grants in [('https://good.example',{}),('http://evil.example',{DIGEST:{'scope':POLICY,'expires':int(time.time())+3600}})]:
        with pytest.raises(ValueError): create_app(origin,grants,str(tmp_path/'db'))


def test_global_limit(setup, monkeypatch):
    now = time.time()
    monkeypatch.setattr("open_rosetta.beacon.app.time.time", lambda: now)
    c=setup[1]
    for _ in range(120): assert c.get('/healthz').status_code==200
    assert c.get('/healthz').status_code==429


def test_ambiguous_headers(setup):
    assert setup[1].get("/", headers=[("Origin", "http://127.0.0.1"), ("Origin", "https://evil.example")]).status_code == 400

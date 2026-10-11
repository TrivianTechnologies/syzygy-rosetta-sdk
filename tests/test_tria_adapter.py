# SPDX-License-Identifier: MPL-2.0
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import pytest
import tria
from open_rosetta.assessment import Observation, REQUIRED
from open_rosetta import tria_adapter as a

NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def configured():
    rel=tria.Tria().create_relationship(['human:a','agent:b'])
    rel.grant_consent('human:a','local-effect',purpose='audit')
    rel.admin.grant_permission('human:a','agent:b','local:effect',tria.Capability.ACT,purpose='audit')
    binding=a.TriaBinding(rel,a.ReleasePolicy('agent:b','local:effect','human:a','local-effect','audit','human:a'))
    return rel,binding


def release(binding, executor, **kw):
    args=dict(request_id='attempt:1', action_id='action:1', input_data={'value':1}, action='local simulated effect',
              observations=[Observation(k,True,'host:fixture') for k in REQUIRED],
              last_correctable_at=NOW,executor=executor)
    args.update(kw)
    context=binding.evidence_binding(**{k:args[k] for k in ('action_id','action','input_data','last_correctable_at')})
    args['observations']=[replace(o,binding=context) if o.binding is None else o for o in args['observations']]
    return binding.release(**args)


@pytest.mark.parametrize('offset,entered', [(-1,True),(0,True),(1,False)])
def test_inclusive_deadline(monkeypatch,offset,entered):
    monkeypatch.setattr(a,'_now',lambda:NOW+timedelta(microseconds=offset))
    _,binding=configured(); calls=[]
    result=release(binding,lambda p:calls.append(p) or a.HostReport('COMPLETED'))
    assert result.host_entered is entered and len(calls)==int(entered)
    assert result.effect_observation == ('UNKNOWN' if entered else 'NOT_ATTEMPTED')
    if not entered:
        assert result.disposition=='DEADLINE_DENIED'
        assert result.backend_receipt.executed  # Wrapper entered, not external host.
        assert result.backend_receipt.result.status=='UNKNOWN_EFFECT'


@pytest.mark.parametrize('kind',['consent','permission'])
def test_revocation_after_translation_blocks_current_handoff(monkeypatch,kind):
    monkeypatch.setattr(a,'_now',lambda:NOW)
    rel,binding=configured(); original=a._LocalTranslation.translate
    def translate(self,plan,**kw):
        payload=original(self,plan,**kw)
        if kind=='consent': rel.revoke_consent('human:a','local-effect')
        else: rel.admin.revoke_permission('human:a','agent:b','local:effect',tria.Capability.ACT)
        return payload
    monkeypatch.setattr(a._LocalTranslation,'translate',translate)
    calls=[]; result=release(binding,lambda p:calls.append(p))
    assert result.disposition=='TRIA_DENIED' and calls==[]


def test_previous_allow_does_not_survive_revocation(monkeypatch):
    monkeypatch.setattr(a,'_now',lambda:NOW)
    rel,binding=configured(); calls=[]
    assert release(binding,lambda p:calls.append(p)).host_entered
    rel.revoke_consent('human:a','local-effect')
    assert not release(binding,lambda p:calls.append(p),request_id='attempt:2').host_entered
    assert len(calls)==1


@pytest.mark.parametrize('value',[False,None])
def test_assessment_denial_never_reaches_tria_or_host(value):
    rel,binding=configured(); before=rel.events; calls=[]
    result=release(binding,lambda p:calls.append(p),observations=[Observation(k,value,'host:fixture') for k in REQUIRED])
    assert result.disposition=='ASSESSMENT_DENIED' and calls==[] and rel.events==before


@pytest.mark.parametrize('response',[None,{},a.HostReport('FAILED'),a.HostReport('COMPLETED')])
def test_host_report_does_not_prove_external_effect(monkeypatch,response):
    monkeypatch.setattr(a,'_now',lambda:NOW)
    _,binding=configured(); calls=[]
    result=release(binding,lambda p:calls.append(p) or response)
    assert len(calls)==1 and result.host_entered and result.effect_observation=='UNKNOWN'


def test_exception_unknown_without_retry_or_secret_leak(monkeypatch):
    monkeypatch.setattr(a,'_now',lambda:NOW)
    _,binding=configured(); calls=[]
    def execute(p): calls.append(p); raise RuntimeError('credential-like-private-detail')
    result=release(binding,execute)
    assert len(calls)==1 and result.disposition=='HOST_ERROR' and result.effect_observation=='UNKNOWN'
    assert 'credential-like-private-detail' not in repr(result)
    with pytest.raises(tria.InvocationAlreadyStartedError): release(binding,execute)
    assert len(calls)==1


def test_binding_has_no_runtime_backend_selection():
    _,binding=configured()
    with pytest.raises(FrozenInstanceError): binding.relationship=tria.Tria().create_relationship(['other'])


@pytest.mark.parametrize('bad',['missing','version','source'])
def test_backend_failure_never_falls_back(monkeypatch,bad):
    _,binding=configured(); calls=[]
    if bad=='missing':
        def missing(name): raise ImportError('missing backend')
        monkeypatch.setattr(a.importlib,'import_module',missing)
    elif bad=='version': monkeypatch.setattr(a,'version',lambda name:'999')
    else: monkeypatch.setattr(a.hashlib,'sha256',lambda value:type('Mismatch',(),{'hexdigest':lambda self:'wrong'})())
    with pytest.raises(a.BackendUnavailable): release(binding,lambda p:calls.append(p))
    assert calls==[]


def test_naive_boundary_rejected():
    _,binding=configured()
    with pytest.raises(ValueError): release(binding,lambda p:None,last_correctable_at=NOW.replace(tzinfo=None))


def test_async_executor_rejected_before_entry():
    _,binding=configured()
    async def execute(p): pass
    with pytest.raises(TypeError): release(binding,execute)

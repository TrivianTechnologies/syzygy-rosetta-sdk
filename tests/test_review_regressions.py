# SPDX-License-Identifier: MPL-2.0
"""Independent-review regressions, added after the first private snapshot."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pytest
import tria
from open_rosetta.assessment import Observation, EvidenceBinding, EVIDENCE_VERSION, REQUIRED, PROFILE, SCHEMA, Verdict, assess
from open_rosetta import tria_adapter as a

NOW=datetime(2026,10,10,tzinfo=timezone.utc)


class PermissiveEquality:
    def __eq__(self, other): return True
    def __ne__(self, other): return False


class StringSubclass(str): pass


@pytest.mark.parametrize('field',['profile','schema'])
@pytest.mark.parametrize('value',[PermissiveEquality(),None,1,b'bytes',StringSubclass(PROFILE)])
def test_identifiers_require_exact_strings(field,value):
    binding=EvidenceBinding('subject','scope','action','a'*64,EVIDENCE_VERSION,'state')
    items=[Observation(k,True,'host:fixture',binding) for k in REQUIRED]
    args={'profile':PROFILE,'schema':SCHEMA,'binding':binding}; args[field]=value
    result=assess(items,**args)
    assert result.verdict is Verdict.UNRESOLVED
    assert 'invalid_'+field+'_type' in result.diagnostics
    assert result.observations==tuple(items)


def setup(monkeypatch):
    monkeypatch.setattr(a,'_now',lambda:NOW)
    rel=tria.Tria().create_relationship(['human:a','agent:b'])
    rel.grant_consent('human:a','scope',purpose='audit')
    rel.admin.grant_permission('human:a','agent:b','local:effect',tria.Capability.ACT,purpose='audit')
    binding=a.TriaBinding(rel,a.ReleasePolicy('agent:b','local:effect','human:a','scope','audit','subject:one'))
    args=dict(action_id='action:stable',action='local action',input_data={'value':[1]},last_correctable_at=NOW)
    evidence=binding.evidence_binding(**args)
    items=[Observation(k,True,'host:fixture',evidence) for k in REQUIRED]
    return rel,binding,args,items


@pytest.mark.parametrize('change',['action','action_id','input','deadline','subject','scope','target','purpose','evidence_version','state'])
def test_cross_action_subject_scope_or_state_replay_denied(monkeypatch,change):
    rel,binding,args,items=setup(monkeypatch)
    if change in ('action','action_id'): args[change]='different'
    elif change=='input': args['input_data']['value'].append(2)
    elif change=='deadline': args['last_correctable_at']+=timedelta(seconds=1)
    elif change=='evidence_version': items=[replace(o,binding=replace(o.binding,evidence_version='unknown')) for o in items]
    elif change=='state': rel.register_claim('agent:b',tria.EpistemicType.OBSERVATION,'new',source_refs=['host:new'])
    else:
        field={'subject':'subject','scope':'consent_scope','target':'resource','purpose':'purpose'}[change]
        binding=a.TriaBinding(rel,replace(binding.policy,**{field:'different'}))
    calls=[]
    result=binding.release(request_id='attempt:1',observations=items,executor=lambda p:calls.append(p),**args)
    assert result.disposition=='ASSESSMENT_DENIED' and calls==[]
    assert any(d.startswith('binding_mismatch:') for d in result.assessment.diagnostics)


@pytest.mark.parametrize('change',['input','state'])
def test_mutation_during_preparation_denied_before_host_entry(monkeypatch,change):
    rel,binding,args,items=setup(monkeypatch); original=a._LocalTranslation.translate
    def translate(self,plan,**kwargs):
        payload=original(self,plan,**kwargs)
        if change=='input': args['input_data']['value'].append(2)
        else: rel.register_claim('agent:b',tria.EpistemicType.OBSERVATION,'new',source_refs=['host:new'])
        return payload
    monkeypatch.setattr(a._LocalTranslation,'translate',translate)
    calls=[]
    result=binding.release(request_id='attempt:1',observations=items,executor=lambda p:calls.append(p),**args)
    assert result.disposition=='BINDING_CHANGED' and not result.host_entered and calls==[]
    assert result.backend_receipt.result.status=='UNKNOWN_EFFECT'


def test_stable_action_correlation_and_boundary_observation(monkeypatch):
    _,binding,args,items=setup(monkeypatch); calls=[]
    result=binding.release(request_id='attempt:1',observations=items,executor=lambda p:calls.append(p),**args)
    assert result.action_id=='action:stable' and result.request_id=='attempt:1'
    assert result.backend_receipt.plan.request.action_ref==result.action_id
    assert calls[0].payload['action_id']==result.action_id
    assert calls[0].payload['action_digest']==result.action_digest==items[0].binding.action_digest
    assert calls[0].payload['subject']=='subject:one'
    assert len(result.boundary_evidence)==2
    assert all(b.deadline==b.observed_at==NOW and b.inclusive for b in result.boundary_evidence)
    assert [b.stage for b in result.boundary_evidence]==['preflight','host-handoff']


def test_canonical_input_order_is_stable(monkeypatch):
    _,binding,args,_=setup(monkeypatch)
    args['input_data']={'b':2,'a':1}; first=binding.evidence_binding(**args)
    args['input_data']={'a':1,'b':2}; assert binding.evidence_binding(**args)==first


def test_unbound_generic_observations_never_authorize(monkeypatch):
    _,binding,args,items=setup(monkeypatch); calls=[]
    result=binding.release(request_id='attempt:1',observations=[replace(o,binding=None) for o in items],executor=lambda p:calls.append(p),**args)
    assert result.disposition=='ASSESSMENT_DENIED' and calls==[]


def test_fabricated_comparison_object_not_valid_binding():
    with pytest.raises(ValueError): EvidenceBinding(PermissiveEquality(),'scope','action','a'*64,EVIDENCE_VERSION,'state')


def test_consent_principal_replay_rejected_with_both_principals_authorized(monkeypatch):
    rel,binding,args,_=setup(monkeypatch)
    rel.grant_consent('agent:b','scope',purpose='audit')
    first=binding.evidence_binding(**args)
    alternative=a.TriaBinding(rel,replace(binding.policy,consent_actor='agent:b'))
    second=alternative.evidence_binding(**args)
    assert first.state_context==second.state_context
    assert first.action_digest!=second.action_digest
    observations=[Observation(k,True,'host:fixture',first) for k in REQUIRED]
    calls=[]; before=rel.events
    denied=alternative.release(request_id='attempt:wrong-consent',observations=observations,executor=lambda p:calls.append(p),**args)
    assert denied.disposition=='ASSESSMENT_DENIED' and calls==[]
    assert rel.events==before and denied.backend_receipt is None
    # Fresh evidence for the second authorized principal can still release.
    accepted=alternative.release(request_id='attempt:correct-consent',
        observations=[replace(o,binding=second) for o in observations],
        executor=lambda p:calls.append(p),**args)
    assert accepted.host_entered and len(calls)==1


@pytest.mark.parametrize('principal',['actor','consent_actor','subject'])
def test_every_policy_principal_changes_evidence_identity(monkeypatch,principal):
    rel,binding,args,_=setup(monkeypatch)
    before=binding.evidence_binding(**args)
    alternative=a.TriaBinding(rel,replace(binding.policy,**{principal:'different-principal'}))
    after=alternative.evidence_binding(**args)
    assert before.state_context==after.state_context
    assert before.action_digest!=after.action_digest

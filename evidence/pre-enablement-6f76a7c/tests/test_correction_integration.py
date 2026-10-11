# SPDX-License-Identifier: MPL-2.0
from datetime import datetime,timezone,timedelta
import pytest
import tria
from open_rosetta.assessment import Observation,REQUIRED
from open_rosetta.tria_adapter import TriaBinding,ReleasePolicy
from open_rosetta.correction import apply_correction


@pytest.fixture(autouse=True)
def offline_conformance_only(monkeypatch):
    # Exercise candidate behavior without enabling the shipped release gate.
    monkeypatch.setattr('open_rosetta.conformance._CORRECTION_EXECUTION_ENABLED', True)


def fixture():
    rel=tria.Tria().create_relationship(['human:a','agent:b'])
    source=rel.register_claim('agent:b',tria.EpistemicType.OBSERVATION,'source',source_refs=['host:source']).claim_id
    child=rel.register_claim('agent:b',tria.EpistemicType.INFERENCE,'decision',derived_from=[source]).claim_id
    rel.grant_consent('human:a','scope')
    for ref,cap in [('local:effect',tria.Capability.ACT),('truth-integrity:corrections',tria.Capability.ACT),('claim:'+source,tria.Capability.READ),('claim:'+child,tria.Capability.READ)]:
        rel.admin.grant_permission('human:a','agent:b',ref,cap)
    binding=TriaBinding(rel,ReleasePolicy('agent:b','local:effect','human:a','scope','audit','subject'),(child,))
    correction=tria.CorrectionEvidence('correction:1',source,'human:a',('host:new',),tria.CorrectionDisposition.WARRANTED)
    return rel,source,child,binding,correction


def release(binding,calls):
    args=dict(action_id='action:1',action='local decision',input_data={},last_correctable_at=datetime.now(timezone.utc)+timedelta(minutes=1))
    identity=binding.evidence_binding(**args)
    return binding.release(request_id='attempt:'+str(len(binding.relationship.events)),observations=[Observation(k,True,'host:check',identity) for k in REQUIRED],executor=lambda p:calls.append(p),**args)


def test_actual_correction_changes_next_consumption_and_withholds_effect():
    rel,source,child,binding,correction=fixture(); calls=[]
    assert release(binding,calls).host_entered
    assert calls[0].payload['claim_context'][0]['status']=='ACTIVE'
    snap=tria.snapshot_correction_graph(rel,source)
    receipt=apply_correction(binding,correction,snap,acceptance_ref='host:accepted')
    assert receipt.backend_receipt.outcome is tria.GovernanceOutcome.ALLOW
    assert receipt.authority_event_ref and receipt.before_head!=receipt.after_head
    denied=release(binding,calls)
    assert denied.disposition=='CLAIM_CONTEXT_DENIED' and len(calls)==1
    context=tria.Runtime().prepare(rel,tria.InvocationRequest('agent:b','inspect','local',context_resources=('claim:'+child,))).context[0]
    assert context.claim_status=='CONTESTED' and context.contestation_refs


def test_ancestor_read_is_mandatory_not_only_declared_child():
    rel,source,child,binding,_=fixture(); calls=[]
    rel.admin.revoke_permission('human:a','agent:b','claim:'+source,tria.Capability.READ)
    assert release(binding,calls).disposition=='TRIA_DENIED' and calls==[]


def test_stale_correction_snapshot_is_not_repaired_silently():
    rel,source,child,binding,correction=fixture()
    snap=tria.snapshot_correction_graph(rel,source)
    rel.register_claim('agent:b',tria.EpistemicType.INFERENCE,'new dependency',derived_from=[source])
    result=apply_correction(binding,correction,snap,acceptance_ref='host:accepted')
    assert result.backend_receipt.outcome is tria.GovernanceOutcome.BLOCK
    assert rel.state.claims[child].status is tria.ClaimStatus.ACTIVE


@pytest.mark.parametrize('invalid',['',None,False])
def test_missing_acceptance_evidence_never_applies(invalid):
    rel,source,child,binding,correction=fixture(); snap=tria.snapshot_correction_graph(rel,source); before=rel.events
    with pytest.raises(ValueError): apply_correction(binding,correction,snap,acceptance_ref=invalid)
    assert rel.events==before


def test_declared_claims_are_part_of_action_identity():
    rel,source,child,binding,_=fixture()
    alternate=TriaBinding(rel,binding.policy,(source,))
    args=dict(action_id='same',action='same',input_data={},last_correctable_at=datetime.now(timezone.utc))
    assert binding.evidence_binding(**args).action_digest!=alternate.evidence_binding(**args).action_digest


def test_unknown_required_claim_fails_closed():
    rel,source,child,binding,_=fixture()
    with pytest.raises(ValueError): TriaBinding(rel,binding.policy,('missing',))


@pytest.mark.parametrize('head',[None,'',' ',False,123,b'a'*64,'a'*63,'a'*65,'g'*64,'A'*64])
def test_invalid_snapshot_head_never_mutates(head):
    rel,source,child,binding,correction=fixture()
    snapshot=tria.snapshot_correction_graph(rel,source)
    # Exercise the SDK boundary independently of constructor validation.
    object.__setattr__(snapshot,'head_hash',head)
    before=tuple(rel.events)
    with pytest.raises(ValueError):
        apply_correction(binding,correction,snapshot,acceptance_ref='host:accepted')
    assert tuple(rel.events)==before
    assert all(rel.state.claims[ref].status is tria.ClaimStatus.ACTIVE for ref in (source,child))

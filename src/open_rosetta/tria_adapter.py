# SPDX-License-Identifier: MPL-2.0
"""Unpublished candidate: one pinned TRIA relationship, synchronous local entry.

The host authenticates identities/evidence and owns transport and effects. This
module grants no distributed freshness or correction-context compatibility.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import version
import inspect
import json
from pathlib import Path

from .assessment import Assessment, EvidenceBinding, EVIDENCE_VERSION, PROFILE, SCHEMA, Verdict, assess
from .conformance import require_correction_conformance


class BackendUnavailable(RuntimeError):
    pass


def _load_backend():
    try:
        pin = json.loads(Path(__file__).with_name('_tria_source_pin.json').read_text())
        tria = importlib.import_module('tria')
        if version('tria-sdk') != pin['version'] or tria.__version__ != pin['version']:
            raise ValueError('version mismatch')
        root = Path(tria.__file__).resolve().parent
        actual = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in root.rglob('*.py')}
        if actual != pin['python_sources']:
            raise ValueError('source pin mismatch')
        return tria
    except (ImportError, OSError, ValueError, AttributeError) as error:
        raise BackendUnavailable('Exact public TRIA source pin unavailable or incompatible.') from error


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ReleasePolicy:
    actor: str
    resource: str
    consent_actor: str
    consent_scope: str
    purpose: str
    subject: str

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() for v in vars(self).values()):
            raise ValueError('All policy fields must be nonempty strings.')


@dataclass(frozen=True)
class HostReport:
    """Host-reported completion is distinct from independently observed effects."""
    status: str

    def __post_init__(self):
        if self.status not in ('COMPLETED', 'FAILED', 'UNKNOWN_EFFECT'):
            raise ValueError('Unrecognized host status.')


@dataclass(frozen=True)
class ReleaseRecord:
    request_id: str
    assessment: Assessment
    disposition: str
    host_entered: bool
    effect_observation: str
    backend_receipt: object | None
    action_id: str
    action_digest: str
    subject: str
    scope: str
    boundary_evidence: tuple


@dataclass(frozen=True)
class BoundaryObservation:
    deadline: datetime
    observed_at: datetime
    stage: str
    state_context: str
    inclusive: bool = True


def _canonical(value):
    # Reject user-defined equality/serialization and lossy key coercion.
    def validate(v):
        if v is None or type(v) in (bool, int, str): return
        if type(v) is list:
            for item in v: validate(item)
        elif type(v) is dict and all(type(k) is str for k in v):
            for item in v.values(): validate(item)
        else: raise TypeError('Input must use JSON objects, arrays, strings, integers, booleans or null.')
    validate(value)
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def _state_context(tria, relationship):
    # Audit cursor changes during Runtime preparation; all semantic projection
    # fields remain bound. This is local context identity, not authentication.
    state = tria.state_to_dict(relationship.state)
    state.pop('last_event_id')
    return 'tria-projection-without-cursor/1:' + hashlib.sha256(_canonical(state).encode()).hexdigest()


class _LocalTranslation:
    def __init__(self, tria):
        self.tria = tria

    def translate(self, plan, *, model, **options):
        return self.tria.ProviderRequest('open-rosetta-local', plan.request.request_id,
            {'action': plan.request.action, 'target': plan.request.target,
             'action_id':plan.request.action_ref, 'subject':plan.request.metadata['subject'],
             'input':json.loads(plan.request.metadata['canonical_input']),
             'action_digest':plan.request.metadata['action_digest'],
             'claim_context':[{'resource':item.resource,'value':item.value,
                               'status':item.claim_status,'version':item.claim_version,
                               'provenance':list(item.provenance),'contestation_refs':list(item.contestation_refs)}
                              for item in plan.context]})

    def normalize_response(self, request_id, response):
        status = response.status if type(response) is HostReport else 'UNKNOWN_EFFECT'
        return self.tria.ProviderResponse('open-rosetta-local', request_id, status)


@dataclass(frozen=True)
class TriaBinding:
    """Bind once; callers cannot swap backend/relationship per release.

    Empty claim_refs retains the host precondition of claim-independent behavior.
    Nonempty claim_refs explicitly declares consequential canonical dependencies;
    their stored ancestors must exist and all must be ACTIVE before release.
    The host remains responsible for declaring all semantic dependencies.
    The frozen binding is an API constraint, not protection from hostile Python.
    """
    relationship: object
    policy: ReleasePolicy
    claim_refs: tuple[str, ...] = ()

    def __post_init__(self):
        tria = _load_backend()
        if type(self.relationship) is not tria.Relationship or type(self.policy) is not ReleasePolicy:
            raise TypeError('Bind one canonical TRIA Relationship and ReleasePolicy.')
        if type(self.claim_refs) is not tuple or any(type(ref) is not str or not ref for ref in self.claim_refs) or len(set(self.claim_refs))!=len(self.claim_refs):
            raise ValueError('claim_refs must be a tuple of unique canonical claim IDs.')
        object.__setattr__(self,'claim_refs',tuple(sorted(self.claim_refs)))
        self._claim_resources()

    def _claim_resources(self):
        state=self.relationship.state
        required=set(self.claim_refs)
        pending=list(self.claim_refs)
        while pending:
            ref=pending.pop()
            if ref not in state.claims:
                raise ValueError('Required claim provenance is missing; release unavailable.')
            for parent in state.claims[ref].derived_from:
                if parent not in required:
                    required.add(parent); pending.append(parent)
        return tuple('claim:'+ref for ref in sorted(required))

    def evidence_binding(self, *, action_id, action, input_data, last_correctable_at):
        """Describe host evidence scope; this method issues no evidence or authority."""
        tria = _load_backend()
        if type(last_correctable_at) is not datetime or last_correctable_at.tzinfo is None or last_correctable_at.utcoffset() is None:
            raise ValueError('last_correctable_at must be timezone-aware.')
        if any(type(v) is not str or not v.strip() for v in (action_id, action)):
            raise ValueError('action_id and action must be exact nonempty strings.')
        policy=self.policy
        identity={'action_id':action_id,'action':action,'subject':policy.subject,
                  'scope':policy.consent_scope,'requested_by':policy.actor,
                  'consent_actor':policy.consent_actor,'target':policy.resource,
                  'purpose':policy.purpose,'input':input_data,
                  'claim_refs':list(self.claim_refs),
                  'last_correctable_at':last_correctable_at.astimezone(timezone.utc).isoformat()}
        return EvidenceBinding(policy.subject,policy.consent_scope,action_id,
            hashlib.sha256(_canonical(identity).encode()).hexdigest(),EVIDENCE_VERSION,
            _state_context(tria,self.relationship))

    def release(self, *, request_id, action_id, action, input_data, observations, last_correctable_at, executor):
        if self.claim_refs:
            require_correction_conformance()
        tria = _load_backend()  # Recheck; no cached compatibility/ALLOW fallback.
        if not callable(executor) or inspect.iscoroutinefunction(executor):
            raise TypeError('executor must be synchronous.')
        canonical_input = _canonical(input_data)
        detached_input = json.loads(canonical_input)
        binding = self.evidence_binding(action_id=action_id,action=action,input_data=detached_input,
                                        last_correctable_at=last_correctable_at)
        assessment = assess(observations, profile=PROFILE, schema=SCHEMA,binding=binding)
        boundary=[BoundaryObservation(last_correctable_at,_now(),'preflight',binding.state_context)]
        def record(disposition,entered,effect,receipt):
            return ReleaseRecord(request_id,assessment,disposition,entered,effect,receipt,
                                 action_id,binding.action_digest,binding.subject,binding.scope,tuple(boundary))
        if assessment.verdict is not Verdict.SURVIVES:
            return record('ASSESSMENT_DENIED',False,'NOT_ATTEMPTED',None)
        resources=self._claim_resources()
        if any(self.relationship.state.claims[r.split(':',1)[1]].status.value!='ACTIVE' for r in resources):
            return record('CLAIM_CONTEXT_DENIED',False,'NOT_ATTEMPTED',None)
        policy = self.policy
        request = tria.InvocationRequest(policy.actor, action, policy.resource,
            context_resources=resources,
            requirements=(tria.CapabilityRequirement(policy.resource, tria.Capability.ACT, purpose=policy.purpose),),
            consent_requirements=(tria.ConsentRequirement(policy.consent_actor, policy.consent_scope, purpose=policy.purpose),),
            request_id=request_id,action_ref=action_id,
            metadata={'subject':policy.subject,'canonical_input':canonical_input,'action_digest':binding.action_digest})
        entered = False
        late = False
        changed = False

        def guarded_host(payload):
            nonlocal entered, late, changed
            current=_state_context(tria,self.relationship)
            observed_at=_now()
            boundary.append(BoundaryObservation(last_correctable_at,observed_at,'host-handoff',current))
            if current != binding.state_context or _canonical(input_data) != canonical_input:
                changed=True
                return None
            if observed_at > last_correctable_at:  # Inclusive boundary.
                late = True
                return None
            entered = True
            return executor(payload)

        try:
            receipt = tria.ExecutionBridge().execute(self.relationship, request,
                _LocalTranslation(tria), guarded_host, model='local')
        except tria.ExecutionError as error:
            return record('HOST_ERROR',entered,'UNKNOWN' if entered else 'NOT_ATTEMPTED',error.receipt)
        disposition = 'BINDING_CHANGED' if changed else 'DEADLINE_DENIED' if late else 'HOST_ENTERED' if entered else 'TRIA_DENIED'
        # A cutoff occurs inside TRIA's executor wrapper: its receipt honestly
        # records wrapper entry/UNKNOWN_EFFECT, separately from zero host calls.
        return record(disposition,entered,'UNKNOWN' if entered else 'NOT_ATTEMPTED',receipt)

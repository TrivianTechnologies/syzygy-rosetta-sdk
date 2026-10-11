# SPDX-License-Identifier: MPL-2.0
"""Local-only assessment, authorized entry, then consent revocation. No network."""
from datetime import datetime, timedelta, timezone
import json

import tria
from open_rosetta.assessment import Observation, REQUIRED, PROFILE, SCHEMA, assess
from open_rosetta.tria_adapter import HostReport, ReleasePolicy, TriaBinding


def run():
    relationship = tria.Tria().create_relationship(['human:demo', 'agent:demo'])
    relationship.grant_consent('human:demo', 'local-example', purpose='tutorial')
    relationship.admin.grant_permission(
        'human:demo', 'agent:demo', 'mock:note', tria.Capability.ACT, purpose='tutorial'
    )
    binding = TriaBinding(relationship, ReleasePolicy(
        'agent:demo', 'mock:note', 'human:demo', 'local-example', 'tutorial', 'human:demo'
    ))
    effects = []

    def attempt(number):
        action = dict(action_id=f'note:{number}', action='append a simulated note',
                      input_data={'message': 'Hello, Open Rosetta'},
                      last_correctable_at=datetime.now(timezone.utc) + timedelta(minutes=1))
        scope = binding.evidence_binding(**action)
        observations = [Observation(check, True, 'tutorial:fixture', scope) for check in REQUIRED]
        assessment = assess(observations, profile=PROFILE, schema=SCHEMA, binding=scope)

        def local_mock(payload):
            effects.append(payload.payload['input']['message'])
            return HostReport('COMPLETED')

        result = binding.release(request_id=f'attempt:{number}', observations=observations,
                                 executor=local_mock, **action)
        return dict(assessment=assessment.verdict.value,
                    assessment_authorizes=assessment.authorizes_execution,
                    disposition=result.disposition, host_entered=result.host_entered,
                    external_effect_observation=result.effect_observation)

    first = attempt(1)
    relationship.revoke_consent('human:demo', 'local-example')
    second = attempt(2)
    assert first['host_entered'] and not second['host_entered']
    assert len(effects) == 1 and not first['assessment_authorizes']
    return dict(evidence_level='local simulation; no external effects',
                before_revocation=first, after_revocation=second,
                observed_mock_effect_count=len(effects), chain_valid=relationship.audit()['chain_valid'])


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))

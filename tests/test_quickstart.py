# SPDX-License-Identifier: MPL-2.0
import runpy
from pathlib import Path


def test_documented_quickstart_revokes_without_network(monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError('The quickstart must not use network services.')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    result = runpy.run_path(str(Path(__file__).parents[1] / 'examples' / 'quickstart.py'))['run']()
    assert result['before_revocation']['disposition'] == 'HOST_ENTERED'
    assert result['after_revocation']['disposition'] == 'TRIA_DENIED'
    assert result['before_revocation']['external_effect_observation'] == 'UNKNOWN'
    assert result['observed_mock_effect_count'] == 1 and result['chain_valid']

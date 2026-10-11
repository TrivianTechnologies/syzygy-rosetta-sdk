# SPDX-License-Identifier: MPL-2.0
"""Release gate; only offline conformance fixtures override this private state."""

_CORRECTION_EXECUTION_ENABLED = False


class CorrectionExecutionUnavailable(RuntimeError):
    pass


def require_correction_conformance():
    if _CORRECTION_EXECUTION_ENABLED is not True:
        raise CorrectionExecutionUnavailable(
            'Correction-dependent execution awaits G01–G03 conformance and required review.'
        )

# SPDX-License-Identifier: MPL-2.0
"""Bounded local correction candidate; see docs/CORRECTION_ENABLEMENT.md.

This transition is under review and does not add distributed guarantees.
"""

_CORRECTION_EXECUTION_ENABLED = True


class CorrectionExecutionUnavailable(RuntimeError):
    pass


def require_correction_conformance():
    if _CORRECTION_EXECUTION_ENABLED is not True:
        raise CorrectionExecutionUnavailable(
            'Correction-dependent execution awaits G01–G03 conformance and required review.'
        )

"""Phase 2 skill validation package.

``validate_skill_rules`` owns CLI parsing; checks register callables here so
later phases can add checks without changing the repository loader.
"""

from .diagnostics import Diagnostic, Diagnostics
from .model import RepositoryModel


def core_checks():
    """Return the Phase 2 checks in their stable execution order."""
    from .structure import CHECKS

    return list(CHECKS)

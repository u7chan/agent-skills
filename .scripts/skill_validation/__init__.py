"""Skill validation package.

``validate_skill_rules`` owns CLI parsing; checks register callables here so
extensions can add checks without changing the repository loader.
"""

from .diagnostics import Diagnostic, Diagnostics
from .model import RepositoryModel


def core_checks():
    """Return the core checks in their stable execution order."""
    from .structure import CHECKS

    return list(CHECKS)

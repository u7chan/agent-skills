#!/usr/bin/env bash
# The public validation entry point.  Keep argument handling in Python so every
# invocation has the same exit-code and diagnostic contract.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$repo_root/.scripts/validate_skill_rules.py" "$@"

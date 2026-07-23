#!/usr/bin/env bash
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
status=0
count=0
while IFS= read -r test_file; do
  count=$((count + 1))
  python3 "$test_file" || status=1
done < <(find "$repo_root" -type f -path '*/tests/test*.py' \
  -not -path '*/.git/*' -not -path '*/.archive/*' | sort)

printf 'Ran %d test files\n' "$count"
exit "$status"

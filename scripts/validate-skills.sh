#!/usr/bin/env bash
set -euo pipefail

MAX_SKILL_LINES=180
IMPORTANT_LINES=150

# Register unavoidable exceptions with a concrete reason.
declare -A LINE_COUNT_EXCEPTIONS=(
)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

failures=0

report_failure() {
  printf 'ERROR: %s\n' "$1" >&2
  failures=$((failures + 1))
}

find_skill_files() {
  find . \
    -path './.git' -prune -o \
    -path './.codex' -prune -o \
    -path './node_modules' -prune -o \
    -type f -name 'SKILL.md' -print |
    sed 's#^\./##' |
    sort
}

find_skill_files > "$tmp_dir/skills.actual"

if [[ ! -s "$tmp_dir/skills.actual" ]]; then
  report_failure 'no SKILL.md files found'
fi

while IFS= read -r skill_file; do
  line_count="$(wc -l < "$skill_file" | tr -d ' ')"
  if (( line_count > MAX_SKILL_LINES )); then
    if [[ -n "${LINE_COUNT_EXCEPTIONS[$skill_file]:-}" ]]; then
      printf 'WARN: %s has %s lines but is excepted: %s\n' \
        "$skill_file" "$line_count" "${LINE_COUNT_EXCEPTIONS[$skill_file]}"
    else
      report_failure "$skill_file has $line_count lines; limit is $MAX_SKILL_LINES"
    fi
  fi

  if (( line_count > IMPORTANT_LINES )); then
    printf 'INFO: %s has %s lines; keep required rules in the first %s lines\n' \
      "$skill_file" "$line_count" "$IMPORTANT_LINES"
  fi
done < "$tmp_dir/skills.actual"

while IFS= read -r skill_file; do
  skill_dir="$(dirname "$skill_file")"

  (grep -Eo '`references/[^`]+`' "$skill_file" || true) |
    tr -d '`' |
    sort -u > "$tmp_dir/refs"

  while IFS= read -r ref_path; do
    [[ -z "$ref_path" ]] && continue
    full_path="$skill_dir/$ref_path"
    if [[ ! -e "$full_path" ]]; then
      report_failure "$skill_file references missing path: $ref_path"
    fi
  done < "$tmp_dir/refs"
done < "$tmp_dir/skills.actual"

if [[ ! -f README.md ]]; then
  report_failure 'README.md is missing'
else
  grep -Eo '\[[^]]+\]\([^)]+/SKILL\.md\)' README.md |
    sed -E 's#.*\(([^)]+)\).*#\1#' |
    sort -u > "$tmp_dir/skills.readme"

  comm -23 "$tmp_dir/skills.actual" "$tmp_dir/skills.readme" > "$tmp_dir/readme.missing"
  comm -13 "$tmp_dir/skills.actual" "$tmp_dir/skills.readme" > "$tmp_dir/readme.stale"

  while IFS= read -r missing_skill; do
    [[ -z "$missing_skill" ]] && continue
    report_failure "README Available Skills is missing: $missing_skill"
  done < "$tmp_dir/readme.missing"

  while IFS= read -r stale_skill; do
    [[ -z "$stale_skill" ]] && continue
    report_failure "README Available Skills references missing skill: $stale_skill"
  done < "$tmp_dir/readme.stale"
fi

# Validate agents/openai.yaml metadata for each skill
MIN_DESC_LEN=25
MAX_DESC_LEN=64

while IFS= read -r skill_file; do
  skill_dir="$(dirname "$skill_file")"
  yaml_file="$skill_dir/agents/openai.yaml"

  # Extract skill name from SKILL.md frontmatter
  skill_name="$(sed -n '/^---$/,/^---$/ { /^name:/ { s/^name:[[:space:]]*//p; q; } }' "$skill_file")"
  if [[ -z "$skill_name" ]]; then
    report_failure "$skill_file: could not extract name from frontmatter"
    continue
  fi

  # Check agents/openai.yaml exists
  if [[ ! -f "$yaml_file" ]]; then
    report_failure "$skill_dir: agents/openai.yaml is missing"
    continue
  fi

  # Check display_name
  display_name="$(sed -n 's/^[[:space:]]*display_name:[[:space:]]*"\(.*\)"/\1/p' "$yaml_file")"
  if [[ -z "$display_name" ]]; then
    report_failure "$yaml_file: display_name is missing or empty"
  fi

  # Check short_description
  short_desc="$(sed -n 's/^[[:space:]]*short_description:[[:space:]]*"\(.*\)"/\1/p' "$yaml_file")"
  if [[ -z "$short_desc" ]]; then
    report_failure "$yaml_file: short_description is missing or empty"
  else
    desc_len=$(python3 -c "import sys; print(len(sys.argv[1]))" "$short_desc")
    if (( desc_len < MIN_DESC_LEN )); then
      report_failure "$yaml_file: short_description is $desc_len chars (min $MIN_DESC_LEN)"
    elif (( desc_len > MAX_DESC_LEN )); then
      report_failure "$yaml_file: short_description is $desc_len chars (max $MAX_DESC_LEN)"
    fi
  fi

  # Check default_prompt
  default_prompt="$(sed -n 's/^[[:space:]]*default_prompt:[[:space:]]*"\(.*\)"/\1/p' "$yaml_file")"
  if [[ -z "$default_prompt" ]]; then
    report_failure "$yaml_file: default_prompt is missing or empty"
  else
    if ! echo "$default_prompt" | grep -qE "\\\$$skill_name([^a-z0-9-]|\$)"; then
      report_failure "$yaml_file: default_prompt does not reference \$$skill_name"
    fi
  fi
done < "$tmp_dir/skills.actual"

if (( failures > 0 )); then
  printf 'Skill validation failed with %s error(s).\n' "$failures" >&2
  exit 1
fi

printf 'Skill validation passed: %s SKILL.md files checked.\n' "$(wc -l < "$tmp_dir/skills.actual" | tr -d ' ')"

#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
helper="$script_dir/agent-message.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin"

cat > "$tmp/bin/tmux" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  display-message)
    while (($#)); do [[ "$1" == -t ]] && { shift; printf '%s\n' "$1"; exit; }; shift; done
    ;;
  send-keys)
    printf '%s\n' "$*" >> "${FAKE_TMUX_LOG:?}"
    ;;
  *) exit 1 ;;
esac
EOF
chmod +x "$tmp/bin/tmux"
cat > "$tmp/bin/mv" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
last="${!#}"
if [[ -n "${FAKE_MV_DELAY_PENDING:-}" && "$last" == */pending/*.json ]]; then sleep 0.2; fi
exec /usr/bin/mv "$@"
EOF
chmod +x "$tmp/bin/mv"

export PATH="$tmp/bin:$PATH"
export FAKE_TMUX_LOG="$tmp/tmux.log"
export TMUX='fake'
export TMUX_AGENT_MESSAGING_ROOT="$tmp/store"
export TMUX_PANE='%1'
touch "$FAKE_TMUX_LOG"
context="$tmp/context.txt"
printf 'context\n' > "$context"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
assert_jq() { jq -e "$2" "$1" >/dev/null || fail "$3"; }

if $helper command --to-pane '%2' --text 'bad context' --context-file relative.txt >/dev/null 2>&1; then fail 'relative context rejection'; fi

long_text="$(printf '長い本文%.0s' {1..1000})"
command_path="$(cd "$tmp" && "$helper" command --to-pane '%2' --text "$long_text" --context-file "$context")"
command_trace_dir="$(dirname "$(dirname "$command_path")")"
assert_jq "$command_path" '.action == "command" and (.text | length > 1000)' 'command payload'
[[ "$(stat -c '%a' "$(dirname "$(dirname "$command_path")")")" == 700 ]] || fail 'trace directory permissions'
[[ "$(stat -c '%a' "$command_path")" == 600 ]] || fail 'payload permissions'
grep -F "$command_path" "$FAKE_TMUX_LOG" >/dev/null || fail 'command notification'
! grep -F "$long_text" "$FAKE_TMUX_LOG" >/dev/null || fail 'tmux must not receive message text'

export TMUX_PANE='%2'
command_json="$($helper read "$command_path")"
[[ "$(jq -r '.text' <<<"$command_json")" == "$long_text" ]] || fail 'command read'
[[ ! -e "$command_path" ]] || fail 'command cleanup after read'
[[ ! -d "$command_trace_dir" ]] || fail 'empty command trace cleanup'

export TMUX_PANE='%1'
request_path="$($helper request --to-pane '%2' --text '調査' --timeout-seconds 30)"
if $helper request --to-pane '%2' --text '重複' --timeout-seconds 30 >/dev/null 2>&1; then fail 'one pending request per pane'; fi

export TMUX_PANE='%2'
request_json="$($helper read "$request_path")"
[[ "$(jq -r '.action' <<<"$request_json")" == request ]] || fail 'request read'
response_path="$($helper respond --request "$request_path" --status completed --text '完了' --context-file "$context")"
assert_jq "$response_path" '.status == "completed" and .contextFiles[0] != null' 'completed response'
if $helper respond --request "$request_path" --status completed --text '遅延' >/dev/null 2>&1; then fail 'response overwrite'; fi

export TMUX_PANE='%1'
response_json="$($helper read "$response_path")"
[[ "$(jq -r '.inReplyTo' <<<"$response_json")" == "$(jq -r '.id' "$request_path")" ]] || fail 'response pairing'
trace="$(jq -r '.traceId' "$request_path")"
$helper cleanup --trace-id "$trace"
[[ ! -d "$TMUX_AGENT_MESSAGING_ROOT/$trace" ]] || fail 'successful cleanup'

# Concurrent requests atomically reserve the one pending slot.
export FAKE_MV_DELAY_PENDING=1
set +e
$helper request --to-pane '%2' --text 'request-a' --timeout-seconds 30 > "$tmp/request-a.out" 2>/dev/null & request_a=$!
$helper request --to-pane '%2' --text 'request-b' --timeout-seconds 30 > "$tmp/request-b.out" 2>/dev/null & request_b=$!
wait "$request_a"; request_a_status=$?
wait "$request_b"; request_b_status=$?
set -e
unset FAKE_MV_DELAY_PENDING
((request_a_status + request_b_status == 1)) || fail 'pending request reservation race'
if ((request_a_status == 0)); then request_path="$(<"$tmp/request-a.out")"; else request_path="$(<"$tmp/request-b.out")"; fi
export TMUX_PANE='%2'
response_path="$($helper respond --request "$request_path" --text 'request race done')"
export TMUX_PANE='%1'
$helper read "$response_path" >/dev/null
trace="$(jq -r '.traceId' "$request_path")"
$helper cleanup --trace-id "$trace"

# A payload addressed to another pane is rejected.
wrong_target="$($helper command --to-pane '%2' --text 'wrong target')"
export TMUX_PANE='%3'
if $helper read "$wrong_target" >/dev/null 2>&1; then fail 'wrong target rejection'; fi
export TMUX_PANE='%2'
$helper read "$wrong_target" >/dev/null
export TMUX_PANE='%1'

# Nested requests inherit traceId and respond one hop at a time.
request_path="$($helper request --to-pane '%2' --text 'root request' --timeout-seconds 30)"
root_trace="$(jq -r '.traceId' "$request_path")"
export TMUX_PANE='%2'
$helper read "$request_path" >/dev/null
nested_request="$($helper request --to-pane '%3' --parent-payload "$request_path" --text 'nested request' --timeout-seconds 30)"
[[ "$(jq -r '.traceId' "$nested_request")" == "$root_trace" ]] || fail 'nested trace inheritance'
export TMUX_PANE='%3'
$helper read "$nested_request" >/dev/null
nested_response="$($helper respond --request "$nested_request" --text 'nested done')"
export TMUX_PANE='%2'
$helper read "$nested_response" >/dev/null
root_response="$($helper respond --request "$request_path" --text 'root done')"
export TMUX_PANE='%1'
$helper read "$root_response" >/dev/null
$helper cleanup --trace-id "$root_trace"

# Concurrent responders share one lock; exactly one response is accepted.
request_path="$($helper request --to-pane '%2' --text 'race' --timeout-seconds 30)"
export TMUX_PANE='%2'
set +e
$helper respond --request "$request_path" --text 'race-a' > "$tmp/race-a.out" 2>/dev/null & race_a=$!
$helper respond --request "$request_path" --text 'race-b' > "$tmp/race-b.out" 2>/dev/null & race_b=$!
wait "$race_a"; race_a_status=$?
wait "$race_b"; race_b_status=$?
set -e
((race_a_status + race_b_status == 1)) || fail 'response lock race'
response_path="$(jq -r '.responseFile' "$request_path")"
export TMUX_PANE='%1'
$helper read "$response_path" >/dev/null
trace="$(jq -r '.traceId' "$request_path")"
$helper cleanup --trace-id "$trace"

request_path="$($helper request --to-pane '%2' --text 'timeout' --timeout-seconds 1)"
sleep 2
response_path="$(jq -r '.responseFile' "$request_path")"
assert_jq "$response_path" '.status == "failed" and .error.code == "timeout"' 'timeout response'
export TMUX_PANE='%2'
if $helper respond --request "$request_path" --text 'late response' >/dev/null 2>&1; then fail 'late response rejection'; fi
export TMUX_PANE='%1'
$helper read "$response_path" >/dev/null
trace="$(jq -r '.traceId' "$request_path")"
if $helper cleanup --trace-id "$trace" >/dev/null 2>&1; then fail 'failed trace retention'; fi

export TMUX_PANE='%9'
bad="$TMUX_AGENT_MESSAGING_ROOT/$trace/responses/bad.json"
jq '. + {unknown:true}' "$response_path" > "$bad"
chmod 600 "$bad"
if $helper read "$bad" >/dev/null 2>&1; then fail 'unknown field rejection'; fi
ln -s "$response_path" "$TMUX_AGENT_MESSAGING_ROOT/$trace/responses/link.json"
if $helper read "$TMUX_AGENT_MESSAGING_ROOT/$trace/responses/link.json" >/dev/null 2>&1; then fail 'symlink rejection'; fi

printf 'All agent-message tests passed.\n'

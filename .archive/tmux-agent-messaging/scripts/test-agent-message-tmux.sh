#!/usr/bin/env bash
set -euo pipefail

command -v tmux >/dev/null 2>&1 || { printf 'SKIP: tmux is not installed.\n'; exit 0; }
command -v jq >/dev/null 2>&1 || { printf 'ERROR: jq is required.\n' >&2; exit 1; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
helper="$script_dir/agent-message.sh"
server="agent-message-test-$$"
root="$(mktemp -d)"
trap 'tmux -L "$server" kill-server 2>/dev/null || true; rm -rf "$root"' EXIT

tmux -L "$server" new-session -d -s test -c "$PWD"
parent="$(tmux -L "$server" display-message -p -t test:0.0 '#{pane_id}')"
child="$(tmux -L "$server" split-window -d -P -F '#{pane_id}' -t "$parent" -c "$PWD")"
pid="$(tmux -L "$server" display-message -p '#{pid}')"
tmux_env="/tmp/tmux-${UID}/${server},${pid},0"

request_path="$(TMUX="$tmux_env" TMUX_PANE="$parent" TMUX_AGENT_MESSAGING_ROOT="$root" "$helper" request --to-pane "$child" --text 'integration' --timeout-seconds 30)"
sleep 0.2
child_capture="$(tmux -L "$server" capture-pane -p -J -t "$child" -S -100)"
grep -F "$(basename "$request_path")" <<<"$child_capture" >/dev/null || { printf 'Child pane did not receive request path:\n%s\n' "$child_capture" >&2; exit 1; }

response_path="$(TMUX="$tmux_env" TMUX_PANE="$child" TMUX_AGENT_MESSAGING_ROOT="$root" "$helper" respond --request "$request_path" --text 'done')"
sleep 0.2
parent_capture="$(tmux -L "$server" capture-pane -p -J -t "$parent" -S -100)"
grep -F "$(basename "$response_path")" <<<"$parent_capture" >/dev/null || { printf 'Parent pane did not receive response path:\n%s\n' "$parent_capture" >&2; exit 1; }
TMUX="$tmux_env" TMUX_PANE="$parent" TMUX_AGENT_MESSAGING_ROOT="$root" "$helper" read "$response_path" | jq -e '.status == "completed"' >/dev/null

printf 'Isolated tmux integration test passed.\n'

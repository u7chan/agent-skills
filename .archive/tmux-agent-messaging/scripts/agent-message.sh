#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly STORAGE_BASE="${TMUX_AGENT_MESSAGING_ROOT:-/tmp/tmux-agent-messaging/${UID}}"
readonly SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
readonly NOTICE_PREFIX='$tmux-agent-messaging を使って次のPayloadを処理してください: '

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
require_command() { command -v "$1" >/dev/null 2>&1 || die "$1 が必要です。インストールしてよいかユーザーへ確認してください"; }
require_tmux_env() { [[ -n "${TMUX:-}" && -n "${TMUX_PANE:-}" ]] || die 'TMUX と TMUX_PANE が必要です'; }

init_storage() {
  [[ ! -L "$STORAGE_BASE" ]] || die "保存ルートにsymlinkは使用できません: $STORAGE_BASE"
  mkdir -p "$STORAGE_BASE/pending"
  [[ "$(stat -c '%u' "$STORAGE_BASE")" == "$UID" ]] || die "保存ルートの所有者が現在ユーザーではありません: $STORAGE_BASE"
  chmod 700 "$STORAGE_BASE" "$STORAGE_BASE/pending"
}

uuid() {
  if command -v uuidgen >/dev/null 2>&1; then uuidgen | tr '[:upper:]' '[:lower:]';
  elif [[ -r /proc/sys/kernel/random/uuid ]]; then tr '[:upper:]' '[:lower:]' < /proc/sys/kernel/random/uuid;
  else die 'UUIDを生成できません'; fi
}

now() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
pane_key() { printf '%s' "${1#%}"; }

assert_pane() {
  local pane="$1" actual
  [[ "$pane" =~ ^%[0-9]+$ ]] || die "不正なペインIDです: $pane"
  actual="$(tmux display-message -p -t "$pane" '#{pane_id}' 2>/dev/null)" || die "送信先ペインが存在しません: $pane"
  [[ "$actual" == "$pane" ]] || die "送信先ペインを確認できません: $pane"
}

notify_pane() {
  local pane="$1" payload="$2"
  tmux send-keys -t "$pane" -l "${NOTICE_PREFIX}${payload}" || return 1
  tmux send-keys -t "$pane" Enter || return 1
}

safe_existing_payload() {
  local path="$1" canonical base
  [[ "$path" == /* && -f "$path" && ! -L "$path" ]] || die "Payloadはsymlinkではない通常ファイルである必要があります: $path"
  [[ "$(stat -c '%u' "$path")" == "$UID" ]] || die "Payloadの所有者が現在ユーザーではありません: $path"
  canonical="$(realpath -e "$path")"
  base="$(realpath -e "$STORAGE_BASE")"
  [[ "$canonical" == "$base"/trace-*/*/*.json ]] || die "Payloadが専用ルート配下にありません: $path"
  printf '%s' "$canonical"
}

validate_context_files() {
  local json="$1" path
  while IFS= read -r path; do
    [[ "$path" == /* && -f "$path" && -r "$path" ]] || die "contextFilesは読み取り可能な絶対パスに限ります: $path"
  done < <(jq -r '.contextFiles[]' <<<"$json")
}

validate_payload_json() {
  local json="$1" action allowed required status
  jq -e 'type == "object"' >/dev/null <<<"$json" || die 'PayloadはJSON objectである必要があります'
  action="$(jq -r '.action // empty' <<<"$json")"
  case "$action" in
    command) allowed='["id","traceId","action","createdAt","fromPaneId","toPaneId","text","contextFiles"]'; required="$allowed" ;;
    request) allowed='["id","traceId","action","createdAt","fromPaneId","toPaneId","text","contextFiles","responseFile","timeoutSeconds"]'; required="$allowed" ;;
    response) allowed='["id","traceId","action","createdAt","fromPaneId","toPaneId","text","contextFiles","inReplyTo","status","error"]'; required='["id","traceId","action","createdAt","fromPaneId","toPaneId","text","contextFiles","inReplyTo","status"]' ;;
    *) die "不正なactionです: $action" ;;
  esac
  jq -e --argjson allowed "$allowed" --argjson required "$required" '
    (keys_unsorted - $allowed | length) == 0 and
    ($required - keys_unsorted | length) == 0 and
    (.id | type == "string" and test("^msg-[0-9a-f-]+$")) and
    (.traceId | type == "string" and test("^trace-[0-9a-f-]+$")) and
    (.createdAt | type == "string" and test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")) and
    (.fromPaneId | type == "string" and test("^%[0-9]+$")) and
    (.toPaneId | type == "string" and test("^%[0-9]+$")) and
    (.text | type == "string") and
    (.contextFiles | type == "array" and all(.[]; type == "string" and startswith("/")))
  ' >/dev/null <<<"$json" || die 'Payloadの共通フィールドまたは未定義フィールドが不正です'
  if [[ "$action" == request ]]; then
    jq -e '.responseFile | type == "string" and startswith("/")' >/dev/null <<<"$json" || die 'responseFileが不正です'
    jq -e '.timeoutSeconds | type == "number" and floor == . and . >= 1' >/dev/null <<<"$json" || die 'timeoutSecondsが不正です'
  elif [[ "$action" == response ]]; then
    jq -e '.inReplyTo | type == "string" and test("^msg-[0-9a-f-]+$")' >/dev/null <<<"$json" || die 'inReplyToが不正です'
    status="$(jq -r '.status' <<<"$json")"
    [[ "$status" == completed || "$status" == failed ]] || die 'statusが不正です'
    if [[ "$status" == failed ]]; then
      jq -e '.error | type == "object" and keys == ["code"] and (.code | type == "string" and length > 0)' >/dev/null <<<"$json" || die 'failed responseにはerror.codeが必要です'
    else
      jq -e 'has("error") | not' >/dev/null <<<"$json" || die 'completed responseにerrorは指定できません'
    fi
  fi
  validate_context_files "$json"
}

load_payload() {
  local path json expected_response
  path="$(safe_existing_payload "$1")"
  json="$(jq -c . "$path" 2>/dev/null)" || die "Payload JSONを解析できません: $path"
  validate_payload_json "$json"
  [[ "$(jq -r '.toPaneId' <<<"$json")" == "$TMUX_PANE" ]] || die "Payloadの宛先が現在のペインと一致しません"
  if [[ "$(jq -r '.action' <<<"$json")" == request ]]; then
    expected_response="$(dirname "$(dirname "$path")")/responses/$(jq -r '.id' <<<"$json").json"
    [[ "$(jq -r '.responseFile' <<<"$json")" == "$expected_response" ]] || die 'responseFileがrequestのtrace配下にありません'
  fi
  printf '%s\n%s' "$path" "$json"
}

atomic_write() {
  local target="$1" content="$2" tmp
  mkdir -p "$(dirname "$target")"
  chmod 700 "$(dirname "$target")" "$(dirname "$(dirname "$target")")"
  tmp="$(dirname "$target")/.tmp.$(uuid)"
  umask 077
  printf '%s\n' "$content" > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$target"
}

parse_text_args() {
  local direct="$1" file="$2"
  [[ -n "$direct" || -n "$file" ]] || die '--text または --text-file が必要です'
  [[ -z "$direct" || -z "$file" ]] || die '--text と --text-file は同時指定できません'
  if [[ -n "$file" ]]; then [[ "$file" == /* && -f "$file" && -r "$file" ]] || die '--text-fileは読み取り可能な絶対パスが必要です'; cat "$file"; else printf '%s' "$direct"; fi
}

context_json() {
  local result='[]' path
  for path in "$@"; do
    [[ "$path" == /* && -f "$path" && -r "$path" ]] || die "contextFilesは読み取り可能な絶対パスに限ります: $path"
    result="$(jq -c --arg path "$path" '. + [$path]' <<<"$result")"
  done
  printf '%s' "$result"
}

trace_from_parent() {
  local parent="$1" loaded json
  if [[ -z "$parent" ]]; then printf 'trace-%s' "$(uuid)"; return; fi
  loaded="$(load_payload "$parent")"
  json="${loaded#*$'\n'}"
  [[ "$(jq -r '.action' <<<"$json")" == request ]] || die '--parent-payloadにはrequestを指定してください'
  jq -r '.traceId' <<<"$json"
}

send_message() {
  local action="$1"; shift
  local to='' text='' text_file='' parent='' timeout=1800 arg trace id dir payload_path response_file='' payload contexts_json pending='' pending_lock=''
  local -a contexts=()
  while (($#)); do
    arg="$1"; shift
    case "$arg" in
      --to-pane) (($#)) || die "$arg に値が必要です"; to="$1"; shift ;;
      --text) (($#)) || die "$arg に値が必要です"; text="$1"; shift ;;
      --text-file) (($#)) || die "$arg に値が必要です"; text_file="$1"; shift ;;
      --context-file) (($#)) || die "$arg に値が必要です"; contexts+=("$1"); shift ;;
      --parent-payload) (($#)) || die "$arg に値が必要です"; parent="$1"; shift ;;
      --timeout-seconds) (($#)) || die "$arg に値が必要です"; timeout="$1"; shift ;;
      *) die "不明な引数です: $arg" ;;
    esac
  done
  [[ -n "$to" ]] || die '--to-paneが必要です'
  [[ "$timeout" =~ ^[1-9][0-9]*$ ]] || die '--timeout-secondsは1以上の整数です'
  assert_pane "$to"
  text="$(parse_text_args "$text" "$text_file")"
  contexts_json="$(context_json "${contexts[@]}")"
  trace="$(trace_from_parent "$parent")"
  id="msg-$(uuid)"
  dir="$STORAGE_BASE/$trace"
  if [[ "$action" == command ]]; then
    payload_path="$dir/commands/$id.json"
    payload="$(jq -cn --arg id "$id" --arg trace "$trace" --arg now "$(now)" --arg from "$TMUX_PANE" --arg to "$to" --arg text "$text" --argjson contexts "$contexts_json" '{id:$id,traceId:$trace,action:"command",createdAt:$now,fromPaneId:$from,toPaneId:$to,text:$text,contextFiles:$contexts}')"
  else
    pending="$STORAGE_BASE/pending/$(pane_key "$TMUX_PANE").json"
    pending_lock="${pending}.lock"
    [[ ! -e "$pending" ]] || die "このペインには未完了requestがあります: $pending"
    payload_path="$dir/requests/$id.json"
    response_file="$dir/responses/$id.json"
    payload="$(jq -cn --arg id "$id" --arg trace "$trace" --arg now "$(now)" --arg from "$TMUX_PANE" --arg to "$to" --arg text "$text" --argjson contexts "$contexts_json" --arg response "$response_file" --argjson timeout "$timeout" '{id:$id,traceId:$trace,action:"request",createdAt:$now,fromPaneId:$from,toPaneId:$to,text:$text,contextFiles:$contexts,responseFile:$response,timeoutSeconds:$timeout}')"
    mkdir "$pending_lock" 2>/dev/null || die "このペインには未完了requestがあります: $pending"
    if ! atomic_write "$pending" "$(jq -cn --arg request "$payload_path" --arg response "$response_file" --arg id "$id" --arg trace "$trace" '{requestFile:$request,responseFile:$response,requestId:$id,traceId:$trace}')"; then
      rmdir "$pending_lock" 2>/dev/null || true
      die '未完了request状態を保存できません'
    fi
  fi
  if ! atomic_write "$payload_path" "$payload"; then
    if [[ "$action" == request ]]; then rm -f "$pending"; rmdir "$pending_lock" 2>/dev/null || true; fi
    die 'Payloadを保存できません'
  fi
  if ! notify_pane "$to" "$payload_path"; then
    rm -f "$payload_path"
    if [[ "$action" == request ]]; then rm -f "$pending"; rmdir "$pending_lock" 2>/dev/null || true; fi
    die 'Payloadの配送に失敗しました'
  fi
  if [[ "$action" == request ]]; then
    ( sleep "$timeout"; "$SCRIPT_PATH" _timeout "$payload_path" ) >/dev/null 2>&1 &
  fi
  printf '%s\n' "$payload_path"
}

read_message() {
  (($# == 1)) || die 'usage: read <payload-path>'
  local loaded path json action pending pending_lock pending_json
  loaded="$(load_payload "$1")"; path="${loaded%%$'\n'*}"; json="${loaded#*$'\n'}"; action="$(jq -r '.action' <<<"$json")"
  if [[ "$action" == response ]]; then
    pending="$STORAGE_BASE/pending/$(pane_key "$TMUX_PANE").json"
    pending_lock="${pending}.lock"
    [[ -f "$pending" && ! -L "$pending" && "$(stat -c '%u' "$pending")" == "$UID" ]] || die '対応する未完了requestがありません'
    pending_json="$(jq -c . "$pending")" || die '未完了request状態が不正です'
    jq -e 'keys == ["requestFile","requestId","responseFile","traceId"]' >/dev/null <<<"$pending_json" || die '未完了request状態に未定義フィールドがあります'
    jq -e --arg path "$path" --arg id "$(jq -r '.inReplyTo' <<<"$json")" '.responseFile == $path and .requestId == $id' >/dev/null <<<"$pending_json" || die 'responseが未完了requestと一致しません'
    rm -f "$pending"
    rmdir "$pending_lock" 2>/dev/null || true
  fi
  printf '%s\n' "$json"
  if [[ "$action" == command ]]; then
    rm -f "$path"
    rmdir "$(dirname "$path")" 2>/dev/null || true
    rmdir "$(dirname "$(dirname "$path")")" 2>/dev/null || true
  fi
  return 0
}

respond() {
  local request='' text='' text_file='' status='completed' error_code='' arg loaded request_path request_json response_file lock payload id contexts_json
  local -a contexts=()
  while (($#)); do
    arg="$1"; shift
    case "$arg" in
      --request) (($#)) || die "$arg に値が必要です"; request="$1"; shift ;;
      --text) (($#)) || die "$arg に値が必要です"; text="$1"; shift ;;
      --text-file) (($#)) || die "$arg に値が必要です"; text_file="$1"; shift ;;
      --status) (($#)) || die "$arg に値が必要です"; status="$1"; shift ;;
      --error-code) (($#)) || die "$arg に値が必要です"; error_code="$1"; shift ;;
      --context-file) (($#)) || die "$arg に値が必要です"; contexts+=("$1"); shift ;;
      *) die "不明な引数です: $arg" ;;
    esac
  done
  [[ -n "$request" ]] || die '--requestが必要です'
  [[ "$status" == completed || "$status" == failed ]] || die '--statusはcompletedまたはfailedです'
  [[ "$status" != failed || -n "$error_code" ]] || die 'failedには--error-codeが必要です'
  [[ "$status" != completed || -z "$error_code" ]] || die 'completedに--error-codeは指定できません'
  text="$(parse_text_args "$text" "$text_file")"
  contexts_json="$(context_json "${contexts[@]}")"
  loaded="$(load_payload "$request")"; request_path="${loaded%%$'\n'*}"; request_json="${loaded#*$'\n'}"
  [[ "$(jq -r '.action' <<<"$request_json")" == request ]] || die '--requestにはrequest Payloadを指定してください'
  response_file="$(jq -r '.responseFile' <<<"$request_json")"
  [[ "$response_file" == "$(dirname "$(dirname "$request_path")")/responses/$(jq -r '.id' <<<"$request_json").json" ]] || die 'responseFileがrequestのtrace配下にありません'
  mkdir -p "$(dirname "$response_file")"
  chmod 700 "$(dirname "$response_file")"
  lock="${response_file}.lock"
  mkdir "$lock" 2>/dev/null || { [[ -f "$response_file" ]] && die 'responseは既に確定しています'; die 'responseロックを取得できません'; }
  trap 'rmdir "$lock" 2>/dev/null || true' EXIT
  [[ ! -e "$response_file" ]] || die 'responseは既に確定しています'
  id="msg-$(uuid)"
  payload="$(jq -cn --arg id "$id" --arg trace "$(jq -r '.traceId' <<<"$request_json")" --arg now "$(now)" --arg from "$TMUX_PANE" --arg to "$(jq -r '.fromPaneId' <<<"$request_json")" --arg text "$text" --argjson contexts "$contexts_json" --arg reply "$(jq -r '.id' <<<"$request_json")" --arg status "$status" '{id:$id,traceId:$trace,action:"response",createdAt:$now,fromPaneId:$from,toPaneId:$to,text:$text,contextFiles:$contexts,inReplyTo:$reply,status:$status}')"
  [[ "$status" != failed ]] || payload="$(jq -c --arg code "$error_code" '. + {error:{code:$code}}' <<<"$payload")"
  atomic_write "$response_file" "$payload"
  if ! notify_pane "$(jq -r '.fromPaneId' <<<"$request_json")" "$response_file"; then
    rmdir "$lock" 2>/dev/null || true
    die "responseは保存しましたが親ペインへの通知に失敗しました: $response_file"
  fi
  rmdir "$lock"
  trap - EXIT
  printf '%s\n' "$response_file"
}

timeout_request() {
  (($# == 1)) || exit 1
  local request="$1" request_json response lock payload
  [[ -f "$request" && ! -L "$request" ]] || exit 0
  request_json="$(jq -c . "$request" 2>/dev/null)" || exit 0
  response="$(jq -r '.responseFile // empty' <<<"$request_json")"; [[ -n "$response" ]] || exit 0
  [[ ! -e "$response" ]] || exit 0
  mkdir -p "$(dirname "$response")"; chmod 700 "$(dirname "$response")"
  lock="${response}.lock"; mkdir "$lock" 2>/dev/null || exit 0
  trap 'rmdir "$lock" 2>/dev/null || true' EXIT
  [[ ! -e "$response" ]] || exit 0
  payload="$(jq -cn --arg id "msg-$(uuid)" --arg trace "$(jq -r '.traceId' <<<"$request_json")" --arg now "$(now)" --arg from "$(jq -r '.toPaneId' <<<"$request_json")" --arg to "$(jq -r '.fromPaneId' <<<"$request_json")" --arg reply "$(jq -r '.id' <<<"$request_json")" '{id:$id,traceId:$trace,action:"response",createdAt:$now,fromPaneId:$from,toPaneId:$to,text:"制限時間内に応答がありませんでした",contextFiles:[],inReplyTo:$reply,status:"failed",error:{code:"timeout"}}')"
  atomic_write "$response" "$payload"
  notify_pane "$(jq -r '.fromPaneId' <<<"$request_json")" "$response" || exit 1
}

cleanup_trace() {
  local trace='' arg dir file context pending
  while (($#)); do arg="$1"; shift; case "$arg" in --trace-id) (($#)) || die "$arg に値が必要です"; trace="$1"; shift;; *) die "不明な引数です: $arg";; esac; done
  [[ "$trace" =~ ^trace-[0-9a-f-]+$ ]] || die '--trace-idが不正です'
  dir="$STORAGE_BASE/$trace"; [[ -d "$dir" && ! -L "$dir" ]] || die "traceが存在しません: $trace"
  while IFS= read -r -d '' file; do
    jq -e '.action == "response" and .status == "failed"' >/dev/null "$file" && die '失敗responseを含むtraceは保持してください'
    while IFS= read -r context; do [[ "$context" != "$dir"/* ]] || die 'responseのcontextFilesがtrace配下を参照しています。成果物をworkspaceへ移してください'; done < <(jq -r 'select(.action == "response") | .contextFiles[]?' "$file")
  done < <(find "$dir" -type f -name '*.json' -print0)
  for pending in "$STORAGE_BASE"/pending/*.json; do
    [[ -e "$pending" ]] || continue
    jq -e --arg trace "$trace" '.traceId == $trace' "$pending" >/dev/null && die '未完了requestがあるためcleanupできません'
  done
  rm -rf -- "$dir"
}

main() {
  require_command jq
  init_storage
  case "${1:-}" in
    command|request) require_tmux_env; local action="$1"; shift; send_message "$action" "$@" ;;
    read) require_tmux_env; shift; read_message "$@" ;;
    respond) require_tmux_env; shift; respond "$@" ;;
    cleanup) shift; cleanup_trace "$@" ;;
    _timeout) shift; timeout_request "$@" ;;
    *) die 'usage: agent-message.sh {command|request|read|respond|cleanup} ...' ;;
  esac
}

main "$@"

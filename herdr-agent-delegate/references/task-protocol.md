# Markdownタスク交換プロトコル

## 保存形式

```text
<workspace>/.herdr-agent-delegate/<uid>/<tag>/
├── task.md
├── marker
├── result.md
├── reply.tmp.md
└── reply.md
```

`<workspace>` は以下の優先順位で決まる。

1. `HERDR_AGENT_DELEGATE_ROOT` が設定済みならその絶対パス
2. `HERDR_AGENT_DELEGATE_WORKSPACE` が設定済みなら `<workspace>/.herdr-agent-delegate/`
3. どちらも未設定ならカレントディレクトリをワークスペースとして `<cwd>/.herdr-agent-delegate/`（運用上非推奨）

`HERDR_AGENT_DELEGATE_ROOT` と `HERDR_AGENT_DELEGATE_WORKSPACE` は両方とも絶対パスで指定する。相対パスはcwdの変化により保存先が不一致になるため許可されず、`task_exchange.py` はエラーで終了する。

どちらの環境変数も未設定の場合、`task_exchange.py` は実行時のカレントディレクトリをワークスペースとしてフォールバックする。このフォールバックは呼び出し時のcwdをワークスペースと見なすため、`create` から `complete`/`collect` までの間にcwdが変わると、タスクディレクトリが保存ルートの外にあると判定され失敗する。Herdr 経由の委譲では、子Agentが親と同一の環境変数・cwdで起動されるにもかかわらず、子側でcwdが変わる可能性があるため、`HERDR_AGENT_DELEGATE_WORKSPACE` を絶対パスで設定することが推奨される。未設定時は `task_exchange.py` がstderrに警告を出力する。

`HERDR_AGENT_DELEGATE_ROOT` による明示的な保存先上書きは維持される。`HERDR_AGENT_DELEGATE_WORKSPACE` を使う場合、保存先をワークスペース基準にする責務は親Agentが負う。保存ルート直下にはユーザーごとの `<uid>` ディレクトリを作り、さらにその下に一意な `<tag>` ディレクトリを作成する。

`task_exchange.py create` がユーザーごとの保存ルート、tag、`task.md`、markerを作る。Agent間では `task.md` の絶対パスだけを通知する。CLIが返すJSONは呼び出し元が各パスを取得するための結果であり、保存・配送するPayloadではない。
入力用に別途作った依頼Markdownは、委譲元ワークスペース内の専用領域（例: `.herdr-agent-delegate/requests/`）へ作成し、`task.md` へのコピーを確認後に呼び出し元が削除する。

## 子Agentの完了

1. `task.md` 全文を読む。
2. 結果を `task.md` 記載の `result.md` へ書く。
3. `task.md` 記載の `task_exchange.py complete` をそのまま実行する。
4. helperは内容を `reply.tmp.md` へ安全に書き、同一ディレクトリ内で `reply.md` へatomic renameする。
5. helperが出力した一意なmarkerを表示する。

既に `reply.md` が存在する場合は上書きしない。親paneへの直接通知は不要で、親のsemantic/marker待機が完了を検知する。

## 親Agentの回収

`task_exchange.py collect` は次を確認する。

- task directoryが絶対パスで専用保存ルートの直下にある
- task directoryとreplyがsymlinkではない
- 現在ユーザーが所有する通常ファイルである
- `reply.md` が空でない

検証成功後はreplyを標準出力へ返し、task directoryを削除する。`--keep` は成功結果を調査用に残す必要がある場合だけ使う。

reply欠損、不正ファイル、blocked、timeout、Agent終了時はcollectしない。task directoryを保持し、`task.md`、Agent出力、状態を診断材料にする。

## ネスト

委譲ごとに新しいtagを作り、相関は直上の親子間だけで扱う。

```text
Parent --task A--> Child --task B--> Grandchild
Parent <--reply A-- Child <--reply B-- Grandchild
```

Childはreply Bを回収・統合してからreply Aを確定する。Grandchildが失敗した場合、Childはtask Bを保持し、その状態と保存先をreply Aまたは失敗報告へ含める。rootから全子孫を横断するtraceは作らない。

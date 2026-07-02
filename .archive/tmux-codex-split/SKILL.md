---
name: tmux-codex-split
description: tmux を分割して新しいペインで Codex CLI を起動する。「隣のペインで Codex」「tmux で Codex」などの依頼で使う。
---

# tmux Codex Split

## 基本動作

ユーザーから指定がなければ、現在実行中の tmux ペインを基準に同じウィンドウを左右分割し、新しい右ペインで `codex` を起動する。

1. `TMUX` と `TMUX_PANE` が設定されていることを確認する。未設定なら、tmux 外から対象を推測して操作せずユーザーへ伝える。
2. 次のコマンドで現在のペインを左右分割し、新規ペイン ID を取得する。

   ```bash
   tmux split-window -h -t "$TMUX_PANE" -c "#{pane_current_path}" -P -F '#{pane_id}'
   ```

3. 取得したペイン ID を `<new-pane-id>` として、文字入力と Enter を分けて送る（`send-keys -l` はリテラル文字しか送らず、Enter キーなど特殊キー名を解釈しないため）。

   ```bash
   tmux send-keys -t '<new-pane-id>' -l 'codex'
   tmux send-keys -t '<new-pane-id>' Enter
   ```

4. `tmux capture-pane -p -t '<new-pane-id>' -S -20` で Codex の起動を確認する。

## Agent間メッセージング

起動後のCodexへ長い指示、複数行の本文、コンテキストファイル、応答が必要な依頼を渡す時は、`../tmux-agent-messaging/SKILL.md`を読み、共通ヘルパーで新規ペインへPayloadパスだけを通知する。短いCLI起動コマンド以外の本文を`tmux send-keys`へ直接渡さない。

- 応答不要なら`command --to-pane '<new-pane-id>'`を使う。
- 応答が必要なら`request --to-pane '<new-pane-id>'`を使い、送信後は入力待ちへ戻る。
- 子ペインから通知されたresponseは共通ヘルパーの`read`で検証する。

## 指定の扱い

- 対象ペインやセッションが指定された場合は、`$TMUX_PANE` より指定を優先する。
- 「上下」指定なら `split-window -v` を使う。指定なしは `-h`（左右）とする。
- 作業ディレクトリが指定された場合は `-c` にそのパスを渡す。指定なしは元ペインの `#{pane_current_path}` を引き継ぐ。
- Codex のオプションや別コマンドが指定された場合は、`codex` の代わりに指定文字列を送る。
- 既存ペインや別セッションを「隣」と推測して使わない。基本動作では必ず現在のウィンドウに新規ペインを作る。

## 安全上の注意

- 分割に失敗した場合は `send-keys` を実行しない。
- ペイン ID は `split-window -P -F '#{pane_id}'` の出力をそのまま使い、位置番号を推測しない。
- 起動確認でエラーが見えた場合は、成功したと報告しない。

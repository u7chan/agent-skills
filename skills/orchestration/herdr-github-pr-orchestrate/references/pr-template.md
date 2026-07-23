# PRテンプレート

PR本文は次の構造を基本とし、有効な役割行がある場合だけ最後にAI作業メタ情報を追加する。

```markdown
## Issues

- Close #123

## Why

変更が必要な背景。

## Summary

変更の要約。

## Changes

- 変更点

## Verification

- `command` - passed

## AI Work Metadata

| Role | Agent | Model | Effort |
| --- | --- | --- | --- |
| `<metadata-backed role>` | `<agent>` | `<model>` | `<effort>` |
```

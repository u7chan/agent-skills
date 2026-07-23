# 実装・レビュー用チェックリスト

## クイックリファレンス

| 必要なもの | 手法 | 初期値・確認点 |
|---|---|---|
| 標準UIスプリング | 臨界減衰、overshootなし | damping ratio `1.0`、response `0.3〜0.4` |
| 慣性・フリック | 少し弱い減衰 | damping ratio約`0.8`、response `0.3〜0.4` |
| 速度の引き継ぎ | リリース速度を渡す | 必要時だけ`velocity / (target - current)`で正規化 |
| 到達位置 | 指数減衰で投影 | `current + (v / 1000) × d / (1 - d)`、`d ≈ 0.998` |
| 割り込み | presentation valueから再開 | 画面上の位置と現在速度を保持 |
| 反転 | target変更後も速度を保持 | 速度を混ぜられるspringを使う |
| reversible transition | 経路とeasingを対称化 | 逆方向の三次ベジェも確認 |
| 確定判定 | 位置、投影、速度方向を併用 | 破壊操作は速度だけで確定しない |
| 1対1 drag | Pointer Events + capture | grab offsetを維持 |
| 境界 | rubberband | 超過するほど追従量を減らす |
| material | backdrop layer | 下のcontentとcontrastを実背景で検証 |
| tracking | サイズごとに調整 | displayは`-0.02em`程度、本文は`0`付近から開始 |
| reduced motion | crossfade / static transition | slide、spring、parallax、bounceを外す |

値は品質保証済みの定数ではなく、プロトタイプを始めるための目安とする。

## 操作モデル

- [ ] 押した瞬間に視覚的な反応がある。
- [ ] 操作中にpointerへ連続追従する。
- [ ] 掴んだ位置が中心へ飛ばない。
- [ ] pointerが要素外へ出ても追跡が続く。
- [ ] cancel、capture喪失、escapeの終了経路がある。
- [ ] gesture競合の判定中に不要な遅延を作っていない。
- [ ] touch、mouse、pen、keyboardで目的を達成できる。

## モーション

- [ ] 実行中の要素を掴み直せる。
- [ ] 新しいモーションが現在表示値から始まる。
- [ ] drag終了時の速度がspringへ引き継がれる。
- [ ] snap先を投影位置から決めている。
- [ ] 反転時に速度が不連続にならない。
- [ ] bounceがジェスチャーの慣性に由来している。
- [ ] X / Yを分離すべき動きで単一進捗を強制していない。
- [ ] 表示と非表示の経路が空間的に一致する。

## 境界と安全性

- [ ] 境界超過へ連続的な抵抗がある。
- [ ] 表示上の超過値が保存データへ混入しない。
- [ ] destructive actionを速度だけで確定しない。
- [ ] undo、復帰、キャンセルが可能である。
- [ ] modalのfocus、読み上げ順、close操作が見た目と一致する。

## ビジュアル

- [ ] 半透明面に階層上の理由がある。
- [ ] 明るい半透明面を重ねて可読性を落としていない。
- [ ] blur非対応でも背景と文字が読める。
- [ ] triggerとpopover / sheetの起点が結び付く。
- [ ] divider、shadow、blurが同じ役割で競合していない。
- [ ] light / dark、画像、動画など実際の背景でcontrastを確認した。
- [ ] typographyのtrackingとleadingをサイズ別に調整した。
- [ ] 文字拡大と翻訳で固定高や切り詰めが破綻しない。

## アクセシビリティ

- [ ] reduced motionで大きな移動、spring、bounce、parallaxを代替した。
- [ ] reduced transparencyで不透明な安全fallbackがある。
- [ ] more contrastで境界と文字が明確になる。
- [ ] 音、振動、色だけに意味を依存していない。
- [ ] 状態変化の情報を代替表現でも維持している。
- [ ] ゆっくりした反復運動、点滅、急な大面積の明暗変化を避けた。

## 性能と検証

- [ ] 主なanimated propertyが`transform`と`opacity`である。
- [ ] layout、paint、long task、同期処理を計測した。
- [ ] 通常速度と低速再生でジャンプやstutterを確認した。
- [ ] 60Hzと高refresh rateで時間ベースに動く。
- [ ] 実機または対象に近い入力デバイスで検証した。
- [ ] interactive prototypeと最終実装の差を比較した。

## レビューコメントの型

```text
[原則] 現在は<観察できる挙動>になっています。
そのため<ユーザーへの影響>が起きます。
<現在値・速度・状態など>を使って<最小の修正>にすると改善できます。
確認方法: <再現操作または計測方法>
```

「Appleらしくない」「動きが硬い」だけで終わらせず、観察、影響、修正、検証を結び付ける。

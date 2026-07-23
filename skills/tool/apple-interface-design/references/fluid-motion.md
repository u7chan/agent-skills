# 流体モーション

## 目次

1. 応答性
2. 直接操作
3. 割り込み可能性
4. スプリングの設計
5. 速度の連続性
6. 2次元モーション

## 1. 応答性

直接操作の感覚は、入力と反応の間に遅延が入ると失われる。次を守る。

- `click`やタッチ終了を待たず、`pointerdown`の時点で押下状態を示す。
- デバウンス、人工的なタイマー、トランジション完了待ち、入力経路上の同期処理を調べる。
- ドラッグ、スライダー、ドロワーは操作中も連続更新する。
- 入力処理が重い場合は、生イベントを保持しつつ描画を`requestAnimationFrame`へまとめる。

```css
.button:active {
  transform: scale(0.97);
  transition: transform 100ms ease-out;
}
```

押下表現は視覚だけに依存させず、フォーカス、無効状態、実行結果も区別する。

## 2. 直接操作

ドラッグ対象をポインターへ1対1で追従させる。要素の中心へ吸着させず、掴んだ位置のオフセットを保つ。

```js
let drag;

el.addEventListener('pointerdown', (event) => {
  el.setPointerCapture(event.pointerId);
  const rect = el.getBoundingClientRect();
  drag = {
    pointerId: event.pointerId,
    grabX: event.clientX - rect.left,
    grabY: event.clientY - rect.top,
    samples: [{ x: event.clientX, y: event.clientY, t: event.timeStamp }],
  };
});
```

- `setPointerCapture`で要素外へ出た後も追跡する。
- `pointercancel`、capture喪失、ウィンドウの非アクティブ化を終了経路として扱う。
- 位置と時刻の短い履歴を保持し、リリース速度を計算する。
- `touch-action`は競合するブラウザジェスチャーだけを抑制し、ページスクロールを不必要に奪わない。

## 3. 割り込み可能性

思考とジェスチャーは並行する。トランジション中も入力を受け付け、動いている要素を途中で掴み直せるようにする。

- 入力開始時に、論理上の目標値ではなく現在表示されているpresentation valueを取得する。
- 実行中のモーションを停止しても、現在位置と現在速度を捨てない。
- 新しい入力を別アニメーションの開始ではなく、同じ系のターゲット変更として扱う。
- 閉じている途中のシートを掴んだ場合、その場から直接操作へ移る。
- モーション中に`pointer-events: none`や一律の操作ロックを設定しない。

CSS transitionや`@keyframes`は、途中の値・速度を安全に引き継ぎにくい。装飾的で一方向の遷移には使えるが、直接操作する要素では割り込み可能なモーション値またはスプリングを優先する。

## 4. スプリングの設計

固定時間のアニメーションではなく、新しい入力に反応する振る舞いとして設計する。

- **減衰比（damping ratio）**: オーバーシュートを制御する。`1.0`は臨界減衰で、通常はバウンドせず収束する。`1.0`未満は振動する。
- **レスポンス（response）**: ターゲットへ近づく速さを表す。固定の継続時間ではない。

初期値の目安:

| 操作 | damping ratio | response |
|---|---:|---:|
| 標準の移動・再配置 | `1.0` | `0.4` |
| 回転 | `0.8` | `0.4` |
| ドロワー・シート | `0.8` | `0.3` |

多くのUIは`1.0`から始める。`0.8`程度のバウンドは、フリックや投げる操作など、入力自体に慣性がある場合だけ試す。

ライブラリの`duration`や`bounce`は物理パラメーターの抽象化であり、Appleのresponse / damping ratioと同一ではない。現行ドキュメントと実際の収束を確認する。

Motionでは、`duration` + `bounce`型のspringは速度を取り込まない。タイミングを揃える非ジェスチャー遷移には使えるが、ドラッグのリリースには`stiffness`、`damping`、`mass`、`velocity`を使う物理ベースspringまたは速度を保持するmotion valueを選ぶ。

```js
import { animate } from 'motion';

// 非ジェスチャー遷移。タイミングとbounceを直接調整する
animate(el, { y: 0 }, { type: 'spring', bounce: 0, duration: 0.4 });
```

```text
// ジェスチャー終了。速度を扱える物理ベースspringを使う
animateSpringTo(target, {
  stiffness: 300,
  damping: 30,
  velocity: releaseVelocity,
});
```

`animateSpringTo`は疑似コードなので採用ライブラリに置き換える。上は調整の出発点であり、速度単位を含め、現行APIで動作を確認する。

## 5. 速度の連続性

反転時に速度をゼロへ戻すと、壁へ衝突したように見える。次を満たす実装を選ぶ。

- リリース時の速度をスプリングの初期速度へ渡す。
- アニメーション途中でターゲットが変わっても現在速度を維持する。
- 直接操作へ移るときは画面上の現在位置から開始する。
- APIが相対速度を要求する場合だけ、残り距離で正規化する。

```text
relativeVelocity = gestureVelocity / (targetValue - currentValue)
```

残り距離がほぼ0の場合は除算を避ける。絶対速度を受け取るAPIへは、通常px/sなどの速度をそのまま渡す。

## 6. 2次元モーション

X軸とY軸で距離や速度が異なる場合は、各軸を独立したスプリングとして扱う。2次元距離全体へ単一の進捗率を適用すると、片方の軸が不自然に同期する。

ただし、円軌道や経路追従のように軌道自体が意味を持つ場合は、経路パラメーターと接線速度を明示して設計する。

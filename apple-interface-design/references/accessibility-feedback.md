# アクセシビリティとマルチモーダルフィードバック

## 目次

1. 因果関係・調和・有用性
2. モーション軽減
3. 透明度とコントラスト
4. 避ける表現
5. 実装例

## 1. 因果関係・調和・有用性

視覚、音、触覚を組み合わせる場合は次の3原則を守る。

### 因果関係

トグルが切り替わる、要素が所定位置へ収まるなど、実際の状態変化と同時にフィードバックを発火する。音や触覚の性質も、操作の重さ、速度、成功・警告などの意味と合わせる。

### 調和

視覚、音、触覚を知覚上同じ瞬間に発生させる。CSS遷移、音声再生、Vibration APIなどの開始遅延を測り、別々の完了イベントへ依存しない。

### 有用性

成功、エラー、確定、スナップなど意味のある瞬間だけに使う。過剰なフィードバックは重要度を失わせる。音と振動を利用できない環境でも状態が伝わるようにする。

Webの触覚対応は環境差が大きい。Vibration APIを必須経路にせず、利用可能性とユーザー設定を尊重する。

## 2. モーション軽減

`prefers-reduced-motion: reduce`は、フィードバックを削除する指示ではない。前庭刺激の少ない代替へ置き換える。

- スライド、スプリング、パララックスを、短いcrossfadeまたは静的切り替えへ変更する。
- 弾性、オーバーシュート、回転、奥行き方向の大きなscaleを外す。
- 状態理解を助ける色、透明度、アイコン、文言の変化は残す。
- 大きな面を移動する必要がある場合は、移動中に弱くfadeし、停止後に戻すことを検討する。
- JSで動きを生成する場合も`matchMedia`などで設定を読み、CSSだけに任せない。

## 3. 透明度とコントラスト

### Reduced transparency

`prefers-reduced-transparency: reduce`を利用できる環境では、半透明面を曇らせるか不透明面へ変更し、backdrop blurを無効化する。このメディア特性は対応が限定的なため、非対応ブラウザでも可読性が保たれる通常背景を定義する。

### More contrast

`prefers-contrast: more`では、ほぼ不透明な背景、明確な境界、十分な文字コントラストを使う。影やblurだけを境界の手掛かりにしない。

## 4. 避ける表現

- 画面全体を覆い続ける移動背景。
- 約0.2Hz、つまり5秒周期程度のゆっくりした反復運動。
- 急激な明暗変化や点滅。
- ライト／ダークテーマの瞬間的で大面積な切り替え。
- スクロールと独立して大きく動くパララックス。
- reduced motion時に、時間だけ短くして移動量を残す対応。

## 5. 実装例

```css
.sheet {
  /* 非ジェスチャー時のフォールバック例 */
  transition:
    transform 320ms,
    opacity 200ms;
}

.toolbar {
  background: rgb(255 255 255 / 60%);
  backdrop-filter: blur(20px);
}

@media (prefers-reduced-motion: reduce) {
  .sheet {
    transform: none !important;
    transition: opacity 200ms ease;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .toolbar {
    background: white;
    backdrop-filter: none;
  }
}

@media (prefers-contrast: more) {
  .toolbar {
    background: Canvas;
    border-color: CanvasText;
  }
}
```

メディア特性の対応状況は変化するため、対象ブラウザで確認する。未対応でも通常スタイルが安全になる順序でCSSを書く。

# UltimateNotePad — Sidebar Refinement v1

対象：Settings v1 と Pin Motion v2 が適用された UltimateNotePad。
GitHub 確認時点のツリー: `118893c6ad02c6ba1e94131f2c00a1570b3877bc`。

## 適用

Flask を停止して、ZIP をリポジトリ直下に展開してください。

```bash
cd /workspaces/UltimateNotePad
unzip UltimateNotePad-Sidebar-Refinement-v1-Apply.zip
python3 install_sidebar_refinement.py --dry-run
python3 install_sidebar_refinement.py
python3 app.py
```

ドライランで失敗した場合は、エラーを確認してください。既存の検索 UI、CSS、翻訳辞書のアンカーが異なる場合は更新を拒否します。アプリケーションの Python、DB、`static/js/autosave.js` は更新対象外です。更新前の3ファイルは `.refactor-backups/before-sidebar-refinement-*.zip` に保存されます。元に戻すには、Flask停止後に該当するバックアップZIPの3ファイルだけをリポジトリルートへ展開してください。

## UI

- 大きな検索フォームを単一の検索入力（44 CSS px、タッチ端末では50px）へ変更。
- 検索ボタンは虫眼鏡アイコン。Enterでも実行可能。入力中の×は未適用の入力を消去し、適用済み検索では一覧をリセットします。
- 並べ替えは件数と同じ行に移動。標準のselectを維持し、短い表示名、ツールチップ、読み上げ用ラベルを用意します。
- `q`、`sort` に加え、表示中のメモの `id` をGETフォームで維持します。検索結果から外れた場合は既存Flaskの選択処理に従います。検索・並べ替えは従来同様に通常のページ遷移であり、未保存時は既存の離脱警告が働きます。
- 編集・モーダル操作を妨げない場合のみ、 `/` で検索入力へフォーカスします。
- 既存のテーマトークン、設定・ピン留めモジュール、View Transitionsを利用。日英切替時に検索SVGを消さないようにラベルだけ翻訳します。
- フォーカス時の輪郭、クリック時の軽い縮小、設定／削除ダイアログの入場、設定タブ、保存済みドット、クリアアイコンに短いモーションを追加。ピン留めの既存FLIPを保持。
- prefers-reduced-motionを尊重し、連続的な装飾アニメーションや全ページの強制フェードは追加しません。

## 更新ファイル

`templates/index.html`, `static/css/app.css`, `static/js/app.js` の3ファイルのみ。既存の検索CSSセクションを置換して、古い検索CSSの重複・競合を減らします。新しいランタイムJS/CSS・ライブラリは不要です。

## 検証状況

確認済み：旧配布資産と現行ソースの確認済みアンカーで再構築したフィクスチャで、ドライラン、バックアップの内容、再実行、アンカー不一致の拒否、Python/DB不変更、Node構文、Jinja描画、検索コントローラーのモックDOMテスト。
未確認：現行GitHub全ファイルの実ブラウザ統合テスト（この環境のブラウザ接続制限）。Codespacesで見た目と以下の操作を確認してください。

1. ライト／ダーク、日英切替（虫眼鏡と×の表示も確認）
2. タイトル・本文検索、Enterと虫眼鏡、検索のクリア、該当なし
3. 新しい順／古い順／タイトル順、検索条件と選択メモの維持
4. ピン留めと並べ替え、未保存の本文の保持、作成／削除／設定
5. キーボードのTab・Enter・/、OSの動きの低減設定、狭い幅

参考: https://web.dev/articles/animations-guide 、 https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum

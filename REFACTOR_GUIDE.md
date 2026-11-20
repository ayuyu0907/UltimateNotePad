# UltimateNotePad フロントエンド整理パッケージ

対象: [ayuyu0907/UltimateNotePad](https://github.com/ayuyu0907/UltimateNotePad) / `main`（2026-11-20に確認した構成）

このZIPは**現行のGitHubソースを整理するための適用パッケージ**です。現在のリポジトリ全体を無条件に置き換えるZIPではありません。プロジェクト内で適用すると、**整理済みの完全なソースZIP** `UltimateNotePad-refactored-full.zip` が自動生成されます。

## 使い方（GitHub Codespaces）

1. GitHub CodespacesでUltimateNotePadの作業フォルダを開く。
2. この配布ZIPの中身を `/workspaces/UltimateNotePad/` に展開する。`app.py` があるディレクトリに `refactor.py` を置く。zipにはデータベースは入っていません。
3. ターミナルから、構成確認を実行:

   ```bash
   cd /workspaces/UltimateNotePad
   python3 refactor.py --dry-run
   ```

4. エラーがなければ統合作業を実行:

   ```bash
   python3 refactor.py
   ```

5. 完了すると以下ができます:
   - `static/css/app.css` — 現在実際に読み込まれている3つのCSSを順番どおり統合
   - `static/js/app.js` — 検索・JST日時・作成/削除モーダルを統合
   - `static/js/autosave.js` — 保存処理を独立維持（元コード無変更）
   - `templates/index.html` — JS/CSSの読み込みを整理
   - `legacy/css/layout-compact.css` — 参照されていない旧CSSを保管
   - `.refactor-backups/` — 変更前の元ファイルをZIPで保存
   - `UltimateNotePad-refactored-full.zip` — 整理後のプロジェクト一式（`.git`、`.venv`、メモDB、環境変数を除外）

6. 起動は従来どおり:

   ```bash
   ./app.py
   ```

   ポート・ホストの設定は変更しません。GitHub Codespacesの転送URLから確認してください。

## 変更するもの・変更しないもの

| 項目 | 対応 |
|---|---|
| JSの共通処理 | 既存4ファイルを`app.js`へ統合、起動処理とダイアログ操作を共通化 |
| 自動保存 | `autosave.js`をそのまま維持（保存順序・再試行・未保存警告を保護） |
| CSS | 読込順を変えず1本に結合、見た目の変更を避ける |
| HTML | スクリプト・CSSリンクの整理と重複クリック処理の削除 |
| Flask / SQLite / 学習課題 | **変更しない** |
| ユーザーの`data/notes.db` | **変更しない**。完成版ZIPにはデータ保護のため含めない |

## 注意点

- 作業途中の最新コードがGitHubへコミットされていなくても、**ローカルの既存CSSを読み取って結合**するため、現在の見た目を維持しやすい方法です。
- ただしJSの共有処理は再実装しているため、利用環境での操作確認が必要です。
- バックアップは必ず作成されます。もとのファイルに戻したければ `.refactor-backups/before-frontend-refactor-*.zip` を展開します。
- 二重実行は検出して停止します。想定外のファイル構成なら自動で止まり、変更しません。
- 「作成→編集→自動保存→再読み込み」「削除」「検索・並べ替え」「Esc/背景クリック」「時刻表示」「通信障害時の再試行」を確認してください。
- **サーバー時刻と表示の整合性について:** 元の `app.py` はタイムゾーン未指定の `datetime.now()` で記録し、UIはUTCとみなして東京時間に変換しています。今回の作業では学習中のPythonに手を加えません。時差が出る場合は別途修正が必要です。

## 開発者向け簡易テスト

```bash
python3 -m unittest discover -s tests -v
node --check static/js/app.js
node --check static/js/autosave.js
```

これらは静的/テスト用の検証であり、ブラウザでの完全なE2Eテストではありません。

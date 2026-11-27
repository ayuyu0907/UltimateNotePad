# UltimateNotePad

**Your space to think.**

UltimateNotePad は、メモの作成・編集・整理を中心とした Web アプリケーションです。
Python・Flask・SQLite を用いて開発しており、シンプルで直感的な操作性と、拡張しやすい設計を重視しています。

将来的には、メモ管理に加えて電卓などの便利ツールや、アカウントによる端末間同期にも対応することを目指しています。

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-64748b)

## 機能

### メモ管理

- メモの新規作成・編集・削除（削除前の確認ダイアログ）
- タイトル・本文のキーワード検索
- 更新日時の新しい順・古い順・タイトル順での並べ替え
- 複数メモのピン留め・解除（固定メモを優先して表示）
- ピン留め時の一覧のアニメーション更新と編集内容の保持
- 星アイコンでお気に入りの登録・解除（ピン留めとは独立）
- お気に入りフィルターと検索・並べ替えの組み合わせ
- お気に入り解除時も編集中の内容を保持。絞り込み中は対象行だけ一覧から除外
- 複数タグの作成・色変更・名前変更・削除、メモへの付与・解除
- タグ絞り込み（検索・お気に入り・並べ替えと併用）
- タグ操作中も現在のエディター・自動保存を維持
- SQLite によるメモの永続化

### 保存

- 入力停止から約1秒後の自動保存（設定で ON / OFF）
- 手動保存
- 保存リクエストの直列実行と最新入力の優先
- 一時的な通信エラーなどに対する最大3回の再試行
- 通信復旧時の再保存（自動保存が有効な場合）
- 保存状態の表示と未保存時のページ離脱警告

### 外観・設定

- ライト・ダーク・システム連動テーマ
- 日本語・英語の UI 切り替え（メモ本文は翻訳しない）
- 編集画面のコンパクト表示
- 共通設定メニュー
- 設定の JSON エクスポート・インポート・初期化
- ブラウザの localStorage による設定の保持

### ユーザーインターフェース

- 左側のメモ一覧と右側の編集画面を組み合わせたレイアウト
- コンパクトな検索欄、検索解除ボタン、メモ一覧と統合した並べ替え
- `/` キーで検索欄へ移動（入力中やダイアログ表示中などを除く）
- ダイアログ・ピン留め・メモ切り替えなどのアニメーション
- `prefers-reduced-motion` への配慮、キーボード操作、読み上げ用ラベル
- メモの内容を主役にするための、控えめな操作フィードバック

> 現在は開発段階です。アカウント認証・クラウド同期・リッチテキスト編集・ゴミ箱は未実装です。設定の JSON 出力にはメモ本文は含まれません。

## 技術スタック

| 分野 | 技術 |
| --- | --- |
| バックエンド | Python / Flask 3.1.3 |
| データベース | SQLite（Python 標準ライブラリ `sqlite3`） |
| テンプレート | Jinja2 |
| フロントエンド | HTML / CSS / Vanilla JavaScript |
| 設定の保存 | localStorage |
| 開発環境 | GitHub Codespaces / Python 仮想環境 |
| バージョン管理 | Git / GitHub |

## セットアップ

Python 3 系と Git が利用できる環境を用意してください。依存パッケージは `requirements.txt` で管理しています。

### 1. リポジトリの取得

```bash
git clone https://github.com/ayuyu0907/UltimateNotePad.git
cd UltimateNotePad
```

GitHub Codespaces でリポジトリを開いている場合は、この手順を省略できます。

### 2. 仮想環境の作成・依存関係のインストール

Linux / GitHub Codespaces:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

以降のコマンドは Codespaces / Linux を基準とします。

### 3. データベースの初期化

プロジェクトルートで実行します。

```bash
mkdir -p data
python3 database.py
python3 migrations/001_add_is_pinned.py
python3 migrations/002_add_is_favorite.py
python3 migrations/003_add_tags.py
```

`database.py` は既存テーブルを削除せず、存在しない場合に `notes` テーブルを作成します。
マイグレーションは `is_pinned` と `is_favorite` 列が存在しない場合に追加します。003 は `tags`・`note_tags` とインデックスを作成します。新規環境でも全マイグレーションを実行してください。

既存の DB に対してマイグレーションを実行する場合は、アプリを停止し、先にバックアップを取得してください。

```bash
mkdir -p backups
cp -p data/notes.db "backups/notes-before-migration-$(date +%Y%m%d-%H%M%S).db"
python3 migrations/001_add_is_pinned.py
python3 migrations/002_add_is_favorite.py
python3 migrations/003_add_tags.py
```

### 4. アプリケーションの起動

```bash
python3 app.py
```

ローカルアクセス先：`http://127.0.0.1:3000`

GitHub Codespaces の場合は、ポートタブで `3000` の転送先を開いてください。開発時はポートを非公開に維持してください。

## ディレクトリ構成

```text
UltimateNotePad/
├── app.py                         # Flask のルーティング・メモ管理
├── database.py                    # DB の初期化
├── requirements.txt               # Python の依存パッケージ
├── README.md
├── .gitignore
│
├── data/                          # ローカルデータ（初期化時に作成）
│   └── notes.db
│
├── migrations/                    # DB スキーマの変更
│   ├── 001_add_is_pinned.py
│   ├── 002_add_is_favorite.py
│   └── 003_add_tags.py
│
├── templates/
│   └── index.html                 # Jinja2 テンプレート
│
├── static/
│   ├── css/
│   │   └── app.css                # 統合スタイル・テーマ・モーション
│   └── js/
│       ├── app.js                 # UI・検索・設定・ピン留め・お気に入り・タグ
│       └── autosave.js            # 独立した保存処理
│
├── learning/
│   └── sqlite/                    # SQLite の学習用スクリプト
├── tests/                         # テストコード
│   ├── test_routes.py             # Flask の基本ルートテスト
│   ├── test_pin.py                # 一時DBによるピン留め・検索・並べ替えテスト
│   ├── test_favorite.py           # お気に入りの unittest
│   └── test_tags.py               # タグ CRUD・関連・絞り込み・回帰テスト
└── legacy/
    └── css/                       # 旧スタイル（現行 UI では未使用）
```

主要なファイルを記載しています。適用パッケージ用の旧テストなど、一部の補助ファイルは省略しています。

## データベース

SQLite ファイル：`data/notes.db`

### `notes` テーブル

| 列 | 型 | 内容 |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | メモ ID |
| `title` | TEXT NOT NULL | タイトル |
| `content` | TEXT NOT NULL | 本文 |
| `created_at` | TEXT NOT NULL | 作成日時 |
| `updated_at` | TEXT NOT NULL | 更新日時 |
| `is_pinned` | INTEGER NOT NULL DEFAULT 0 | 0 = 通常、1 = ピン留め |
| `is_favorite` | INTEGER NOT NULL DEFAULT 0 | 0 = 未登録、1 = お気に入り |

新しいメモは未固定・お気に入り未登録で作成されます。ピン留め・お気に入りの変更だけでは `updated_at` は変更されません。

### `tags` テーブル

| 列 | 型 | 内容 |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | タグID |
| `name` | TEXT NOT NULL UNIQUE | 名前（前後空白を除き1〜40文字、大文字小文字を区別） |
| `color` | TEXT NOT NULL DEFAULT '#64748b' | #RRGGBB |
| `created_at` | TEXT NOT NULL | 作成日時 |

### `note_tags` テーブル

`note_id` / `tag_id` は INTEGER NOT NULL、複合主キーです。両外部キーは `ON DELETE CASCADE`。`tag_id` にインデックスを設定しています。アプリの全DB接続で外部キーを有効化します。タグやメモの削除で関連付けのみ自動整理され、タグ削除ではメモ本体を削除しません。タグ操作でメモの `updated_at` は更新しません。

## Flask ルーティング

| メソッド | パス | 処理 |
| --- | --- | --- |
| GET | `/` | メモ一覧・検索・並べ替え・選択メモの表示 |
| POST | `/notes/create` | メモの作成 |
| POST | `/notes/<note_id>/update` | メモの編集・保存 |
| POST | `/notes/<note_id>/delete` | メモの削除 |
| POST | `/notes/<note_id>/pin` | ピン留めの切り替え |
| POST | `/notes/<note_id>/favorite` | `is_favorite=0` または `1` を設定（成功302、不正値400、対象なし404） |
| GET | `/api/tags` | タグ一覧・任意の `note_id` の付与済みID |
| POST | `/tags/create` | `name`, `color` で作成（201） |
| POST | `/tags/<tag_id>/update` | `name`, `color` を更新（200） |
| POST | `/tags/<tag_id>/delete` | タグと関連付けを削除（200） |
| POST | `/notes/<note_id>/tags/<tag_id>` | `assigned=0/1` で解除・付与（200、冪等） |

タグAPIは JSON (`ok` と結果、失敗時 `error`) を返します。不正値400、対象なし404、タグ名重複409、DBエラー500です。

### 一覧のクエリパラメーター

| パラメーター | 内容 |
| --- | --- |
| `q` | 検索キーワード |
| `sort` | `new`（既定） / `old` / `title` |
| `id` | 選択するメモ ID |
| `favorite` | `1` のときお気に入りのみ。それ以外は全メモ |
| `tag` | タグID。0・未指定・存在しないIDは全タグ |

例：`/?favorite=1&q=Python&sort=title&tag=2`

検索結果とお気に入り条件に一致するメモだけを対象として、ピン留め状態を優先し、その中で指定された並べ替えを行います。

星ボタンは変更後の値をPOSTし、ピンボタンは反転をPOSTします。JSは両方を直列化し、サーバーの応答と現在の一覧を確認して行だけを更新します。成功テキストは出しません。お気に入り一覧で選択中のメモを解除しても、現在のエディターは次の画面遷移まで維持します。検索・ソート・メモ選択・表示フィルターはGET遷移で、未保存時の既存離脱警告が有効です。JSが無効な場合、登録・解除は通常のPOSTとリダイレクトで行われ、全メモ表示に戻ります。新規作成・削除も既存ルートのリダイレクト仕様に従います。

タグ管理はサイドバーのタグアイコン、付与・解除はエディターの「メモのタグ」から行います。タグ操作はJSで実行し、現在の検索・ソート・お気に入り・タグ条件を維持して一覧だけを更新します。編集中のメモが絞り込み対象から外れてもエディターを次の画面遷移まで維持します。絞り込み中のタグ自体を削除すると全タグに戻ります。タグ管理・付与にはJSが必要です。正常時のテキスト通知は出さず、エラー時のみ表示します。

## テスト

DB の初期化とマイグレーションを済ませた後、プロジェクトルートで実行します。

```bash
python3 -m tests.test_routes
```

現行のルートテストでは、トップページ、検索、並べ替え、検索と並べ替えの組み合わせ、存在しない URL の HTTP ステータスを確認します。
テストは GET リクエストを使用するため、メモの作成・更新・削除は行いません。

ピン留めの更新・解除、検索、並べ替え、404/405は以下で検証します。`main()` が一時ディレクトリを作成してテストDBを準備するため、個別関数やpytestによる自動検出で実行しないでください。

```bash
python3 -m tests.test_pin
```

お気に入り（課題10-2E）の11件の自動テスト、およびタグのテスト：

```bash
python3 -m unittest tests.test_favorite -v
python3 -m unittest tests.test_tags -v
```

両方ともテストごとに一時DBを作成します。タグテストは 003 の再実行、CRUD、入力検証、重複、関連付け、複合フィルター、削除時のCASCADE、既存のルート・テンプレート連携を確認します。個別モジュールで順番に実行してください。

`tests/test_installer.py` と `tests/test_settings_core.js` は旧適用パッケージを前提としたテストです。現行リポジトリには必要なインストーラーや `payload/` が揃っていないため、そのままでは実行できません。

## 開発方針

- Python・Flask・SQLite の学習と、実用的なアプリ開発を両立する。
- HTML・CSS・JavaScript のランタイムファイルをむやみに増やさず、役割別に整理する。
- DB スキーマの変更はマイグレーションで管理し、既存データを保護する。
- 新機能はライト・ダークモード、日本語・英語への対応を考慮する。
- 成功時の通知テキストは必要最小限にし、アイコン・色・短いアニメーションを活用する。
- 操作性・アクセシビリティ・パフォーマンスを重視する。
- 新機能を追加する際には、既存機能への回帰がないか確認する。

## ロードマップ

### メモ管理の拡張

- [x] 基本的なメモ CRUD
- [x] 自動保存・検索・並べ替え
- [x] テーマ・多言語・共通設定
- [x] ピン留め
- [x] ピン留めの自動テスト（課題 10-1E）
- [x] お気に入り（DB・バックエンド・UI、課題 10-2A〜D）
- [x] お気に入りの自動テスト（課題 10-2E）
- [x] タグ（DB・バックエンド・UI・自動テスト、課題10-3）
- [ ] フォルダー
- [ ] アーカイブ・ゴミ箱
- [ ] メモテンプレート

### 便利ツール

- [ ] 電卓
- [ ] ToDo・タスク管理
- [ ] カレンダー
- [ ] タイマー
- [ ] 単位変換

### 長期構想

- [ ] ユーザーアカウントと認証・認可
- [ ] 共通 API・ユーザーごとのデータ管理
- [ ] メモ・設定の端末間同期
- [ ] Web 版を基盤とする Android アプリ
- [ ] 専用サーバーでの運用

ロードマップは開発予定であり、実装順や仕様は変更される場合があります。

## データ保護と注意事項

- `data/notes.db`、バックアップ、`.env`、仮想環境などを Git にコミットしないでください。
- `.gitignore` は未追跡ファイルを除外します。すでに追跡済みのファイルには別途追跡解除が必要です。
- メモを削除すると DB から直接削除されます。現時点では復元機能はありません。
- UI の設定はブラウザ単位で保存されます。アカウント同期やメモのバックアップを提供するものではありません。
- 現在は認証・認可や CSRF 対策が未整備で、Flask のデバッグモードを使用しています。一般公開・複数ユーザー利用向けの本番構成ではありません。
- 日時は現行コードが DB の日時文字列を UTC として解釈して JST 表示する一方、保存側はサーバーのローカル時刻を使用しています。サーバーのタイムゾーンが UTC 以外の場合は表示にずれが生じる可能性があり、今後統一する必要があります。

## 更新履歴

- 2026-11-26 / 10-2D: お気に入りの表示フィルター・星ボタン・ピンと共通の非同期更新、日英・テーマ・モーション対応。セットアップ、DB、ルート、テスト手順も更新。

- 2026-11-27 / 10-3: タグのCRUD、複数関連付け、絞り込み、日英・テーマ対応、外部キー・テスト追加。

<!-- UNP_FAVORITES_V1 -->
<!-- UNP_TAGS_V1 -->

## Project

[GitHub — ayuyu0907/UltimateNotePad](https://github.com/ayuyu0907/UltimateNotePad)

現在は学習・開発中のプロジェクトです。

# matsuazwaakira

## Markdown 記事を WordPress へ一括アップロード

`upload_to_wordpress.py` を使って、Markdown ファイルを [fudousan.tech](https://fudousan.tech/) へ自動投稿できます。

---

### 事前準備

#### 1. WordPress アプリケーションパスワードの取得

1. WordPress 管理画面にログイン
2. **ユーザー → プロフィール** を開く
3. ページ下部「アプリケーションパスワード」セクションで名前を入力して **追加**
4. 表示されたパスワードをコピー（一度しか表示されません）

#### 2. `.env` ファイルの作成

```bash
cp .env.example .env
```

`.env` を編集して認証情報を入力:

```
WP_URL=https://fudousan.tech
WP_USERNAME=your_username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

#### 3. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

---

### 使い方

#### まず3記事で実験（推奨）

```bash
# ドライラン（実際には投稿しない）
python upload_to_wordpress.py --dir /path/to/markdown/files --limit 3 --dry-run

# 実際に3記事だけ投稿して確認
python upload_to_wordpress.py --dir /path/to/markdown/files --limit 3
```

#### 全記事を一括アップロード

```bash
python upload_to_wordpress.py --dir /path/to/markdown/files
```

#### オプション一覧

| オプション | 説明 |
|---|---|
| `--dir` | Markdown ファイルが入ったディレクトリ（必須） |
| `--limit N` | 最初の N 件のみアップロード |
| `--dry-run` | 実際には投稿せず確認のみ |
| `--log` | ログ CSV の保存先（デフォルト: `upload_log.csv`） |

---

### Markdown ファイルの形式

YAML frontmatter に対応しています（省略可）:

```markdown
---
title: 記事タイトル
date: 2024-01-15
slug: article-slug
categories:
  - 不動産
  - 宇都宮
tags:
  - 墓地
  - 霊園
status: publish   # publish / draft
---

本文をここに書きます...
```

frontmatter がない場合はファイル名をタイトルとして使用します。

---

### 結果ログ

実行後、`upload_log.csv` に成功・失敗の一覧が保存されます。

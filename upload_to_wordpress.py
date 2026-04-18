#!/usr/bin/env python3
"""
Markdown 記事を WordPress REST API で一括アップロードするスクリプト。
使い方:
  python upload_to_wordpress.py --dir /path/to/markdown/files
  python upload_to_wordpress.py --dir /path/to/markdown/files --dry-run
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import frontmatter
import markdown
import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")


def check_env():
    missing = [k for k, v in {"WP_URL": WP_URL, "WP_USERNAME": WP_USERNAME, "WP_APP_PASSWORD": WP_APP_PASSWORD}.items() if not v]
    if missing:
        print(f"エラー: .env に以下の変数が設定されていません: {', '.join(missing)}")
        sys.exit(1)


def title_from_filename(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").strip()


def api_url(path: str) -> str:
    return f"{WP_URL}/?rest_route={path}"


def get_or_create_term(name: str, taxonomy: str, session: requests.Session) -> int | None:
    route = f"/wp/v2/{'categories' if taxonomy == 'category' else 'tags'}"
    r = session.get(api_url(route), params={"search": name})
    r.raise_for_status()
    results = r.json()
    if results:
        return results[0]["id"]
    r = session.post(api_url(route), json={"name": name})
    r.raise_for_status()
    return r.json()["id"]


def upload_post(md_path: Path, session: requests.Session, dry_run: bool) -> dict:
    post = frontmatter.load(md_path)
    meta = post.metadata

    title = meta.get("title") or title_from_filename(md_path)
    body_html = markdown.markdown(post.content, extensions=["extra", "nl2br"])
    status = meta.get("status", "publish")
    date = meta.get("date") or meta.get("published")
    slug = meta.get("slug") or None

    payload: dict = {
        "title": title,
        "content": body_html,
        "status": status,
    }
    if date:
        if hasattr(date, "isoformat"):
            payload["date"] = date.isoformat()
        else:
            payload["date"] = str(date)
    if slug:
        payload["slug"] = slug

    if not dry_run:
        # カテゴリ
        raw_cats = meta.get("categories") or meta.get("category") or []
        if isinstance(raw_cats, str):
            raw_cats = [raw_cats]
        cat_ids = [get_or_create_term(c, "category", session) for c in raw_cats if c]
        if cat_ids:
            payload["categories"] = [i for i in cat_ids if i]

        # タグ
        raw_tags = meta.get("tags") or []
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        tag_ids = [get_or_create_term(t, "tag", session) for t in raw_tags if t]
        if tag_ids:
            payload["tags"] = [i for i in tag_ids if i]

        r = session.post(api_url("/wp/v2/posts"), json=payload)
        r.raise_for_status()
        post_id = r.json().get("id")
        post_url = r.json().get("link")
        return {"file": md_path.name, "title": title, "status": "success", "id": post_id, "url": post_url, "error": ""}

    return {"file": md_path.name, "title": title, "status": "dry-run", "id": "", "url": "", "error": ""}


def main():
    parser = argparse.ArgumentParser(description="Markdown → WordPress 一括アップロード")
    parser.add_argument("--dir", required=True, help="Markdown ファイルが入ったディレクトリ")
    parser.add_argument("--dry-run", action="store_true", help="実際には投稿せず確認のみ")
    parser.add_argument("--limit", type=int, default=None, help="アップロード件数の上限 (例: --limit 3 で最初の3記事のみ)")
    parser.add_argument("--log", default="upload_log.csv", help="ログファイル名 (デフォルト: upload_log.csv)")
    args = parser.parse_args()

    check_env()

    md_dir = Path(args.dir)
    if not md_dir.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {md_dir}")
        sys.exit(1)

    md_files = sorted(md_dir.rglob("*.md"))
    if args.limit:
        md_files = md_files[: args.limit]
    if not md_files:
        print(f"Markdown ファイルが見つかりませんでした: {md_dir}")
        sys.exit(0)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}対象ファイル数: {len(md_files)}")

    session = requests.Session()
    session.auth = (WP_USERNAME, WP_APP_PASSWORD)
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    results = []
    for i, md_path in enumerate(md_files, 1):
        print(f"  [{i}/{len(md_files)}] {md_path.name} ... ", end="", flush=True)
        try:
            result = upload_post(md_path, session, args.dry_run)
            print(result["status"])
        except requests.HTTPError as e:
            result = {"file": md_path.name, "title": "", "status": "error", "id": "", "url": "", "error": str(e)}
            print(f"失敗: {e}")
        except Exception as e:
            result = {"file": md_path.name, "title": "", "status": "error", "id": "", "url": "", "error": str(e)}
            print(f"失敗: {e}")
        results.append(result)

    # ログ保存
    log_path = Path(args.log)
    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "title", "status", "id", "url", "error"])
        writer.writeheader()
        writer.writerows(results)

    success = sum(1 for r in results if r["status"] in ("success", "dry-run"))
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\n完了: 成功 {success} 件 / エラー {errors} 件")
    print(f"ログ保存先: {log_path.resolve()}")


if __name__ == "__main__":
    main()

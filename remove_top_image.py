#!/usr/bin/env python3
"""
featured_media が設定されている記事の本文先頭画像を除去する。
Cocoon テーマはアイキャッチ（featured_media）を記事上部に自動表示するため、
本文先頭の同一画像が二重表示になる問題を修正する。
"""

import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")


def api_url(path: str) -> str:
    return f"{WP_URL}/?rest_route={path}"


def make_wp() -> requests.Session:
    s = requests.Session()
    s.auth = (WP_USERNAME, WP_APP_PASSWORD)
    s.headers["User-Agent"] = "Mozilla/5.0"
    return s


def paginate(wp, path, extra=None):
    items = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page, **(extra or {})}
        r = wp.get(api_url(path), params=params)
        batch = r.json()
        if not batch or isinstance(batch, dict):
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def remove_first_img(html: str) -> tuple[str, bool]:
    """本文の最初の<img>タグ（および周囲の空の<p>/<figure>）を除去する。"""
    # 最初の<img>タグの位置を見つける
    m = re.search(r'<img\b[^>]*>', html)
    if not m:
        return html, False

    start = m.start()
    end = m.end()
    new_html = html[:start] + html[end:]

    # 空になった <p></p> や <figure>...</figure> を除去
    new_html = re.sub(r'<p>\s*</p>', '', new_html)
    new_html = re.sub(r'<figure[^>]*>\s*</figure>', '', new_html)
    new_html = re.sub(r'\n{3,}', '\n\n', new_html).strip()

    return new_html, True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wp = make_wp()

    print("記事を取得中...", flush=True)
    posts = paginate(wp, "/wp/v2/posts", {
        "_fields": "id,content,featured_media",
        "context": "edit",
    })
    print(f"  記事数: {len(posts)}件")

    target = [p for p in posts
              if p.get("featured_media", 0) > 0
              and "<img" in (p.get("content", {}).get("raw", "") if isinstance(p.get("content"), dict) else "")]

    print(f"  featured_media 設定済み + 画像あり: {len(target)}件")

    updated = 0
    skipped = 0
    errors = 0

    for i, post in enumerate(target, 1):
        pid = post["id"]
        raw = post.get("content", {})
        if isinstance(raw, dict):
            raw = raw.get("raw", "")

        new_html, changed = remove_first_img(raw)
        if not changed:
            skipped += 1
            continue

        print(f"[{i}/{len(target)}] 記事 {pid}: 先頭画像を除去", flush=True)

        if args.dry_run:
            updated += 1
            continue

        try:
            r = wp.post(api_url(f"/wp/v2/posts/{pid}"), json={"content": new_html})
            r.raise_for_status()
            updated += 1
        except Exception as e:
            print(f"  ✗ エラー: {e}", flush=True)
            errors += 1

        time.sleep(0.3)

    print()
    print(f"完了: 更新 {updated}件 / スキップ {skipped}件 / エラー {errors}件")


if __name__ == "__main__":
    main()

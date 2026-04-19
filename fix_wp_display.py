#!/usr/bin/env python3
"""
WordPressの3つの問題を修正:
1. Cocoon lazyloadをnative化してPC表示を修正
2. 200×200pxプレースホルダー画像をメディアから削除し記事から除去
3. 各記事の最初の本物画像をfeatured_media(アイキャッチ)に設定
"""

import json
import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

PLACEHOLDER_W = 200
PLACEHOLDER_H = 200
PLACEHOLDER_BYTES = 10177  # 既知のプレースホルダー正確なサイズ


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


def is_placeholder(m: dict) -> bool:
    d = m.get("media_details", {})
    w = d.get("width", 0)
    h = d.get("height", 0)
    fs = d.get("filesize", 0)
    # 既知のプレースホルダー: 200×200px、10177バイト
    return w == PLACEHOLDER_W and h == PLACEHOLDER_H and fs == PLACEHOLDER_BYTES


def remove_placeholder_imgs(html: str, placeholder_urls: set) -> str:
    """プレースホルダー画像タグを除去し、空になった<p>/<figure>も除去"""
    def check_img(m):
        tag = m.group(0)
        for url in placeholder_urls:
            if url in tag:
                return ""
        return tag

    html = re.sub(r'<img[^>]+>', check_img, html)
    # 空になった <p></p> や <figure>...</figure> を除去
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<figure[^>]*>\s*</figure>', '', html)
    return html


def get_first_img_src(html: str) -> str | None:
    """最初の<img>のsrcまたはdata-srcを返す"""
    m = re.search(r'<img\b[^>]*?\b(?:src|data-src)=["\']([^"\']+)["\']', html)
    return m.group(1) if m else None


def try_fix_cocoon_lazyload(wp: requests.Session) -> bool:
    """CocoonのlazyloadをBrowser Nativeに変更を試みる。成功ならTrue。"""
    # 方法1: WP REST API settings経由
    try:
        r = wp.get(api_url("/wp/v2/settings"))
        settings = r.json()
        keys = list(settings.keys())
        print(f"  WP設定キー数: {len(keys)}", flush=True)

        # Cocoonのlazyload設定キーを試す
        for key in ["lazy_load_type", "cocoon_lazy_load_type"]:
            if key in settings:
                r2 = wp.post(api_url("/wp/v2/settings"), json={key: "native"})
                if r2.ok:
                    print(f"  ✓ {key} = 'native' に設定完了", flush=True)
                    return True
    except Exception as e:
        print(f"  REST API設定エラー: {e}", flush=True)

    return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-lazyload", action="store_true", help="lazyload設定変更をスキップ")
    parser.add_argument("--dry-run", action="store_true", help="実際の変更をしない（確認のみ）")
    args = parser.parse_args()

    wp = make_wp()

    # ===== 1. Cocoon lazyload修正 =====
    print("=" * 50)
    print("1. Cocoon lazyload設定確認")
    print("=" * 50)
    if not args.skip_lazyload:
        fixed = try_fix_cocoon_lazyload(wp)
        if not fixed:
            print()
            print("  ⚠ REST API経由でCocoon設定を変更できませんでした。")
            print("  PC表示修正のために以下の手順を実行してください:")
            print("  WordPress管理画面 → Cocoon Settings → Contents タブ")
            print("  → 遅延読み込み(Lazy Loading) → 「ブラウザのlazyload」に変更")
            print()
    else:
        print("  スキップ")

    # ===== 2. メディア取得 =====
    print("=" * 50)
    print("2. WPメディアを取得中...")
    print("=" * 50)
    all_media = paginate(wp, "/wp/v2/media", {
        "_fields": "id,source_url,media_details,title",
        "media_type": "image",
    })
    print(f"  メディア合計: {len(all_media)}件", flush=True)

    placeholders = [m for m in all_media if is_placeholder(m)]
    placeholder_urls = {m["source_url"] for m in placeholders}
    placeholder_ids = {m["id"] for m in placeholders}
    url_to_id = {m["source_url"]: m["id"] for m in all_media}

    print(f"  プレースホルダー: {len(placeholders)}件 (200×200px, 10177bytes の同一画像)")
    if placeholders:
        for m in placeholders[:5]:
            d = m.get("media_details", {})
            print(f"    例: id={m['id']} {d.get('width')}×{d.get('height')}px {d.get('filesize',0)//1024}KB {m['source_url'][-40:]}")
        if len(placeholders) > 5:
            print(f"    ... 他{len(placeholders)-5}件")

    # ===== 3. 記事取得・修正 =====
    print()
    print("=" * 50)
    print("3. 記事を取得・修正中...")
    print("=" * 50)
    posts = paginate(wp, "/wp/v2/posts", {
        "_fields": "id,content,featured_media",
        "context": "edit",
    })
    print(f"  記事数: {len(posts)}件", flush=True)

    updated = 0
    errors = 0
    featured_set = 0
    placeholder_removed = 0

    for i, post in enumerate(posts, 1):
        pid = post["id"]
        raw = post.get("content", {})
        if isinstance(raw, dict):
            raw = raw.get("raw", "")
        if not raw:
            continue

        current_fm = post.get("featured_media", 0)
        has_placeholder = any(url in raw for url in placeholder_urls)
        has_img = "<img" in raw

        if not has_placeholder and not has_img:
            continue

        new_html = raw

        # プレースホルダー除去
        if has_placeholder:
            new_html = remove_placeholder_imgs(new_html, placeholder_urls)

        update: dict = {}

        if new_html != raw:
            update["content"] = new_html

        # featured_media設定
        first_src = get_first_img_src(new_html)
        if first_src and (current_fm == 0 or current_fm in placeholder_ids):
            mid = url_to_id.get(first_src)
            if mid and mid not in placeholder_ids:
                update["featured_media"] = mid

        if not update:
            continue

        fm_info = f"featured={update.get('featured_media', '変更なし')}"
        content_changed = "content" in update
        print(f"[{i}/{len(posts)}] 記事 {pid}: "
              f"{'プレースホルダー除去 ' if content_changed else ''}"
              f"{fm_info}", flush=True)

        if args.dry_run:
            if content_changed:
                placeholder_removed += 1
            if "featured_media" in update:
                featured_set += 1
            continue

        try:
            r = wp.post(api_url(f"/wp/v2/posts/{pid}"), json=update)
            r.raise_for_status()
            if content_changed:
                placeholder_removed += 1
            if "featured_media" in update:
                featured_set += 1
            updated += 1
        except Exception as e:
            print(f"  ✗ 更新エラー: {e}", flush=True)
            errors += 1

        time.sleep(0.3)

    # ===== 4. プレースホルダーメディア削除 =====
    print()
    print("=" * 50)
    print(f"4. プレースホルダーメディア {len(placeholders)}件を削除中...")
    print("=" * 50)
    del_ok = 0
    del_err = 0
    for m in placeholders:
        if args.dry_run:
            print(f"  [DRY] 削除予定: {m['id']} {m.get('source_url','')[-40:]}")
            del_ok += 1
            continue
        try:
            r = wp.delete(api_url(f"/wp/v2/media/{m['id']}"), params={"force": "true"})
            r.raise_for_status()
            del_ok += 1
        except Exception as e:
            print(f"  ✗ 削除失敗 id={m['id']}: {e}", flush=True)
            del_err += 1
        time.sleep(0.2)

    print()
    print("=" * 50)
    print("完了サマリー")
    print("=" * 50)
    if args.dry_run:
        print("[DRY RUN モード: 実際の変更なし]")
    print(f"  記事更新: {updated}件 (エラー {errors}件)")
    print(f"    うちプレースホルダー除去: {placeholder_removed}件")
    print(f"    うちfeatured_media設定: {featured_set}件")
    print(f"  メディア削除: {del_ok}件 (エラー {del_err}件)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
同カテゴリの関連記事への内部リンクを各記事末尾に追加する。
すでに「関連記事」セクションがある記事はスキップ。
"""
import os, re, time, random, requests
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

WP_URL = os.getenv("WP_URL","").rstrip("/")
s = requests.Session()
s.auth = (os.getenv("WP_USERNAME"), os.getenv("WP_APP_PASSWORD"))
s.headers["User-Agent"] = "Mozilla/5.0"

def api(p): return f"{WP_URL}/?rest_route={p}"

def paginate(path, extra=None):
    items, page = [], 1
    while True:
        r = s.get(api(path), params={"per_page":100,"page":page,**(extra or {})})
        b = r.json()
        if not b or isinstance(b,dict): break
        items.extend(b)
        if len(b)<100: break
        page += 1
    return items

def make_related_html(related):
    items = "".join(
        f'<li><a href="{p["link"]}">{p["title"]["rendered"]}</a></li>'
        for p in related
    )
    return f'\n<hr>\n<p><strong>関連記事</strong></p>\n<ul>\n{items}\n</ul>\n'

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {
    "context": "edit",
    "_fields": "id,title,content,categories,link",
    "status": "publish",
})
print(f"  記事数: {len(posts)}")

# カテゴリ別インデックス
cat_posts = defaultdict(list)
for p in posts:
    for cid in p.get("categories", []):
        cat_posts[cid].append(p)

targets = [
    p for p in posts
    if "関連記事" not in p.get("content",{}).get("raw","")
    and p.get("categories")
]
print(f"  内部リンクなし: {len(targets)}件 → 追加します")

updated = skipped = errors = 0
for i, post in enumerate(targets, 1):
    pid = post["id"]
    cats = post.get("categories", [])

    # 同カテゴリから最大3件をランダム選出（自分を除く）
    pool = []
    for cid in cats:
        pool.extend([p for p in cat_posts[cid] if p["id"] != pid])
    pool = list({p["id"]: p for p in pool}.values())  # 重複除去

    if len(pool) < 2:
        skipped += 1
        continue

    related = random.sample(pool, min(3, len(pool)))
    addition = make_related_html(related)

    raw = post.get("content",{}).get("raw","")
    new_content = raw.rstrip() + addition

    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"content": new_content})
        r.raise_for_status()
        updated += 1
        if i % 50 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
        print(f"  ✗ 記事{pid}: {e}")
    time.sleep(0.25)

print(f"\n完了: 追加 {updated}件 / スキップ {skipped}件 / エラー {errors}件")

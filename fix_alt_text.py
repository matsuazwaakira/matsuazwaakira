#!/usr/bin/env python3
"""
image_N.jpg 形式のalt textを記事タイトルベースの説明的テキストに変換。
"""
import os, re, time, requests
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
        page+=1
    return items

def fix_alts(html, title):
    img_counter = [0]
    def replacer(m):
        tag = m.group()
        # alt="image_N.jpg" パターンのみ対象
        if not re.search(r'alt="image_\d+\.jpg"', tag):
            return tag
        n = img_counter[0]
        img_counter[0] += 1
        if n == 0:
            new_alt = f"{title}"
        else:
            new_alt = f"{title} 写真{n+1}"
        return re.sub(r'alt="image_\d+\.jpg"', f'alt="{new_alt}"', tag)
    return re.sub(r'<img[^>]+>', replacer, html)

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {
    "context": "edit",
    "_fields": "id,title,content",
    "status": "publish",
})

# image_N.jpg alt を持つ記事のみ対象
targets = []
for p in posts:
    raw = p.get("content",{}).get("raw","")
    if re.search(r'alt="image_\d+\.jpg"', raw):
        targets.append(p)

print(f"  対象記事: {len(targets)}件")

updated = errors = 0
for i, post in enumerate(targets, 1):
    pid = post["id"]
    title = re.sub(r'【[^】]+】\s*', '', post.get("title",{}).get("rendered","")).strip()
    raw = post.get("content",{}).get("raw","")
    new_html = fix_alts(raw, title)
    if new_html == raw:
        continue
    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"content": new_html})
        r.raise_for_status()
        updated += 1
        if i % 100 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
        print(f"  ✗ 記事{pid}: {e}")
    time.sleep(0.2)

print(f"\n完了: alt text修正 {updated}件 / エラー {errors}件")

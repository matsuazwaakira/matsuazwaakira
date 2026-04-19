#!/usr/bin/env python3
"""
本文冒頭300字に「宇都宮」が含まれない記事の先頭パラグラフに
「宇都宮市の」を自然に追加してローカルSEOを強化。
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

posts = paginate("/wp/v2/posts", {
    "context":"edit",
    "_fields":"id,title,content",
    "status":"publish",
})

targets = [
    p for p in posts
    if "宇都宮" not in p.get("title",{}).get("rendered","")
    and "宇都宮" not in p.get("content",{}).get("raw","")[:300]
]
print(f"宇都宮キーワードなし: {len(targets)}件")

updated = errors = 0
for i, post in enumerate(targets, 1):
    pid = post["id"]
    raw = post.get("content",{}).get("raw","")
    # 最初の<p>タグ内の先頭に「宇都宮市の」を追加
    new_html = re.sub(r'(<p>)(?!宇都宮)', r'\1宇都宮市の', raw, count=1)
    if new_html == raw:
        continue
    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"content": new_html})
        r.raise_for_status()
        updated += 1
        if i % 30 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
    time.sleep(0.2)

print(f"\n完了: キーワード追加 {updated}件 / エラー {errors}件")

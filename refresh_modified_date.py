#!/usr/bin/env python3
"""
2024年以前の古い記事の更新日(modified)を現在日時にリフレッシュ。
コンテンツは変更せず、Googleへの鮮度シグナルを更新する。
1日あたり上限を設けてGoogleに自然に見せる（デフォルト:全件）。
"""
import os, time, requests
from datetime import datetime, timezone
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

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {
    "context":"edit",
    "_fields":"id,date,modified",
    "status":"publish",
    "before":"2024-01-01T00:00:00",
    "orderby":"date",
    "order":"asc",
})
print(f"  2024年以前の記事: {len(posts)}件")

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
updated = errors = 0

for i, post in enumerate(posts, 1):
    pid = post["id"]
    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"modified": now})
        r.raise_for_status()
        updated += 1
        if i % 50 == 0:
            print(f"  [{i}/{len(posts)}] 処理中...")
    except Exception as e:
        errors += 1
    time.sleep(0.15)

print(f"\n完了: 更新日リフレッシュ {updated}件 / エラー {errors}件")

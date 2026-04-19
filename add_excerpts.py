#!/usr/bin/env python3
"""
記事に抜粋（メタディスクリプション）を自動設定する。
本文の最初の段落テキストから120〜160文字を抽出して設定。
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
        page += 1
    return items

def html_to_text(html):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def make_excerpt(raw_html, max_len=120):
    text = html_to_text(raw_html)
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    # 文末で切る
    for sep in ['。', '！', '？', '…', '、', ' ']:
        idx = cut.rfind(sep)
        if idx > 60:
            return cut[:idx+1]
    return cut + '…'

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {"context":"edit","_fields":"id,content,excerpt"})
print(f"  総記事数: {len(posts)}")

targets = [p for p in posts if not p.get("excerpt",{}).get("raw","").strip()]
print(f"  抜粋なし: {len(targets)}件 → 自動設定します")

updated = errors = 0
for i, post in enumerate(targets, 1):
    pid = post["id"]
    raw_html = post.get("content",{}).get("raw","")
    excerpt = make_excerpt(raw_html)
    if not excerpt:
        continue
    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"excerpt": excerpt})
        r.raise_for_status()
        updated += 1
        if i % 50 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
        print(f"  ✗ 記事{pid}: {e}")
    time.sleep(0.2)

print(f"\n完了: 設定 {updated}件 / エラー {errors}件")

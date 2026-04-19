#!/usr/bin/env python3
"""
タグなし記事に、タイトル・本文から地名・キーワードを抽出して自動タグ付け。
既存タグから一致するものを優先使用し、新規タグは地名のみ作成。
"""
import os, re, time, requests
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
        page+=1
    return items

def get_or_create_tag(name, tag_cache):
    if name in tag_cache:
        return tag_cache[name]
    r = s.post(api("/wp/v2/tags"), json={"name": name})
    if r.status_code in (200, 201):
        tid = r.json()["id"]
        tag_cache[name] = tid
        return tid
    # すでに存在する場合
    search = s.get(api("/wp/v2/tags"), params={"search": name, "per_page": 1})
    results = search.json()
    if results:
        tid = results[0]["id"]
        tag_cache[name] = tid
        return tid
    return None

# 宇都宮の地名・エリアキーワード（タグ候補）
AREA_KEYWORDS = [
    "オリオン通り","JR宇都宮駅","東宿郷","駅前通り","カフェ","馬場通り",
    "インターパーク","鶴田町","今泉","平松町","簗瀬","西川田","雀宮",
    "清原","岡本","宝木","石井","若松原","緑が丘","大曽","宮の原",
    "別所","滝谷町","上戸祭","峰","松が峰","江野町","大通り","二荒山",
    "東武宇都宮","宇都宮大学","陽東","瑞穂野","上河内","河内","芳賀",
    "真岡","LRT","ライトライン","ベルモール","パセオ","コープ",
]

# カテゴリ→タグのマッピング
CAT_TAG_MAP = {
    "ラーメン": ["ラーメン","麺"],
    "餃子": ["餃子","宇都宮餃子"],
    "カフェ": ["カフェ","コーヒー"],
    "グルメ": ["グルメ","飲食"],
    "居酒屋": ["居酒屋","飲み"],
    "パン屋": ["パン","ベーカリー"],
    "定食": ["定食","ランチ"],
    "観光": ["観光","宇都宮観光"],
    "くらし": ["生活","宇都宮"],
    "レストラン": ["レストラン","ディナー"],
}

print("既存タグを取得中...")
existing_tags = paginate("/wp/v2/tags", {"_fields":"id,name","per_page":100})
tag_cache = {t["name"]: t["id"] for t in existing_tags}
print(f"  既存タグ数: {len(tag_cache)}")

print("カテゴリ情報を取得中...")
cats = paginate("/wp/v2/categories", {"_fields":"id,name"})
cat_map = {c["id"]: c["name"] for c in cats}

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {
    "context":"edit",
    "_fields":"id,title,content,tags,categories",
    "status":"publish",
})
targets = [p for p in posts if not p.get("tags")]
print(f"  タグなし記事: {len(targets)}件")

updated = skipped = errors = 0

for i, post in enumerate(targets, 1):
    pid = post["id"]
    title = post.get("title",{}).get("rendered","")
    raw = re.sub(r'<[^>]+>', ' ', post.get("content",{}).get("raw",""))
    text = title + " " + raw

    tag_ids = set()

    # 地名マッチ
    for kw in AREA_KEYWORDS:
        if kw in text:
            tid = get_or_create_tag(kw, tag_cache)
            if tid:
                tag_ids.add(tid)

    # カテゴリ→タグ
    for cid in post.get("categories",[]):
        cname = cat_map.get(cid,"")
        for tag_name in CAT_TAG_MAP.get(cname, []):
            tid = get_or_create_tag(tag_name, tag_cache)
            if tid:
                tag_ids.add(tid)

    if not tag_ids:
        # 最低限「宇都宮」タグを付与
        tid = get_or_create_tag("宇都宮", tag_cache)
        if tid:
            tag_ids.add(tid)

    if not tag_ids:
        skipped += 1
        continue

    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"tags": list(tag_ids)})
        r.raise_for_status()
        updated += 1
        if i % 50 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
        print(f"  ✗ 記事{pid}: {e}")
    time.sleep(0.2)

print(f"\n完了: タグ付与 {updated}件 / スキップ {skipped}件 / エラー {errors}件")

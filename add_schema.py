#!/usr/bin/env python3
"""
記事にJSON-LD構造化データを追加。
飲食カテゴリ → Restaurant schema
イベント・くらし → Article schema
"""
import os, re, time, json, requests
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

# カテゴリ→料理タイプマッピング
CUISINE_MAP = {
    "ラーメン": "Ramen",
    "餃子": "Japanese",
    "カフェ": "Cafe",
    "グルメ": "Japanese",
    "レストラン": "Japanese",
    "パン屋": "Bakery",
    "定食": "Japanese",
    "居酒屋": "Japanese",
    "焼肉": "Yakiniku",
    "寿司": "Sushi",
    "イタリアン": "Italian",
    "フレンチ": "French",
    "カレー": "Indian",
}
FOOD_CATS = set(CUISINE_MAP.keys())

def make_restaurant_schema(title, url, excerpt, cuisine, date_pub):
    clean_title = re.sub(r'【[^】]+】\s*', '', title).strip()
    return {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": clean_title,
        "url": url,
        "description": excerpt[:160] if excerpt else clean_title,
        "servesCuisine": cuisine,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "宇都宮市",
            "addressRegion": "栃木県",
            "addressCountry": "JP"
        },
        "areaServed": "宇都宮市"
    }

def make_article_schema(title, url, excerpt, date_pub, date_mod):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "url": url,
        "description": excerpt[:160] if excerpt else title,
        "datePublished": date_pub,
        "dateModified": date_mod,
        "author": {
            "@type": "Organization",
            "name": "宇都宮くらし",
            "url": WP_URL
        },
        "publisher": {
            "@type": "Organization",
            "name": "宇都宮くらし",
            "url": WP_URL
        }
    }

def wrap_schema(schema_dict):
    json_str = json.dumps(schema_dict, ensure_ascii=False, indent=None)
    return f'\n<script type="application/ld+json">\n{json_str}\n</script>\n'

print("カテゴリ情報を取得中...")
cats = paginate("/wp/v2/categories", {"_fields":"id,name"})
cat_map = {c["id"]: c["name"] for c in cats}

print("記事を取得中...")
posts = paginate("/wp/v2/posts", {
    "context": "edit",
    "_fields": "id,title,content,excerpt,categories,link,date,modified",
    "status": "publish",
})
print(f"  総記事数: {len(posts)}")

# すでにschemaがある記事を除外
targets = [p for p in posts if 'application/ld+json' not in p.get("content",{}).get("raw","")]
print(f"  Schema未設定: {len(targets)}件")

updated = errors = 0
for i, post in enumerate(targets, 1):
    pid = post["id"]
    title = post.get("title",{}).get("rendered","")
    url = post.get("link","")
    excerpt = re.sub(r'<[^>]+>', '', post.get("excerpt",{}).get("rendered","")).strip()
    date_pub = post.get("date","")
    date_mod = post.get("modified","")
    cat_names = [cat_map.get(cid,"") for cid in post.get("categories",[])]

    # カテゴリ判定
    food_cat = next((c for c in cat_names if c in FOOD_CATS), None)

    if food_cat:
        cuisine = CUISINE_MAP.get(food_cat, "Japanese")
        schema = make_restaurant_schema(title, url, excerpt, cuisine, date_pub)
    else:
        schema = make_article_schema(title, url, excerpt, date_pub, date_mod)

    raw = post.get("content",{}).get("raw","")
    new_content = raw.rstrip() + wrap_schema(schema)

    try:
        r = s.post(api(f"/wp/v2/posts/{pid}"), json={"content": new_content})
        r.raise_for_status()
        updated += 1
        if i % 100 == 0:
            print(f"  [{i}/{len(targets)}] 処理中...")
    except Exception as e:
        errors += 1
        print(f"  ✗ 記事{pid}: {e}")
    time.sleep(0.2)

print(f"\n完了: Schema追加 {updated}件 / エラー {errors}件")

#!/usr/bin/env python3
"""
Google Drive の検索結果JSONからコンテンツを取り出し、WordPress へ一括アップロード。
「宇都宮」が含まれる記事のみ対象。
"""

import json
import os
import re
import csv
import sys
import requests
import markdown as md
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

BASE_DIR = "/root/.claude/projects/-home-user-matsuazwaakira/2a9424fe-f0ca-436d-a507-6a0270751ea3/tool-results/"

# page 1の5記事（inline返却でファイル保存なし）
PAGE1_SNIPPETS = []  # 後から手動追加が必要な場合はここに追加


def api_url(path: str) -> str:
    return f"{WP_URL}/?rest_route={path}"


def extract_title(snippet: str) -> str:
    """最初のH1行からタイトルを取得。"""
    for line in snippet.splitlines():
        clean = line.lstrip("\ufeff").strip()
        # \\# または # で始まる行
        if clean.startswith("\\#") or clean.startswith("#"):
            title = re.sub(r"^\\?#+\s*", "", clean).strip()
            # \#エキスパートトピ のようなハッシュタグ末尾を除去
            title = re.sub(r"\s*\\?#\S+$", "", title).strip()
            return title
    return ""


def parse_article(snippet: str) -> dict:
    """snippet からタイトル・日付・本文を抽出。"""
    title = extract_title(snippet)
    lines = snippet.splitlines()
    date_str = ""
    body_lines = []
    in_body = False

    for line in lines:
        clean = line.lstrip("\ufeff").strip()

        # H1行が来たら本文開始
        if not in_body:
            if clean.startswith("\\#") or clean.startswith("#"):
                in_body = True
            continue  # H1行自体は本文に入れない

        # 日付行
        if clean.startswith("Date:"):
            date_str = clean.replace("Date:", "").strip()
            continue
        # URL行スキップ
        if clean.startswith("URL:"):
            continue
        # フッター以降をカット
        if "宇都宮のはかせの最近の記事" in clean:
            break
        if "重要なお知らせ" in clean:
            break
        body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # バックスラッシュエスケープを戻す（画像除去より先に行う）
    body = re.sub(r"\\#", "#", body)
    body = re.sub(r"\\!", "!", body)
    body = re.sub(r"\\\[", "[", body)
    body = re.sub(r"\\\]", "]", body)
    body = re.sub(r"\\_", "_", body)

    # 画像参照を除去（画像はWordPressにないため）
    body = re.sub(r"^\s*!\[Image\]\(image_\d+\.jpg\)\s*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    # 日付パース: "2024/5/26(日) 18:43" または "5/26(日) 18:43"
    wp_date = None
    if date_str:
        m = re.match(r"(?:(\d{4})/)?(\d{1,2})/(\d{1,2})", date_str)
        if m:
            year = int(m.group(1)) if m.group(1) else 2024
            try:
                wp_date = f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T00:00:00"
            except Exception:
                pass

    return {"title": title, "body": body, "date": wp_date}


def upload_article(session, title, body_markdown, date_str):
    body_html = md.markdown(body_markdown, extensions=["extra", "nl2br"])
    payload = {
        "title": title,
        "content": body_html,
        "status": "publish",
    }
    if date_str:
        payload["date"] = date_str

    r = session.post(api_url("/wp/v2/posts"), json=payload)
    r.raise_for_status()
    return r.json().get("id"), r.json().get("link")


def collect_articles():
    """全検索結果JSONから宇都宮記事のみ収集。"""
    seen = set()
    articles = []

    result_files = sorted(
        f for f in os.listdir(BASE_DIR) if "search_files" in f
    )

    for fname in result_files:
        data = json.load(open(os.path.join(BASE_DIR, fname)))
        for item in data.get("files", []):
            fid = item.get("id")
            snippet = item.get("contentSnippet", "")
            if not fid or fid in seen or not snippet:
                continue
            title = extract_title(snippet)
            if "宇都宮" not in title:
                continue  # 無関係ファイルをスキップ
            seen.add(fid)
            articles.append({"id": fid, "snippet": snippet, "title": title})

    return articles


def main():
    session = requests.Session()
    session.auth = (WP_USERNAME, WP_APP_PASSWORD)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    articles = collect_articles()
    total = len(articles)
    print(f"対象記事数: {total} 件（宇都宮関連のみ）")

    results = []
    for i, art in enumerate(articles, 1):
        parsed = parse_article(art["snippet"])
        title = parsed["title"] or art["title"]
        body = parsed["body"]
        date_str = parsed["date"]

        print(f"  [{i}/{total}] {title[:55]} ... ", end="", flush=True)
        try:
            post_id, post_url = upload_article(session, title, body, date_str)
            print("success")
            results.append({
                "drive_id": art["id"], "title": title,
                "status": "success", "id": post_id, "url": post_url, "error": ""
            })
        except Exception as e:
            print(f"失敗: {e}")
            results.append({
                "drive_id": art["id"], "title": title,
                "status": "error", "id": "", "url": "", "error": str(e)
            })

    # ログ保存
    log_path = "/home/user/matsuazwaakira/upload_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["drive_id", "title", "status", "id", "url", "error"])
        writer.writeheader()
        writer.writerows(results)

    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\n完了: 成功 {success} 件 / エラー {errors} 件")
    print(f"ログ: {log_path}")


if __name__ == "__main__":
    main()

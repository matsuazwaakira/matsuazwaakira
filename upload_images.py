#!/usr/bin/env python3
"""
Google Drive の画像を WordPress にアップロードし、記事本文（画像付き）に更新するスクリプト。

処理フロー:
1. upload_log.csv から article_drive_id → WP Post ID のマッピングを取得
2. 検索結果JSON から article_drive_id → (parentId, snippet) を取得
3. Drive から全画像ファイルを収集し parentId でグループ化
4. 各記事の画像を Drive からダウンロード → WP Media にアップロード
5. スニペット内の image_N.jpg を WP URL に置換して記事を更新
"""

import base64
import csv
import json
import os
import re
import sys
from pathlib import Path

import markdown as md
import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

MCP_CONFIG_FILE = "/tmp/mcp-config-cse_01EjwUDTf38kjH78FdSU4XUJ.json"
SESSION_TOKEN_FILE = "/home/claude/.claude/remote/.session_ingress_token"
SEARCH_RESULTS_DIR = "/root/.claude/projects/-home-user-matsuazwaakira/2a9424fe-f0ca-436d-a507-6a0270751ea3/tool-results/"
UPLOAD_LOG = "/home/user/matsuazwaakira/upload_log.csv"


def api_url(path: str) -> str:
    return f"{WP_URL}/?rest_route={path}"


def make_wp_session() -> requests.Session:
    s = requests.Session()
    s.auth = (WP_USERNAME, WP_APP_PASSWORD)
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return s


def make_drive_session() -> tuple[requests.Session, str]:
    cfg = json.load(open(MCP_CONFIG_FILE))
    srv = cfg["mcpServers"]["963b7bc2-a160-4b4c-836c-7c9b95f52911"]
    token = open(SESSION_TOKEN_FILE).read().strip()
    headers = dict(srv["headers"])
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"
    s = requests.Session()
    s.headers.update(headers)
    return s, srv["url"]


def parse_sse(response: requests.Response) -> dict:
    """SSE レスポンスから JSON データを取り出す。"""
    text = response.content.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                outer = json.loads(line[5:].strip())
                result_text = outer.get("result", {}).get("content", [{}])[0].get("text", "{}")
                return json.loads(result_text)
            except Exception:
                continue
    return {}


def download_drive_image(drive_session, proxy_url, file_id) -> tuple[bytes, str]:
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "download_file_content", "arguments": {"fileId": file_id}}
    }
    r = drive_session.post(proxy_url, json=payload, timeout=60)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                outer = json.loads(line[5:].strip())
                inner_text = outer.get("result", {}).get("content", [{}])[0].get("text", "{}")
                inner = json.loads(inner_text)
                for item in inner.get("content", []):
                    resource = item.get("embeddedResource", {})
                    blob_data = resource.get("contents", {})
                    mime = blob_data.get("mimeType", "image/jpeg")
                    blob = blob_data.get("blob", "")
                    if blob:
                        return base64.b64decode(blob), mime
            except Exception:
                continue
    raise ValueError(f"画像取得失敗: {file_id}")


def upload_to_wp_media(wp_session, image_bytes, mime_type, filename) -> str:
    r = wp_session.post(
        api_url("/wp/v2/media"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                 "Content-Type": mime_type},
        data=image_bytes,
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("source_url", "")


def search_drive_images_all(drive_session, proxy_url) -> list[dict]:
    images = []
    seen = set()
    page_token = None
    print("  Drive 内の画像ファイルを収集中...", flush=True)
    while True:
        args: dict = {"query": "mimeType contains 'image'", "pageSize": 50,
                      "excludeContentSnippets": True}
        if page_token:
            args["pageToken"] = page_token
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "search_files", "arguments": args}}
        r = drive_session.post(proxy_url, json=payload, timeout=30)
        r.raise_for_status()
        result = parse_sse(r)
        for item in result.get("files", []):
            fid = item.get("id")
            if fid and fid not in seen:
                seen.add(fid)
                images.append({"id": fid, "title": item.get("title", ""),
                                "parentId": item.get("parentId", ""),
                                "mimeType": item.get("mimeType", "image/jpeg")})
        page_token = result.get("nextPageToken")
        if not page_token:
            break
        if len(images) % 200 == 0:
            print(f"  収集中: {len(images)}件...", flush=True)
    return images


def load_upload_log() -> dict:
    mapping = {}
    with open(UPLOAD_LOG, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] == "success":
                mapping[row["drive_id"]] = {"wp_id": int(row["id"]), "title": row["title"]}
    return mapping


def load_article_data() -> dict:
    """検索結果JSONから {drive_id: {parentId, snippet}} を返す。"""
    data = {}
    seen = set()
    for fname in sorted(os.listdir(SEARCH_RESULTS_DIR)):
        if "search_files" not in fname:
            continue
        jdata = json.load(open(os.path.join(SEARCH_RESULTS_DIR, fname)))
        for item in jdata.get("files", []):
            fid = item.get("id")
            if fid and fid not in seen:
                seen.add(fid)
                data[fid] = {
                    "parentId": item.get("parentId", ""),
                    "snippet": item.get("contentSnippet", ""),
                }
    return data


def rebuild_body_with_images(snippet: str, img_url_map: dict) -> str:
    """スニペットから本文を再構築し画像URLを置換する。"""
    lines = snippet.splitlines()
    body_lines = []
    in_body = False

    for line in lines:
        clean = line.lstrip("\ufeff").strip()
        if not in_body:
            if clean.startswith("\\#") or clean.startswith("#"):
                in_body = True
            continue
        if clean.startswith("Date:") or clean.startswith("URL:"):
            continue
        if "宇都宮のはかせの最近の記事" in clean or "重要なお知らせ" in clean:
            break
        body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # エスケープ解除
    body = re.sub(r"\\#", "#", body)
    body = re.sub(r"\\!", "!", body)
    body = re.sub(r"\\\[", "[", body)
    body = re.sub(r"\\\]", "]", body)
    body = re.sub(r"\\_", "_", body)

    # 画像URLを置換（なければ除去）
    def replace_image(m):
        img_name = m.group(1)
        if img_name in img_url_map:
            return f"![{img_name}]({img_url_map[img_name]})"
        return ""

    body = re.sub(r"!\[Image\]\((image_\d+\.jpg)\)", replace_image, body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip", type=int, default=0, help="最初のN件をスキップして再開")
    args = parser.parse_args()

    wp = make_wp_session()
    drive_session, proxy_url = make_drive_session()

    print("ログ読み込み中...")
    log = load_upload_log()
    print(f"  WP投稿済み: {len(log)}件")

    print("Driveメタデータ読み込み中...")
    article_data = load_article_data()

    print("Drive 画像収集中...")
    all_images = search_drive_images_all(drive_session, proxy_url)
    print(f"  画像合計: {len(all_images)}件")

    images_by_parent: dict[str, list] = {}
    for img in all_images:
        images_by_parent.setdefault(img["parentId"], []).append(img)

    # 記事 drive_id → parentId の逆引き
    processable = []
    for art_id, wp_info in log.items():
        art_meta = article_data.get(art_id, {})
        pid = art_meta.get("parentId", "")
        if pid and pid in images_by_parent:
            processable.append({
                "art_id": art_id,
                "wp_id": wp_info["wp_id"],
                "title": wp_info["title"],
                "pid": pid,
                "snippet": art_meta.get("snippet", ""),
            })

    if args.skip:
        processable = processable[args.skip:]
        print(f"  → {args.skip}件スキップ、{len(processable)}件から再開")

    print(f"\n画像あり記事: {len(processable)}件 / 全{len(log)}件")
    print("アップロード開始...\n")

    success = 0
    errors = 0

    for i, art in enumerate(processable, args.skip + 1):
        images = sorted(images_by_parent[art["pid"]], key=lambda x: x["title"])
        print(f"[{i}/{len(processable)}] {art['title'][:50]} ({len(images)}枚)", flush=True)

        img_url_map = {}
        for img in images:
            img_name = img["title"]
            fname = f"{art['wp_id']}_{img_name}"
            try:
                img_bytes, mime = download_drive_image(drive_session, proxy_url, img["id"])
                wp_url = upload_to_wp_media(wp, img_bytes, mime, fname)
                img_url_map[img_name] = wp_url
                print(f"  ✓ {img_name}", flush=True)
            except Exception as e:
                print(f"  ✗ {img_name}: {e}", flush=True)
                errors += 1

        # 記事本文を画像付きで再構築・更新
        try:
            body = rebuild_body_with_images(art["snippet"], img_url_map)
            body_html = md.markdown(body, extensions=["extra", "nl2br"])
            wp.post(api_url(f"/wp/v2/posts/{art['wp_id']}"), json={"content": body_html})
            print(f"  → 記事更新完了\n", flush=True)
            success += 1
        except Exception as e:
            print(f"  → 記事更新エラー: {e}\n", flush=True)
            errors += 1

    print(f"完了: 成功 {success}件 / エラー {errors}件")


if __name__ == "__main__":
    main()

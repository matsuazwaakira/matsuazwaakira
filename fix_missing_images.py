#!/usr/bin/env python3
"""
画像なし記事の画像を個別検索でDriveから取得してWordPressに挿入するスクリプト。
bulk search がページネーション上限で漏れた記事を対象にする。
"""

import base64
import csv
import json
import os
import re
import time

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
PROGRESS_FILE = "/tmp/fix_missing_images_progress.json"


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


def search_images_by_title(drive_session, proxy_url, title: str) -> list[dict]:
    """指定ファイル名の画像を全Drive内から検索しparentIdとIDのリストを返す。"""
    images = []
    page_token = None
    while True:
        args: dict = {
            "query": f"mimeType contains 'image' and title = '{title}'",
            "pageSize": 50,
            "excludeContentSnippets": True,
        }
        if page_token:
            args["pageToken"] = page_token
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "search_files", "arguments": args}}
        for attempt in range(3):
            try:
                r = drive_session.post(proxy_url, json=payload, timeout=60)
                r.raise_for_status()
                result = parse_sse(r)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                else:
                    return images
        for item in result.get("files", []):
            fid = item.get("id")
            if fid:
                images.append({
                    "id": fid,
                    "title": item.get("title", ""),
                    "parentId": item.get("parentId", ""),
                    "mimeType": item.get("mimeType", "image/jpeg"),
                })
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return images


def read_full_article(drive_session, proxy_url, file_id: str) -> str:
    """Drive からMarkdownファイルの完全なテキストを取得する（download_file_content使用）。"""
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "download_file_content", "arguments": {"fileId": file_id}}
    }
    for attempt in range(3):
        try:
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
                            blob = blob_data.get("blob", "")
                            if blob:
                                return base64.b64decode(blob).decode("utf-8", errors="replace")
                    except Exception:
                        continue
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    return ""


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


def extract_image_refs_from_full_content(content: str) -> list[str]:
    """完全なMarkdownコンテンツから画像参照を抽出する。"""
    # After unescape, looks for ![Image](image_N.jpg)
    content = re.sub(r"\\#", "#", content)
    content = re.sub(r"\\!", "!", content)
    content = re.sub(r"\\\[", "[", content)
    content = re.sub(r"\\\]", "]", content)
    content = re.sub(r"\\_", "_", content)
    refs = re.findall(r"!\[Image\]\((image_\d+\.jpg)\)", content)
    return list(dict.fromkeys(refs))  # deduplicate preserving order


def rebuild_html_with_images(full_content: str, img_url_map: dict) -> str:
    """完全なMarkdownから本文を再構築し画像URLを挿入してHTMLに変換する。"""
    lines = full_content.splitlines()
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
    body = re.sub(r"\\#", "#", body)
    body = re.sub(r"\\!", "!", body)
    body = re.sub(r"\\\[", "[", body)
    body = re.sub(r"\\\]", "]", body)
    body = re.sub(r"\\_", "_", body)

    def replace_image(m):
        img_name = m.group(1)
        if img_name in img_url_map:
            return f"![{img_name}]({img_url_map[img_name]})"
        return ""

    body = re.sub(r"!\[Image\]\((image_\d+\.jpg)\)", replace_image, body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return md.markdown(body, extensions=["extra", "nl2br"])


def load_progress() -> set:
    try:
        return set(json.load(open(PROGRESS_FILE)))
    except Exception:
        return set()


def save_progress(done_ids: set):
    json.dump(list(done_ids), open(PROGRESS_FILE, "w"))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="進捗リセット")
    args = parser.parse_args()

    if args.reset and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    done_ids = load_progress()

    wp = make_wp_session()
    drive_session, proxy_url = make_drive_session()

    # Load upload log
    log = {}
    with open(UPLOAD_LOG, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] == "success":
                log[row["drive_id"]] = {"wp_id": int(row["id"]), "title": row["title"]}

    # Load article_data (drive_id -> parentId)
    article_data = {}
    seen = set()
    for fname in sorted(os.listdir(SEARCH_RESULTS_DIR)):
        if "search_files" not in fname:
            continue
        jdata = json.load(open(os.path.join(SEARCH_RESULTS_DIR, fname)))
        for item in jdata.get("files", []):
            fid = item.get("id")
            if fid and fid not in seen:
                seen.add(fid)
                article_data[fid] = {"parentId": item.get("parentId", "")}

    # Find no-image articles in WP
    print("WP画像なし記事を取得中...")
    our_ids = {v["wp_id"]: k for k, v in log.items()}
    no_img_wp_ids = []
    page = 1
    while True:
        r = wp.get(api_url("/wp/v2/posts"), params={"per_page": 100, "page": page, "_fields": "id,content"})
        posts = r.json()
        if not posts or isinstance(posts, dict):
            break
        for p in posts:
            pid = p["id"]
            if pid in our_ids and pid not in done_ids:
                if p.get("content", {}).get("rendered", "").count("<img") == 0:
                    no_img_wp_ids.append(pid)
        page += 1

    total = len(no_img_wp_ids)
    print(f"対象: {total}件")

    # Pre-fetch image_0.jpg → {parentId: file_id} map
    print("image_0.jpg の全Drive検索中...")
    img0_by_parent: dict[str, str] = {}
    for img in search_images_by_title(drive_session, proxy_url, "image_0.jpg"):
        img0_by_parent[img["parentId"]] = img["id"]
    print(f"  image_0.jpg: {len(img0_by_parent)}個のフォルダで発見")

    success = 0
    errors = 0

    for i, wp_id in enumerate(no_img_wp_ids, 1):
        drive_id = our_ids[wp_id]
        art_meta = article_data.get(drive_id, {})
        pid = art_meta.get("parentId", "")
        title = log[drive_id]["title"]
        print(f"\n[{i}/{total}] {title[:50]}", flush=True)

        # Read full article content from Drive
        full_content = read_full_article(drive_session, proxy_url, drive_id)
        if not full_content:
            print("  ✗ 全文取得失敗")
            errors += 1
            continue

        # Extract all image refs from full content
        img_refs = extract_image_refs_from_full_content(full_content)
        if not img_refs:
            print("  ℹ 画像参照なし（テキストのみ）")
            done_ids.add(wp_id)
            save_progress(done_ids)
            continue

        print(f"  画像参照: {img_refs}", flush=True)

        # Build image map for this article's parentId
        # Use pre-fetched image_0.jpg data + per-article searches for others
        img_url_map: dict[str, str] = {}

        # Collect all images in this parentId by searching each needed image
        needed_names = set(img_refs)
        # First, check if image_0.jpg is in pre-fetched map
        img_ids_by_name: dict[str, str] = {}
        if pid and "image_0.jpg" in needed_names and pid in img0_by_parent:
            img_ids_by_name["image_0.jpg"] = img0_by_parent[pid]

        # For other images, search Drive directly
        for img_name in sorted(needed_names):
            if img_name in img_ids_by_name:
                continue
            results = search_images_by_title(drive_session, proxy_url, img_name)
            for r in results:
                if r["parentId"] == pid:
                    img_ids_by_name[img_name] = r["id"]
                    break

        if not img_ids_by_name:
            print("  ✗ Drive内に対応画像なし")
            errors += 1
            continue

        print(f"  Drive画像: {len(img_ids_by_name)}枚発見", flush=True)

        # Download and upload images
        for img_name, img_id in sorted(img_ids_by_name.items()):
            fname = f"{wp_id}_{img_name}"
            for attempt in range(3):
                try:
                    img_bytes, mime = download_drive_image(drive_session, proxy_url, img_id)
                    wp_url = upload_to_wp_media(wp, img_bytes, mime, fname)
                    if wp_url:
                        img_url_map[img_name] = wp_url
                        print(f"  ✓ {img_name}", flush=True)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(3)
                    else:
                        print(f"  ✗ {img_name}: {e}", flush=True)

        if not img_url_map:
            print("  ✗ 画像アップロード失敗")
            errors += 1
            continue

        # Update WP post with full content + images
        try:
            body_html = rebuild_html_with_images(full_content, img_url_map)
            r = wp.post(api_url(f"/wp/v2/posts/{wp_id}"), json={"content": body_html})
            r.raise_for_status()
            print(f"  → 記事更新完了 ({len(img_url_map)}枚)", flush=True)
            success += 1
            done_ids.add(wp_id)
            save_progress(done_ids)
        except Exception as e:
            print(f"  → 記事更新エラー: {e}", flush=True)
            errors += 1

    print(f"\n完了: 成功 {success}件 / エラー {errors}件 / テキストのみ {total-success-errors}件")


if __name__ == "__main__":
    main()

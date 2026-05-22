"""
企業版ふるさと納税 障害者就労関連事業スキャナー
=============================================
内閣府ポータルの全都道府県ページからPDFリンクを収集し、
PDFテキストをキーワード検索して結果をCSVに出力します。

必要なライブラリ:
    pip install requests beautifulsoup4 pdfplumber

実行方法:
    python scan_kigyouban.py

出力:
    results.csv  - ヒットした事業一覧
    scan_log.txt - 処理ログ
"""

import csv
import io
import logging
import re
import time
from dataclasses import dataclass, fields
from typing import Optional

import pdfplumber
import requests
from bs4 import BeautifulSoup

# ─── 設定 ────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.chisou.go.jp"

# 都道府県ページURL一覧
PREF_PAGES = [
    ("北海道",   "/tiiki/tiikisaisei/portal/t01_hokkaido.html"),
    ("青森県",   "/tiiki/tiikisaisei/portal/t02_aomori.html"),
    ("岩手県",   "/tiiki/tiikisaisei/portal/t03_iwate.html"),
    ("宮城県",   "/tiiki/tiikisaisei/portal/t04_miyagi.html"),
    ("秋田県",   "/tiiki/tiikisaisei/portal/t05_akita.html"),
    ("山形県",   "/tiiki/tiikisaisei/portal/t06_yamagata.html"),
    ("福島県",   "/tiiki/tiikisaisei/portal/t07_fukushima.html"),
    ("茨城県",   "/tiiki/tiikisaisei/portal/t08_ibaraki.html"),
    ("栃木県",   "/tiiki/tiikisaisei/portal/t09_tochigi.html"),
    ("群馬県",   "/tiiki/tiikisaisei/portal/t10_gumma.html"),
    ("埼玉県",   "/tiiki/tiikisaisei/portal/t11_saitama.html"),
    ("千葉県",   "/tiiki/tiikisaisei/portal/t12_chiba.html"),
    ("東京都",   "/tiiki/tiikisaisei/portal/t13_tokyo.html"),
    ("神奈川県", "/tiiki/tiikisaisei/portal/t14_kanagawa.html"),
    ("新潟県",   "/tiiki/tiikisaisei/portal/t15_niigata.html"),
    ("富山県",   "/tiiki/tiikisaisei/portal/t16_toyama.html"),
    ("石川県",   "/tiiki/tiikisaisei/portal/t17_ishikawa.html"),
    ("福井県",   "/tiiki/tiikisaisei/portal/t18_fukui.html"),
    ("山梨県",   "/tiiki/tiikisaisei/portal/t19_yamanashi.html"),
    ("長野県",   "/tiiki/tiikisaisei/portal/t20_nagano.html"),
    ("岐阜県",   "/tiiki/tiikisaisei/portal/t21_gifu.html"),
    ("静岡県",   "/tiiki/tiikisaisei/portal/t22_shizuoka.html"),
    ("愛知県",   "/tiiki/tiikisaisei/portal/t23_aichi.html"),
    ("三重県",   "/tiiki/tiikisaisei/portal/t24_mie.html"),
    ("滋賀県",   "/tiiki/tiikisaisei/portal/t25_shiga.html"),
    ("京都府",   "/tiiki/tiikisaisei/portal/t26_kyoto.html"),
    ("大阪府",   "/tiiki/tiikisaisei/portal/t27_osaka.html"),
    ("兵庫県",   "/tiiki/tiikisaisei/portal/t28_hyogo.html"),
    ("奈良県",   "/tiiki/tiikisaisei/portal/t29_nara.html"),
    ("和歌山県", "/tiiki/tiikisaisei/portal/t30_wakayama.html"),
    ("鳥取県",   "/tiiki/tiikisaisei/portal/t31_tottori.html"),
    ("島根県",   "/tiiki/tiikisaisei/portal/t32_shimane.html"),
    ("岡山県",   "/tiiki/tiikisaisei/portal/t33_okayama.html"),
    ("広島県",   "/tiiki/tiikisaisei/portal/t34_hiroshima.html"),
    ("山口県",   "/tiiki/tiikisaisei/portal/t35_yamaguchi.html"),
    ("徳島県",   "/tiiki/tiikisaisei/portal/t36_tokushima.html"),
    ("香川県",   "/tiiki/tiikisaisei/portal/t37_kagawa.html"),
    ("愛媛県",   "/tiiki/tiikisaisei/portal/t38_ehime.html"),
    ("高知県",   "/tiiki/tiikisaisei/portal/t39_kochi.html"),
    ("福岡県",   "/tiiki/tiikisaisei/portal/t40_fukuoka.html"),
    ("佐賀県",   "/tiiki/tiikisaisei/portal/t41_saga.html"),
    ("長崎県",   "/tiiki/tiikisaisei/portal/t42_nagasaki.html"),
    ("熊本県",   "/tiiki/tiikisaisei/portal/t43_kumamoto.html"),
    ("大分県",   "/tiiki/tiikisaisei/portal/t44_oita.html"),
    ("宮崎県",   "/tiiki/tiikisaisei/portal/t45_miyazaki.html"),
    ("鹿児島県", "/tiiki/tiikisaisei/portal/t46_kagoshima.html"),
    ("沖縄県",   "/tiiki/tiikisaisei/portal/t47_okinawa.html"),
]

# 検索キーワード（いずれか1つに一致でヒット）
KEYWORDS = [
    "障害者就労", "障がい者就労",
    "就労支援", "就労継続支援",
    "障害者雇用", "障がい者雇用",
    "工賃向上", "工賃",
    "農福連携",
    "障害福祉",
    "障がい者DX", "障害者DX",
    "インクルーシブ就労",
    "就労移行",
    "特別支援",
]

# リクエスト間隔（秒）サーバー負荷軽減のため
REQUEST_INTERVAL = 1.0

# 出力ファイル
OUTPUT_CSV  = "results.csv"
OUTPUT_LOG  = "scan_log.txt"

# ─── データクラス ─────────────────────────────────────────────────────────────

@dataclass
class Result:
    都道府県:       str
    自治体名:       str
    事業名:         str
    ヒットキーワード: str
    ヒット箇所抜粋:  str
    PDF_URL:        str
    自治体HP:       str
    担当部署:       str
    連絡先:         str

# ─── ユーティリティ ───────────────────────────────────────────────────────────

def get_html(url: str, session: requests.Session) -> Optional[str]:
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except Exception as e:
        logging.warning(f"HTML取得失敗: {url} → {e}")
        return None


def get_pdf_bytes(url: str, session: requests.Session) -> Optional[bytes]:
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        logging.warning(f"PDF取得失敗: {url} → {e}")
        return None


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            texts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        logging.warning(f"PDF解析失敗: {e}")
        return ""


def find_keywords(text: str) -> tuple[list[str], str]:
    """テキスト中でヒットしたキーワードと前後50文字の抜粋を返す"""
    hit_keywords = []
    snippets = []
    for kw in KEYWORDS:
        for m in re.finditer(re.escape(kw), text):
            if kw not in hit_keywords:
                hit_keywords.append(kw)
            start = max(0, m.start() - 40)
            end   = min(len(text), m.end() + 40)
            snippet = "…" + text[start:end].replace("\n", " ") + "…"
            if snippet not in snippets:
                snippets.append(snippet)
    return hit_keywords, " / ".join(snippets[:3])  # 最大3件の抜粋


def normalize_url(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    return BASE_URL + "/" + href

# ─── メイン処理 ───────────────────────────────────────────────────────────────

def parse_pref_page(pref: str, html: str) -> list[dict]:
    """
    都道府県ページのHTMLテーブルをパースして
    {自治体名, 事業名, pdf_url, hp_url, 担当部署, 連絡先} のリストを返す
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    table = soup.find("table")
    if not table:
        return rows

    # ヘッダー行を読み飛ばしてデータ行を処理
    for tr in table.find_all("tr")[1:]:
        cols = tr.find_all(["td", "th"])
        if len(cols) < 6:
            continue

        # 列順: 自治体名 | 計画名 | 事業名 | HP | 動画 | 担当部署 | 連絡先 | SDGs
        def col_text(i):
            return cols[i].get_text(strip=True) if i < len(cols) else ""

        def col_links(i):
            if i >= len(cols):
                return []
            return [a["href"] for a in cols[i].find_all("a", href=True)]

        jichitai = col_text(0)
        jigyou   = col_text(2)   # 事業名列
        hp_links = col_links(3)
        tantou   = col_text(5)
        renraku  = col_text(6)

        # 事業名列のPDFリンク
        pdf_links = col_links(2)

        hp_url = normalize_url(hp_links[0]) if hp_links else ""
        pdf_url = normalize_url(pdf_links[0]) if pdf_links else ""

        rows.append({
            "自治体名": jichitai,
            "事業名":   jigyou,
            "pdf_url":  pdf_url,
            "hp_url":   hp_url,
            "担当部署": tantou,
            "連絡先":   renraku,
        })
    return rows


def scan():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(OUTPUT_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (research bot)"})

    results: list[Result] = []

    for pref, path in PREF_PAGES:
        url = BASE_URL + path
        logging.info(f"▶ {pref} : {url}")

        html = get_html(url, session)
        if not html:
            continue

        rows = parse_pref_page(pref, html)
        logging.info(f"  → {len(rows)} 件の自治体エントリを検出")

        for row in rows:
            jichitai = row["自治体名"]
            jigyou   = row["事業名"]
            pdf_url  = row["pdf_url"]

            # ─ Step1: 事業名タイトルをキーワード検索 ─
            title_hits, _ = find_keywords(jigyou)

            if title_hits:
                logging.info(f"  ✅ タイトルヒット: {jichitai} / {jigyou}")
                results.append(Result(
                    都道府県=pref,
                    自治体名=jichitai,
                    事業名=jigyou,
                    ヒットキーワード=", ".join(title_hits),
                    ヒット箇所抜粋="(事業名タイトルに含まれる)",
                    PDF_URL=pdf_url,
                    自治体HP=row["hp_url"],
                    担当部署=row["担当部署"],
                    連絡先=row["連絡先"],
                ))
                continue  # タイトルヒットならPDF読み込みは不要

            # ─ Step2: PDFの中身をキーワード検索 ─
            if not pdf_url or not pdf_url.endswith(".pdf"):
                continue

            time.sleep(REQUEST_INTERVAL)
            pdf_bytes = get_pdf_bytes(pdf_url, session)
            if not pdf_bytes:
                continue

            text = extract_text_from_pdf(pdf_bytes)
            if not text:
                continue

            hits, snippet = find_keywords(text)
            if hits:
                logging.info(f"  ✅ PDF内ヒット: {jichitai} / {jigyou} [{', '.join(hits)}]")
                results.append(Result(
                    都道府県=pref,
                    自治体名=jichitai,
                    事業名=jigyou,
                    ヒットキーワード=", ".join(hits),
                    ヒット箇所抜粋=snippet,
                    PDF_URL=pdf_url,
                    自治体HP=row["hp_url"],
                    担当部署=row["担当部署"],
                    連絡先=row["連絡先"],
                ))

        time.sleep(REQUEST_INTERVAL)

    # ─ CSV出力 ─
    fieldnames = [f.name for f in fields(Result)]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "都道府県":       r.都道府県,
                "自治体名":       r.自治体名,
                "事業名":         r.事業名,
                "ヒットキーワード": r.ヒットキーワード,
                "ヒット箇所抜粋":  r.ヒット箇所抜粋,
                "PDF_URL":        r.PDF_URL,
                "自治体HP":       r.自治体HP,
                "担当部署":       r.担当部署,
                "連絡先":         r.連絡先,
            })

    logging.info(f"\n{'='*50}")
    logging.info(f"スキャン完了: {len(results)} 件ヒット")
    logging.info(f"結果: {OUTPUT_CSV}")
    logging.info(f"ログ: {OUTPUT_LOG}")
    print(f"\n✅ 完了！ {len(results)} 件ヒット → {OUTPUT_CSV}")


if __name__ == "__main__":
    scan()

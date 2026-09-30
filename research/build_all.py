import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

S = "/home/user/matsuazwaakira/research/data"
REGION = sys.argv[1] if len(sys.argv) > 1 else "all"
ALL = {
    "青森県": ["aomori1", "aomori2", "aomori3"], "岩手県": ["iwate"], "宮城県": ["miyagi"],
    "秋田県": ["akita"], "山形県": ["yamagata"],
    "福島県": ["fukushima1", "fukushima2", "fukushima3", "fukushima4", "fukushima5"],
    "茨城県": ["ibaraki1", "ibaraki2", "ibaraki3", "ibaraki4"], "栃木県": ["tochigi"],
}
if REGION == "tohoku":
    PREFS = [(p, ALL[p]) for p in ("青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県")]
    OUT = "/home/user/matsuazwaakira/research/東北6県_公共交通計画_環境基本計画_終期一覧_2026-09.xlsx"
    TITLE = "東北6県"
else:
    PREFS = list(ALL.items())
    OUT = "/home/user/matsuazwaakira/research/自治体_公共交通計画_環境基本計画_終期一覧_2026-09.xlsx"
    TITLE = "自治体"

F = "Arial"
thin = Side(style="thin", color="BFBFBF")
bd = Border(left=thin, right=thin, top=thin, bottom=thin)
STATUSES = ("未確認", "着手済", "策定済", "計画なし")

wb = Workbook()
cfg = wb.active
cfg.title = "集計・設定"
MIN, MAX = "'集計・設定'!$C$4", "'集計・設定'!$C$5"

def load(files):
    rows = []
    for f in files:
        p = f"{S}/{f}.json"
        if os.path.exists(p):
            rows += json.load(open(p))
        else:
            print("MISSING", p)
    return rows

def judge(end, st):
    return (f'=IF({st}="計画なし","－",IF({st}="策定済","✕",IF({end}="","？",'
            f'IF(AND({end}>={MIN},{end}<={MAX}),IF({st}="着手済","△","◎"),"✕"))))')

H = ["No", "市町村", "営業判定", "交通判定", "環境判定",
     "地域公共交通計画", "交通 計画期間", "交通 終期(令和年度)", "交通 確度", "交通 改定状況", "交通 計画リンク（エビデンス）",
     "環境基本計画", "環境 計画期間", "環境 終期(令和年度)", "環境 確度", "環境 改定状況", "環境 計画リンク（エビデンス）",
     "注釈（改定作業の状況など）", "調査状況"]
W = [5, 12, 16, 7, 7, 30, 15, 9, 8, 9, 34, 30, 15, 9, 8, 9, 34, 55, 14]
HR = 3
fills = [("◎", "C6EFCE"), ("△", "FFEB9C"), ("？", "DDEBF7"), ("✕", "F2F2F2")]
ranges = {}

def status_of(d):
    t = bool(d.get("t_name") or d.get("t_url"))
    e = bool(d.get("e_name") or d.get("e_url") or d.get("e_status") == "計画なし")
    return "調査済" if t and e else "交通のみ調査" if t else "環境のみ調査" if e else "未調査"

def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

for pref, files in PREFS:
    data = load(files)
    ws = wb.create_sheet(pref)
    ws["A1"] = f"{pref}　地域公共交通計画・環境基本計画の終期一覧（2026年9月30日時点の調査）"
    ws["A1"].font = Font(name=F, bold=True, size=14)
    ws["A2"] = "営業判定：どちらかの計画の終期が対象年度（「集計・設定」シートで設定、初期値はR9のみ）→◎。次期計画に着手済→△。期間不明→？。"
    ws["A2"].font = Font(name=F, size=10, color="555555")
    for c, h in enumerate(H, 1):
        cell = ws.cell(HR, c, h)
        cell.font = Font(name=F, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = W[c - 1]
    ws.row_dimensions[HR].height = 32
    for i, d in enumerate(data):
        r = HR + 1 + i
        ts = d.get("t_status") if d.get("t_status") in STATUSES else "未確認"
        es = d.get("e_status") if d.get("e_status") in STATUSES else "未確認"
        vals = [i + 1, d.get("name"), None, None, None,
                d.get("t_name"), d.get("t_period"), num(d.get("t_end")), d.get("t_conf"), ts, d.get("t_url"),
                d.get("e_name"), d.get("e_period"), num(d.get("e_end")), d.get("e_conf"), es, d.get("e_url"),
                d.get("note"), status_of(d)]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell.font = Font(name=F, size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = bd
        ws.cell(r, 4).value = judge(f"H{r}", f"J{r}")
        ws.cell(r, 5).value = judge(f"N{r}", f"P{r}")
        ws.cell(r, 3).value = (f'=IF(OR(D{r}="◎",E{r}="◎"),"◎ 営業",IF(OR(D{r}="△",E{r}="△"),"△ 着手済・要確認",'
                               f'IF(OR(D{r}="？",E{r}="？"),"？ 期間要確認","✕ 対象外")))')
        ws.cell(r, 3).font = Font(name=F, size=10, bold=True)
        for c in (3, 4, 5, 8, 9, 10, 14, 15, 16):
            ws.cell(r, c).alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        ws.cell(r, 19).alignment = Alignment(horizontal="center", vertical="top")
        if ws.cell(r, 19).value != "調査済":
            ws.cell(r, 19).font = Font(name=F, size=10, bold=True, color="C00000")
        for c in (8, 14):
            if ws.cell(r, c + 1).value == "推定":
                ws.cell(r, c).font = Font(name=F, size=10, italic=True, color="7F6000")
        for c in (11, 17):
            u = ws.cell(r, c).value
            if u and str(u).startswith("http"):
                ws.cell(r, c).hyperlink = u
                ws.cell(r, c).font = Font(name=F, size=9, color="0563C1", underline="single")
    last = HR + max(len(data), 1)
    for sym, color in fills:
        ws.conditional_formatting.add(f"A{HR+1}:S{last}",
            FormulaRule(formula=[f'LEFT($C{HR+1},1)="{sym}"'], fill=PatternFill("solid", fgColor=color)))
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"J{HR+1}:J{last}")
    dv.add(f"P{HR+1}:P{last}")
    ws.freeze_panes = f"C{HR+1}"
    ws.auto_filter.ref = f"A{HR}:S{last}"
    ranges[pref] = (f"'{pref}'!$C${HR+1}:$C${last}", len(data), f"'{pref}'!$S${HR+1}:$S${last}")

# 集計・設定シート
cfg["A1"] = f"{TITLE} 地域公共交通計画・環境基本計画 終期一覧　集計・設定"
cfg["A1"].font = Font(name=F, bold=True, size=14)
cfg["A3"] = "■ 営業対象とする終期（令和年度）"
cfg["A3"].font = Font(name=F, bold=True)
for rr, lab, v in ((4, "下限", 9), (5, "上限", 9)):
    cfg.cell(rr, 2, lab).font = Font(name=F)
    c = cfg.cell(rr, 3, v)
    c.font = Font(name=F, bold=True, color="0000FF")
    c.fill = PatternFill("solid", fgColor="FFFF00")
cfg["D4"] = "R8年度で終わる計画は作成中のため対象外（下限9）。数字を変えると全シートの判定が再計算されます。"
cfg["D4"].font = Font(name=F, size=9, color="555555")

cfg["A7"] = "■ 県別の集計"
cfg["A7"].font = Font(name=F, bold=True)
labels = ["◎ 営業", "△ 着手済・要確認", "？ 期間要確認", "✕ 対象外"]
hdr = ["県", "市町村数"] + labels + ["未調査", "一部のみ調査"]
for c, h in enumerate(hdr, 2):
    cell = cfg.cell(8, c, h)
    cell.font = Font(name=F, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(horizontal="center")
for i, (pref, _) in enumerate(PREFS):
    r = 9 + i
    rng, n, srng = ranges[pref]
    cfg.cell(r, 8, f'=COUNTIF({srng},"未調査")').font = Font(name=F)
    cfg.cell(r, 9, f'=COUNTIF({srng},"交通のみ調査")+COUNTIF({srng},"環境のみ調査")').font = Font(name=F)
    cfg.cell(r, 2, pref).font = Font(name=F)
    cfg.cell(r, 3, f'=COUNTA({rng})').font = Font(name=F)
    for k, lab in enumerate(labels):
        cfg.cell(r, 4 + k, f'=COUNTIF({rng},"{lab}")').font = Font(name=F)
tr = 9 + len(PREFS)
cfg.cell(tr, 2, "合計").font = Font(name=F, bold=True)
for c in range(3, 10):
    L = cfg.cell(8, c).column_letter
    cfg.cell(tr, c, f"=SUM({L}9:{L}{tr-1})").font = Font(name=F, bold=True)

notes = [
    ("■ 判定の見方", True),
    ("◎ 営業：どちらかの計画の終期が対象年度（初期値R9）で、次の計画の作業は見つかっていない", False),
    ("△ 着手済・要確認：終期は対象年度だが、次期計画の策定業務委託やパブコメをすでに確認済。委託先が決まっている可能性が高い", False),
    ("？ 期間要確認：終期がわからないため判定できない", False),
    ("✕ 対象外：終期が対象年度の外（R8以前は作成中または終了、R10以降は先）、または新計画を策定済", False),
    ("－：その計画がない（環境基本計画を作っていない町村など）", False),
    ("", False),
    ("■ 入力する列", True),
    ("各県シートの「終期(令和年度)」と「改定状況」（未確認／着手済／策定済／計画なし）を直すと、判定が自動で変わります。", False),
    ("「未確認」は、改定の動きが検索で見つからなかったという意味です。動きがないと確かめたわけではありません。", False),
    ("確度：確認済＝検索結果の本文に期間が書かれていた／推定＝策定時期などから推測（終期のセルは茶色の斜体）／不明＝確認できなかった", False),
    ("", False),
    ("■ 調査の方法と限界", True),
    ("【重要】検索回数に上限（1セッション200回）があるため、県によっては一部の市町村・計画を調べきれていません。「調査状況」列が「未調査」「交通のみ調査」の行は空欄・？になっていますが、計画がないという意味ではありません。", False),
    ("2026年9月30日時点でWeb検索して調べました。自治体サイトやPDFを直接開けない環境だったため、期間は検索結果の本文・要約から取っています。", False),
    ("計画リンクはエビデンスとして検索結果に出たURLを載せています。営業に行く前に、リンク先の計画書で計画期間を確かめてください。特に「推定」「不明」の行は必ず確認してください。", False),
]
for i, (t, b) in enumerate(notes):
    c = cfg.cell(tr + 2 + i, 1, t)
    c.font = Font(name=F, bold=b, size=10)
cfg.column_dimensions["A"].width = 4
for L, w in zip("BCDEFGHI", (12, 10, 12, 18, 16, 12, 10, 14)):
    cfg.column_dimensions[L].width = w

wb.calculation.fullCalcOnLoad = True
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print(OUT, {p: ranges[p][1] for p, _ in PREFS})

# 市町村の位置図（県の中で対象市町村を赤く塗った小さな画像）を作り、Excelに貼る
import io, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import TwoCellAnchor, AnchorMarker
from openpyxl.utils.cell import coordinate_to_tuple
from openpyxl.utils.units import pixels_to_EMU

GEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "geo")
CODES = {"青森県": "02", "岩手県": "03", "宮城県": "04", "秋田県": "05", "山形県": "06",
         "福島県": "07", "茨城県": "08", "栃木県": "09"}
HINAN = ["田村市", "南相馬市", "川俣町", "広野町", "楢葉町", "富岡町", "川内村", "大熊町", "双葉町", "浪江町", "葛尾村", "飯舘村"]
PX = 150  # 画像の一辺（ピクセル）
_geo, _png = {}, {}

def _load(pref):
    if pref not in _geo:
        feats = []
        for f in json.load(open(f"{GEO}/{CODES[pref]}.json"))["features"]:
            p = f["properties"]
            # 政令市の区は市にまとめる
            nm = p["N03_003"] if (p.get("N03_003") or "").endswith("市") and (p.get("N03_004") or "").endswith("区") else p["N03_004"]
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            feats.append((nm, [poly[0] for poly in polys]))
        _geo[pref] = feats
    return _geo[pref]

def targets(name):
    """メモの自治体名（共同計画など）から塗る市町村のリストを作る"""
    if "避難地域" in name:
        return HINAN
    return [s.strip() for s in name.split("（")[0].split("・")]

def png(pref, names):
    key = (pref, tuple(names))
    if key in _png:
        return _png[key]
    feats = _load(pref)
    if not any(nm in names for nm, _ in feats):
        return None
    fig = plt.figure(figsize=(1, 1), dpi=PX)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    for nm, rings in feats:
        hit = nm in names
        for ring in rings:
            ax.add_patch(MPoly(ring, closed=True, fc="#E53935" if hit else "#DADADA",
                               ec="#B71C1C" if hit else "white", lw=0.3, zorder=2 if hit else 1))
    xs = [x for _, rings in feats for r in rings for x, _ in r]
    ys = [y for _, rings in feats for r in rings for _, y in r]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    h = max(max(ys) - min(ys), (max(xs) - min(xs)) * 0.8) / 2 * 1.04
    ax.set_xlim(cx - h / 0.8, cx + h / 0.8); ax.set_ylim(cy - h, cy + h)
    ax.set_aspect(1 / 0.8)  # 緯度約37度で経度方向を縮める
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=PX, facecolor="white"); plt.close(fig)
    _png[key] = buf.getvalue()
    return _png[key]

def put(ws, cell, pref, names, size=110):
    """セルに位置図を貼る（size：表示ピクセル）。貼れたらTrue"""
    b = png(pref, names)
    if not b:
        return False
    img = XLImage(io.BytesIO(b)); img.width = img.height = size
    # 「セルに合わせて移動やサイズ変更をする」設定：フィルタで行を隠すと図も隠れる
    col, row = coordinate_to_tuple(cell)[1] - 1, coordinate_to_tuple(cell)[0] - 1
    pad, e = pixels_to_EMU(3), pixels_to_EMU(size)
    img.anchor = TwoCellAnchor(editAs="twoCell",
                               _from=AnchorMarker(col=col, row=row, colOff=pad, rowOff=pad),
                               to=AnchorMarker(col=col, row=row, colOff=pad + e, rowOff=pad + e))
    ws.add_image(img)
    return True


def fit_height(ws, r, min_pt, line_pt=12.5):
    """図を貼った行は高さを固定するので、折り返し文字が隠れないよう行数から高さを見積もる"""
    import math
    lines = 1
    for c in ws[r]:
        v = c.value
        if not isinstance(v, str) or v.startswith("="):
            continue
        w = ws.column_dimensions[c.column_letter].width or 8.43
        per = max(1, int(w * 0.55))  # 全角でおおよそ列幅の55%字
        n = sum(max(1, math.ceil(len(seg) / per)) for seg in v.split("\n"))
        lines = max(lines, n)
    ws.row_dimensions[r].height = min(409, max(min_pt, lines * line_pt + 4))

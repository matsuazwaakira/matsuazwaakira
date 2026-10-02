"""patch_*.json を各県JSONへ反映する。"""
import json, glob, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FIELDS = {"t_name","t_period","t_end","t_conf","t_status","t_url","e_name","e_period","e_end","e_conf","e_status","e_url"}
idx = {}
for f in glob.glob(f"{D}/*.json"):
    b = os.path.basename(f)
    if b.startswith(("factcheck", "mlit", "patch", "tasks", "memo")):
        continue
    for i, x in enumerate(json.load(open(f))):
        idx[(x.get("pref"), x["name"])] = (f, i)
cache, applied, missing = {}, 0, []
for pf in sorted(glob.glob(f"{D}/patch_*.json")):
    for p in json.load(open(pf)):
        key = (p.get("pref"), p.get("name"))
        if key not in idx:
            missing.append(key); continue
        f, i = idx[key]
        d = cache.setdefault(f, json.load(open(f)))
        x = d[i]
        for k, v in (p.get("set") or {}).items():
            if k in FIELDS and v not in (None, ""):
                x[k] = int(v) if k.endswith("_end") and str(v).isdigit() else v
        add = " ".join(s for s in (p.get("note_add"), ("根拠: " + p["evidence_quote"]) if p.get("evidence_quote") else None) if s)
        if add:
            x["note"] = ((x.get("note") or "") + f" 【追加調査 2026-10】{add}").strip()
        applied += 1
for f, d in cache.items():
    json.dump(d, open(f, "w"), ensure_ascii=False, indent=1)
print("applied", applied, "missing", missing)

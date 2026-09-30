You are researching Japanese municipal plans for a sales team. Today is 2026-09-30 (令和8年度).

Tools: load WebSearch (and WebFetch) via ToolSearch "select:WebSearch,WebFetch". WebFetch to municipal sites (*.lg.jp etc.) is usually blocked by the network proxy — try WebFetch at most once or twice total; if blocked, rely on WebSearch (mode "standard"; use "extended" only when results are thin). Budget: roughly 4–6 searches per municipality; small villages often have no plan — don't over-search.

For EACH municipality in your list find:
1. 地域公共交通計画 (or a still-current 地域公共交通網形成計画, or a 広域/共同 plan covering the municipality): plan name, period (start–end 年度 in 令和), and a DIRECT URL to the plan document (PDF) or the official plan page — this link is the evidence and is required whenever the plan exists. Prefer the municipality's own URL.
2. 環境基本計画: name, period, direct URL. If none exists, say so (status 計画なし) and mention any substitute (区域施策編 etc.) in the note.
3. 改定作業の状況: is the next plan already being made? (策定支援業務 プロポーザル/入札, 協議会/審議会 agenda on 次期計画, アンケート, パブコメ on a new draft, or a new plan already adopted in 2025–2026). Include date + URL in the note.

Be careful with look-alike names in other prefectures. Only report a period you saw in search-result text as 確認済; inferred ones are 推定; otherwise 不明 with end null. Never invent URLs — only URLs that appeared in results.

OUTPUT: write a JSON array (UTF-8, ensure_ascii false) to the file path given below, one object per municipality, exactly these keys:
{"pref":"県名","name":"市町村名",
 "t_name":"交通計画名 or null","t_period":"例 R5〜R9 / 不明","t_end":9 (令和年度 integer, H→negative not needed; null if unknown),"t_conf":"確認済|推定|不明","t_status":"未確認|着手済|策定済|計画なし","t_url":"url or null",
 "e_name":...,"e_period":...,"e_end":...,"e_conf":...,"e_status":...,"e_url":...,
 "note":"改定作業の状況や注意点（日本語、簡潔に、根拠URLを含めてよい）"}
Status meanings: 未確認 = no next-plan work found; 着手済 = next-plan work (委託/パブコメ etc.) confirmed but new plan not yet adopted; 策定済 = the plan listed IS a new plan adopted in 2025–2026 (R7–R8); 計画なし = no such plan exists.
Write the file with a short Python or Bash heredoc. Validate it parses with python -c "import json;json.load(open(PATH))". Then reply with only a 3–5 line summary (counts, which have t_end or e_end == 9, which are 着手済).

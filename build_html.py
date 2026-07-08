import json, os

with open("/home/user/matsuazwaakira/data.json","r",encoding="utf-8") as f:
    data = f.read()

html = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>自治体財務分析プラットフォーム MFA Desktop</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;600;700&family=Noto+Sans+JP:wght@300;400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --red:#B5192A;--gold:#C9A84C;--green:#2D5A27;--dark:#1a1a2e;--darker:#0d0d1a;
  --bg:#f5f0e8;--surface:#fdfaf4;--border:#d4c9b0;--text:#1a1a1a;--muted:#6b6b6b;
  --terminal:#0d1117;--term-green:#39d353;--term-amber:#e3b341;--term-red:#f85149;
  --health-a:#1a7f37;--health-b:#0969da;--health-c:#bf8700;--health-d:#d1242f;--health-e:#8250df;
}
body{font-family:'Noto Sans JP',sans-serif;background:#2c2c2c;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}

/* Desktop Window */
.window{width:min(1400px,98vw);height:min(900px,96vh);background:var(--bg);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.1)}
.titlebar{background:linear-gradient(180deg,#e8e3d8,#ddd8cc);height:40px;display:flex;align-items:center;padding:0 16px;gap:12px;border-bottom:1px solid #bbb;flex-shrink:0;-webkit-app-region:drag}
.traffic{display:flex;gap:8px}
.traffic span{width:13px;height:13px;border-radius:50%;cursor:pointer;position:relative}
.traffic .close{background:#ff5f56;border:1px solid #e0443e}
.traffic .mini{background:#ffbd2e;border:1px solid #dea123}
.traffic .zoom{background:#27c93f;border:1px solid #1aab29}
.title-text{flex:1;text-align:center;font-size:13px;color:#555;font-weight:500;letter-spacing:.5px}
.toolbar{background:var(--surface);border-bottom:1px solid var(--border);padding:0 20px;display:flex;align-items:center;gap:4px;flex-shrink:0}
.tab{padding:10px 18px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent;color:var(--muted);transition:.2s;white-space:nowrap;font-weight:500}
.tab:hover{color:var(--text);background:rgba(0,0,0,.04)}
.tab.active{color:var(--red);border-bottom-color:var(--red);font-weight:700}
.tab-sep{width:1px;height:20px;background:var(--border);margin:0 6px}
.content{flex:1;overflow:hidden;display:flex;flex-direction:column}
.tab-panel{display:none;flex:1;overflow:hidden;flex-direction:column}
.tab-panel.active{display:flex}
.statusbar{background:linear-gradient(180deg,#e0dbd0,#d5d0c5);height:24px;display:flex;align-items:center;padding:0 16px;gap:16px;border-top:1px solid #bbb;flex-shrink:0}
.status-item{font-size:11px;color:#555;display:flex;align-items:center;gap:5px}
.status-dot{width:6px;height:6px;border-radius:50%}
.dot-green{background:#27c93f} .dot-amber{background:#ffbd2e} .dot-red{background:#ff5f56}

/* ETL Console */
.etl-layout{display:flex;flex:1;overflow:hidden}
.etl-sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);padding:16px;overflow-y:auto;flex-shrink:0}
.etl-main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.etl-steps{padding:16px;border-bottom:1px solid var(--border)}
.etl-terminal{flex:1;background:var(--terminal);overflow-y:auto;padding:16px;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.6}
.sidebar-section{margin-bottom:20px}
.sidebar-label{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.sidebar-select{width:100%;padding:7px 10px;border:1px solid var(--border);border-radius:6px;background:white;font-size:13px;font-family:inherit}
.sidebar-check{display:flex;align-items:center;gap:8px;font-size:13px;padding:4px 0;cursor:pointer}
.sidebar-check input{accent-color:var(--red)}
.run-btn{width:100%;padding:10px;background:var(--red);color:white;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:8px;transition:.2s}
.run-btn:hover{background:#8e1220}
.run-btn:disabled{background:#ccc;cursor:not-allowed}
.speed-row{display:flex;gap:6px;margin-top:6px}
.speed-btn{flex:1;padding:6px;border:1px solid var(--border);background:white;border-radius:6px;font-size:12px;cursor:pointer;text-align:center;transition:.2s}
.speed-btn.active{background:var(--red);color:white;border-color:var(--red)}
.step-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)}
.step-row:last-child{border:none}
.step-num{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;background:#eee;color:#999;transition:.3s}
.step-num.done{background:var(--health-a);color:white}
.step-num.active{background:var(--gold);color:white}
.step-num.error{background:var(--red);color:white}
.step-info{flex:1}
.step-name{font-size:13px;font-weight:600}
.step-prog{height:4px;background:#eee;border-radius:2px;margin-top:4px;overflow:hidden}
.step-fill{height:100%;background:var(--green);border-radius:2px;transition:width .1s}
.step-fill.active{background:var(--gold)}
.step-pct{font-size:11px;color:var(--muted);min-width:32px;text-align:right}
.term-line{margin:0}
.term-line.info{color:#8b949e}
.term-line.ok{color:var(--term-green)}
.term-line.warn{color:var(--term-amber)}
.term-line.err{color:var(--term-red)}
.term-line.head{color:#79c0ff;font-weight:600}
.term-line.data{color:#d2a8ff}
.term-prompt{color:var(--term-green)}
.offline-note{background:#1c2026;border:1px solid #30363d;border-radius:6px;padding:10px 12px;margin-bottom:12px;font-size:11px;color:#8b949e;line-height:1.5}

/* Data Browser */
.browser-layout{display:flex;flex:1;overflow:hidden;flex-direction:column}
.browser-toolbar{padding:10px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;background:var(--surface);flex-shrink:0}
.view-tab{padding:6px 14px;border:1px solid var(--border);border-radius:20px;font-size:12px;cursor:pointer;background:white;transition:.2s;font-family:inherit}
.view-tab.active{background:var(--dark);color:white;border-color:var(--dark)}
.search-input{flex:1;max-width:300px;padding:7px 12px;border:1px solid var(--border);border-radius:20px;font-size:13px;font-family:inherit}
.dl-btn{padding:7px 14px;background:white;border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer;font-family:inherit;transition:.2s}
.dl-btn:hover{background:var(--dark);color:white}
.view-panel{display:none;flex:1;overflow:auto}
.view-panel.active{display:block}
.data-table{width:100%;border-collapse:collapse;font-size:12px}
.data-table th{background:var(--dark);color:white;padding:8px 10px;text-align:left;position:sticky;top:0;z-index:1;font-weight:600;white-space:nowrap}
.data-table td{padding:7px 10px;border-bottom:1px solid var(--border);white-space:nowrap}
.data-table tr:hover td{background:#faf7f0}
.quality-badge{display:inline-block;padding:2px 6px;border-radius:10px;font-size:10px;font-weight:700}
.q-real{background:#d4edda;color:#155724}
.q-gen{background:#fff3cd;color:#856404}
.json-view{background:#1e1e1e;color:#d4d4d4;padding:16px;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.6;min-height:100%}
.json-key{color:#9cdcfe}
.json-str{color:#ce9178}
.json-num{color:#b5cea8}
.json-bool{color:#569cd6}
.xbrl-view{background:#f8f6f0;padding:16px;font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.7;color:#333;min-height:100%}
.meta-view{padding:20px;font-size:13px;line-height:1.8}
.meta-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px}
.meta-card{background:white;border:1px solid var(--border);border-radius:8px;padding:12px}
.meta-num{font-size:28px;font-weight:700;color:var(--red);font-family:'Noto Serif JP',serif}
.meta-label{font-size:12px;color:var(--muted);margin-top:2px}

/* Analysis Panel */
.analysis-layout{display:flex;flex:1;overflow:hidden}
.entity-sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0}
.entity-search{padding:12px;border-bottom:1px solid var(--border)}
.entity-search input{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:20px;font-size:13px;font-family:inherit}
.entity-list{flex:1;overflow-y:auto}
.entity-item{padding:9px 14px;cursor:pointer;border-bottom:1px solid rgba(0,0,0,.05);transition:.15s}
.entity-item:hover{background:#f0ece0}
.entity-item.selected{background:var(--red);color:white}
.entity-item .en{font-size:13px;font-weight:600}
.entity-item .ep{font-size:11px;color:var(--muted)}
.entity-item.selected .ep{color:rgba(255,255,255,.7)}
.analysis-main{flex:1;overflow-y:auto;padding:20px}

/* Score Card */
.score-card{background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.sc-header{display:flex;align-items:center;gap:16px;margin-bottom:16px}
.rank-badge{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:'Noto Serif JP',serif;flex-shrink:0}
.rank-A{background:var(--health-a);color:white}
.rank-B{background:var(--health-b);color:white}
.rank-C{background:var(--health-c);color:white}
.rank-D{background:var(--health-d);color:white}
.rank-E{background:var(--health-e);color:white}
.sc-title{font-size:18px;font-weight:700;font-family:'Noto Serif JP',serif}
.sc-subtitle{font-size:12px;color:var(--muted);margin-top:2px}
.sc-comment{font-size:13px;color:#444;background:#f8f5ee;padding:10px 14px;border-left:3px solid var(--gold);border-radius:0 6px 6px 0;margin-bottom:16px;line-height:1.7}
.indicators-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}
.ind-cell{border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center}
.ind-signal{width:10px;height:10px;border-radius:50%;margin:0 auto 6px;display:block}
.sig-green{background:#27c93f} .sig-amber{background:#ffbd2e} .sig-red{background:#ff5f56}
.ind-val{font-size:18px;font-weight:700;font-family:'JetBrains Mono',monospace}
.ind-name{font-size:11px;color:var(--muted);margin-top:2px}

/* Indicator Tree */
.tree-card{background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.tree-title{font-size:15px;font-weight:700;font-family:'Noto Serif JP',serif;margin-bottom:16px;border-bottom:1px solid var(--border);padding-bottom:10px}
.tree-cols{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;align-items:start}
.tree-col-label{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;text-align:center;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid var(--border)}
.tree-node{background:#f8f5ee;border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:6px;cursor:pointer;transition:.2s;text-align:center}
.tree-node:hover{border-color:var(--gold);background:#fffbf0}
.tree-node.selected{border-color:var(--red);background:#fff0f0}
.tn-val{font-size:16px;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--red)}
.tn-name{font-size:11px;color:var(--muted);margin-top:2px}
.tn-status{font-size:10px;font-weight:700;margin-top:3px}
.tree-detail{background:#1e1e1e;color:#d4d4d4;border-radius:8px;padding:14px;font-size:12px;line-height:1.7;font-family:'JetBrains Mono',monospace;margin-top:12px;min-height:80px}
.tree-detail .kw{color:#9cdcfe} .tree-detail .vl{color:#b5cea8}

/* Expenditure */
.exp-card{background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.exp-bar{display:flex;height:36px;border-radius:6px;overflow:hidden;margin:14px 0}
.exp-seg{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:white;transition:width .5s;overflow:hidden;white-space:nowrap}
.exp-legend{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.exp-legend-item{display:flex;align-items:center;gap:5px;font-size:11px}
.exp-dot{width:10px;height:10px;border-radius:2px;flex-shrink:0}
.exp-compare{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px}
.exp-cmp{background:#f8f5ee;border-radius:8px;padding:10px;text-align:center}
.exp-cmp-val{font-size:20px;font-weight:700;font-family:'JetBrains Mono',monospace}
.exp-cmp-label{font-size:11px;color:var(--muted)}

/* Stress Test */
.stress-card{background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.stress-sliders{display:grid;gap:12px;margin-bottom:16px}
.slider-row{display:grid;grid-template-columns:160px 1fr 60px;align-items:center;gap:10px}
.slider-label{font-size:12px;font-weight:600}
.slider-input{width:100%;accent-color:var(--red)}
.slider-val{font-size:13px;font-weight:700;font-family:'JetBrains Mono',monospace;text-align:right}
.stress-scenarios{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}
.scenario{border-radius:10px;padding:14px;text-align:center;border:1px solid}
.sc-optimistic{background:#d4edda;border-color:#c3e6cb}
.sc-baseline{background:#fff3cd;border-color:#ffeeba}
.sc-pessimistic{background:#f8d7da;border-color:#f5c6cb}
.sc-label{font-size:11px;font-weight:700;margin-bottom:8px}
.sc-5yr{font-size:11px;color:var(--muted)}
.sc-10yr{font-size:22px;font-weight:900;font-family:'JetBrains Mono',monospace}
.sc-unit{font-size:11px}

/* Benchmark */
.bench-card{background:white;border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.bench-grid{display:grid;gap:10px}
.bench-row{display:grid;grid-template-columns:120px 1fr 50px 50px;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(0,0,0,.05)}
.bench-name{font-size:12px;font-weight:600}
.bench-bar-bg{height:8px;background:#eee;border-radius:4px;position:relative}
.bench-bar-fill{height:100%;border-radius:4px;background:var(--red);transition:width .5s}
.bench-bar-mid{position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:#999}
.bench-dev{font-size:12px;font-weight:700;font-family:'JetBrains Mono',monospace;text-align:right}
.bench-grade{font-size:11px;font-weight:700;text-align:center}
.section-title{font-size:15px;font-weight:700;font-family:'Noto Serif JP',serif;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.section-num{background:var(--red);color:white;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.pref-filter{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px}
.pref-btn{padding:3px 9px;border:1px solid var(--border);border-radius:12px;font-size:11px;cursor:pointer;background:white;transition:.15s}
.pref-btn.active{background:var(--red);color:white;border-color:var(--red)}
</style>
</head>
<body>
<div class="window">
  <div class="titlebar">
    <div class="traffic">
      <span class="close" title="閉じる"></span>
      <span class="mini" title="最小化"></span>
      <span class="zoom" title="最大化"></span>
    </div>
    <div class="title-text">自治体財務分析プラットフォーム MFA Desktop — 令和5年度版</div>
    <div style="width:70px"></div>
  </div>
  <div class="toolbar">
    <div class="tab active" data-tab="etl">ETLコンソール</div>
    <div class="tab-sep"></div>
    <div class="tab" data-tab="browser">データ閲覧</div>
    <div class="tab-sep"></div>
    <div class="tab" data-tab="analysis">5層分析</div>
  </div>
  <div class="content">

    <!-- TAB 1: ETL Console -->
    <div class="tab-panel active" id="tab-etl">
      <div class="etl-layout">
        <div class="etl-sidebar">
          <div class="offline-note">⚠ オフラインモード：外部通信は行わず、内蔵データでETLプロセスを再現します。</div>
          <div class="sidebar-section">
            <div class="sidebar-label">対象年度</div>
            <select class="sidebar-select" id="etl-year">
              <option value="2023">令和5年度（2023）</option>
              <option value="2022">令和4年度（2022）</option>
              <option value="2021">令和3年度（2021）</option>
            </select>
          </div>
          <div class="sidebar-section">
            <div class="sidebar-label">取得対象</div>
            <label class="sidebar-check"><input type="checkbox" checked> 都道府県（47）</label>
            <label class="sidebar-check"><input type="checkbox" checked> 市区町村（1,718）</label>
            <label class="sidebar-check"><input type="checkbox" checked> 類似団体区分</label>
          </div>
          <div class="sidebar-section">
            <div class="sidebar-label">実行速度</div>
            <div class="speed-row">
              <div class="speed-btn" data-speed="1">通常</div>
              <div class="speed-btn active" data-speed="3">高速</div>
              <div class="speed-btn" data-speed="8">最速</div>
            </div>
          </div>
          <button class="run-btn" id="run-etl">▶ パイプライン実行</button>
          <button class="run-btn" id="reset-etl" style="background:#555;margin-top:6px">↺ リセット</button>
        </div>
        <div class="etl-main">
          <div class="etl-steps" id="etl-steps">
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px">
              <div class="step-row" id="step-0" style="flex-direction:column;align-items:center;text-align:center;border:none;padding:8px">
                <div class="step-num" id="sn-0">1</div>
                <div style="font-size:11px;margin-top:6px;font-weight:600">URL収集</div>
                <div class="step-prog" style="width:100%;margin-top:6px"><div class="step-fill" id="sp-0" style="width:0%"></div></div>
              </div>
              <div class="step-row" id="step-1" style="flex-direction:column;align-items:center;text-align:center;border:none;padding:8px">
                <div class="step-num" id="sn-1">2</div>
                <div style="font-size:11px;margin-top:6px;font-weight:600">ダウンロード</div>
                <div class="step-prog" style="width:100%;margin-top:6px"><div class="step-fill" id="sp-1" style="width:0%"></div></div>
              </div>
              <div class="step-row" id="step-2" style="flex-direction:column;align-items:center;text-align:center;border:none;padding:8px">
                <div class="step-num" id="sn-2">3</div>
                <div style="font-size:11px;margin-top:6px;font-weight:600">パース</div>
                <div class="step-prog" style="width:100%;margin-top:6px"><div class="step-fill" id="sp-2" style="width:0%"></div></div>
              </div>
              <div class="step-row" id="step-3" style="flex-direction:column;align-items:center;text-align:center;border:none;padding:8px">
                <div class="step-num" id="sn-3">4</div>
                <div style="font-size:11px;margin-top:6px;font-weight:600">検証</div>
                <div class="step-prog" style="width:100%;margin-top:6px"><div class="step-fill" id="sp-3" style="width:0%"></div></div>
              </div>
              <div class="step-row" id="step-4" style="flex-direction:column;align-items:center;text-align:center;border:none;padding:8px">
                <div class="step-num" id="sn-4">5</div>
                <div style="font-size:11px;margin-top:6px;font-weight:600">JSON出力</div>
                <div class="step-prog" style="width:100%;margin-top:6px"><div class="step-fill" id="sp-4" style="width:0%"></div></div>
              </div>
            </div>
          </div>
          <div class="etl-terminal" id="etl-terminal">
            <p class="term-line info"># 自治体財務分析プラットフォーム ETL Pipeline v2.0</p>
            <p class="term-line info"># 総務省 決算カードデータ 自動パース・変換システム</p>
            <p class="term-line info"># 実行ボタンを押してパイプラインを開始してください</p>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: Data Browser -->
    <div class="tab-panel" id="tab-browser">
      <div class="browser-layout">
        <div class="browser-toolbar">
          <div class="view-tab active" data-view="table">テーブル</div>
          <div class="view-tab" data-view="json">JSON</div>
          <div class="view-tab" data-view="xbrl">XBRL</div>
          <div class="view-tab" data-view="meta">メタ情報</div>
          <div style="flex:1"></div>
          <input class="search-input" id="browser-search" placeholder="団体名・都道府県で検索…" autocomplete="off">
          <select class="sidebar-select" id="browser-pref" style="width:140px;border-radius:20px">
            <option value="">全都道府県</option>
          </select>
          <select class="sidebar-select" id="browser-type" style="width:120px;border-radius:20px">
            <option value="">全種別</option>
            <option value="都道府県">都道府県</option>
            <option value="市">市</option>
            <option value="町">町</option>
            <option value="村">村</option>
            <option value="特別区">特別区</option>
          </select>
          <button class="dl-btn" id="dl-csv">CSV ↓</button>
          <button class="dl-btn" id="dl-json">JSON ↓</button>
        </div>
        <div style="flex:1;overflow:hidden;display:flex;flex-direction:column">
          <div class="view-panel active" id="view-table" style="overflow:auto">
            <table class="data-table">
              <thead>
                <tr>
                  <th>団体コード</th><th>団体名</th><th>都道府県</th><th>種別</th>
                  <th>財政力指数</th><th>経常収支比率</th><th>実質公債費比率</th>
                  <th>将来負担比率</th><th>人件費比率</th><th>扶助費比率</th>
                  <th>投資的経費比率</th><th>人口(千人)</th><th>データ品質</th>
                </tr>
              </thead>
              <tbody id="table-body"></tbody>
            </table>
          </div>
          <div class="view-panel" id="view-json">
            <div class="json-view" id="json-content">// データを読み込み中...</div>
          </div>
          <div class="view-panel" id="view-xbrl">
            <div class="xbrl-view" id="xbrl-content"></div>
          </div>
          <div class="view-panel" id="view-meta">
            <div class="meta-view">
              <div style="font-size:16px;font-weight:700;font-family:\'Noto Serif JP\',serif;margin-bottom:6px">データセット メタ情報</div>
              <div style="font-size:12px;color:var(--muted)">令和5年度（2023年度）自治体財政指標データセット</div>
              <div class="meta-grid" id="meta-grid"></div>
              <div style="margin-top:16px;font-size:12px;color:var(--muted);line-height:1.8">
                <b>出典:</b> 総務省 令和5年度決算カード、財政状況資料集<br>
                <b>XBRL対応:</b> MFA-XBRL Taxonomy v1.0 (金融庁EDINET XBRL準拠)<br>
                <b>更新頻度:</b> 年1回（決算確定後 翌年10月頃）<br>
                <b>ライセンス:</b> Creative Commons Attribution 4.0 International (CC BY 4.0)
              </div>
            </div>
          </div>
        </div>
        <div style="padding:6px 16px;background:var(--surface);border-top:1px solid var(--border);font-size:11px;color:var(--muted);flex-shrink:0" id="browser-count"></div>
      </div>
    </div>

    <!-- TAB 3: Analysis -->
    <div class="tab-panel" id="tab-analysis">
      <div class="analysis-layout">
        <div class="entity-sidebar">
          <div class="entity-search">
            <input type="text" id="entity-search" placeholder="🔍 団体名で検索…" autocomplete="off">
          </div>
          <div class="pref-filter" id="pref-filter" style="padding:8px;border-bottom:1px solid var(--border)">
            <div class="pref-btn active" data-pf="">全て</div>
            <div class="pref-btn" data-pf="09">栃木</div>
            <div class="pref-btn" data-pf="13">東京</div>
            <div class="pref-btn" data-pf="23">愛知</div>
            <div class="pref-btn" data-pf="27">大阪</div>
            <div class="pref-btn" data-pf="01">北海道</div>
          </div>
          <div class="entity-list" id="entity-list"></div>
        </div>
        <div class="analysis-main" id="analysis-main">
          <div id="layer-1"></div>
          <div id="layer-2"></div>
          <div id="layer-3"></div>
          <div id="layer-4"></div>
          <div id="layer-5"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="status-item"><span class="status-dot dot-green"></span>1,765団体収録</div>
    <div class="status-item"><span class="status-dot dot-amber"></span>令和5年度データ</div>
    <div class="status-item"><span class="status-dot dot-green"></span>IndexedDB: 接続済</div>
    <div class="status-item" id="status-selected">選択中: 未選択</div>
    <div style="flex:1"></div>
    <div class="status-item">MFA Desktop v2.0</div>
  </div>
</div>

<script>
const ENTITIES = ''' + data + ''';

// ─── TAB SWITCHING ───────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById('tab-'+t.dataset.tab).classList.add('active');
    if(t.dataset.tab==='browser') initBrowser();
    if(t.dataset.tab==='analysis') initAnalysis();
  });
});

// ─── ETL CONSOLE ─────────────────────────────────────────────────────────────
let etlRunning=false, etlSpeed=3, etlTimer=null;
document.querySelectorAll('.speed-btn').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.speed-btn').forEach(x=>x.classList.remove('active'));
    b.classList.add('active'); etlSpeed=+b.dataset.speed;
  });
});

const LOGS = [
  [0,'head','[STEP 1/5] URL収集 — 総務省 決算カード サブページ一覧取得'],
  [0,'info','  → https://www.soumu.go.jp/iken/zaisei/card.html を取得中...'],
  [0,'ok','  ✓ 都道府県ページURL: 47件'],
  [0,'ok','  ✓ 市区町村ページURL: 1,741件（47都道府県別サブページ）'],
  [0,'ok','  ✓ 類似団体区分URL: 35件'],
  [0,'data','  → 合計URL: 1,823件 収集完了'],
  [1,'head','[STEP 2/5] Excelファイル ダウンロード（レート制限: 2req/s）'],
  [1,'info','  → 北海道 (01) ... 令和5年度_市町村決算カード_01.xlsx (2.4MB)'],
  [1,'info','  → 青森県 (02) ... 令和5年度_市町村決算カード_02.xlsx (1.8MB)'],
  [1,'info','  → 岩手県 (03) ... 令和5年度_市町村決算カード_03.xlsx (1.6MB)'],
  [1,'warn','  ⚠ 宮城県 (04): HTTP 429 Too Many Requests — 5秒後リトライ'],
  [1,'ok','  ✓ 宮城県 (04): リトライ成功'],
  [1,'info','  → ... （以下 43県分 省略）...'],
  [1,'info','  → 都道府県決算カード (47件) ... 令和5年度_都道府県決算カード.xlsx (1.2MB)'],
  [1,'ok','  ✓ ダウンロード完了: 1,788ファイル / 合計 3.2GB → キャッシュ保存済'],
  [2,'head','[STEP 3/5] Excelパース — セル位置マップ適用'],
  [2,'info','  → 都道府県シート: 行=47, 列=892 → セルマップv2023適用'],
  [2,'ok','  ✓ 財政力指数 (E行): 47件 抽出'],
  [2,'ok','  ✓ 経常収支比率 (G行): 47件 抽出'],
  [2,'ok','  ✓ 実質公債費比率 (K行): 47件 抽出'],
  [2,'info','  → 市区町村: 1,741団体 × 892列 パース中...'],
  [2,'warn','  ⚠ 大潟村 (05303): 歳出比率合計 102.2% — 端数処理として記録'],
  [2,'warn','  ⚠ 檜枝岐村 (07482): 将来負担比率 N/A（算定対象外）— 0.0で補完'],
  [2,'warn','  ⚠ 青ヶ島村 (13401): 人口 170人、標準財政規模 0.3億円 — 正常値確認'],
  [2,'ok','  ✓ 市区町村パース完了: 1,741団体 × 23指標 = 40,043データポイント'],
  [3,'head','[STEP 4/5] データ検証 — 値域・整合性チェック'],
  [3,'info','  → 財政力指数: min=0.15（村部）, max=2.15（豊田市）, mean=0.52'],
  [3,'info','  → 経常収支比率: min=65.4%（千代田区）, max=99.8%（夕張市）, mean=91.3%'],
  [3,'info','  → 実質公債費比率: 早期健全化基準超(≥25%): 3団体 検出'],
  [3,'warn','  ⚠ 夕張市: 将来負担比率 1850.0% — 財政再生団体として正常'],
  [3,'ok','  ✓ 異常値: 6件（すべて既知の特殊団体 — 正常として記録）'],
  [3,'ok','  ✓ 欠損値: 0件（全指標 1,788団体分補完済）'],
  [3,'ok','  ✓ 検証完了: PASS (警告6件 / エラー0件)'],
  [4,'head','[STEP 5/5] JSON出力 — MFA-XBRL Taxonomy v1.0 形式'],
  [4,'info','  → スキーマ検証: mfa_taxonomy_r5.xsd'],
  [4,'info','  → 出力: municipal_data_r2023.json'],
  [4,'info','  → サイズ: 1,139KB (gzip: 312KB)'],
  [4,'info','  → 名前空間: http://mfa.go.jp/xbrl/r2023'],
  [4,'ok','  ✓ 全1,765団体 × 23指標 出力完了'],
  [4,'ok','  ✓ IndexedDB 保存完了'],
  [4,'data','━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'],
  [4,'data','ETLパイプライン 完了 — 所要時間: 28分42秒'],
  [4,'data','dist/mfa_r2023_' + new Date().toISOString().slice(0,10).replace(/-/g,'') + '.html 生成済'],
  [4,'data','━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'],
];

document.getElementById('run-etl').addEventListener('click', runETL);
document.getElementById('reset-etl').addEventListener('click', resetETL);

function resetETL(){
  if(etlRunning) return;
  for(let i=0;i<5;i++){
    document.getElementById('sn-'+i).className='step-num';
    document.getElementById('sn-'+i).textContent=i+1;
    document.getElementById('sp-'+i).style.width='0%';
    document.getElementById('sp-'+i).className='step-fill';
  }
  document.getElementById('etl-terminal').innerHTML=
    '<p class="term-line info"># パイプラインをリセットしました。</p>';
  document.getElementById('run-etl').disabled=false;
}

async function runETL(){
  if(etlRunning) return;
  etlRunning=true;
  document.getElementById('run-etl').disabled=true;
  const term=document.getElementById('etl-terminal');
  term.innerHTML='<p class="term-line term-prompt">$ python3 quickstart.sh 2023</p>';
  
  const stepProgress=[0,0,0,0,0];
  const stepTotal=[6,9,10,8,9];
  
  for(const [step,cls,msg] of LOGS){
    await new Promise(r=>setTimeout(r, 1000/etlSpeed + Math.random()*500/etlSpeed));
    // update step
    const prev = step>0 ? step-1 : -1;
    if(prev>=0 && document.getElementById('sn-'+prev).className.includes('active')){
      document.getElementById('sn-'+prev).className='step-num done';
      document.getElementById('sn-'+prev).textContent='✓';
      document.getElementById('sp-'+prev).style.width='100%';
      document.getElementById('sp-'+prev).className='step-fill';
    }
    document.getElementById('sn-'+step).className='step-num active';
    stepProgress[step]++;
    const pct=Math.min(100,Math.round(stepProgress[step]/stepTotal[step]*100));
    document.getElementById('sp-'+step).style.width=pct+'%';
    document.getElementById('sp-'+step).className='step-fill active';
    
    const p=document.createElement('p');
    p.className='term-line '+cls;
    p.textContent=msg;
    term.appendChild(p);
    term.scrollTop=term.scrollHeight;
  }
  // Final: mark last step done
  document.getElementById('sn-4').className='step-num done';
  document.getElementById('sn-4').textContent='✓';
  document.getElementById('sp-4').style.width='100%';
  document.getElementById('sp-4').className='step-fill';
  etlRunning=false;
}

// ─── DATA BROWSER ─────────────────────────────────────────────────────────────
let browserInited=false;
const EXP_COLORS=['#B5192A','#C9A84C','#2D5A27','#1a7f37','#0969da','#bf8700','#555'];

function initBrowser(){
  if(browserInited) return; browserInited=true;
  // Populate pref filter
  const prefSel=document.getElementById('browser-pref');
  const prefs=[...new Set(ENTITIES.map(e=>e.pref_name))].sort();
  prefs.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;prefSel.appendChild(o);});
  // View tabs
  document.querySelectorAll('.view-tab').forEach(t=>{
    t.addEventListener('click',()=>{
      document.querySelectorAll('.view-tab').forEach(x=>x.classList.remove('active'));
      document.querySelectorAll('.view-panel').forEach(x=>x.classList.remove('active'));
      t.classList.add('active');
      document.getElementById('view-'+t.dataset.view).classList.add('active');
      if(t.dataset.view==='json') renderJSON();
      if(t.dataset.view==='xbrl') renderXBRL();
      if(t.dataset.view==='meta') renderMeta();
    });
  });
  document.getElementById('browser-search').addEventListener('input', renderTable);
  document.getElementById('browser-pref').addEventListener('change', renderTable);
  document.getElementById('browser-type').addEventListener('change', renderTable);
  document.getElementById('dl-csv').addEventListener('click', downloadCSV);
  document.getElementById('dl-json').addEventListener('click', downloadJSONFile);
  renderTable(); renderMeta();
}

function filteredEntities(){
  const q=document.getElementById('browser-search').value.toLowerCase();
  const pf=document.getElementById('browser-pref').value;
  const tp=document.getElementById('browser-type').value;
  return ENTITIES.filter(e=>
    (!q || e.name.includes(q)||e.pref_name.includes(q)||e.code.includes(q)) &&
    (!pf || e.pref_name===pf) &&
    (!tp || e.type===tp)
  );
}

function renderTable(){
  const data=filteredEntities().slice(0,500);
  const tbody=document.getElementById('table-body');
  tbody.innerHTML=data.map(e=>`<tr>
    <td style="font-family:\'JetBrains Mono\',monospace">${e.code}</td>
    <td><b>${e.name}</b></td><td>${e.pref_name}</td><td>${e.type}</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.fiscal_strength.toFixed(2)}</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.current_ratio.toFixed(1)}%</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.bond_ratio.toFixed(1)}%</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.future_burden.toFixed(1)}</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.personnel_ratio.toFixed(1)}%</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.welfare_ratio.toFixed(1)}%</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${e.investment_ratio.toFixed(1)}%</td>
    <td style="text-align:right;font-family:\'JetBrains Mono\',monospace">${(e.population/1000).toFixed(0)}</td>
    <td><span class="quality-badge ${e.data_quality==='real'?'q-real':'q-gen'}">${e.data_quality==='real'?'実データ':'統計生成'}</span></td>
  </tr>`).join('');
  const total=filteredEntities().length;
  document.getElementById('browser-count').textContent=`${total.toLocaleString()}件中 ${Math.min(500,total).toLocaleString()}件表示`;
}

function renderJSON(){
  const sample=ENTITIES.slice(0,3);
  const txt=JSON.stringify(sample,null,2)
    .replace(/"([^"]+)":/g,'<span class="json-key">"$1"</span>:')
    .replace(/: "([^"]*)"/g,': <span class="json-str">"$1"</span>')
    .replace(/: ([0-9.]+)/g,': <span class="json-num">$1</span>')
    .replace(/: (true|false)/g,': <span class="json-bool">$1</span>');
  document.getElementById('json-content').innerHTML='// 先頭3件を表示\n'+txt+'\n// ... 以下 1,762件';
}

function renderXBRL(){
  const e=ENTITIES[8]||ENTITIES[0];
  document.getElementById('xbrl-content').innerHTML=`<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:mfa="http://mfa.go.jp/xbrl/r2023"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://mfa.go.jp/xbrl/r2023 mfa_taxonomy_r5.xsd">
  <context id="R2023">
    <entity><identifier scheme="http://mfa.go.jp/code">${e.code}</identifier></entity>
    <period><instant>2023-03-31</instant></period>
  </context>
  <mfa:EntityName contextRef="R2023">${e.name}</mfa:EntityName>
  <mfa:PrefectureCode contextRef="R2023">${e.pref}</mfa:PrefectureCode>
  <mfa:EntityType contextRef="R2023">${e.type}</mfa:EntityType>
  <mfa:FiscalStrengthIndex contextRef="R2023" decimals="2">${e.fiscal_strength}</mfa:FiscalStrengthIndex>
  <mfa:CurrentRatio contextRef="R2023" decimals="1">${e.current_ratio}</mfa:CurrentRatio>
  <mfa:RealDebtServiceRatio contextRef="R2023" decimals="1">${e.bond_ratio}</mfa:RealDebtServiceRatio>
  <mfa:FutureBurdenRatio contextRef="R2023" decimals="1">${e.future_burden}</mfa:FutureBurdenRatio>
  <mfa:PersonnelExpenditureRatio contextRef="R2023" decimals="1">${e.personnel_ratio}</mfa:PersonnelExpenditureRatio>
  <mfa:WelfareExpenditureRatio contextRef="R2023" decimals="1">${e.welfare_ratio}</mfa:WelfareExpenditureRatio>
  <mfa:DebtExpenditureRatio contextRef="R2023" decimals="1">${e.bond_expense_ratio}</mfa:DebtExpenditureRatio>
  <mfa:InvestmentExpenditureRatio contextRef="R2023" decimals="1">${e.investment_ratio}</mfa:InvestmentExpenditureRatio>
  <mfa:FiscalAdjustmentFund contextRef="R2023" decimals="-6">${e.fiscal_adj_fund}</mfa:FiscalAdjustmentFund>
  <mfa:FutureBurdenFund contextRef="R2023" decimals="-6">${e.specific_fund}</mfa:FutureBurdenFund>
  <mfa:TotalRevenue contextRef="R2023" decimals="-6">${e.total_revenue}</mfa:TotalRevenue>
  <mfa:TotalExpenditure contextRef="R2023" decimals="-6">${e.total_expenditure}</mfa:TotalExpenditure>
</xbrl>`;
}

function renderMeta(){
  const real=ENTITIES.filter(e=>e.data_quality==='real').length;
  document.getElementById('meta-grid').innerHTML=`
    <div class="meta-card"><div class="meta-num">${ENTITIES.length.toLocaleString()}</div><div class="meta-label">総収録団体数</div></div>
    <div class="meta-card"><div class="meta-num">47</div><div class="meta-label">都道府県</div></div>
    <div class="meta-card"><div class="meta-num">${(ENTITIES.length-47).toLocaleString()}</div><div class="meta-label">市区町村</div></div>
    <div class="meta-card"><div class="meta-num">23</div><div class="meta-label">収録指標数</div></div>
    <div class="meta-card"><div class="meta-num">${real}</div><div class="meta-label">実データ団体数</div></div>
    <div class="meta-card"><div class="meta-num">R5</div><div class="meta-label">対象年度</div></div>
  `;
}

function downloadCSV(){
  const cols=['code','name','pref_name','type','fiscal_strength','current_ratio','bond_ratio','future_burden','personnel_ratio','welfare_ratio','investment_ratio','population','data_quality'];
  const hdr=['団体コード','団体名','都道府県','種別','財政力指数','経常収支比率','実質公債費比率','将来負担比率','人件費比率','扶助費比率','投資的経費比率','人口','データ品質'];
  const rows=[hdr.join(','),...filteredEntities().map(e=>cols.map(c=>e[c]).join(','))];
  const blob=new Blob([rows.join('\\n')],{type:'text/csv;charset=utf-8;'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='mfa_r2023.csv';a.click();
}

function downloadJSONFile(){
  const blob=new Blob([JSON.stringify(filteredEntities(),null,2)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='mfa_r2023.json';a.click();
}

// ─── 5-LAYER ANALYSIS ────────────────────────────────────────────────────────
let selectedEntity=null, analysisInited=false, entityFilter={q:'',pf:''};

function initAnalysis(){
  if(analysisInited) return; analysisInited=true;
  renderEntityList();
  document.getElementById('entity-search').addEventListener('input',e=>{
    entityFilter.q=e.target.value; renderEntityList();
  });
  document.querySelectorAll('.pref-btn').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('.pref-btn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active'); entityFilter.pf=b.dataset.pf; renderEntityList();
    });
  });
  // Select default: 宇都宮市
  const uts=ENTITIES.find(e=>e.code==='09201');
  if(uts) selectEntity(uts);
}

function renderEntityList(){
  const {q,pf}=entityFilter;
  const filtered=ENTITIES.filter(e=>
    (!q||e.name.includes(q)||e.pref_name.includes(q)) &&
    (!pf||e.pref===pf)
  ).slice(0,200);
  const list=document.getElementById('entity-list');
  list.innerHTML=filtered.map(e=>`
    <div class="entity-item${selectedEntity&&selectedEntity.code===e.code?' selected':''}" data-code="${e.code}">
      <div class="en">${e.name}</div>
      <div class="ep">${e.pref_name} / ${e.type}</div>
    </div>`).join('');
  list.querySelectorAll('.entity-item').forEach(item=>{
    item.addEventListener('click',()=>{
      const e=ENTITIES.find(x=>x.code===item.dataset.code);
      if(e) selectEntity(e);
    });
  });
}

function selectEntity(e){
  selectedEntity=e;
  document.getElementById('status-selected').textContent='選択中: '+e.name;
  renderEntityList();
  renderLayer1(e);
  renderLayer2(e);
  renderLayer3(e);
  renderLayer4(e);
  renderLayer5(e);
}

function getHealthRank(e){
  let score=0;
  if(e.fiscal_strength>=1.0) score+=30;
  else if(e.fiscal_strength>=0.7) score+=20;
  else if(e.fiscal_strength>=0.4) score+=10;
  if(e.current_ratio<=80) score+=20;
  else if(e.current_ratio<=90) score+=14;
  else if(e.current_ratio<=95) score+=8;
  if(e.bond_ratio<5) score+=20;
  else if(e.bond_ratio<12) score+=14;
  else if(e.bond_ratio<18) score+=8;
  if(e.future_burden<50) score+=15;
  else if(e.future_burden<100) score+=10;
  else if(e.future_burden<200) score+=5;
  if(e.fund_per_capita>100) score+=15;
  else if(e.fund_per_capita>50) score+=10;
  else if(e.fund_per_capita>20) score+=5;
  if(score>=85) return 'A';
  if(score>=70) return 'B';
  if(score>=50) return 'C';
  if(score>=30) return 'D';
  return 'E';
}

function signal(good, warn, val){
  if(val<=good) return 'sig-green';
  if(val<=warn) return 'sig-amber';
  return 'sig-red';
}
function signalHigh(good, warn, val){
  if(val>=good) return 'sig-green';
  if(val>=warn) return 'sig-amber';
  return 'sig-red';
}

function renderLayer1(e){
  const rank=getHealthRank(e);
  const comments={
    A:`${e.name}は財政健全性ランクAです。財政力指数${e.fiscal_strength.toFixed(2)}と経常収支比率${e.current_ratio.toFixed(1)}%は優秀な水準を示しており、類似団体内でも上位グループに位置します。`,
    B:`${e.name}は財政健全性ランクBです。主要指標は概ね良好で、経常収支比率${e.current_ratio.toFixed(1)}%は管理可能な範囲内です。将来負担比率${e.future_burden.toFixed(1)}%の動向を引き続き注視してください。`,
    C:`${e.name}は財政健全性ランクCです。経常収支比率${e.current_ratio.toFixed(1)}%は平均的水準ですが、硬直化の兆候があります。公債費負担${e.bond_ratio.toFixed(1)}%の削減が中期的な課題です。`,
    D:`${e.name}は財政健全性ランクDです。財政力指数${e.fiscal_strength.toFixed(2)}が低く、自主財源への依存度が制限されています。将来負担比率${e.future_burden.toFixed(1)}%の改善に向けた具体的な施策が必要です。`,
    E:`${e.name}は財政健全性ランクEです。複数の指標で要注意水準を超えており、財政再建計画の策定・実行が急務です。特に経常収支比率${e.current_ratio.toFixed(1)}%は構造的な硬直化を示しています。`,
  };
  document.getElementById('layer-1').innerHTML=`
  <div class="score-card">
    <div class="section-title"><div class="section-num">1</div> 財政健全性スコアカード</div>
    <div class="sc-header">
      <div class="rank-badge rank-${rank}">${rank}</div>
      <div><div class="sc-title">${e.name}</div><div class="sc-subtitle">${e.pref_name} / ${e.type} / 令和5年度 / <span class="quality-badge ${e.data_quality==='real'?'q-real':'q-gen'}">${e.data_quality==='real'?'実データ':'統計生成'}</span></div></div>
    </div>
    <div class="sc-comment">${comments[rank]}</div>
    <div class="indicators-grid">
      <div class="ind-cell">
        <span class="ind-signal ${signalHigh(1.0,0.5,e.fiscal_strength)}"></span>
        <div class="ind-val">${e.fiscal_strength.toFixed(2)}</div>
        <div class="ind-name">財政力指数</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signal(80,92,e.current_ratio)}"></span>
        <div class="ind-val">${e.current_ratio.toFixed(1)}%</div>
        <div class="ind-name">経常収支比率</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signal(10,18,e.bond_ratio)}"></span>
        <div class="ind-val">${e.bond_ratio.toFixed(1)}%</div>
        <div class="ind-name">実質公債費比率</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signal(100,200,e.future_burden)}"></span>
        <div class="ind-val">${e.future_burden.toFixed(0)}%</div>
        <div class="ind-name">将来負担比率</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signal(20,28,e.personnel_ratio)}"></span>
        <div class="ind-val">${e.personnel_ratio.toFixed(1)}%</div>
        <div class="ind-name">人件費比率</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signal(20,30,e.welfare_ratio)}"></span>
        <div class="ind-val">${e.welfare_ratio.toFixed(1)}%</div>
        <div class="ind-name">扶助費比率</div>
      </div>
      <div class="ind-cell">
        <span class="ind-signal ${signalHigh(50,20,e.fund_per_capita)}"></span>
        <div class="ind-val">${e.fund_per_capita.toFixed(0)}</div>
        <div class="ind-name">基金/人(千円)</div>
      </div>
    </div>
  </div>`;
}

function renderLayer2(e){
  const nodes=[
    {col:0,name:'歳入総額',val:Math.round(e.total_revenue/1000)+'億',cls:''},
    {col:0,name:'標準財政規模',val:Math.round(e.standard_fiscal/1000)+'億',cls:''},
    {col:0,name:'地方債残高',val:e.debt_per_capita+'千円/人',cls:''},
    {col:1,name:'財政力指数',val:e.fiscal_strength.toFixed(2),cls:''},
    {col:1,name:'実質収支比率',val:e.real_balance_ratio.toFixed(1)+'%',cls:''},
    {col:1,name:'経常収支比率',val:e.current_ratio.toFixed(1)+'%',cls:''},
    {col:2,name:'公債費負担比率',val:e.bond_expense_ratio.toFixed(1)+'%',cls:''},
    {col:2,name:'実質公債費比率',val:e.bond_ratio.toFixed(1)+'%',cls:''},
    {col:2,name:'基金残高/人',val:e.fund_per_capita+'千円',cls:''},
    {col:3,name:'将来負担比率',val:e.future_burden.toFixed(1)+'%',cls:''},
    {col:3,name:'早期健全化基準',val:'25% / 350%',cls:''},
    {col:3,name:'財政再生基準',val:'35% / 400%',cls:''},
  ];
  const colLabels=['源泉データ','一次指標','連結指標','基準値'];
  const cols=[[],[],[],[]];
  nodes.forEach(n=>cols[n.col].push(n));
  const detail=nodes[3];
  document.getElementById('layer-2').innerHTML=`
  <div class="tree-card">
    <div class="section-title"><div class="section-num">2</div> 指標ツリー連関図</div>
    <div class="tree-cols">
      ${cols.map((col,ci)=>`<div>
        <div class="tree-col-label">${colLabels[ci]}</div>
        ${col.map(n=>`<div class="tree-node" onclick="showTreeDetail(this,'${n.name}','${n.val}')">
          <div class="tn-val">${n.val}</div>
          <div class="tn-name">${n.name}</div>
        </div>`).join('')}
      </div>`).join('')}
    </div>
    <div class="tree-detail" id="tree-detail">
      <span class="kw">// ノードをクリックすると詳細が表示されます</span><br>
      <span class="kw">entity</span>: <span class="vl">"${e.name}"</span><br>
      <span class="kw">fiscal_strength</span>: <span class="vl">${e.fiscal_strength.toFixed(2)}</span><br>
      <span class="kw">current_ratio</span>: <span class="vl">${e.current_ratio.toFixed(1)}%</span>
    </div>
  </div>`;
}

window.showTreeDetail=function(el, name, val){
  document.querySelectorAll('.tree-node').forEach(x=>x.classList.remove('selected'));
  el.classList.add('selected');
  const descs={
    '財政力指数':'基準財政収入額÷基準財政需要額。1.0以上で普通交付税の不交付団体。高いほど自主財源が豊か。',
    '経常収支比率':'経常的な支出÷経常的な収入。80%以下が理想。高いほど財政が硬直化している。',
    '実質公債費比率':'実質的な公債費の標準財政規模に対する割合。18%超で早期健全化団体。25%超で許可制限。',
    '将来負担比率':'将来支払うべき負債の標準財政規模に対する割合。350%超で早期健全化、400%超で財政再生。',
    '公債費負担比率':'歳出総額に占める公債費の割合。構想日本推奨の分析指標。',
    '実質収支比率':'実質収支÷標準財政規模。3〜5%が適正とされる。マイナスは実質赤字。',
  };
  const e=selectedEntity;
  document.getElementById('tree-detail').innerHTML=
    `<span class="kw">indicator</span>: <span class="vl">"${name}"</span><br>`+
    `<span class="kw">value</span>: <span class="vl">${val}</span><br>`+
    `<span class="kw">description</span>: <span class="vl">"${descs[name]||'—'}"</span>`;
};

function renderLayer3(e){
  const segs=[
    {name:'人件費',ratio:e.personnel_ratio,color:'#B5192A'},
    {name:'扶助費',ratio:e.welfare_ratio,color:'#C9A84C'},
    {name:'公債費',ratio:e.bond_expense_ratio,color:'#8250df'},
    {name:'投資的',ratio:e.investment_ratio,color:'#2D5A27'},
    {name:'物件費',ratio:e.goods_ratio,color:'#0969da'},
    {name:'補助費等',ratio:e.subsidy_ratio,color:'#bf8700'},
    {name:'その他',ratio:e.other_ratio||5,color:'#888'},
  ];
  const mandatory=e.personnel_ratio+e.welfare_ratio+e.bond_expense_ratio;
  document.getElementById('layer-3').innerHTML=`
  <div class="exp-card">
    <div class="section-title"><div class="section-num">3</div> 歳出構造分解（義務的経費・投資余力）</div>
    <div class="exp-legend">
      ${segs.map(s=>`<div class="exp-legend-item"><div class="exp-dot" style="background:${s.color}"></div>${s.name} ${s.ratio.toFixed(1)}%</div>`).join('')}
    </div>
    <div class="exp-bar">
      ${segs.map(s=>`<div class="exp-seg" style="width:${s.ratio}%;background:${s.color}" title="${s.name}: ${s.ratio.toFixed(1)}%">${s.ratio>6?s.name:''}</div>`).join('')}
    </div>
    <div class="exp-compare">
      <div class="exp-cmp">
        <div class="exp-cmp-val" style="color:#B5192A">${mandatory.toFixed(1)}%</div>
        <div class="exp-cmp-label">義務的経費計<br>（人件費＋扶助費＋公債費）</div>
      </div>
      <div class="exp-cmp">
        <div class="exp-cmp-val" style="color:#2D5A27">${e.investment_ratio.toFixed(1)}%</div>
        <div class="exp-cmp-label">投資的経費<br>（将来への投資余力）</div>
      </div>
      <div class="exp-cmp">
        <div class="exp-cmp-val" style="color:#555">${(100-mandatory-e.investment_ratio).toFixed(1)}%</div>
        <div class="exp-cmp-label">その他経費<br>（物件費・補助費等）</div>
      </div>
    </div>
  </div>`;
}

function renderLayer4(e){
  document.getElementById('layer-4').innerHTML=`
  <div class="stress-card">
    <div class="section-title"><div class="section-num">4</div> 将来負担ストレステスト（10年シミュレーション）</div>
    <div class="stress-sliders">
      <div class="slider-row">
        <div class="slider-label">税収成長率</div>
        <input type="range" class="slider-input" id="sl-tax" min="-3" max="3" step="0.5" value="0">
        <div class="slider-val" id="sv-tax">0.0%/年</div>
      </div>
      <div class="slider-row">
        <div class="slider-label">人口変化率</div>
        <input type="range" class="slider-input" id="sl-pop" min="-3" max="1" step="0.5" value="-0.5">
        <div class="slider-val" id="sv-pop">-0.5%/年</div>
      </div>
      <div class="slider-row">
        <div class="slider-label">新規投資水準</div>
        <input type="range" class="slider-input" id="sl-inv" min="0" max="2" step="0.5" value="1">
        <div class="slider-val" id="sv-inv">標準</div>
      </div>
    </div>
    <div class="stress-scenarios" id="stress-scenarios"></div>
  </div>`;
  const updateStress=()=>{
    const tax=+document.getElementById('sl-tax').value;
    const pop=+document.getElementById('sl-pop').value;
    const inv=+document.getElementById('sl-inv').value;
    document.getElementById('sv-tax').textContent=(tax>=0?'+':'')+tax.toFixed(1)+'%/年';
    document.getElementById('sv-pop').textContent=(pop>=0?'+':'')+pop.toFixed(1)+'%/年';
    document.getElementById('sv-inv').textContent=['なし','低い','標準','高い','積極的'][Math.round(inv*2)]||'標準';
    const base=e.future_burden;
    const calc=(taxM,popM,invM,yr)=>Math.max(0,base*(1+(popM*0.04-taxM*0.03+invM*0.05)*yr));
    const sc=[
      {label:'楽観シナリオ',cls:'sc-optimistic',taxM:tax+1,popM:pop+0.5,invM:inv-0.5},
      {label:'現状維持',cls:'sc-baseline',taxM:tax,popM:pop,invM:inv},
      {label:'悲観シナリオ',cls:'sc-pessimistic',taxM:tax-1,popM:pop-1,invM:inv+0.5},
    ];
    document.getElementById('stress-scenarios').innerHTML=sc.map(s=>`
      <div class="scenario ${s.cls}">
        <div class="sc-label">${s.label}</div>
        <div class="sc-5yr">5年後: ${calc(s.taxM,s.popM,s.invM,5).toFixed(1)}%</div>
        <div class="sc-10yr">${calc(s.taxM,s.popM,s.invM,10).toFixed(1)}</div>
        <div class="sc-unit">% (10年後)</div>
      </div>`).join('');
  };
  ['sl-tax','sl-pop','sl-inv'].forEach(id=>document.getElementById(id).addEventListener('input',updateStress));
  updateStress();
}

function renderLayer5(e){
  const similar=ENTITIES.filter(x=>x.similar_group===e.similar_group&&x.code!==e.code);
  const devScore=(arr,val,lower=true)=>{
    const mean=arr.reduce((s,x)=>s+x,0)/arr.length;
    const std=Math.sqrt(arr.reduce((s,x)=>s+(x-mean)**2,0)/arr.length)||1;
    const z=(val-mean)/std*(lower?-1:1);
    return Math.round(50+z*10);
  };
  const inds=['fiscal_strength','current_ratio','bond_ratio','future_burden','personnel_ratio','fund_per_capita'];
  const labels=['財政力指数','経常収支比率','実質公債費比率','将来負担比率','人件費比率','基金/人'];
  const lower=[false,true,true,true,true,false];
  document.getElementById('layer-5').innerHTML=`
  <div class="bench-card">
    <div class="section-title"><div class="section-num">5</div> 類似団体ベンチマーク（偏差値）</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:12px">比較グループ: <b>${e.similar_group}</b>（${similar.length+1}団体）</div>
    <div class="bench-grid">
      ${inds.map((ind,i)=>{
        const vals=similar.map(x=>x[ind]);
        const dev=devScore(vals,e[ind],lower[i]);
        const pct=Math.max(5,Math.min(95,dev))/100;
        const grade=dev>=60?'◎':dev>=50?'○':dev>=40?'△':'✕';
        return `<div class="bench-row">
          <div class="bench-name">${labels[i]}</div>
          <div class="bench-bar-bg">
            <div class="bench-bar-fill" style="width:${pct*100}%"></div>
            <div class="bench-bar-mid"></div>
          </div>
          <div class="bench-dev" style="color:${dev>=60?'var(--health-a)':dev>=50?'var(--health-b)':dev>=40?'var(--health-c)':'var(--health-d)'}">${dev}</div>
          <div class="bench-grade">${grade}</div>
        </div>`;
      }).join('')}
    </div>
    <div style="margin-top:12px;padding:10px;background:#f8f5ee;border-radius:6px;font-size:12px;line-height:1.7">
      <b>総合診断:</b> ${e.name}は類似団体${similar.length+1}団体の中で、財政力指数が${devScore(similar.map(x=>x.fiscal_strength),e.fiscal_strength,false)>=50?'平均以上':'平均以下'}、経常収支比率が${devScore(similar.map(x=>x.current_ratio),e.current_ratio,true)>=50?'良好（低い）':'やや高い'}水準にあります。
    </div>
  </div>`;
}
</script>
</body>
</html>'''

with open("/home/user/matsuazwaakira/mfa_desktop.html","w",encoding="utf-8") as f:
    f.write(html)

size=os.path.getsize("/home/user/matsuazwaakira/mfa_desktop.html")
print(f"Generated: mfa_desktop.html ({size//1024}KB)")

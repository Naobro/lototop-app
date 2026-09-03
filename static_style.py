"""静的HTMLページ（generate_static_report.py / generate_static_stats.py）で
共通して使うCSS。1箇所にまとめて、両ページの見た目を揃える。"""

CSS = """
body { font-family: "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif; background:#f4f6f8; margin:0; padding:0; color:#222; }
.wrap { max-width: 760px; margin: 0 auto; padding: 16px; }
.header { background:#1a5490; color:#fff; border-radius:10px; padding:20px; text-align:center; }
.header h1 { margin:0; font-size:26px; }
.header .date { margin-top:6px; font-size:14px; opacity:0.9; }
.nav { text-align:center; margin: 10px 0; }
.nav a { color:#1a5490; text-decoration:none; font-weight:bold; margin: 0 10px; }
h2 { border-left:6px solid #1a5490; padding-left:10px; margin-top:36px; }
h3 { color:#1565c0; }
table { border-collapse: collapse; width:100%; margin: 10px 0 20px; background:#fff; }
th, td { border:1px solid #ddd; padding:8px; text-align:center; font-size:14px; }
th { background:#1a5490; color:#fff; }
.badge-S { color:#d32f2f; font-weight:bold; }
.winning { font-size:26px; font-weight:bold; color:#d32f2f; text-align:center; padding:14px; background:#fff3f3; border-radius:8px; }
.note { color:#666; font-size:13px; }
.card { background:#fff; border-radius:8px; padding:16px; margin: 14px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.combo { padding:10px 14px; border:1px solid #ddd; border-radius:8px; margin:6px 0; background:#fff; }
.combo .num { font-size:20px; font-weight:bold; color:#1a5490; margin:0 8px; }
.combo .note { font-size:12px; color:#777; }
.footer { text-align:center; color:#999; font-size:12px; margin: 30px 0; }
pre { white-space: pre-wrap; background:#fafafa; border:1px solid #eee; padding:12px; border-radius:8px; font-size:13px; }
button.axis-btn { padding:10px 20px; font-size:16px; border-radius:8px; border:none; background:#1a5490; color:#fff; cursor:pointer; }
select.axis-select { padding:8px; font-size:16px; border-radius:6px; border:1px solid #ccc; margin-right:10px; }
.tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:bold; margin-left:4px; }
.tag-tier1 { background:#ffe0b2; color:#e65100; }
.tag-tier2 { background:#e1f5fe; color:#0277bd; }
.tag-cut { background:#eeeeee; color:#999; text-decoration: line-through; }
.verify-hit { background:#e8f5e8; color:#2e7d32; font-weight:bold; }
.verify-miss { color:#999; }
.number-pool { display:flex; flex-wrap:wrap; gap:6px; margin:10px 0; }
.number-pool span { display:inline-block; width:34px; height:34px; line-height:34px; text-align:center; border-radius:50%; font-size:13px; font-weight:bold; }
.stat-grid { display:flex; flex-wrap:wrap; gap:10px; margin:14px 0; }
.stat-box { flex:1; min-width:140px; background:#fff; border-radius:8px; padding:14px; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.stat-box .stat-value { font-size:20px; font-weight:bold; color:#1a5490; }
.stat-box .stat-label { font-size:12px; color:#777; margin-top:4px; }
button { padding:8px 16px; font-size:14px; border-radius:8px; border:none; background:#1a5490; color:#fff; cursor:pointer; }
"""

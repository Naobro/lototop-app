"""
無料公開の「当選番号・統計データ」ページを静的HTML化するスクリプト。
=================================================
pages/numbers3_top.py / pages/numbers4_top.py と同じ内容（予想AIロジックは
含まない、統計データのみ）を、Streamlitなしの1ファイルHTMLとして出力する。
ColorfulBoxのような共有（レンタル）サーバーにそのままアップロードできる。

「軸数字を選んで20パターンランダム表示」ボタンは、Pythonサーバーがない
静的ページでは動かせないので、同じロジックをJavaScriptで書き直して
ブラウザ側で完結するようにしている。

使い方:
    python3 generate_static_stats.py numbers3
    python3 generate_static_stats.py numbers4

出力:
    output/numbers3_stats.html （または numbers4_stats.html）
    ※ 予想レポート（generate_static_report.py の出力）と違い、回号を
      ファイル名に含めない。ブックマークやリンク先のURLを固定するため、
      更新のたびに同じファイル名で上書きアップロードする運用を想定。
"""
from __future__ import annotations

import sys
from datetime import datetime

import numbers_common as nc
from static_style import CSS

GAMES = {
    "numbers3": {
        "digit_count": 3,
        "label": "ナンバーズ3",
        "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv",
    },
    "numbers4": {
        "digit_count": 4,
        "label": "ナンバーズ4",
        "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv",
    },
}


def df_to_html_table(df, escape: bool = True) -> str:
    return df.to_html(index=False, escape=escape, border=0)


def axis_tool_js(digit_count: int) -> str:
    """軸数字を選んで20パターンをランダム生成するツール（JavaScript版）。
    元のStreamlit版(pages/numbers3_top.py・numbers4_top.py)のロジックを踏襲：
    ・ナンバーズ3: 軸数字 + ランダム2桁（重複あり得る、独立抽選）
    ・ナンバーズ4: 軸数字 + ランダム3桁（互いに重複しない、軸とも重複しない）
    """
    others = digit_count - 1
    if digit_count == 3:
        pick_others_js = f"""
          const o = [];
          for (let k = 0; k < {others}; k++) {{
            o.push(pool[Math.floor(Math.random() * pool.length)]);
          }}
          """
    else:
        pick_others_js = f"""
          const shuffled = pool.slice().sort(() => Math.random() - 0.5);
          const o = shuffled.slice(0, {others});
          """
    return f"""
    <div class="card">
      <p>軸数字を選んで、他{others}桁をランダムに組み合わせた20パターンを表示します（AIモデルは使用しない簡易ツールです）。</p>
      <select id="axisSelect" class="axis-select">
        {"".join(f'<option value="{i}">{i}</option>' for i in range(10))}
      </select>
      <button class="axis-btn" onclick="generateAxisPredictions()">20パターン表示</button>
      <div id="axisResult" style="margin-top:14px;"></div>
    </div>
    <script>
      function generateAxisPredictions() {{
        const axis = parseInt(document.getElementById('axisSelect').value, 10);
        const pool = [];
        for (let i = 0; i < 10; i++) {{ if (i !== axis) pool.push(i); }}
        const results = [];
        const seen = new Set();
        let attempts = 0;
        while (results.length < 20 && attempts < 5000) {{
          attempts++;
          {pick_others_js}
          const combo = [axis, ...o].sort((a, b) => a - b);
          const key = combo.join(',');
          if (!seen.has(key)) {{
            seen.add(key);
            results.push(combo);
          }}
        }}
        let html = '<table><tr><th>#</th>' + Array.from({{length: {digit_count}}}, (_, i) => `<th>予測${{i+1}}</th>`).join('') + '</tr>';
        results.forEach((combo, idx) => {{
          html += `<tr><td>${{idx + 1}}</td>` + combo.map(n => `<td>${{n}}</td>`).join('') + '</tr>';
        }});
        html += '</table>';
        document.getElementById('axisResult').innerHTML = html;
      }}
    </script>
    """


def build_stats_html(game_key: str) -> tuple[str, str]:
    game = GAMES[game_key]
    digit_count = game["digit_count"]
    label = game["label"]

    df = nc.load_df(game["csv_path"], digit_count)
    df_recent = nc.recent(df, 24)
    cols = nc.digit_cols(digit_count)
    latest = df.iloc[0]
    latest_round = int(latest["回号"])

    maps = nc.sab_maps(df_recent, digit_count)
    sab_table = nc.sab_annotated_table(df_recent, digit_count, maps)
    ranking_table = nc.ranking_table(df_recent, digit_count)
    parity_df = nc.parity_per_draw(df_recent, digit_count)
    pattern_table, parity_overall = nc.parity_summary(parity_df, digit_count)
    sum_range_df = nc.sum_range_distribution(df_recent, digit_count)
    sum_value_df = nc.sum_value_counts(df_recent, digit_count)
    type_counts = nc.type_counts(df_recent, digit_count)
    range_dist = nc.range_distribution(df_recent, digit_count)
    pair_df = nc.pair_counts(df_recent, digit_count).head(15)
    hoppari = nc.hoppari_count(df_recent, digit_count)

    number_str = "".join(str(int(latest[c])) for c in cols)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    other_key = "numbers4" if game_key == "numbers3" else "numbers3"
    other_label = GAMES[other_key]["label"]

    doc = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} 当選番号・統計データ</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>{label} - 当選番号・統計データ</h1>
    <div class="date">最終更新 {generated_at}</div>
  </div>
  <div class="nav">
    <a href="{other_key}_stats.html">{other_label}はこちら</a> |
    <a href="{game_key}_report_{latest_round + 1}.html">AI予想レポート（有料note用）</a> |
    <a href="../index.html">TOPへ戻る</a>
  </div>
  <p class="note">このページは当選番号と統計データのみを掲載しています。AIによる予想は別途noteで公開しています。</p>

  <h2>① 最新の当選番号（第{latest_round}回）</h2>
  <div class="winning">{number_str}</div>

  <h2>② 直近24回の当選番号（SAB分類付き）</h2>
  <p class="note">SAB分類はロトのページと同じ定義：S=直近24回で5回以上出現 / A=3〜4回 / B=2回以下</p>
  {df_to_html_table(sab_table, escape=False)}

  <h2>③ 各桁の出現ランキング（直近24回）</h2>
  {df_to_html_table(ranking_table)}

  <h2>④ 偶数・奇数の比率（直近24回）</h2>
  {df_to_html_table(pattern_table)}
  <p class="note">全体比率: 偶数 {parity_overall['even']}/{parity_overall['total_slots']}
  （{parity_overall['even_pct']:.1f}%） ／ 奇数 {parity_overall['odd']}/{parity_overall['total_slots']}
  （{parity_overall['odd_pct']:.1f}%）</p>

  <h2>⑤ 合計値のレンジ分布（0〜{9*digit_count}を3分割・直近24回）</h2>
  {df_to_html_table(sum_range_df)}

  <h2>シングル・ダブル・トリプル回数（直近24回）</h2>
  <table><tr><th>タイプ</th><th>回数</th></tr>{"".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in type_counts.items())}</table>

  <h2>ひっぱり回数（直近24回）</h2>
  <p>直近24回中 {hoppari} 回、前回と同じ数字を含んでいました。</p>

  <h2>数字の範囲ごとの分布（直近24回）</h2>
  <table><tr><th>範囲</th><th>出現回数</th></tr>{"".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in range_dist.items())}</table>

  <h2>ペア出現（上位15・直近24回）</h2>
  {df_to_html_table(pair_df)}

  <h2>合計値の出現回数（直近24回）</h2>
  {df_to_html_table(sum_value_df)}

  <h2>軸数字予想（ランダム・簡易ツール）</h2>
  {axis_tool_js(digit_count)}

  <div class="footer">{generated_at} 生成 ／ NAOKIのロト・ナンバーズ予想</div>
</div>
</body>
</html>
"""
    return doc, f"output/{game_key}_stats.html"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in GAMES:
        print("使い方: python3 generate_static_stats.py [numbers3|numbers4]")
        sys.exit(1)

    game_key = sys.argv[1]
    print(f"{GAMES[game_key]['label']} の統計ページを生成中...")
    doc, out_path = build_stats_html(game_key)
    import os
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"完成: {out_path}")
    print("このHTMLファイルをそのままサーバー（ColorfulBox等）にアップロードすれば表示されます。")

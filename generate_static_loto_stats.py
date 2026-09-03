"""
ロト6・ロト7・ミニロトの無料公開「当選番号・統計データ」ページを静的HTML化するスクリプト。
generate_static_stats.py（ナンバーズ用）と対になるロト版。
ColorfulBoxのような共有サーバーにそのままアップロードできる。

使い方:
    python3 generate_static_loto_stats.py loto6
    python3 generate_static_loto_stats.py loto7
    python3 generate_static_loto_stats.py miniloto

出力:
    output/loto6_stats.html （など）
    ※ ナンバーズの統計ページと同じく、回号をファイル名に含めない
      （毎回同じファイル名で上書きアップロードする運用）。
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import loto_common as lc
from static_style import CSS

GAMES = {
    "loto6": {"label": "ロト6", "csv_path": "data/loto6_50.csv"},
    "loto7": {"label": "ロト7", "csv_path": "data/loto7_50.csv"},
    "miniloto": {"label": "ミニロト", "csv_path": "data/miniloto_50.csv"},
}


def df_to_html_table(df, escape: bool = True) -> str:
    return df.to_html(index=False, escape=escape, border=0)


def tier_pool_html(tiers: lc.TierResult) -> str:
    def spans(nums, cls):
        return "".join(f'<span class="{cls}">{n}</span>' for n in sorted(nums))
    return (
        '<p><strong>1軍（最有力）</strong></p><div class="number-pool">' + spans(tiers.tier1, "tag tag-tier1") + "</div>"
        '<p><strong>2軍（次点）</strong></p><div class="number-pool">' + spans(tiers.tier2, "tag tag-tier2") + "</div>"
        '<p><strong>削除予定（今回は見送り）</strong></p><div class="number-pool">' + spans(tiers.cut, "tag tag-cut") + "</div>"
    )


def build_stats_html(game_key: str) -> tuple[str, str]:
    game = GAMES[game_key]
    spec = lc.GAME_SPEC[game_key]
    pool_size, pick_count = spec["pool_size"], spec["pick_count"]
    label = game["label"]

    df = lc.load_df(game["csv_path"], pick_count)
    df_recent = lc.recent(df, 24)
    cols = lc.digit_cols(pick_count)
    latest = df.iloc[0]
    latest_round = int(latest["回号"])

    amap = lc.abc_maps(df_recent, pick_count, pool_size)
    scores = lc.tier_scores(df, pool_size, pick_count)
    tiers = lc.classify_tiers(scores, pool_size, spec["selected_count"])

    # ランキング表（直近24回の出現回数）
    import pandas as pd
    from collections import Counter
    all_nums = df_recent[cols].values.flatten()
    counts = Counter(int(x) for x in all_nums if x == x)
    ranking_rows = [{"数字": n, "出現回数(直近24回)": counts.get(n, 0), "ABC分類": amap[n]} for n in range(1, pool_size + 1)]
    ranking_df = pd.DataFrame(ranking_rows).sort_values("出現回数(直近24回)", ascending=False).reset_index(drop=True)

    gap_df = lc.gap_table(df, pick_count, pool_size).head(15)
    pair_df = lc.pair_counts(df_recent, pick_count).head(15)

    number_str = " - ".join(str(int(latest[c])) for c in cols)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    other_games = [k for k in GAMES if k != game_key]
    nav_links = " | ".join(f'<a href="{k}_stats.html">{GAMES[k]["label"]}はこちら</a>' for k in other_games)

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
    {nav_links} |
    <a href="{game_key}_report_{latest_round + 1}.html">AI予想レポート（有料note用）</a> |
    <a href="../index.html">TOPへ戻る</a>
  </div>
  <p class="note">このページは当選番号と統計データのみを掲載しています。AIによる予想は別途noteで公開しています。</p>

  <h2>① 最新の当選番号（第{latest_round}回）</h2>
  <div class="winning">{number_str}</div>

  <h2>② 厳選数字（1軍・2軍・削除予定）</h2>
  <p class="note">単純な「よく出ている＝良い」「最近出ていない＝良い」という短絡的な判定ではなく、
  直近{50}回の出現頻度・出現間隔のバランス・末尾（1の位）が同じ数字グループの動向を
  組み合わせたスコアで、厳選数字（1軍＋2軍　計{spec['selected_count']}個）と
  削除予定（{pool_size - spec['selected_count']}個）に分類しています。1軍/2軍の人数は
  固定せず、スコアの分かれ目で自動的に決まります。</p>
  {tier_pool_html(tiers)}

  <h2>③ 各数字の出現ランキング（直近24回・ABC分類付き）</h2>
  <p class="note">ABC分類：A=直近24回で3〜4回出現 / B=5回以上出現 / C=それ以外（ロトのページと同じ定義）</p>
  {df_to_html_table(ranking_df)}

  <h2>④ 出現間隔（最終出現からの回数・上位15）</h2>
  {df_to_html_table(gap_df)}

  <h2>⑤ ペア出現（上位15・直近24回）</h2>
  {df_to_html_table(pair_df)}

  <div class="footer">{generated_at} 生成 ／ NAOKIのロト・ナンバーズ予想</div>
</div>
</body>
</html>
"""
    return doc, f"output/{game_key}_stats.html"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in GAMES:
        print("使い方: python3 generate_static_loto_stats.py [loto6|loto7|miniloto]")
        sys.exit(1)

    game_key = sys.argv[1]
    print(f"{GAMES[game_key]['label']} の統計ページを生成中...")
    doc, out_path = build_stats_html(game_key)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"完成: {out_path}")

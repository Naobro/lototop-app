"""
ロト6・ロト7・ミニロトの無料公開「当選番号・統計データ」ページを静的HTML化するスクリプト。
generate_static_stats.py（ナンバーズ用）と対になるロト版。
ColorfulBoxのような共有サーバーにそのままアップロードできる。

※このファイルは元のStreamlit版 pages/loto6_top.py 等にあった分析項目
　（各回のSAB構成・ひっぱり・連続、S/A/B比率、パターン分析、位別S/A内訳、
　各位・各数字のTOP5、連続ペア、直近100回vs24回の頻度比較、出現間隔の詳細分析）
　を静的ページ側に復元したもの。新設の1軍/2軍/削除予定（厳選数字）セクションは
　追加であり、既存分析を置き換えるものではない。

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
from collections import Counter
from datetime import datetime

import pandas as pd

import loto_common as lc
from static_style import CSS

GAMES = {
    "loto6": {"label": "ロト6", "csv_path": "data/loto6_50.csv"},
    "loto7": {"label": "ロト7", "csv_path": "data/loto7_50.csv"},
    "miniloto": {"label": "ミニロト", "csv_path": "data/miniloto_50.csv"},
}


def df_to_html_table(df, escape: bool = True) -> str:
    return df.to_html(index=False, escape=escape, border=0)


def area_heatmap_html(position_freq: list[dict], pool_size: int) -> str:
    """エリア分析：位置×数字のヒートマップ表HTML。
    エリア内（min〜max）は行の色で塗る（出現回数0でも塗る、数値は0なら空欄）。
    エリア外は黒（lc.AREA_OUT_COLOR）で塗り、数値は出さない。
    """
    colors = lc.position_row_colors(len(position_freq))
    head_cells = "".join(f"<th>{n}</th>" for n in range(1, pool_size + 1))
    rows_html = []
    for row, (bg, fg) in zip(position_freq, colors):
        mn, mx = row["min"], row["max"]
        cells = []
        for n in range(1, pool_size + 1):
            in_area = mn is not None and mn <= n <= mx
            if in_area:
                count = row["counts"].get(n, 0)
                text = str(count) if count > 0 else ""
                cells.append(f'<td style="background:{bg};color:{fg};">{text}</td>')
            else:
                cells.append(f'<td style="background:{lc.AREA_OUT_COLOR};"></td>')
        area_text = f"{mn}〜{mx}" if mn is not None else "-"
        rows_html.append(
            f'<tr><th style="background:{bg};color:{fg};text-align:left;">第{row["position"]}数字</th>'
            f'<td style="background:{bg};color:{fg};">{area_text}</td>{"".join(cells)}</tr>'
        )
    return (
        '<div class="table-scroll" style="overflow-x:auto;">'
        '<table class="analysis-table" style="min-width:1400px;font-size:0.72rem;border-collapse:collapse;">'
        f'<thead><tr><th>位置</th><th>エリア</th>{head_cells}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        "</table></div>"
    )


def tier_pool_html(tiers: lc.TierResult) -> str:
    def spans(nums, cls):
        return "".join(f'<span class="{cls}">{n}</span>' for n in sorted(nums))
    return (
        '<p><strong>1軍（最有力）</strong></p><div class="number-pool">' + spans(tiers.tier1, "tag tag-tier1") + "</div>"
        '<p><strong>2軍（次点）</strong></p><div class="number-pool">' + spans(tiers.tier2, "tag tag-tier2") + "</div>"
        '<p><strong>削除予定（今回は見送り）</strong></p><div class="number-pool">' + spans(tiers.cut, "tag tag-cut") + "</div>"
    )


def build_ai_copy_text(game_label: str, latest_round: int, number_str: str, summary: dict,
                        tiers: lc.TierResult, ranking_df: pd.DataFrame, parity_overall: dict) -> str:
    """ページの要点をAIコピー用にまとめたプレーンテキスト（元のStreamlit版のAIコピー機能相当）。"""
    top10 = ranking_df.head(10)
    top10_str = ", ".join(f"{int(r['数字'])}({r['SAB分類']})" for _, r in top10.iterrows())
    lines = [
        f"【{game_label} 第{latest_round}回 統計サマリー】",
        f"当選番号: {number_str}",
        f"S/A/B構成比率: S {summary['s_pct']}% / A {summary['a_pct']}% / B {summary['b_pct']}%",
        f"ひっぱり率(前回との数字重複): {summary['pull_rate']}%",
        f"連続数字が出た割合: {summary['cont_rate']}%",
        f"奇偶比率(直近24回全体): 奇{parity_overall['odd']} / 偶{parity_overall['even']} ({parity_overall['odd_pct']}% / {parity_overall['even_pct']}%)",
        f"直近24回 出現数TOP10: {top10_str}",
        f"1軍（最有力・{len(tiers.tier1)}個）: {', '.join(map(str, sorted(tiers.tier1)))}",
        f"2軍（次点・{len(tiers.tier2)}個）: {', '.join(map(str, sorted(tiers.tier2)))}",
    ]
    return "\n".join(lines)


def build_stats_html(game_key: str) -> tuple[str, str]:
    game = GAMES[game_key]
    spec = lc.GAME_SPEC[game_key]
    pool_size, pick_count = spec["pool_size"], spec["pick_count"]
    label = game["label"]
    buckets = lc.BUCKETS_BY_GAME[game_key]

    df = lc.load_df(game["csv_path"], pick_count)
    df_recent = lc.recent(df, 24)
    cols = lc.digit_cols(pick_count)
    latest = df.iloc[0]
    latest_round = int(latest["回号"])

    smap = lc.sab_maps(df_recent, pick_count, pool_size)
    scores = lc.tier_scores(df, pool_size, pick_count)
    tiers = lc.classify_tiers(scores, pool_size, spec["selected_count"])

    # ③ ランキング表（直近24回の出現回数・SAB分類付き）
    all_nums = df_recent[cols].values.flatten()
    counts = Counter(int(x) for x in all_nums if x == x)
    ranking_rows = [{"数字": n, "出現回数(直近24回)": counts.get(n, 0), "SAB分類": smap[n]} for n in range(1, pool_size + 1)]
    ranking_df = pd.DataFrame(ranking_rows).sort_values("出現回数(直近24回)", ascending=False).reset_index(drop=True)

    # ④ 直近24回の当選番号一覧（SAB構成・SAB集計・偶奇・合計数字・ひっぱり・連続付き）
    sab_annotated = lc.sab_annotated_draws(df_recent, pick_count, smap)
    summary = lc.sab_summary_stats(sab_annotated, pick_count)
    draw_table_df = sab_annotated.rename(columns={c: c for c in sab_annotated.columns})
    parity_pattern_df, parity_overall = lc.parity_summary(sab_annotated, pick_count)
    sum_range_df = lc.sum_range_distribution(sab_annotated, pool_size, pick_count)

    # ⑤ S/A数字の位別内訳
    bucket_breakdown_df = lc.sab_bucket_breakdown(smap, buckets)

    # ⑥ 各位の出現回数TOP5／各数字（第n数字）の出現回数TOP5
    bucket_top5_df = lc.bucket_top5(df_recent, pick_count, buckets)
    position_top5_df = lc.position_top5(df_recent, pick_count)

    # ⑦ 連続ペア出現ランキング
    consec_df = lc.consecutive_pair_counts(df_recent, pick_count).head(15)

    # ⑧ パターン分析（直近24回の位内訳パターン）
    pattern_df = lc.pattern_analysis_table(df, pick_count, buckets, window=24)

    # ⑨ 直近100回 vs 直近24回の出現頻度・ランク比較
    freq_df = lc.frequency_100_vs_24(df, pick_count, pool_size)

    # ⑩ 出現間隔の詳細分析
    interval_df = lc.interval_analysis(df, pick_count, pool_size)

    # 従来からあった簡易版（出現間隔TOP15・ペア出現TOP15）も維持
    gap_df = lc.gap_table(df, pick_count, pool_size).head(15)
    pair_df = lc.pair_counts(df_recent, pick_count).head(15)

    # エリア分析（位置×数字のヒートマップ、エリアはmin/max動的計算）
    position_freq = lc.position_frequency(df_recent, pick_count, pool_size)
    area_html = area_heatmap_html(position_freq, pool_size)

    number_str = " - ".join(str(int(latest[c])) for c in cols)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    other_games = [k for k in GAMES if k != game_key]
    nav_links = " | ".join(f'<a href="{k}_stats.html">{GAMES[k]["label"]}はこちら</a>' for k in other_games)

    ai_copy_text = build_ai_copy_text(label, latest_round, number_str, summary, tiers, ranking_df, parity_overall)
    ai_copy_js = ai_copy_text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

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
  直近50回の出現頻度・出現間隔のバランス・末尾（1の位）が同じ数字グループの動向を
  組み合わせたスコアで、厳選数字（1軍＋2軍　計{spec['selected_count']}個）と
  削除予定（{pool_size - spec['selected_count']}個）に分類しています。1軍/2軍の人数は
  固定せず、スコアの分かれ目で自動的に決まります。</p>
  {tier_pool_html(tiers)}

  <h2>③ 各数字の出現ランキング（直近24回・SAB分類付き）</h2>
  <p class="note">SAB分類はナンバーズのページと同じ定義：S=直近24回で5回以上出現 / A=3〜4回 / B=2回以下</p>
  {df_to_html_table(ranking_df)}

  <h2>④ 直近24回の当選番号一覧（SAB構成・SAB集計・偶奇・合計数字・ひっぱり・連続）</h2>
  <p class="note">「SAB集計」＝その回のS/A/B数字の内訳（例:S2A4はS数字2個・A数字4個）。「偶奇」＝奇数と偶数の個数。
  「合計数字」＝本数字の合計値。「ひっぱり」＝前回と共通する数字の個数。「連続」＝当選番号の中に連続する数字（例:5と6）が含まれるかどうか。</p>
  <div class="stat-grid">
    <div class="stat-box"><div class="stat-value">S {summary['s_pct']}%</div><div class="stat-label">A {summary['a_pct']}% ／ B {summary['b_pct']}%</div></div>
    <div class="stat-box"><div class="stat-value">{summary['pull_rate']}%</div><div class="stat-label">ひっぱり率</div></div>
    <div class="stat-box"><div class="stat-value">{summary['cont_rate']}%</div><div class="stat-label">連続数字が出た割合</div></div>
    <div class="stat-box"><div class="stat-value">奇{parity_overall['odd']} / 偶{parity_overall['even']}</div><div class="stat-label">全体の奇偶比率（{parity_overall['odd_pct']}% / {parity_overall['even_pct']}%）</div></div>
  </div>
  {df_to_html_table(draw_table_df)}

  <h3>偶奇パターン別出現回数（直近24回）</h3>
  {df_to_html_table(parity_pattern_df)}

  <h3>合計数字のレンジ分布（直近24回）</h3>
  {df_to_html_table(sum_range_df)}

  <h2>⑤ S・A数字の位別内訳</h2>
  {df_to_html_table(bucket_breakdown_df)}

  <h2>⑥ 各位の出現回数TOP5・各数字（出目の順番）の出現回数TOP5</h2>
  <p class="note">各位（1の位・10の位…）でよく出る数字、および第1数字〜第{pick_count}数字それぞれの位置でよく出る数字の上位5つです。</p>
  {df_to_html_table(bucket_top5_df)}
  {df_to_html_table(position_top5_df)}

  <h2>⑦ エリア分析（直近24回）</h2>
  <p class="note">当選番号を小さい順に並べたとき、各数字がどの位置（第1〜第{pick_count}数字）に出現したかを直近24回で集計した表です。
  各行の「エリア」は、その位置に実際に出現した数字の最小値〜最大値の範囲です。エリア内は行ごとの色（未出現のマスは色のみで数値は空欄）、
  エリア外は黒で表示しています。第1数字は小さい数字帯に、第{pick_count}数字は大きい数字帯に偏る傾向があり、各位の出現範囲を確認する参考情報です。</p>
  {area_html}

  <h2>⑧ 連続ペア出現ランキング（直近24回・上位15）</h2>
  {df_to_html_table(consec_df) if not consec_df.empty else '<p class="note">直近24回では連続ペアの出現はありませんでした。</p>'}

  <h2>⑨ パターン分析（位の内訳パターン・直近24回）</h2>
  <p class="note">実際の当選データから、位（1の位/10の位/…）の内訳パターンごとの出現頻度を集計したものです。
  予想では、いずれかの位に4個以上偏る珍しいパターンは除外しています。</p>
  {df_to_html_table(pattern_df)}

  <h2>⑩ 出現頻度比較（直近100回 vs 直近24回）</h2>
  {df_to_html_table(freq_df)}

  <h2>⑪ 出現間隔の詳細分析（全{pool_size}数字）</h2>
  <p class="note">「平均間隔」は数字が出てから次に出るまでの平均回数、「最後の出現経過回数」は直近の抽せんから何回出ていないかを表します。
  抽せんは毎回独立しており、間隔が長いほど次に出やすくなるわけではない点にご注意ください。</p>
  {df_to_html_table(interval_df)}

  <h2>⑫ 出現間隔ランキング（最終出現からの回数・上位15）</h2>
  {df_to_html_table(gap_df)}

  <h2>⑬ ペア出現（上位15・直近24回）</h2>
  {df_to_html_table(pair_df)}

  <h2>AIコピー用テキスト</h2>
  <p class="note">下のボタンでこのページの要点をコピーできます（note執筆や外部AIへの入力用）。</p>
  <button onclick="navigator.clipboard.writeText(document.getElementById('ai-copy-text').textContent).then(()=>{{this.textContent='コピーしました';setTimeout(()=>{{this.textContent='テキストをコピー';}},1500);}})">テキストをコピー</button>
  <pre id="ai-copy-text">{ai_copy_js}</pre>

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

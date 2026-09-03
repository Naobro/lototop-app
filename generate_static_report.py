"""
Streamlitを使わない静的HTMLレポート生成スクリプト。
=================================================
「予想ロジックはStreamlitになってしまいますか？」への回答として作成。
numbers_common.py / numbers_predict.py / predict_image.py は元々
Streamlitに依存していないので、このスクリプトも標準ライブラリと
pandas / scikit-learn / Pillow だけで完結する。

生成される .html は1ファイルで完結した静的ページ（画像もbase64で
埋め込み済み）なので、Streamlitのようなアプリサーバーは不要。
ColorfulBoxなど、PythonアプリのホスティングができないHTMLのみの
サーバーにそのままFTP等でアップロードすれば表示できる。

使い方:
    python3 generate_static_report.py numbers3
    python3 generate_static_report.py numbers4

出力:
    output/numbers3_report_<回号>.html （または numbers4_...）
"""
from __future__ import annotations

import base64
import html
import os
import sys
from datetime import datetime, timedelta

import numbers_common as nc
import numbers_predict as npred
from predict_image import create_prediction_image_pair

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

from static_style import CSS


def df_to_html_table(df, escape: bool = True) -> str:
    return df.to_html(index=False, escape=escape, border=0)


def build_report_html(game_key: str) -> tuple[str, str]:
    game = GAMES[game_key]
    digit_count = game["digit_count"]
    label = game["label"]

    df = nc.load_df(game["csv_path"], digit_count)
    df_recent = nc.recent(df, 24)
    cols = nc.digit_cols(digit_count)
    latest = df.iloc[0]
    latest_round = int(latest["回号"])
    next_round = latest_round + 1

    # --- 統計 ---
    maps = nc.sab_maps(df_recent, digit_count)
    sab_table = nc.sab_annotated_table(df_recent, digit_count, maps)
    sab_text, sab_counts, sab_total = nc.sab_stats_text(df_recent, digit_count, maps)
    ranking_table = nc.ranking_table(df_recent, digit_count)
    parity_df = nc.parity_per_draw(df_recent, digit_count)
    pattern_table, parity_overall = nc.parity_summary(parity_df, digit_count)
    sum_range_df = nc.sum_range_distribution(df_recent, digit_count)
    sum_value_df = nc.sum_value_counts(df_recent, digit_count)
    type_counts = nc.type_counts(df_recent, digit_count)
    range_dist = nc.range_distribution(df_recent, digit_count)
    pair_df = nc.pair_counts(df_recent, digit_count).head(15)
    hoppari = nc.hoppari_count(df_recent, digit_count)

    # --- 予想（note有料公開想定のセクション、20通り・根拠つき）---
    report_text, joint_top_combos, backtest, combo_explanations = npred.build_prediction_report_text(
        df, digit_count, n_combos=20
    )

    def next_drawing_date() -> datetime:
        d = datetime.now() + timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    backtest_summary_text = "\n".join(
        f"{npred.MODEL_NAMES[m]} 的中率 {backtest[m]['hit_rate_pct']:.1f}%（直近{backtest[m]['tested']}回検証・ランダム基準30%）"
        for m in ["RF", "NN", "MC", "WH"]
    )
    combos = [ce["combo"] for ce in combo_explanations]
    combo_meta = [{"sab_pattern": ce["sab_pattern"], "type": ce["type"]} for ce in combo_explanations]
    prev_winning = [int(latest[c]) for c in cols]
    os.makedirs("output", exist_ok=True)
    image_paths = create_prediction_image_pair(
        digit_count=digit_count,
        combinations=combos,
        current_round=next_round,
        current_date=next_drawing_date(),
        output_path_prefix=f"output/{game_key}_prediction_{next_round}",
        combo_meta=combo_meta,
        previous_round=latest_round,
        previous_winning=prev_winning,
        backtest_summary_text=backtest_summary_text,
        split_size=10,
    )
    image_data_uris = []
    for image_path in image_paths:
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            image_data_uris.append(f"data:image/png;base64,{b64}")

    number_str = "".join(str(int(latest[c])) for c in cols)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    combo_html = "".join(
        f'<div class="combo"><div><span>{i+1}位</span> '
        f'<span class="num">{"".join(map(str, ce["combo"]))}</span> '
        f'<span class="note">SAB:{ce["sab_pattern"]}　{ce["type"]}　合計{ce["sum"]}</span></div>'
        f'<div class="note">{" ／ ".join(ce["reasons"])}</div></div>'
        for i, ce in enumerate(combo_explanations)
    )

    images_html = "".join(
        f'<div class="card"><img src="{uri}" style="max-width:100%;border-radius:8px;"></div>'
        for uri in image_data_uris
    )

    bt_rows_html = "".join(
        f"<tr><td>{npred.MODEL_NAMES[m]}</td><td>{backtest[m]['hit_rate_pct']:.1f}%</td></tr>"
        for m in ["RF", "NN", "MC", "WH"]
    ) + '<tr><td>ランダム基準(理論値)</td><td>30.0%</td></tr>'

    doc = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} 予想レポート 第{next_round}回</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>NAOKIの{label} 予想レポート</h1>
    <div class="date">第{next_round}回向け ／ 生成日時 {generated_at}</div>
  </div>
  <div class="nav">
    <a href="{game_key}_stats.html">統計ページへ戻る</a> | <a href="../index.html">TOPへ戻る</a>
  </div>

  <h2>前回の当選番号（第{latest_round}回）</h2>
  <div class="winning">{number_str}</div>

  <h2>今回の予想TOP{len(combo_explanations)}（選出根拠つき）</h2>
  <div class="card">
    {combo_html}
    <p class="note">※統計分析による数字です。当選を保証するものではありません。SABは直近24回のその桁での出現回数による分類（S=5回以上／A=3〜4回／B=2回以下）。「がTOP3に選出」は直近24回データでの各モデルの予測に基づく根拠です。</p>
  </div>

  <h2>各モデルの直近バックテスト的中率</h2>
  <table><tr><th>モデル</th><th>的中率(TOP3)</th></tr>{bt_rows_html}</table>
  <p class="note">直近{backtest['RF']['tested']}回について、その回より前のデータだけで予測を再現し、
  実際の当選数字がTOP3に入っていたかを集計したもの。ランダムに3つ選んだ場合の理論値は30%。</p>

  {f'<h2>予想画像（SNS/note添付用・10通り×{len(image_data_uris)}枚）</h2>{images_html}' if image_data_uris else ""}

  <h2>直近24回の当選番号（SAB分類付き）</h2>
  <p class="note">SAB分類はロトのページと同じ定義：S=直近24回で5回以上出現 / A=3〜4回 / B=2回以下</p>
  {df_to_html_table(sab_table, escape=False)}

  <h2>各桁の出現ランキング（直近24回）</h2>
  {df_to_html_table(ranking_table)}

  <h2>SAB出現統計</h2>
  <pre>{html.escape(sab_text)}</pre>

  <h2>偶数・奇数の比率（直近24回）</h2>
  {df_to_html_table(pattern_table)}
  <p class="note">全体比率: 偶数 {parity_overall['even']}/{parity_overall['total_slots']}
  （{parity_overall['even_pct']:.1f}%） ／ 奇数 {parity_overall['odd']}/{parity_overall['total_slots']}
  （{parity_overall['odd_pct']:.1f}%）</p>

  <h2>合計値のレンジ分布（0〜{9*digit_count}を3分割・直近24回）</h2>
  {df_to_html_table(sum_range_df)}

  <h2>タイプ別（シングル・ダブル・トリプル）</h2>
  <table><tr><th>タイプ</th><th>回数</th></tr>{"".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in type_counts.items())}</table>

  <h2>ひっぱり回数</h2>
  <p>直近24回中 {hoppari} 回、前回と同じ数字を含んでいました。</p>

  <h2>数字の範囲ごとの分布</h2>
  <table><tr><th>範囲</th><th>出現回数</th></tr>{"".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in range_dist.items())}</table>

  <h2>ペア出現（上位15）</h2>
  {df_to_html_table(pair_df)}

  <h2>合計値の出現回数</h2>
  {df_to_html_table(sum_value_df)}

  <h2>各モデルTOP3・合算スコアTOP5（詳細テキスト）</h2>
  <pre>{html.escape(report_text)}</pre>

  <div class="footer">{generated_at} 生成 ／ NAOKIのロト・ナンバーズ予想</div>
</div>
</body>
</html>
"""
    return doc, f"output/{game_key}_report_{next_round}.html"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in GAMES:
        print("使い方: python3 generate_static_report.py [numbers3|numbers4]")
        sys.exit(1)

    game_key = sys.argv[1]
    print(f"{GAMES[game_key]['label']} のレポートを生成中...（RF/NN学習とバックテストのため数十秒かかります）")
    doc, out_path = build_report_html(game_key)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"完成: {out_path}")
    print("このHTMLファイル1つをそのままサーバー（ColorfulBox等）にアップロードすれば表示されます。")

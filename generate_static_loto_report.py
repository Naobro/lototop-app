"""
ロト6・ロト7・ミニロトの予想レポート（有料note公開想定）を静的HTML化するスクリプト。
generate_static_report.py（ナンバーズ用）と対になるロト版。

1軍・2軍分類＋バケットパターン絞り込み（同じ位が4個以上に偏るレアパターンを除外）＋
末尾グループの連動ボーナスを組み込んだ loto_predict.py のロジックを使う。
生成した予想は prediction_log.py で回号付きに保存し、あとで検証ページ
（generate_static_verify.py）から突き合わせられるようにする。

使い方:
    python3 generate_static_loto_report.py loto6
    python3 generate_static_loto_report.py loto7
    python3 generate_static_loto_report.py miniloto

出力:
    output/loto6_report_<回号>.html （など）
"""
from __future__ import annotations

import base64
import os
import sys
from datetime import datetime

import loto_common as lc
import loto_predict as lp
import prediction_log as plog
from loto_predict_image import create_loto_prediction_image_pair
from static_style import CSS

GAMES = {
    "loto6": {"label": "ロト6", "csv_path": "data/loto6_50.csv"},
    "loto7": {"label": "ロト7", "csv_path": "data/loto7_50.csv"},
    "miniloto": {"label": "ミニロト", "csv_path": "data/miniloto_50.csv"},
}


def build_report_html(game_key: str) -> tuple[str, str]:
    game = GAMES[game_key]
    spec = lc.GAME_SPEC[game_key]
    pool_size, pick_count = spec["pool_size"], spec["pick_count"]
    label = game["label"]
    buckets = lc.BUCKETS_BY_GAME[game_key]

    df = lc.load_df(game["csv_path"], pick_count)
    cols = lc.digit_cols(pick_count)
    latest = df.iloc[0]
    latest_round = int(latest["回号"])
    next_round = latest_round + 1
    prev_winning = [int(latest[c]) for c in cols]

    scores = lc.tier_scores(df, pool_size, pick_count)
    tiers = lc.classify_tiers(scores, pool_size, spec["selected_count"])
    preds = lp.generate_predictions(df, pool_size, pick_count, buckets, tiers, n_combos=20)

    # 予想ログを保存（検証ページで使う）
    combos_for_log = [p["combo"] for p in preds]
    plog.save_prediction(game_key, next_round, combos_for_log, meta={
        "generated_at": datetime.now().isoformat(),
        "based_on_round": latest_round,
    })

    combo_meta = [
        {"tiers": "/".join("1軍" if n in tiers.tier1 else "2軍" for n in p["combo"])}
        for p in preds
    ]
    os.makedirs("output", exist_ok=True)
    image_paths = create_loto_prediction_image_pair(
        game_label=label,
        combinations=combos_for_log,
        current_round=next_round,
        current_date=datetime.now(),
        output_path_prefix=f"output/{game_key}_prediction_{next_round}",
        combo_meta=combo_meta,
        previous_round=latest_round,
        previous_winning=prev_winning,
        backtest_summary_text="1軍・2軍分類とバケットパターン絞り込みに基づく予想です（ランダム性の排除ではなく、選び方の指針です）",
        split_size=10,
    )
    image_data_uris = []
    for p in image_paths:
        if p and os.path.exists(p):
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            image_data_uris.append(f"data:image/png;base64,{b64}")

    number_str = " - ".join(map(str, prev_winning))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    combo_html = "".join(
        f'<div class="combo"><div><span>{i + 1}位</span> '
        f'<span class="num">{" - ".join(f"{n:02d}" for n in p["combo"])}</span> '
        f'<span class="note">パターン:{p["pattern"]}　スコア{p["score"]:.2f}</span></div>'
        f'<div class="note">{" ／ ".join(p["reasons"])}</div></div>'
        for i, p in enumerate(preds)
    )
    images_html = "".join(
        f'<div class="card"><img src="{uri}" style="max-width:100%;border-radius:8px;"></div>'
        for uri in image_data_uris
    )

    tier_html = (
        '<p><strong>1軍</strong></p><div class="number-pool">'
        + "".join(f'<span class="tag tag-tier1">{n}</span>' for n in sorted(tiers.tier1))
        + '</div><p><strong>2軍</strong></p><div class="number-pool">'
        + "".join(f'<span class="tag tag-tier2">{n}</span>' for n in sorted(tiers.tier2))
        + "</div>"
    )

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

  <h2>前回の本数字（第{latest_round}回）</h2>
  <div class="winning">{number_str}</div>

  <h2>今回使用した厳選数字</h2>
  {tier_html}
  <p class="note">削除予定に分類した数字は今回の予想には使っていません。1軍/2軍の人数はスコアの分かれ目で自動決定しています。</p>

  <h2>今回の予想TOP{len(preds)}（選出根拠つき）</h2>
  <div class="card">
    {combo_html}
    <p class="note">※統計分析による数字です。当選を保証するものではありません。「同じ位（1の位/10の位/…）が4個以上」に偏るレアパターンは除外しています。パターン欄はバケットごとの個数内訳です。</p>
  </div>

  {f'<h2>予想画像（SNS/note添付用・10通り×{len(image_data_uris)}枚）</h2>{images_html}' if image_data_uris else ""}

  <div class="footer">{generated_at} 生成 ／ NAOKIのロト・ナンバーズ予想</div>
</div>
</body>
</html>
"""
    return doc, f"output/{game_key}_report_{next_round}.html"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in GAMES:
        print("使い方: python3 generate_static_loto_report.py [loto6|loto7|miniloto]")
        sys.exit(1)

    game_key = sys.argv[1]
    print(f"{GAMES[game_key]['label']} のレポートを生成中...")
    doc, out_path = build_report_html(game_key)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"完成: {out_path}")

"""
「前回の予想がどうだったか」を検証する静的HTMLページを生成する共通スクリプト。
ナンバーズ3/4・ロト6/7/ミニロトの全ゲーム共通で使う。

このページは prediction_log.py に保存された過去の予想と、CSVデータ上の
実際の当せん結果を突き合わせて表示する。まだ運用開始前（そのログが存在しない）
回号については、エラーにせず「まだ記録がありません」と表示する。

使い方:
    python3 generate_static_verify.py numbers4 7062
    python3 generate_static_verify.py loto7 692

出力:
    output/{game}_verify_{回号}.html
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import numbers_common as nc
import loto_common as lc
import prediction_log as plog
from static_style import CSS

NUMBERS_GAMES = {
    "numbers3": {"digit_count": 3, "label": "ナンバーズ3", "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"},
    "numbers4": {"digit_count": 4, "label": "ナンバーズ4", "csv_path": "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"},
}
LOTO_GAMES = {
    "loto6": {"label": "ロト6", "csv_path": "data/loto6_50.csv"},
    "loto7": {"label": "ロト7", "csv_path": "data/loto7_50.csv"},
    "miniloto": {"label": "ミニロト", "csv_path": "data/miniloto_50.csv"},
}
ALL_LABELS = {**{k: v["label"] for k, v in NUMBERS_GAMES.items()}, **{k: v["label"] for k, v in LOTO_GAMES.items()}}


def _actual_numbers_for_round(game_key: str, round_no: int) -> list[int] | None:
    if game_key in NUMBERS_GAMES:
        g = NUMBERS_GAMES[game_key]
        df = nc.load_df(g["csv_path"], g["digit_count"])
        cols = nc.digit_cols(g["digit_count"])
    else:
        g = LOTO_GAMES[game_key]
        spec = lc.GAME_SPEC[game_key]
        df = lc.load_df(g["csv_path"], spec["pick_count"])
        cols = lc.digit_cols(spec["pick_count"])
    row = df[df["回号"] == round_no]
    if row.empty:
        return None
    row = row.iloc[0]
    return [int(row[c]) for c in cols]


def build_verify_html(game_key: str, round_no: int) -> tuple[str, str]:
    label = ALL_LABELS[game_key]
    actual = _actual_numbers_for_round(game_key, round_no)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    if actual is None:
        body = f"""<div class="card"><p>第{round_no}回はまだ抽せん結果がデータに反映されていません。抽せん後、データ更新してから再度お試しください。</p></div>"""
    else:
        result = plog.verify(game_key, round_no, actual)
        if not result["found"]:
            body = f"""<div class="card"><p>{result['message']}</p>
            <p class="note">この検証機能は今回新設したもので、運用を開始した回号以降のみ検証できます。過去分は記録されていないため対象外です。</p></div>"""
        elif result["kind"] == "numbers":
            actual_str = "".join(map(str, result["actual"]))
            record = plog.load_prediction(game_key, round_no) or {"combos": []}
            rows = "".join(
                f'<tr class="{"verify-hit" if list(c) == result["actual"] or sorted(c) == sorted(result["actual"]) else ""}">'
                f'<td>{i + 1}</td><td>{"".join(map(str, c))}</td>'
                f'<td>{"ストレート的中" if list(c) == result["actual"] else ("ボックス的中" if sorted(c) == sorted(result["actual"]) else "-")}</td></tr>'
                for i, c in enumerate(record["combos"])
            )
            body = f"""
            <div class="winning">当せん番号: {actual_str}</div>
            <p>予想{result['n_combos']}通り中：
            ストレート的中 {'<span class="verify-hit">あり</span>' if result['straight_hit'] else 'なし'} ／
            ボックス的中 {'<span class="verify-hit">あり</span>' if result['box_hit'] else 'なし'}</p>
            <table><tr><th>順位</th><th>予想</th><th>結果</th></tr>{rows}</table>
            """
        else:  # loto
            actual_str = " - ".join(str(n) for n in result["actual"])
            rows = "".join(
                f'<tr><td>{i + 1}</td><td>{" - ".join(f"{n:02d}" for n in c)}</td>'
                f'<td class="{"verify-hit" if m >= 3 else "verify-miss"}">{m}個一致</td></tr>'
                for i, (c, m) in enumerate(result["combos_by_match"])
            )
            body = f"""
            <div class="winning">本数字: {actual_str}</div>
            <p>予想{result['n_combos']}通り中、最高一致数 <strong>{result['best_match']}個</strong> ／
            平均一致数 {result['avg_match']}個（ランダムに選んだ場合の理論期待値: {result['random_expected_match']}個）</p>
            <table><tr><th>順位</th><th>予想</th><th>一致数</th></tr>{rows}</table>
            <p class="note">一致数がランダム期待値を上回っているかどうかは、あくまで参考情報です。抽せんは毎回独立しており、過去の傾向が次回の当選確率を上げるものではありません。</p>
            """

    doc = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} 検証 第{round_no}回</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>{label} 予想の検証</h1>
    <div class="date">第{round_no}回分 ／ 生成日時 {generated_at}</div>
  </div>
  <div class="nav">
    <a href="{game_key}_stats.html">統計ページへ戻る</a> | <a href="../index.html">TOPへ戻る</a>
  </div>
  <div class="card">{body}</div>
  <div class="footer">{generated_at} 生成 ／ NAOKIのロト・ナンバーズ予想</div>
</div>
</body>
</html>
"""
    return doc, f"output/{game_key}_verify_{round_no}.html"


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ALL_LABELS:
        print("使い方: python3 generate_static_verify.py [game_key] [回号]")
        print("game_key:", list(ALL_LABELS.keys()))
        sys.exit(1)
    game_key = sys.argv[1]
    round_no = int(sys.argv[2])
    print(f"{ALL_LABELS[game_key]} 第{round_no}回の検証ページを生成中...")
    doc, out_path = build_verify_html(game_key, round_no)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"完成: {out_path}")

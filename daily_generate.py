"""
日次生成ドライバ。schedule.py の曜日別ルールに従って、その日「予想を出すゲーム」の
統計ページ・予想レポート（＋note画像）と、「前回分の検証を出すゲーム」の検証ページを
まとめて output/ に生成する。

自動化（ColorfulBoxへの自動アップロードなど）はこのスクリプトの範囲外。
これを1回実行すれば output/ にその日アップロードすべきファイルが揃うので、
手動でColorfulBoxにアップロードする、という運用を想定している
（将来、自動アップロードの手段（FTP情報など）が用意できれば、この1本を
cronから叩くだけで自動化に拡張できる設計にしてある）。

使い方:
    python3 daily_generate.py            # 今日の日付で実行
    python3 daily_generate.py 2026-09-07 # 日付を指定して実行（曜日から自動判定）
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime

import schedule as sch

STATS_GENERATORS = {}
REPORT_GENERATORS = {}


def _lazy_imports():
    """重い依存（sklearn等）を実際に使うときだけ読み込む。"""
    global STATS_GENERATORS, REPORT_GENERATORS
    if STATS_GENERATORS:
        return
    import generate_static_stats as gss
    import generate_static_report as gsr
    import generate_static_loto_stats as glss
    import generate_static_loto_report as glsr

    STATS_GENERATORS = {
        "numbers3": lambda: gss.build_stats_html("numbers3"),
        "numbers4": lambda: gss.build_stats_html("numbers4"),
        "loto6": lambda: glss.build_stats_html("loto6"),
        "loto7": lambda: glss.build_stats_html("loto7"),
        "miniloto": lambda: glss.build_stats_html("miniloto"),
    }
    REPORT_GENERATORS = {
        "numbers3": lambda: gsr.build_report_html("numbers3"),
        "numbers4": lambda: gsr.build_report_html("numbers4"),
        "loto6": lambda: glsr.build_report_html("loto6"),
        "loto7": lambda: glsr.build_report_html("loto7"),
        "miniloto": lambda: glsr.build_report_html("miniloto"),
    }


def _latest_round_for(game_key: str) -> int:
    if game_key in ("numbers3", "numbers4"):
        import numbers_common as nc
        digit_count = 3 if game_key == "numbers3" else 4
        csv_path = f"https://raw.githubusercontent.com/Naobro/lototop-app/main/data/{game_key}_24.csv"
        df = nc.load_df(csv_path, digit_count)
    else:
        import loto_common as lc
        spec = lc.GAME_SPEC[game_key]
        df = lc.load_df(f"data/{game_key}_50.csv", spec["pick_count"])
    return int(df.iloc[0]["回号"])


def _write(doc: str, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  完成: {out_path}")


def run(target_date: date) -> dict:
    _lazy_imports()
    import generate_static_verify as gsv

    plan = sch.plan_for_date(target_date)
    written: list[str] = []

    print(sch.describe(target_date))

    for game_key in plan["predict"]:
        print(f"[予想] {game_key} の統計ページを生成中...")
        doc, path = STATS_GENERATORS[game_key]()
        _write(doc, path)
        written.append(path)

        print(f"[予想] {game_key} の予想レポートを生成中...")
        doc, path = REPORT_GENERATORS[game_key]()
        _write(doc, path)
        written.append(path)

    for game_key in plan["verify"]:
        try:
            round_no = _latest_round_for(game_key)
        except Exception as e:
            print(f"[検証] {game_key} のデータ取得に失敗したためスキップ: {e}")
            continue
        print(f"[検証] {game_key} 第{round_no}回の検証ページを生成中...")
        doc, path = gsv.build_verify_html(game_key, round_no)
        _write(doc, path)
        written.append(path)

    return {"date": target_date.isoformat(), "plan": plan, "written": written}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    else:
        target = date.today()
    result = run(target)
    print()
    print(f"=== {result['date']} 分の生成完了：{len(result['written'])}件のファイルを output/ に書き出しました ===")
    print("この output/ の中身を、ColorfulBoxの page フォルダにアップロードしてください。")

"""
予想結果を回号付きで保存し、あとで実際の当せん結果と突き合わせて検証するための
共通モジュール（ナンバーズ3/4・ロト6/7/ミニロト共通）。

【運用の前提】
このログの仕組みは今回新設したものなので、過去に遡って検証することはできない
（そもそも過去には予想を保存していないため）。運用を開始した回号以降の予想から
順次、検証ができるようになっていく。ログが無い回号については verify() が
「まだ記録がありません」という結果を返すので、呼び出し側はエラーにせず
その旨を表示すればよい。
"""
from __future__ import annotations

import json
import os
from math import comb

LOG_DIR = "predictions_log"

NUMBERS_GAMES = {"numbers3": 3, "numbers4": 4}
LOTO_GAMES = {"loto6": (43, 6), "loto7": (37, 7), "miniloto": (31, 5)}


def _log_path(game_key: str, round_no: int) -> str:
    return os.path.join(LOG_DIR, f"{game_key}_{round_no}.json")


def save_prediction(game_key: str, round_no: int, combos: list, meta: dict | None = None) -> str:
    """combos: ナンバーズなら [(d1,d2,...), ...] のリスト、ロトなら [[n1,n2,...], ...] のリスト。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    payload = {
        "game_key": game_key,
        "round_no": round_no,
        "combos": [list(c) for c in combos],
        "meta": meta or {},
    }
    path = _log_path(game_key, round_no)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_prediction(game_key: str, round_no: int) -> dict | None:
    path = _log_path(game_key, round_no)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _verify_numbers(digit_count: int, combos: list[list[int]], actual: list[int]) -> dict:
    actual_t = list(actual)
    straight_hits = [c for c in combos if list(c) == actual_t]
    box_hits = [c for c in combos if sorted(c) == sorted(actual_t)]
    return {
        "kind": "numbers",
        "actual": actual_t,
        "n_combos": len(combos),
        "straight_hit": len(straight_hits) > 0,
        "straight_hit_combos": straight_hits,
        "box_hit": len(box_hits) > 0,
        "box_hit_combos": box_hits,
    }


def _verify_loto(pool_size: int, pick_count: int, combos: list[list[int]], actual: list[int]) -> dict:
    actual_set = set(actual)
    match_counts = [len(set(c) & actual_set) for c in combos]
    best = max(match_counts) if match_counts else 0
    avg = sum(match_counts) / len(match_counts) if match_counts else 0.0
    # ランダムにpick_count個選んだ場合の期待一致数（超幾何分布の平均 = k*K/N）
    random_expected = pick_count * pick_count / pool_size
    # 参考：ランダム抽選でbest一致数以上になる期待組数（1組あたりの確率×組数、簡易近似）
    return {
        "kind": "loto",
        "actual": sorted(actual),
        "n_combos": len(combos),
        "match_counts": match_counts,
        "best_match": best,
        "avg_match": round(avg, 2),
        "random_expected_match": round(random_expected, 2),
        "combos_by_match": sorted(zip(combos, match_counts), key=lambda t: -t[1]),
    }


def verify(game_key: str, round_no: int, actual_numbers: list[int]) -> dict:
    """actual_numbers: ナンバーズは桁順のリスト、ロトは本数字のリスト（順不同）。"""
    record = load_prediction(game_key, round_no)
    if record is None:
        return {"found": False, "game_key": game_key, "round_no": round_no,
                "message": f"第{round_no}回の予想ログが見つかりません（この回はまだ記録されていません）"}

    combos = record["combos"]
    if game_key in NUMBERS_GAMES:
        result = _verify_numbers(NUMBERS_GAMES[game_key], combos, actual_numbers)
    elif game_key in LOTO_GAMES:
        pool_size, pick_count = LOTO_GAMES[game_key]
        result = _verify_loto(pool_size, pick_count, combos, actual_numbers)
    else:
        raise ValueError(f"unknown game_key: {game_key}")

    result["found"] = True
    result["game_key"] = game_key
    result["round_no"] = round_no
    result["meta"] = record.get("meta", {})
    return result

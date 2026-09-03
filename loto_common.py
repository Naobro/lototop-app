"""
ロト6・ロト7・ミニロト共通の統計・階層分類（1軍・2軍・削除予定）エンジン。
=================================================
numbers_common.py と対になるモジュール。pool_size（数字の母数）と
pick_count（1回に選ぶ個数）でパラメータ化し、3ゲームを同じコードで扱う。

【設計思想】
・「よく出てる数字＝高得点」という単純な発想も、
  「最近出てない数字＝高得点」という単純な発想も、どちらもNGという
  ユーザー方針に基づき、tier_scores() は複数の要素を組み合わせたスコアを出す。
・「末尾（1の位）が同じ数字は連動して出やすい」というオカルト的パターンを
  last_digit_bonus として明示的にスコアへ組み込む。
・厳選数字（1軍＋2軍）の人数は固定するが、1軍/2軍の内訳は固定せず、
  スコアの下落幅（ギャップ）が最大の場所で自動的に線引きする。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ゲームごとの位バケット定義（既存 pages/loto*_top.py の慣習を踏襲）
BUCKETS_BY_GAME = {
    "loto6": [("1の位", 1, 9), ("10の位", 10, 19), ("20の位", 20, 29), ("30の位", 30, 43)],
    "loto7": [("1の位", 1, 9), ("10の位", 10, 19), ("20の位", 20, 29), ("30の位", 30, 37)],
    "miniloto": [("1の位", 1, 9), ("10の位", 10, 19), ("20の位", 20, 31)],
}

GAME_SPEC = {
    "loto6": {"pool_size": 43, "pick_count": 6, "label": "ロト6", "selected_count": 30},
    "loto7": {"pool_size": 37, "pick_count": 7, "label": "ロト7", "selected_count": 27},
    "miniloto": {"pool_size": 31, "pick_count": 5, "label": "ミニロト", "selected_count": 20},
}


def digit_cols(pick_count: int) -> list[str]:
    return [f"第{i}数字" for i in range(1, pick_count + 1)]


def _normalize_parens(s: str) -> str:
    return s.replace("（", "(").replace("）", ")")


def load_df(csv_path: str, pick_count: int) -> pd.DataFrame:
    """常に昇順（古い→新しい）で内部管理したうえで、抽せん日降順のDataFrameを返す。
    numbers_common.load_df と同じ規約（呼び出し側は df.iloc[0] が最新回）。
    """
    df = pd.read_csv(csv_path)
    df.columns = [_normalize_parens(str(c)).strip() for c in df.columns]
    cols = digit_cols(pick_count)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    if "回号" in df.columns:
        df["回号"] = pd.to_numeric(df["回号"], errors="coerce").astype("Int64")
    df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
    df = df.dropna(subset=cols + ["抽せん日"]).copy()
    # 常に昇順に正規化してから、降順（最新が先頭）で返す
    df = df.sort_values("抽せん日", ascending=True).reset_index(drop=True)
    df = df.sort_values("抽せん日", ascending=False).reset_index(drop=True)
    return df


def recent(df: pd.DataFrame, n: int = 24) -> pd.DataFrame:
    """df は降順（最新が先頭）想定。直近n回を新しい順で返す。"""
    return df.head(n).reset_index(drop=True)


def sab_maps(df_recent: pd.DataFrame, pick_count: int, pool_size: int) -> dict[int, str]:
    """ナンバーズ・ロト6の既存ページと同一閾値・同一表記（S=直近24回で5回以上出現、
    A=3〜4回、B=それ以外）。サイト全体でSAB表記に統一するため、ロト側もこの名称で揃える。"""
    cols = digit_cols(pick_count)
    all_numbers = df_recent[cols].values.flatten()
    all_numbers = pd.Series([int(x) for x in all_numbers if pd.notna(x)])
    counts = all_numbers.value_counts()
    result: dict[int, str] = {}
    for n in range(1, pool_size + 1):
        c = int(counts.get(n, 0))
        if c >= 5:
            result[n] = "S"
        elif c >= 3:
            result[n] = "A"
        else:
            result[n] = "B"
    return result


# 後方互換のためのエイリアス（過去にabc_mapsという名前で呼んでいた箇所があっても動くように）
abc_maps = sab_maps


def _recency_weighted_freq(df_window: pd.DataFrame, pick_count: int, pool_size: int, decay: float = 0.95) -> dict[int, float]:
    """df_window は降順（先頭ほど新しい）。新しい回ほど重みが大きい出現頻度を pool 内で0〜1正規化。"""
    cols = digit_cols(pick_count)
    weights = {n: 0.0 for n in range(1, pool_size + 1)}
    for i, (_, row) in enumerate(df_window.iterrows()):
        w = decay ** i
        for c in cols:
            v = row[c]
            if pd.notna(v):
                weights[int(v)] += w
    max_w = max(weights.values()) or 1.0
    return {n: v / max_w for n, v in weights.items()}


def _gap_balance_score(df_window: pd.DataFrame, pick_count: int, pool_size: int) -> dict[int, float]:
    """理論平均間隔に対する実際の空き具合をもとにした山型スコア（0〜1）。
    出た直後（gap比率<0.5）は低評価、gap比率1.0〜1.8あたりでピーク、
    極端に長期間出ていない数字（gap比率>3.5）は頭打ちにして過大評価しない。
    """
    cols = digit_cols(pick_count)
    expected_gap = pool_size / pick_count
    last_seen_idx: dict[int, int] = {}
    for i, (_, row) in enumerate(df_window.iterrows()):
        for c in cols:
            v = row[c]
            if pd.notna(v):
                n = int(v)
                if n not in last_seen_idx:
                    last_seen_idx[n] = i  # 0 = 直近回

    scores: dict[int, float] = {}
    for n in range(1, pool_size + 1):
        gap = last_seen_idx.get(n, len(df_window))  # 出てない数字は窓全体を空きとみなす
        ratio = gap / expected_gap
        if ratio < 0.5:
            score = ratio / 0.5 * 0.4  # 出たばかりは低評価（最大0.4）
        elif ratio <= 1.8:
            # 0.5〜1.8 の間で 0.4 -> 1.0 -> なだらかに山型
            score = 0.4 + 0.6 * (1 - abs(ratio - 1.15) / 0.65)
            score = max(0.4, min(1.0, score))
        elif ratio <= 3.5:
            score = 1.0 - 0.3 * (ratio - 1.8) / 1.7  # 徐々に下げる
        else:
            score = 0.55  # 極端な長期未出現は頭打ち（"ただ運が悪いだけ"を過大評価しない）
        scores[n] = max(0.0, min(1.0, score))
    return scores


def _last_digit_bonus(recency_freq: dict[int, float], pool_size: int) -> dict[int, float]:
    """末尾（1の位）が同じ数字グループの直近人気度を、そのグループ内の各数字へボーナスとして加点。
    例：末尾1のグループ（1,11,21,31,41）が全体的に直近よく出ていれば、そのグループ内の
    まだ目立っていない数字（例：41）にも「連動して出やすい」ボーナスを与える。
    """
    groups: dict[int, list[int]] = {}
    for n in range(1, pool_size + 1):
        groups.setdefault(n % 10, []).append(n)
    group_avg = {g: (sum(recency_freq[n] for n in ns) / len(ns)) for g, ns in groups.items()}
    max_avg = max(group_avg.values()) or 1.0
    return {n: group_avg[n % 10] / max_avg for n in range(1, pool_size + 1)}


# スコア合成の重み（調整しやすいようここにまとめる）
WEIGHT_RECENCY = 0.45
WEIGHT_GAP_BALANCE = 0.35
WEIGHT_LAST_DIGIT = 0.20


def tier_scores(df: pd.DataFrame, pool_size: int, pick_count: int, window: int = 50) -> dict[int, dict]:
    """数字ごとの合成スコアと内訳を返す。df は降順（最新が先頭）。
    戻り値: {n: {"score": float, "recency": float, "gap_balance": float, "last_digit": float}}
    """
    df_window = df.head(window)
    recency = _recency_weighted_freq(df_window, pick_count, pool_size)
    gap_balance = _gap_balance_score(df_window, pick_count, pool_size)
    last_digit = _last_digit_bonus(recency, pool_size)

    out = {}
    for n in range(1, pool_size + 1):
        score = (
            WEIGHT_RECENCY * recency[n]
            + WEIGHT_GAP_BALANCE * gap_balance[n]
            + WEIGHT_LAST_DIGIT * last_digit[n]
        )
        out[n] = {
            "score": score,
            "recency": recency[n],
            "gap_balance": gap_balance[n],
            "last_digit": last_digit[n],
        }
    return out


@dataclass
class TierResult:
    tier1: list[int]  # 1軍
    tier2: list[int]  # 2軍
    cut: list[int]  # 削除予定
    scores: dict[int, dict]


def classify_tiers(scores: dict[int, dict], pool_size: int, selected_count: int) -> TierResult:
    """スコア降順に並べ、上位 selected_count 個を厳選数字（1軍+2軍）、残りを削除予定とする。
    厳選数字の中で、隣接スコアの下落幅が最大になる箇所を境目に1軍/2軍を分割する
    （人数を固定しない）。
    """
    ranked = sorted(range(1, pool_size + 1), key=lambda n: scores[n]["score"], reverse=True)
    selected = ranked[:selected_count]
    cut = ranked[selected_count:]

    if len(selected) <= 1:
        return TierResult(tier1=list(selected), tier2=[], cut=cut, scores=scores)

    selected_scores = [scores[n]["score"] for n in selected]
    # 上位側(index 1〜len-1)の中で隣接差分が最大の位置を探す（境目が極端に偏らないよう
    # 全体の20%〜80%の範囲に限定）
    lo = max(1, int(len(selected) * 0.2))
    hi = max(lo + 1, int(len(selected) * 0.8))
    gaps = [(i, selected_scores[i - 1] - selected_scores[i]) for i in range(lo, min(hi, len(selected)))]
    if gaps:
        split_at = max(gaps, key=lambda t: t[1])[0]
    else:
        split_at = max(1, len(selected) // 2)

    tier1 = selected[:split_at]
    tier2 = selected[split_at:]
    return TierResult(tier1=tier1, tier2=tier2, cut=cut, scores=scores)


def pair_counts(df_recent: pd.DataFrame, pick_count: int) -> pd.DataFrame:
    """直近データでの数字ペア共起回数（上位順）。"""
    from collections import Counter
    from itertools import combinations

    cols = digit_cols(pick_count)
    counter: Counter = Counter()
    for _, row in df_recent.iterrows():
        nums = sorted(int(row[c]) for c in cols if pd.notna(row[c]))
        for a, b in combinations(nums, 2):
            counter[(a, b)] += 1
    rows = [{"ペア": f"{a}-{b}", "回数": c} for (a, b), c in counter.most_common()]
    return pd.DataFrame(rows)


def gap_table(df: pd.DataFrame, pick_count: int, pool_size: int) -> pd.DataFrame:
    """各数字の平均間隔・最終出現からの経過回数（df全体を使用、降順=最新が先頭）。"""
    cols = digit_cols(pick_count)
    rows = []
    for n in range(1, pool_size + 1):
        idxs = [i for i, (_, row) in enumerate(df.iterrows()) if n in {int(row[c]) for c in cols if pd.notna(row[c])}]
        if not idxs:
            rows.append({"数字": n, "最終出現からの回数": len(df), "平均間隔": None, "出現回数": 0})
            continue
        gaps = [idxs[i + 1] - idxs[i] for i in range(len(idxs) - 1)]
        avg_gap = round(sum(gaps) / len(gaps), 1) if gaps else None
        rows.append({"数字": n, "最終出現からの回数": idxs[0], "平均間隔": avg_gap, "出現回数": len(idxs)})
    return pd.DataFrame(rows).sort_values("最終出現からの回数", ascending=False).reset_index(drop=True)


def bucket_for_number(n: int, buckets: list[tuple[str, int, int]]) -> str:
    for label, lo, hi in buckets:
        if lo <= n <= hi:
            return label
    return buckets[-1][0]

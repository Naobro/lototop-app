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
from collections import Counter
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
    """各数字の平均間隔・最終出現からの経過回数（df全体を使用、降順=最新が先頭）。
    interval_analysis() の簡易版（後方互換のため残す）。"""
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


# ------------------------------------------------------------------
# 以下、元の pages/loto6_top.py・loto7_top.py・miniloto_top.py にあった
# 詳細分析を、pool_size/pick_count汎用の形で復元したもの。
# ------------------------------------------------------------------

def sab_annotated_draws(df_recent: pd.DataFrame, pick_count: int, smap: dict[int, str]) -> pd.DataFrame:
    """直近N回の当選番号表に、SAB構成・ひっぱり（前回との共通数）・連続数字の有無を付けた表。
    df_recent は新しい順（先頭が最新）。元のpages/loto6_top.pyの「直近24回の当選番号」相当。
    """
    cols = digit_cols(pick_count)
    rows = []
    draws = df_recent.reset_index(drop=True)
    for i in range(len(draws)):
        row = draws.iloc[i]
        nums = sorted(int(row[c]) for c in cols)
        tags = [smap.get(n, "-") for n in nums]
        sab_str = ",".join(tags)
        tag_counts = Counter(tags)
        sab_count_str = "".join(f"{k}{tag_counts[k]}" for k in ("S", "A", "B") if tag_counts.get(k))
        even_n = sum(1 for n in nums if n % 2 == 0)
        odd_n = len(nums) - even_n
        parity_str = f"奇{odd_n}・偶{even_n}"
        sum_val = sum(nums)
        has_cont = any(b - a == 1 for a, b in zip(nums, nums[1:]))
        if i >= len(draws) - 1:
            pulls_str = "-"
        else:
            prev_nums = {int(draws.iloc[i + 1][c]) for c in cols}
            pulls = len(set(nums) & prev_nums)
            pulls_str = f"{pulls}個" if pulls > 0 else "なし"
        rows.append({
            "回号": int(row["回号"]),
            "抽せん日": row["抽せん日"].strftime("%Y-%m-%d") if pd.api.types.is_datetime64_any_dtype(draws["抽せん日"]) else row["抽せん日"],
            **{c: int(row[c]) for c in cols},
            "SAB構成": sab_str,
            "SAB集計": sab_count_str,
            "偶奇": parity_str,
            "合計数字": sum_val,
            "ひっぱり": pulls_str,
            "連続": "あり" if has_cont else "なし",
        })
    return pd.DataFrame(rows)


def parity_summary(sab_annotated: pd.DataFrame, pick_count: int) -> tuple[pd.DataFrame, dict]:
    """sab_annotated_draws()の「偶奇」列から、パターン別出現回数表と全体の偶数/奇数比率を返す
    （numbers_common.parity_summary と対になるロト版）。"""
    pattern_counts = sab_annotated["偶奇"].value_counts()
    order = [f"奇{o}・偶{pick_count - o}" for o in range(pick_count, -1, -1)]
    pattern_table = pd.DataFrame({
        "パターン": order,
        "回数": [int(pattern_counts.get(p, 0)) for p in order],
    })
    total_slots = pick_count * len(sab_annotated)
    total_odd = sum(int(p.split("奇")[1].split("・")[0]) for p in sab_annotated["偶奇"])
    total_even = total_slots - total_odd
    overall = {
        "total_slots": total_slots,
        "even": total_even,
        "odd": total_odd,
        "even_pct": round(total_even / total_slots * 100, 1) if total_slots else 0,
        "odd_pct": round(total_odd / total_slots * 100, 1) if total_slots else 0,
    }
    return pattern_table, overall


def sum_range_distribution(sab_annotated: pd.DataFrame, pool_size: int, pick_count: int, n_bins: int = 4) -> pd.DataFrame:
    """合計数字（本数字の合計）の理論最小〜最大をn_bins個の等幅レンジに分け、
    直近N回がどのレンジに何回入ったかを集計する（numbers_common.sum_range_distribution のロト版）。"""
    min_sum = pick_count * (pick_count + 1) // 2
    max_sum = pick_count * pool_size - pick_count * (pick_count - 1) // 2
    sums = sab_annotated["合計数字"]
    edges = [round(min_sum + (max_sum - min_sum) * i / n_bins) for i in range(n_bins + 1)]
    labels, counts = [], []
    for i in range(n_bins):
        lo = edges[i] if i == 0 else edges[i] + 1
        hi = edges[i + 1]
        if i == 0:
            lo = edges[0]
        label = f"{lo}〜{hi}"
        cnt = int(((sums >= lo) & (sums <= hi)).sum())
        labels.append(label)
        counts.append(cnt)
    return pd.DataFrame({"合計値レンジ": labels, "回数": counts})


def sab_summary_stats(sab_annotated: pd.DataFrame, pick_count: int) -> dict:
    """sab_annotated_draws() の結果から、S/A/B割合・ひっぱり率・連続数字率を集計する。"""
    total_slots = pick_count * len(sab_annotated)
    counts = {"S": 0, "A": 0, "B": 0}
    for s in sab_annotated["SAB構成"]:
        for tag in s.split(","):
            if tag in counts:
                counts[tag] += 1
    pull_total = sum(1 for v in sab_annotated["ひっぱり"] if v not in ("-", "なし"))
    pull_denom = max(1, len(sab_annotated) - 1)
    cont_total = sum(1 for v in sab_annotated["連続"] if v == "あり")
    return {
        "s_pct": round(counts["S"] / total_slots * 100, 1) if total_slots else 0,
        "a_pct": round(counts["A"] / total_slots * 100, 1) if total_slots else 0,
        "b_pct": round(counts["B"] / total_slots * 100, 1) if total_slots else 0,
        "pull_rate": round(pull_total / pull_denom * 100, 1),
        "cont_rate": round(cont_total / len(sab_annotated) * 100, 1) if len(sab_annotated) else 0,
    }


def sab_bucket_breakdown(smap: dict[int, str], buckets: list[tuple[str, int, int]]) -> pd.DataFrame:
    """位（バケット）ごとに、S数字・A数字・B数字がそれぞれ何かを一覧にした表
    （元の「A数字・B数字の位別分類」に相当、Sも追加）。"""
    rows = []
    for label, lo, hi in buckets:
        in_range = [n for n in range(lo, hi + 1)]
        rows.append({
            "位": label,
            "S数字": ", ".join(str(n) for n in in_range if smap.get(n) == "S") or "-",
            "A数字": ", ".join(str(n) for n in in_range if smap.get(n) == "A") or "-",
            "B数字": ", ".join(str(n) for n in in_range if smap.get(n) == "B") or "-",
        })
    return pd.DataFrame(rows)


def bucket_top5(df_recent: pd.DataFrame, pick_count: int, buckets: list[tuple[str, int, int]]) -> pd.DataFrame:
    """各位（バケット）の出現回数TOP5（元の「各位の出現回数TOP5」）。"""
    cols = digit_cols(pick_count)
    groups: dict[str, list[int]] = {label: [] for label, _, _ in buckets}
    for c in cols:
        for v in df_recent[c]:
            if pd.notna(v):
                groups[bucket_for_number(int(v), buckets)].append(int(v))
    data = {}
    for label, _, _ in buckets:
        top5 = pd.Series(groups[label]).value_counts().head(5).index.tolist() if groups[label] else []
        while len(top5) < 5:
            top5.append(None)
        data[label] = top5
    return pd.DataFrame(data)


def position_top5(df_recent: pd.DataFrame, pick_count: int) -> pd.DataFrame:
    """第n数字（出目の順番）ごとの出現回数TOP5（元の「各数字の出現回数TOP5」）。"""
    cols = digit_cols(pick_count)
    results = {"順位": [f"{i}位" for i in range(1, 6)]}
    for c in cols:
        counts = df_recent[c].dropna().astype(int).value_counts().sort_values(ascending=False)
        top5 = counts.head(5)
        vals = [f"{n}（{cnt}回）" for n, cnt in zip(top5.index, top5.values)]
        while len(vals) < 5:
            vals.append("")
        results[c] = vals
    return pd.DataFrame(results)


def consecutive_pair_counts(df_recent: pd.DataFrame, pick_count: int) -> pd.DataFrame:
    """連続する2数字（例:5-6）が同じ抽せんに含まれた回数のランキング。"""
    cols = digit_cols(pick_count)
    counter: Counter = Counter()
    for _, row in df_recent.iterrows():
        nums = sorted(int(row[c]) for c in cols if pd.notna(row[c]))
        for a, b in zip(nums, nums[1:]):
            if b - a == 1:
                counter[f"{a}-{b}"] += 1
    rows = [{"連続ペア": k, "出現回数": v} for k, v in counter.most_common()]
    return pd.DataFrame(rows)


def frequency_100_vs_24(df: pd.DataFrame, pick_count: int, pool_size: int) -> pd.DataFrame:
    """直近100回・直近24回それぞれの出現回数・出現率・ランクを一覧にした表
    （元の「各数字の出現回数・出現率一覧」）。df は降順（最新が先頭）。"""
    cols = digit_cols(pick_count)

    def build(window: pd.DataFrame, cnt_label: str, rate_label: str, rank_label: str) -> pd.DataFrame:
        total = len(window)
        vals = window[cols].values.flatten()
        vals = pd.to_numeric(pd.Series(vals), errors="coerce").dropna().astype(int)
        counts = vals.value_counts().to_dict()
        rows = []
        for n in range(1, pool_size + 1):
            c = int(counts.get(n, 0))
            rate = round(c / total * 100, 1) if total else 0.0
            rows.append({"数字": n, cnt_label: c, rate_label: rate})
        out = pd.DataFrame(rows)
        ranked = out.sort_values(by=[cnt_label, rate_label, "数字"], ascending=[False, False, True]).reset_index(drop=True)
        ranked[rank_label] = range(1, len(ranked) + 1)
        return out.merge(ranked[["数字", rank_label]], on="数字", how="left")

    win100 = df.head(min(100, len(df)))
    win24 = df.head(min(24, len(df)))
    f100 = build(win100, "直近100回出現回数", "直近100回出現率", "100回ランク")
    f24 = build(win24, "直近24回出現回数", "直近24回出現率", "24回ランク")
    merged = f100.merge(f24, on="数字")
    merged["直近100回出現率"] = merged["直近100回出現率"].map(lambda x: f"{x:.1f}%")
    merged["直近24回出現率"] = merged["直近24回出現率"].map(lambda x: f"{x:.1f}%")
    return merged[["数字", "直近100回出現回数", "直近100回出現率", "100回ランク",
                   "直近24回出現回数", "直近24回出現率", "24回ランク"]]


def _detect_draw_weekdays(df: pd.DataFrame, top_n: int = 2) -> list[int]:
    """データから実際の抽せん曜日を自動検出する（loto6のMon/Thuのような
    ハードコードを避け、CSVの実際の抽せん日から判定する）。"""
    wd_counts = df["抽せん日"].dt.weekday.value_counts()
    threshold = max(3, len(df) * 0.1)
    return [int(wd) for wd, c in wd_counts.items() if c >= threshold][:top_n]


def interval_analysis(df: pd.DataFrame, pick_count: int, pool_size: int) -> pd.DataFrame:
    """各数字の出現間隔の詳細分析（元の「各数字の出現間隔分析一覧」相当）。
    df は降順（最新が先頭）で渡す。直近100回・直近12ヶ月・実際の抽せん曜日別の
    平均間隔、最大経過回数、直近5回の間隔、最後の出現からの経過回数・出現日を出す。
    """
    weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
    cols = digit_cols(pick_count)
    chrono = df.sort_values("抽せん日", ascending=True).reset_index(drop=True)
    win100 = chrono.tail(min(100, len(chrono))).reset_index(drop=True)

    latest_date = win100.iloc[-1]["抽せん日"]
    last12m = win100[win100["抽せん日"] >= latest_date - pd.DateOffset(months=12)].reset_index(drop=True)
    draw_weekdays = _detect_draw_weekdays(win100)
    per_weekday = {wd: win100[win100["抽せん日"].dt.weekday == wd].reset_index(drop=True) for wd in draw_weekdays}

    def hit_positions(source: pd.DataFrame, n: int) -> list[int]:
        return [i for i in range(len(source)) if n in {int(source.iloc[i][c]) for c in cols if pd.notna(source.iloc[i][c])}]

    def intervals(positions: list[int]) -> list[int]:
        return [positions[i] - positions[i - 1] for i in range(1, len(positions))]

    def avg(vals: list[int]) -> str:
        return str(round(sum(vals) / len(vals), 1)) if vals else "-"

    rows = []
    for n in range(1, pool_size + 1):
        pos100 = hit_positions(win100, n)
        iv100 = intervals(pos100)
        pos12 = hit_positions(last12m, n)
        iv12 = intervals(pos12)

        row = {
            "数字": n,
            "直近100回平均間隔": avg(iv100),
            "直近12ヶ月平均間隔": avg(iv12),
            "直近100回最大経過回数": str(max(iv100)) if iv100 else "-",
            "直近5回の出現間隔": "-".join(str(x) for x in reversed(iv100[-5:])) if iv100 else "-",
        }
        for wd in draw_weekdays:
            wpos = hit_positions(per_weekday[wd], n)
            wiv = intervals(wpos)
            row[f"{weekday_labels[wd]}曜日平均間隔"] = avg(wiv)

        if pos100:
            last_idx = pos100[-1]
            elapsed = len(win100) - 1 - last_idx
            row["最後の出現経過回数"] = "-" if elapsed == 0 else str(elapsed)
            row["一番最近の出現日"] = win100.iloc[last_idx]["抽せん日"].strftime("%Y-%m-%d")
        else:
            row["最後の出現経過回数"] = "-"
            row["一番最近の出現日"] = "-"
        rows.append(row)
    return pd.DataFrame(rows)


def pattern_analysis_table(df: pd.DataFrame, pick_count: int, buckets: list[tuple[str, int, int]], window: int = 24) -> pd.DataFrame:
    """直近window回について、各回の位パターン（例:1-10-10-20-20-30）の出現回数を集計した表。"""
    from loto_predict import historical_pattern_freq
    counter = historical_pattern_freq(df, pick_count, buckets, window=window)
    bucket_labels = [label for label, _, _ in buckets]

    def pattern_to_str(pattern: tuple[int, ...]) -> str:
        parts = []
        for label, count in zip(bucket_labels, pattern):
            parts.extend([label] * count)
        return "-".join(parts)

    rows = [{"パターン": pattern_to_str(p), "出現回数": c} for p, c in counter.most_common()]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# エリア分析：位置（第1〜第pick_count数字）×数字(1〜pool_size)のヒートマップ。
# 各位置の「エリア」＝その位置に実際に出現した数字の最小値〜最大値（データから動的算出）。
# ------------------------------------------------------------------

# 位置ごとの行配色（背景色, 文字色）。虹の並び（赤→紫）。
# pick_count=5(ミニロト)/6(ロト6)/7(ロト7) のいずれでも使えるよう7色分用意し、
# 少ない場合は均等に間引いて使う。
_RAINBOW_7 = [
    ("#E53935", "#ffffff"),  # 赤
    ("#FB8C00", "#ffffff"),  # オレンジ
    ("#FDD835", "#000000"),  # 黄（黒背景に黄文字は見えにくいため黒文字）
    ("#43A047", "#ffffff"),  # 緑
    ("#1E88E5", "#ffffff"),  # 青
    ("#7986CB", "#ffffff"),  # 藍
    ("#8E24AA", "#ffffff"),  # 紫
]
AREA_OUT_COLOR = "#1a1a1a"


def position_row_colors(pick_count: int) -> list[tuple[str, str]]:
    """pick_count個の行に、虹7色から均等間引きした配色を割り当てる。"""
    if pick_count == 7:
        return _RAINBOW_7
    if pick_count <= 1:
        return [_RAINBOW_7[0]]
    idxs = [round(i * (len(_RAINBOW_7) - 1) / (pick_count - 1)) for i in range(pick_count)]
    return [_RAINBOW_7[i] for i in idxs]


def position_frequency(df_recent: pd.DataFrame, pick_count: int, pool_size: int) -> list[dict]:
    """直近N回（df_recentに渡した範囲）について、位置（第1〜第pick_count数字、
    小さい順に並べた順位）ごとに、1〜pool_sizeの各数字が何回その位置に出現したかを集計する。
    各位置の「エリア」＝実際に出現した数字のmin〜max（0件ならNone）。
    戻り値: [{"position": 1, "counts": {num: count, ...}, "min": int|None, "max": int|None}, ...]
    """
    cols = digit_cols(pick_count)
    position_counts: list[dict[int, int]] = [dict() for _ in range(pick_count)]
    for _, row in df_recent.iterrows():
        nums = sorted(int(row[c]) for c in cols if pd.notna(row[c]))
        for i, n in enumerate(nums):
            position_counts[i][n] = position_counts[i].get(n, 0) + 1

    rows = []
    for i in range(pick_count):
        counts = position_counts[i]
        if counts:
            mn, mx = min(counts), max(counts)
        else:
            mn = mx = None
        rows.append({"position": i + 1, "counts": counts, "min": mn, "max": mx})
    return rows

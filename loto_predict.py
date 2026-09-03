"""
ロト6・ロト7・ミニロトの予想エンジン（パターン分類＋決定的な組み合わせ生成）。
=================================================
方針：
1. 過去の実データから「各位バケットに何個ずつ入っていたか」の分布を集計し、
   実際によく出ているパターンを優先する（発明した重みではなく実データ由来）。
2. 「同じ位が4個以上」に偏るレアパターンは最初から除外する。
3. 許可されたパターンの各バケットに、loto_common.classify_tiers で分類した
   1軍・2軍の数字を優先的に割り当て、乱数を使わず決定的にスコア降順で
   組み合わせを生成する（毎回同じ結果になる＝再現性を担保）。
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations, product

import loto_common as lcm


def historical_pattern_freq(df, pick_count: int, buckets: list[tuple[str, int, int]], window: int = 100) -> Counter:
    """過去 window 回の抽せんについて、各回の「バケットごとの個数タプル」の出現頻度を集計する。"""
    cols = lcm.digit_cols(pick_count)
    counter: Counter = Counter()
    for _, row in df.head(window).iterrows():
        nums = [int(row[c]) for c in cols if row[c] == row[c]]
        counts = [0] * len(buckets)
        for n in nums:
            for i, (label, lo, hi) in enumerate(buckets):
                if lo <= n <= hi:
                    counts[i] += 1
                    break
        counter[tuple(counts)] += 1
    return counter


def valid_bucket_patterns(pick_count: int, buckets: list[tuple[str, int, int]], max_per_bucket: int = 3) -> list[tuple[int, ...]]:
    """合計が pick_count になるバケット別個数パターンのうち、
    いずれかのバケットが4個以上を占めるレアパターンを除いたものを列挙する。
    """
    n_buckets = len(buckets)

    def rec(remaining_slots, remaining_total):
        if remaining_slots == 1:
            if 0 <= remaining_total <= max_per_bucket:
                yield (remaining_total,)
            return
        for k in range(0, min(max_per_bucket, remaining_total) + 1):
            for rest in rec(remaining_slots - 1, remaining_total - k):
                yield (k,) + rest

    return list(rec(n_buckets, pick_count))


def _bucket_candidates(bucket_range: tuple[int, int], tiers: lcm.TierResult, limit: int = 5) -> list[int]:
    """あるバケット範囲内の候補数字を、1軍優先→2軍の順にスコア降順で最大limit件返す。"""
    lo, hi = bucket_range
    in_range = lambda seq: [n for n in seq if lo <= n <= hi]
    t1 = sorted(in_range(tiers.tier1), key=lambda n: -tiers.scores[n]["score"])
    t2 = sorted(in_range(tiers.tier2), key=lambda n: -tiers.scores[n]["score"])
    return (t1 + t2)[:limit]


def explain_number(n: int, tiers: lcm.TierResult) -> str:
    s = tiers.scores[n]
    tier_label = "1軍" if n in tiers.tier1 else ("2軍" if n in tiers.tier2 else "削除予定")
    reasons = []
    if s["recency"] >= 0.6:
        reasons.append("直近の出現頻度が高い")
    if s["gap_balance"] >= 0.75:
        reasons.append("程よく間隔が空き「そろそろ」のタイミング")
    if s["last_digit"] >= 0.7:
        reasons.append(f"末尾{n % 10}のグループの調子が良い(連動パターン)")
    if not reasons:
        reasons.append("複合スコアでの選出")
    return f"{n}（{tier_label}／{'・'.join(reasons)}）"


def generate_predictions(df, pool_size: int, pick_count: int, buckets, tiers: lcm.TierResult,
                          n_combos: int = 20, per_bucket_limit: int = 6, max_patterns: int = 20,
                          diversity_cap_ratio: float = 0.45) -> list[dict]:
    """許可されたバケットパターンを実データ頻度順に優先し、1軍/2軍の数字で
    決定的に組み合わせを生成、合成スコア順に上位 n_combos 件を返す。
    各要素: {"combo": [...], "score": float, "pattern": (...), "reasons": [...]}
    """
    pattern_freq = historical_pattern_freq(df, pick_count, buckets)
    patterns = valid_bucket_patterns(pick_count, buckets)
    # 実データでの出現頻度が高いパターンを優先（未観測=0のパターンも許可はするが後回し）
    patterns.sort(key=lambda p: -pattern_freq.get(p, 0))

    bucket_ranges = [(lo, hi) for (_, lo, hi) in buckets]
    candidates_by_bucket = [_bucket_candidates(r, tiers, limit=per_bucket_limit) for r in bucket_ranges]

    all_combos: list[dict] = []
    seen_sets: set[frozenset] = set()

    # 上位パターン（実データでの出現頻度順）から、余裕を持った件数のパターンを使って
    # 候補バケット内の組み合わせを「全列挙」する（itertools.combinations の出力順に
    # 特定の数字が先頭に来やすい偏りがあるため、順序に頼らず全列挙してからスコアで
    # ソートする＝分散処理が正しく働くための前提条件）。
    patterns_to_use = patterns[:max_patterns]
    for pattern in patterns_to_use:
        # そのパターンを埋めるのに十分な候補数が各バケットに無ければスキップ
        if any(pattern[i] > len(candidates_by_bucket[i]) for i in range(len(pattern))):
            continue
        per_bucket_choice_lists = []
        for i, k in enumerate(pattern):
            if k == 0:
                per_bucket_choice_lists.append([()])
            else:
                per_bucket_choice_lists.append(list(combinations(candidates_by_bucket[i], k)))

        for combo_parts in product(*per_bucket_choice_lists):
            nums = tuple(sorted(x for part in combo_parts for x in part))
            if len(nums) != pick_count:
                continue
            key = frozenset(nums)
            if key in seen_sets:
                continue
            seen_sets.add(key)
            score = sum(tiers.scores[x]["score"] for x in nums)
            all_combos.append({"combo": list(nums), "score": score, "pattern": pattern,
                                "pattern_freq": pattern_freq.get(pattern, 0)})

    all_combos.sort(key=lambda c: -c["score"])

    # 分散処理：特定の数字ばかりに偏らないよう、各数字の登場回数に上限を設けて貪欲選択。
    # 上限を満たせず埋まらない場合は、上限を1件ずつ緩めて再選出する
    # （「上限を無視して無制限に補充」はしない＝偏り防止を最後まで保つ）。
    cap = max(2, int(n_combos * diversity_cap_ratio))
    selected: list[dict] = []
    while cap <= n_combos:
        usage: Counter = Counter()
        selected = []
        for c in all_combos:
            if len(selected) >= n_combos:
                break
            if any(usage[x] >= cap for x in c["combo"]):
                continue
            selected.append(c)
            for x in c["combo"]:
                usage[x] += 1
        if len(selected) >= min(n_combos, len(all_combos)):
            break
        cap += 1

    for c in selected:
        c["reasons"] = [explain_number(x, tiers) for x in c["combo"]]

    return selected[:n_combos]

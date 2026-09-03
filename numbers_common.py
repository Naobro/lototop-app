"""
ナンバーズ3 / ナンバーズ4 共通ユーティリティ
=================================================
両ゲームで重複していたデータ読み込み・集計ロジックを1箇所にまとめたもの。
digit_count（3 または 4）を渡すことで両ゲームに対応する。

このモジュールは「予想（AI/モデル）」を一切含まない。
無料公開ページ（pages/numbers3_top.py, pages/numbers4_top.py）専用の
統計・集計ロジックだけを置く。予想ロジックは numbers_predict.py 側。
"""
from __future__ import annotations

import pandas as pd
from collections import Counter


def digit_cols(digit_count: int) -> list[str]:
    return [f"第{i}数字" for i in range(1, digit_count + 1)]


def load_df(csv_path: str, digit_count: int) -> pd.DataFrame:
    """CSVを読み込み、型を整え、抽せん日の降順（最新が先頭）で返す。

    元のコードでは全角/半角カッコの正規化方向が関数によってバラバラだったため
    （'（'→'(' の関数と '('→'（' の関数が混在）、ここでは半角に統一する。
    """
    cols = digit_cols(digit_count)
    df = pd.read_csv(csv_path)
    df.columns = [c.replace("（", "(").replace("）", ")") for c in df.columns]
    df = df.dropna(subset=cols)
    df[cols] = df[cols].astype(int)
    df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
    df = df.dropna(subset=["抽せん日"]).sort_values("抽せん日", ascending=False).reset_index(drop=True)
    return df


def recent(df: pd.DataFrame, n: int = 24) -> pd.DataFrame:
    return df.head(min(n, len(df))).reset_index(drop=True)


# ------------------------------------------------------------------
# 出現ランキング
# ------------------------------------------------------------------
def ranking_series(df_recent: pd.DataFrame, digit_count: int) -> list[pd.Series]:
    """各桁について、0〜9の出現回数を多い順に並べたSeriesのリストを返す。"""
    cols = digit_cols(digit_count)
    return [
        df_recent[c].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False)
        for c in cols
    ]


def ranking_table(df_recent: pd.DataFrame, digit_count: int, top_n: int = 10) -> pd.DataFrame:
    cols = digit_cols(digit_count)
    rankings = ranking_series(df_recent, digit_count)
    data = {"順位": [f"{i + 1}位" for i in range(top_n)]}
    for i, c in enumerate(cols):
        data[c] = [f"{rankings[i].index[r]}（{rankings[i].iloc[r]}回）" for r in range(top_n)]
    return pd.DataFrame(data)


# ------------------------------------------------------------------
# ABC分類（出現頻度ランク）
# 元のコードは「A=1-4位/B=5-7位/C=8-10位」の関数と
# 「A=1-3位/B=4-6位/C=7-10位」の関数が同じファイル内に混在していた。
# ここでは A=1-3位・B=4-6位・C=7-10位 に統一する。
# S/A/B分類（ロト6/ロト7のページと同じ定義）
# ロトのページ（pages/loto6_top.py）は「直近24回での出現回数」そのものを
# しきい値にしていて、出現順位（何位か）ではない。
#   B_set = count >= 5         （最頻出）
#   A_set = 3 <= count <= 4    （中位）
#   それ以外(count <= 2)       （低頻出）
# ナンバーズでは呼び方をS/A/Bにそろえる: S=最頻出 / A=中位 / B=低頻出。
# ※ ナンバーズは1桁あたり0〜9の10種類しかなく、ロトの1〜37/43種類よりも
#   母数が少ないため、同じ「5回以上」でもSに入る数字の割合はロトより
#   高くなる（1桁24回中、平均は2.4回なので5回以上はロトより出やすい）。
#   しきい値そのものをロトと完全に揃える、という今回の指定を優先している。
# ------------------------------------------------------------------
def sab_maps(df_recent: pd.DataFrame, digit_count: int) -> list[dict[int, str]]:
    cols = digit_cols(digit_count)
    maps = []
    for c in cols:
        counts = df_recent[c].value_counts()
        m: dict[int, str] = {}
        for digit in range(10):
            cnt = int(counts.get(digit, 0))
            if cnt >= 5:
                m[digit] = "S"
            elif cnt >= 3:
                m[digit] = "A"
            else:
                m[digit] = "B"
        maps.append(m)
    return maps


def sab_annotated_table(df_recent: pd.DataFrame, digit_count: int, maps: list[dict[int, str]]) -> pd.DataFrame:
    """直近N回の当選番号表に、桁ごとのSAB分類列を付けたHTML表示用DataFrameを返す。"""
    cols = digit_cols(digit_count)
    df_disp = df_recent.copy()

    def colorize(x: str) -> str:
        return f'<span style="color:red;font-weight:bold">{x}</span>' if x == "S" else x

    def row_sab(row) -> str:
        parts = [colorize(maps[i].get(row[cols[i]], "-")) for i in range(digit_count)]
        return ",".join(parts)

    df_disp["SAB分類"] = df_disp.apply(row_sab, axis=1)
    show_cols = ["回号", "抽せん日"] + cols + ["SAB分類"]
    out = df_disp[show_cols].copy()
    if pd.api.types.is_datetime64_any_dtype(out["抽せん日"]):
        out["抽せん日"] = out["抽せん日"].dt.strftime("%Y-%m-%d")
    return out


def sab_stats_text(df_recent: pd.DataFrame, digit_count: int, maps: list[dict[int, str]]) -> tuple[str, dict, int]:
    cols = digit_cols(digit_count)
    counts = {"S": 0, "A": 0, "B": 0}
    for _, row in df_recent.iterrows():
        for i, c in enumerate(cols):
            v = int(row[c])
            counts[maps[i].get(v, "B")] += 1
    total = digit_count * len(df_recent)
    lines = ["=== SAB出現統計（直近{}回） ===".format(len(df_recent)),
             "S:直近24回で5回以上出現 / A:3〜4回 / B:2回以下（ロトのページと同じ定義）"]
    for k in ["S", "A", "B"]:
        pct = counts[k] / total * 100 if total else 0
        lines.append(f"{k}数字: {counts[k]}回 ({pct:.1f}%)")
    return "\n".join(lines), counts, total


# 旧名（後方互換のためのエイリアス）。新規コードは sab_* を使う。
abc_maps = sab_maps
abc_annotated_table = sab_annotated_table
abc_stats_text = sab_stats_text


# ------------------------------------------------------------------
# シングル / ダブル / トリプル（同じ数字の重複具合）
# ------------------------------------------------------------------
def type_counts(df_recent: pd.DataFrame, digit_count: int) -> dict[str, int]:
    cols = digit_cols(digit_count)
    result = {"シングル": 0, "ダブル": 0, "トリプル": 0, "ボックス(4つ同数字)": 0}
    for _, row in df_recent.iterrows():
        nums = [int(row[c]) for c in cols]
        counter = Counter(nums)
        max_dup = max(counter.values())
        n_unique = len(counter)
        if digit_count == 4:
            if max_dup >= 4:
                result["ボックス(4つ同数字)"] += 1
            elif max_dup == 3:
                result["トリプル"] += 1
            elif max_dup == 2:
                result["ダブル"] += 1
            else:
                result["シングル"] += 1
        else:  # digit_count == 3
            if max_dup == 3:
                result["トリプル"] += 1
            elif max_dup == 2:
                result["ダブル"] += 1
            else:
                result["シングル"] += 1
    if digit_count != 4:
        del result["ボックス(4つ同数字)"]
    return result


# ------------------------------------------------------------------
# ひっぱり（前回と同じ数字を含むか）
# ------------------------------------------------------------------
def hoppari_count(df_recent: pd.DataFrame, digit_count: int) -> int:
    cols = digit_cols(digit_count)
    count = 0
    for i in range(len(df_recent) - 1):
        cur = set(int(df_recent.iloc[i][c]) for c in cols)
        prev = set(int(df_recent.iloc[i + 1][c]) for c in cols)
        if cur & prev:
            count += 1
    return count


# ------------------------------------------------------------------
# 数字の範囲分布（0-2 / 3-5 / 6-9）
# ------------------------------------------------------------------
def range_distribution(df_recent: pd.DataFrame, digit_count: int) -> dict[str, int]:
    cols = digit_cols(digit_count)
    result = {"A (0-2)": 0, "B (3-5)": 0, "C (6-9)": 0}
    for _, row in df_recent.iterrows():
        for c in cols:
            n = int(row[c])
            if 0 <= n <= 2:
                result["A (0-2)"] += 1
            elif 3 <= n <= 5:
                result["B (3-5)"] += 1
            else:
                result["C (6-9)"] += 1
    return result


# ------------------------------------------------------------------
# NEW: 偶数・奇数の比率
# ------------------------------------------------------------------
def parity_per_draw(df_recent: pd.DataFrame, digit_count: int) -> pd.DataFrame:
    """各回ごとに 偶数がいくつ・奇数がいくつ出たかの内訳表。"""
    cols = digit_cols(digit_count)
    rows = []
    for _, row in df_recent.iterrows():
        nums = [int(row[c]) for c in cols]
        even = sum(1 for n in nums if n % 2 == 0)
        odd = digit_count - even
        rows.append({
            "回号": int(row["回号"]),
            "抽せん日": row["抽せん日"].strftime("%Y-%m-%d") if pd.api.types.is_datetime64_any_dtype(df_recent["抽せん日"]) else row["抽せん日"],
            "偶数": even,
            "奇数": odd,
            "パターン": f"偶{even}・奇{odd}",
        })
    return pd.DataFrame(rows)


def parity_summary(parity_df: pd.DataFrame, digit_count: int) -> tuple[pd.DataFrame, dict]:
    """パターン（例:偶4奇0）ごとの出現回数の表と、全体の偶数/奇数の比率を返す。"""
    pattern_counts = parity_df["パターン"].value_counts()
    # 表示順を「偶数の数」が多い順に整える
    order = [f"偶{e}・奇{digit_count - e}" for e in range(digit_count, -1, -1)]
    pattern_table = pd.DataFrame({
        "パターン": order,
        "回数": [int(pattern_counts.get(p, 0)) for p in order],
    })
    total_slots = digit_count * len(parity_df)
    total_even = int(parity_df["偶数"].sum())
    total_odd = total_slots - total_even
    overall = {
        "total_slots": total_slots,
        "even": total_even,
        "odd": total_odd,
        "even_pct": (total_even / total_slots * 100) if total_slots else 0,
        "odd_pct": (total_odd / total_slots * 100) if total_slots else 0,
    }
    return pattern_table, overall


# ------------------------------------------------------------------
# 合計値の分布 と NEW: 合計値のレンジ分布
# ------------------------------------------------------------------
def sum_series(df_recent: pd.DataFrame, digit_count: int) -> pd.Series:
    cols = digit_cols(digit_count)
    return df_recent[cols].sum(axis=1)


def sum_value_counts(df_recent: pd.DataFrame, digit_count: int) -> pd.DataFrame:
    sums = sum_series(df_recent, digit_count)
    counts = Counter(sums.tolist())
    df = pd.DataFrame(counts.items(), columns=["合計値", "出現回数"]).sort_values(
        by="出現回数", ascending=False
    ).reset_index(drop=True)
    return df


def sum_range_distribution(df_recent: pd.DataFrame, digit_count: int, n_bins: int = 3) -> pd.DataFrame:
    """合計値（0 〜 9×桁数）を n_bins 個の等幅レンジに分け、直近N回がどのレンジに
    何回入ったかを集計する。例: 4桁なら 0〜36 を 0-12 / 13-24 / 25-36 の3レンジに分割。
    """
    max_sum = 9 * digit_count
    sums = sum_series(df_recent, digit_count)
    edges = [round(max_sum * i / n_bins) for i in range(n_bins + 1)]
    labels = []
    counts = []
    for i in range(n_bins):
        lo = edges[i] if i == 0 else edges[i] + 1
        hi = edges[i + 1]
        if i == 0:
            lo = 0
        label = f"{lo}〜{hi}"
        cnt = int(((sums >= lo) & (sums <= hi)).sum())
        labels.append(label)
        counts.append(cnt)
    return pd.DataFrame({"合計値レンジ": labels, "回数": counts})


# ------------------------------------------------------------------
# ペア出現（2つの数字の組み合わせ）
# ------------------------------------------------------------------
def pair_counts(df_recent: pd.DataFrame, digit_count: int) -> pd.DataFrame:
    cols = digit_cols(digit_count)
    counter = Counter()
    for _, row in df_recent.iterrows():
        nums = [int(row[c]) for c in cols]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair = tuple(sorted([nums[i], nums[j]]))
                counter[pair] += 1
    df = pd.DataFrame(counter.items(), columns=["ペア", "出現回数"]).sort_values(
        by="出現回数", ascending=False
    ).reset_index(drop=True)
    return df

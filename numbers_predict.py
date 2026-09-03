"""
ナンバーズ3 / ナンバーズ4 予想エンジン（有料note用に切り離したロジック）
=================================================================
pages/ 配下の無料公開ページからは一切importしない。
predict_report_numbers3.py / predict_report_numbers4.py からのみ使う。

【今回のバグ修正まとめ】
1. マルコフ連鎖の遷移方向が逆だったのを修正。
   元のコードは df が「新しい順」に並んでいる状態で
   trans[series[i]][series[i+1]] を集計していたため、
   実際には「直前に何が出ていたか」を学習してしまっていた
   （＝「次に何が出るか」の逆）。ここでは内部で時系列を古い順に
   並べ直してから遷移を数える。
2. evaluate_hit_rate が RF/NN/風車盤を実際には評価しておらず、
   単純な頻出数字（value_counts）を3つの名前で重複計算していただけ
   だったのを、実際に過去データでウォークフォワード検証する方式に
   置き換えた（walk_forward_backtest）。あわせて「ランダムに3つ
   選んだ場合の理論的中率(30%)」も比較として出せるようにした。
3. 合算TOP5の生成が random.choices によるものだったため、
   同じデータでも実行のたびに結果が変わっていた（再現性なし）。
   ここでは重みスコア×同時確率で決定的にTOP5組み合わせを選ぶ
   （itertools.product による全探索、乱数を使わない）。
4. RF/NN/マルコフ/風車盤の学習をStreamlitの再実行のたびに毎回
   やり直していたのをやめ、このモジュールはStreamlitに依存しない
   純粋なロジックとして切り出した（呼び出し側でキャッシュしやすい）。
"""
from __future__ import annotations

import itertools
from collections import Counter, defaultdict

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from numbers_common import digit_cols, recent as nc_recent, sab_maps as nc_sab_maps

# 桁数ごとの風車盤パターン（元のnumbers3_top.py / numbers4_top.pyの値を踏襲）
WHEELS_BY_DIGIT: dict[int, list[list[int]]] = {
    3: [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
        [0, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    ],
    4: [
        [0, 3, 6, 9, 2, 5, 8, 1, 4, 7],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [0, 7, 4, 1, 8, 5, 2, 9, 6, 3],
        [0, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    ],
}

MODEL_NAMES = {"RF": "ランダムフォレスト", "NN": "ニューラルネット", "MC": "マルコフ連鎖", "WH": "風車盤"}


# ------------------------------------------------------------------
# マルコフ連鎖（方向修正版）
# ------------------------------------------------------------------
def markov_top3(series_desc: list[int], top_n: int = 3) -> list[int]:
    """series_desc: 新しい順（先頭が最新）の出目リスト。
    「直近の出目の次に何が出やすいか」を過去の遷移から求める。
    """
    if not series_desc:
        return []
    chrono = list(reversed(series_desc))  # 古い→新しい に変換
    trans: dict[int, Counter] = defaultdict(Counter)
    for i in range(len(chrono) - 1):
        trans[chrono[i]][chrono[i + 1]] += 1
    last = series_desc[0]
    return [n for n, _ in trans[last].most_common(top_n)]


def wheel_top3(series_desc: list[int], wheel: list[int], top_n: int = 3) -> list[int]:
    count = Counter()
    for val in series_desc:
        if val in wheel:
            count[wheel.index(val)] += 1
    top_pos = [p for p, _ in count.most_common(top_n)]
    return [wheel[p] for p in top_pos if p < len(wheel)]


# ------------------------------------------------------------------
# RF / NN
# ------------------------------------------------------------------
def _build_xy(df_window_desc: pd.DataFrame, digit_count: int):
    """df_window_desc: 新しい順のDataFrame。
    内部で古い順に並べ替えてから (前回の出目 -> 次回の出目) の学習データを作る。
    """
    cols = digit_cols(digit_count)
    chrono = df_window_desc.sort_values("抽せん日").reset_index(drop=True)
    X, ys = [], [[] for _ in range(digit_count)]
    for i in range(len(chrono) - 1):
        prev = chrono.iloc[i]
        curr = chrono.iloc[i + 1]
        X.append([prev[c] for c in cols])
        for j in range(digit_count):
            ys[j].append(curr[cols[j]])
    return X, ys


def _top3_from_proba(model, x_query, top_n: int = 3) -> list[int]:
    probs = model.predict_proba([x_query])[0]
    classes = model.classes_
    pairs = sorted(zip(classes, probs), key=lambda t: -t[1])[:top_n]
    return [int(c) for c, _ in pairs]


def run_models_for_window(df_window_desc: pd.DataFrame, digit_count: int) -> dict[str, list[list[int]]]:
    """新しい順のDataFrame(ある時点までのデータ)を受け取り、
    RF/NN/マルコフ/風車盤それぞれの桁別TOP3を返す。
    """
    cols = digit_cols(digit_count)
    wheels = WHEELS_BY_DIGIT[digit_count]
    X, ys = _build_xy(df_window_desc, digit_count)
    latest_input = [df_window_desc.iloc[0][c] for c in cols]

    rf_top3, nn_top3, mc_top3, wh_top3 = [], [], [], []
    for j in range(digit_count):
        if len(X) >= 5:
            try:
                rf = RandomForestClassifier(n_estimators=50, random_state=42)
                rf.fit(X, ys[j])
                rf_top3.append(_top3_from_proba(rf, latest_input))
            except Exception:
                rf_top3.append([])
            try:
                nn = MLPClassifier(max_iter=300, random_state=42)
                nn.fit(X, ys[j])
                nn_top3.append(_top3_from_proba(nn, latest_input))
            except Exception:
                nn_top3.append([])
        else:
            rf_top3.append([])
            nn_top3.append([])
        series_desc = df_window_desc[cols[j]].tolist()
        mc_top3.append(markov_top3(series_desc))
        wh_top3.append(wheel_top3(series_desc, wheels[j]))
    return {"RF": rf_top3, "NN": nn_top3, "MC": mc_top3, "WH": wh_top3}


# ------------------------------------------------------------------
# ウォークフォワード バックテスト（本物の的中率評価）
# ------------------------------------------------------------------
def walk_forward_backtest(
    df_desc: pd.DataFrame,
    digit_count: int,
    window: int = 24,
    min_history: int = 30,
) -> dict:
    """直近 window 回それぞれについて、その回より古いデータだけを使って
    各モデルのTOP3を再現し、実際の当せん数字がTOP3に入っていたかを集計する。
    データが不足している場合は検証可能な範囲だけ実行する。
    """
    cols = digit_cols(digit_count)
    n = len(df_desc)
    eval_count = max(0, min(window, n - min_history))
    hits = {m: [0] * digit_count for m in ["RF", "NN", "MC", "WH"]}
    tested = 0
    for k in range(eval_count):
        target_row = df_desc.iloc[k]
        history = df_desc.iloc[k + 1:]
        if len(history) < min_history:
            continue
        result = run_models_for_window(history, digit_count)
        for m in hits:
            for j in range(digit_count):
                if int(target_row[cols[j]]) in result[m][j]:
                    hits[m][j] += 1
        tested += 1

    summary = {}
    for m in hits:
        total_checks = tested * digit_count
        total_hits = sum(hits[m])
        summary[m] = {
            "hits_by_digit": hits[m],
            "tested": tested,
            "hit_rate_pct": (total_hits / total_checks * 100) if total_checks else 0.0,
        }
    summary["RANDOM"] = {"hit_rate_pct": 30.0, "tested": tested, "note": "TOP3をランダムに選んだ場合の理論値(3/10)"}
    return summary


# ------------------------------------------------------------------
# 複数時間窓 × 複数モデルの合算スコア
# ------------------------------------------------------------------
def build_dfs_map(df_desc: pd.DataFrame) -> dict[str, tuple[pd.DataFrame, float]]:
    return {
        "全データ": (df_desc, 0.1),
        "直近100回": (df_desc.head(min(100, len(df_desc))), 0.3),
        "直近24回": (df_desc.head(min(24, len(df_desc))), 0.6),
    }


def combined_digit_scores(
    df_desc: pd.DataFrame,
    digit_count: int,
    model_weights: dict[str, float],
) -> tuple[list[Counter], dict[str, dict]]:
    dfs_map = build_dfs_map(df_desc)
    scores = [Counter() for _ in range(digit_count)]
    results_by_label: dict[str, dict] = {}
    for label, (data, window_weight) in dfs_map.items():
        if len(data) < 10:
            continue
        result = run_models_for_window(data, digit_count)
        results_by_label[label] = result
        for j in range(digit_count):
            for model_key in ["RF", "NN", "MC", "WH"]:
                w = model_weights.get(model_key, 1.0)
                for rank, num in enumerate(result[model_key][j]):
                    scores[j][num] += (3 - rank) * window_weight * w
    return scores, results_by_label


def top_joint_combinations(
    scores: list[Counter],
    digit_count: int,
    top_k_per_digit: int = 8,
    n_results: int = 20,
    max_dup: int = 2,
) -> list[tuple[tuple[int, ...], float]]:
    """桁ごとのスコア上位候補から、重複しすぎない組み合わせを
    スコア合計が高い順に決定的に選ぶ（乱数を使わないので再現性がある）。
    """
    candidates = []
    for j in range(digit_count):
        top = [n for n, _ in scores[j].most_common(top_k_per_digit)]
        candidates.append(top if top else list(range(10)))

    scored_combos = []
    for combo in itertools.product(*candidates):
        if max(Counter(combo).values()) > max_dup:
            continue
        total_score = sum(scores[j].get(combo[j], 0) for j in range(digit_count))
        scored_combos.append((combo, total_score))
    scored_combos.sort(key=lambda t: -t[1])

    # 同スコアの重複を除きつつ上位n_resultsを取る
    seen = set()
    out = []
    for combo, score in scored_combos:
        if combo in seen:
            continue
        seen.add(combo)
        out.append((combo, score))
        if len(out) >= n_results:
            break
    return out


def combo_type_label(combo: tuple[int, ...]) -> str:
    max_dup = max(Counter(combo).values())
    if max_dup >= 4:
        return "ボックス(4つ同数字)"
    if max_dup == 3:
        return "トリプル"
    if max_dup == 2:
        return "ダブル"
    return "シングル"


def explain_combo(
    combo: tuple[int, ...],
    digit_count: int,
    reasoning_result: dict[str, list[list[int]]],
    sab_maps_list: list[dict[int, str]],
) -> tuple[str, str, list[str]]:
    """1つの組み合わせについて、
    - SABパターン文字列（例: "ASAA"）
    - タイプ（シングル/ダブル/トリプル/ボックス）
    - 桁ごとの選出根拠（どのモデルがTOP3に入れていたか＋SAB分類）
    を返す。reasoning_result は combined_digit_scores が返す
    results_by_label のうち、根拠として使う1つの時間窓（通常「直近24回」）。
    """
    sab_pattern = ""
    reasons = []
    for j in range(digit_count):
        digit = combo[j]
        sab = sab_maps_list[j].get(digit, "B")
        sab_pattern += sab
        hits = [MODEL_NAMES[mk] for mk in ["RF", "NN", "MC", "WH"] if digit in reasoning_result[mk][j]]
        hit_text = "・".join(hits) if hits else "直近24回では上位圏外（他の時間窓のスコアで選出）"
        reasons.append(f"第{j + 1}数字={digit}（SAB:{sab}／{hit_text}がTOP3に選出）")
    type_label = combo_type_label(combo)
    return sab_pattern, type_label, reasons


# ------------------------------------------------------------------
# note公開用レポートテキスト
# ------------------------------------------------------------------
def build_prediction_report_text(
    df_desc: pd.DataFrame, digit_count: int, n_combos: int = 20
) -> tuple[str, list[tuple[tuple[int, ...], float]], dict, list[dict]]:
    cols = digit_cols(digit_count)
    latest_round = int(df_desc.iloc[0]["回号"])
    next_round = latest_round + 1
    prev_winning = "".join(str(int(df_desc.iloc[0][c])) for c in cols)

    backtest = walk_forward_backtest(df_desc, digit_count)
    model_weights = {m: backtest[m]["hit_rate_pct"] / 100 for m in ["RF", "NN", "MC", "WH"]}
    # 全モデルが0（学習データ不足等）の場合に備えて均等ウェイトへフォールバック
    if sum(model_weights.values()) == 0:
        model_weights = {m: 1.0 for m in model_weights}

    scores, results_by_label = combined_digit_scores(df_desc, digit_count, model_weights)
    top5_by_digit = [[n for n, _ in scores[j].most_common(5)] for j in range(digit_count)]
    joint_top_combos = top_joint_combinations(scores, digit_count, n_results=n_combos)

    # 根拠説明には「直近24回」窓の各モデルTOP3を使う（一番重みが高く、直感的にも説明しやすいため）
    reasoning_result = results_by_label.get("直近24回") or next(iter(results_by_label.values()))
    sab_maps_list = nc_sab_maps(nc_recent(df_desc, 24), digit_count)

    combo_explanations: list[dict] = []
    for combo, score in joint_top_combos:
        sab_pattern, type_label, reasons = explain_combo(combo, digit_count, reasoning_result, sab_maps_list)
        combo_explanations.append({
            "combo": combo,
            "score": score,
            "sab_pattern": sab_pattern,
            "type": type_label,
            "sum": sum(combo),
            "reasons": reasons,
        })

    lines = []
    lines.append(f"【ナンバーズ{digit_count} 予想レポート（note公開用）】")
    lines.append(f"対象: 第{next_round}回（前回 第{latest_round}回 当選番号 {prev_winning}）")
    lines.append("")
    lines.append("=== 各モデルの直近バックテスト的中率（TOP3に実際の数字が入っていたか） ===")
    lines.append(f"※ 検証回数: 直近{backtest['RF']['tested']}回 / ランダムにTOP3を選んだ場合の理論値: 30.0%")
    for m in ["RF", "NN", "MC", "WH"]:
        lines.append(f"  {MODEL_NAMES[m]:<10} 的中率 {backtest[m]['hit_rate_pct']:.1f}%")
    lines.append("")

    lines.append("=== 各モデルTOP3（桁別・直近データより） ===")
    for label, result in results_by_label.items():
        lines.append(f"【{label}】")
        for model_key in ["RF", "NN", "MC", "WH"]:
            tops = result[model_key]
            row = " / ".join(
                f"第{i + 1}:{','.join(map(str, tops[i])) if tops[i] else '-'}" for i in range(digit_count)
            )
            lines.append(f"  {MODEL_NAMES[model_key]:<10} {row}")
        lines.append("")

    lines.append("=== 桁別 合算スコアTOP5 ===")
    header = "順位  " + "  ".join(cols)
    lines.append(header)
    for rank in range(5):
        vals = [str(top5_by_digit[j][rank]) if rank < len(top5_by_digit[j]) else "-" for j in range(digit_count)]
        lines.append(f"{rank + 1}位   " + "   ".join(vals))
    lines.append("")

    lines.append(f"=== 組み合わせ合算TOP{len(combo_explanations)}（重複しすぎる組は除外・決定的に算出／根拠つき） ===")
    for rank, ce in enumerate(combo_explanations, 1):
        num_str = "".join(map(str, ce["combo"]))
        lines.append(
            f"{rank}位: {num_str}（SAB:{ce['sab_pattern']} {ce['type']}, 合計:{ce['sum']}, スコア:{ce['score']:.2f}）"
        )
        for r in ce["reasons"]:
            lines.append(f"    - {r}")

    text = "\n".join(lines)
    joint_top_combos_out = [(ce["combo"], ce["score"]) for ce in combo_explanations]
    return text, joint_top_combos_out, backtest, combo_explanations

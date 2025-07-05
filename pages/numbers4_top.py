import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

check_password()
st.set_page_config(layout="centered")

import ssl
import pandas as pd
import random
import html

from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.exceptions import NotFittedError

CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"

def format_number(val):
    try:
        return f"{int(float(val)):,}"
    except:
        return "未定義"

# 最新表示 + df_recent抽出 + 表示
def show_latest_results(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.replace("(", "（").replace(")", "）") for col in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("未定義")
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])
        df = df.sort_values(by="抽せん日", ascending=False).reset_index(drop=True)

        latest = df.iloc[0]
        global df_recent
        df_recent = df[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字"]].head(24)

        number_str = f"{latest['第1数字']}{latest['第2数字']}{latest['第3数字']}{latest['第4数字']}"

        st.header("最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(latest['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽せん日</td>
                <td style="padding: 10px; font-size: 20px;">{latest['抽せん日'].strftime('%Y-%m-%d')}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {number_str}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ストレート</td>
                <td colspan="2">{format_number(latest['ストレート口数'])}口</td>
                <td>{format_number(latest['ストレート当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ボックス</td>
                <td colspan="2">{format_number(latest['ボックス口数'])}口</td>
                <td>{format_number(latest['ボックス当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ストレート</td>
                <td colspan="2">{format_number(latest['セット（ストレート）口数'])}口</td>
                <td>{format_number(latest['セット（ストレート）当選金額'])}円</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ボックス</td>
                <td colspan="2">{format_number(latest['セット（ボックス）口数'])}口</td>
                <td>{format_number(latest['セット（ボックス）当選金額'])}円</td>
            </tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.error(f"エラー詳細: {type(e)}")

# 最新結果と df_recent 定義
show_latest_results(CSV_PATH)

import pandas as pd
import streamlit as st

st.header("直近24回の当選番号（ABC分類付き）")

def generate_recent_numbers4_table(csv_path):
    try:
        # CSV読み込みと整形
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["第1数字", "第2数字", "第3数字", "第4数字"])
        df[["第1数字", "第2数字", "第3数字", "第4数字"]] = df[["第1数字", "第2数字", "第3数字", "第4数字"]].astype(int)
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce").dt.strftime("%Y-%m-%d")

        # 直近24回に絞る
        df_recent = df.sort_values("回号", ascending=False).head(24).reset_index(drop=True)

        # ABC分類マップ作成（各桁ごと）
        def get_abc_rank_map(series):
            counts = series.value_counts().sort_values(ascending=False)
            digits = counts.index.tolist()
            abc_map = {}
            for i, num in enumerate(digits[:10]):
                if i < 4:
                    abc_map[num] = "A"
                elif i < 7:
                    abc_map[num] = "B"
                else:
                    abc_map[num] = "C"
            return abc_map

        abc_map_1 = get_abc_rank_map(df_recent["第1数字"])
        abc_map_2 = get_abc_rank_map(df_recent["第2数字"])
        abc_map_3 = get_abc_rank_map(df_recent["第3数字"])
        abc_map_4 = get_abc_rank_map(df_recent["第4数字"])

        # ABC分類列（Aだけ赤文字で強調）
        def abc_with_color(d1, d2, d3, d4):
            def colorize(x):
                return f'<span style="color:red;font-weight:bold">{x}</span>' if x == "A" else x
            a1 = colorize(abc_map_1.get(d1, "-"))
            a2 = colorize(abc_map_2.get(d2, "-"))
            a3 = colorize(abc_map_3.get(d3, "-"))
            a4 = colorize(abc_map_4.get(d4, "-"))
            return f"{a1},{a2},{a3},{a4}"

        df_recent["ABC分類"] = df_recent.apply(
            lambda row: abc_with_color(
                row["第1数字"], row["第2数字"], row["第3数字"], row["第4数字"]
            ),
            axis=1
        )

        # 表示テーブル（HTML形式）
        df_display = df_recent[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字", "ABC分類"]]
        st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# 実行
numbers4_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"
generate_recent_numbers4_table(numbers4_csv_path)
# ③ 各桁の出現ランキング
st.header("各桁の出現ランキング")
try:
    ranking_df = pd.DataFrame({
        "順位": [f"{i+1}位" for i in range(10)],
        "第1数字": df_recent["第1数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第2数字": df_recent["第2数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第3数字": df_recent["第3数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
        "第4数字": df_recent["第4数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
    })
    st.dataframe(ranking_df, use_container_width=True)
except Exception as e:
    st.error(f"ランキングの表示に失敗しました: {e}")


st.header("AIによる次回数字予測（ナンバーズ4）")

def show_ai_predictions_n4(csv_path):
    try:
        # CSV読み込みと整形
        df = pd.read_csv(csv_path)
        df = df.loc[
            df["第1数字"].notnull() &
            df["第2数字"].notnull() &
            df["第3数字"].notnull() &
            df["第4数字"].notnull()
        ]
        df = df.dropna(subset=["第1数字", "第2数字", "第3数字", "第4数字"])
        df[["第1数字", "第2数字", "第3数字", "第4数字"]] = df[["第1数字", "第2数字", "第3数字", "第4数字"]].astype(int)
        
        # 最新データの直後を予測対象とする
        latest = [int(df.iloc[0][f"第{i}数字"]) for i in range(1, 5)]

        # 学習データと正解ラベルを作成
        X = []
        y = {i: [] for i in range(1, 5)}
        for i in range(len(df) - 1):
            row = [int(df.iloc[i][f"第{j}数字"]) for j in range(1, 5)]
            next_row = [int(df.iloc[i + 1][f"第{j}数字"]) for j in range(1, 5)]
            X.append(row)
            for j in range(1, 5):
                y[j].append(next_row[j - 1])

        # モデル定義
        rf_models = {i: RandomForestClassifier() for i in range(1, 5)}
        nn_models = {i: MLPClassifier(max_iter=1000, random_state=42) for i in range(1, 5)}

        # 学習
        for i in range(1, 5):
            rf_models[i].fit(X, y[i])
            nn_models[i].fit(X, y[i])

        # 予測（出力をintで整形）
        rf_pred = [int(rf_models[i].predict([latest])[0]) for i in range(1, 5)]
        nn_pred = [int(nn_models[i].predict([latest])[0]) for i in range(1, 5)]

        # マルコフ連鎖的予測（最頻値）
        next_numbers = list(zip(*X))[0]
        mc_pred = []
        for i in range(1, 5):
            nexts = []
            for j in range(len(X)):
                if X[j] == latest:
                    nexts.append(y[i][j])
            if nexts:
                mc_pred.append(Counter(nexts).most_common(1)[0][0])
            else:
                mc_pred.append(random.choice(range(10)))  # fallback

        # 表示
        st.subheader("🔍 AIモデル予測（次に来る数字の予測）")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 🌲 ランダムフォレスト")
            st.write(rf_pred)
        with col2:
            st.markdown("#### 🧠 ニューラルネット")
            st.write(nn_pred)
        with col3:
            st.markdown("#### 🔁 マルコフ連鎖")
            st.write(mc_pred)

    except Exception as e:
        st.error("AI予測中にエラーが発生しました")
        st.error(str(e))

st.header("AIによる次回数字予測（ナンバーズ4）")
show_ai_predictions_n4("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/n4.csv")

# ④ W/S/T カウント
st.subheader("シングル・ダブル・トリプル分析")
s = d = t = 0
for _, row in df_recent.iterrows():
    cnts = Counter([row[f"第{i}数字"] for i in range(1, 5)])
    vals = list(cnts.values())
    if 3 in vals:
        t += 1
    elif vals.count(2) == 1:
        d += 1
    else:
        s += 1
st.write(pd.DataFrame({
    "タイプ": ["シングル", "ダブル", "トリプル"],
    "回数": [s, d, t]
}))

# ⑤ ひっぱり数字
st.subheader("ひっぱり数字の回数")
hoppari = 0
for i in range(1, len(df_recent)):
    prev = set(df_recent.iloc[i - 1][[f"第{n}数字" for n in range(1, 5)]])
    curr = set(df_recent.iloc[i][[f"第{n}数字" for n in range(1, 5)]])
    if prev & curr:
        hoppari += 1
st.write(f"ひっぱり数字の回数：{hoppari} 回")
# ⑥ 数字の範囲分布
st.subheader("⑥ 数字の範囲ごとの分布")
range_counts = {'0-2': 0, '3-5': 0, '6-9': 0}
for _, row in df_recent.iterrows():
    for i in range(1, 5):
        num = row[f"第{i}数字"]
        if num <= 2:
            range_counts['0-2'] += 1
        elif num <= 5:
            range_counts['3-5'] += 1
        else:
            range_counts['6-9'] += 1
st.write(pd.DataFrame({
    "範囲": list(range_counts.keys()),
    "出現回数": list(range_counts.values())
}))

# ⑦ ペア分析
st.subheader("ペア（2つ組）出現回数")
pair_counts = Counter()
for _, row in df_recent.iterrows():
    nums = [row[f"第{i}数字"] for i in range(1, 5)]
    for i in range(4):
        for j in range(i+1, 4):
            pair = tuple(sorted([nums[i], nums[j]]))
            pair_counts[pair] += 1
pair_df = pd.DataFrame(pair_counts.items(), columns=["ペア", "出現回数"]).sort_values(by="出現回数", ascending=False)
st.dataframe(pair_df)

# ⑧ 合計値分析
st.subheader("合計値の出現回数")
sum_counts = Counter()
for _, row in df_recent.iterrows():
    total = sum([row[f"第{i}数字"] for i in range(1, 5)])
    sum_counts[total] += 1
sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False)
st.dataframe(sum_df)

# ⑪ スキップ回数分析（数字ごとに直近3回の出現位置を「◯回前」で表示）
st.subheader("スキップ回数分析（数字ごとに直近3回の出現：◯回前）")

try:
    # 各数字の出現位置（インデックス）を記録（0が最新）
    history_map = {i: [] for i in range(10)}

    for idx in range(len(df_recent)):
        row = df_recent.iloc[idx]
        for d in range(1, 5):
            num = row[f"第{d}数字"]
            if idx not in history_map[num]:
                history_map[num].append(idx)

    # 表示用に「◯回前」形式に変換（なければ「出現なし」）
    def format_rank(n):
        return f"{n}回前" if isinstance(n, int) else "出現なし"

    display_rows = []
    for num in range(10):
        last_1 = format_rank(history_map[num][0]) if len(history_map[num]) > 0 else "出現なし"
        last_2 = format_rank(history_map[num][1]) if len(history_map[num]) > 1 else "出現なし"
        last_3 = format_rank(history_map[num][2]) if len(history_map[num]) > 2 else "出現なし"
        display_rows.append({
            "数字": num,
            "直近出現": last_1,
            "2回前出現": last_2,
            "3回前出現": last_3
        })

    skip_df = pd.DataFrame(display_rows)
    st.dataframe(skip_df)

except Exception as e:
    st.error(f"スキップ分析の表示に失敗しました: {e}")

# ⑨ 軸数字から予想
st.header("⑨ ナンバーズ4予想（軸数字指定）")
axis = st.selectbox("軸数字を選んでください（0〜9）", list(range(10)))
if st.button("20通りを表示"):
    preds = []
    while len(preds) < 20:
        others = random.sample([i for i in range(10) if i != axis], 3)
        combo = sorted([axis] + others)
        if combo not in preds:
            preds.append(combo)
    st.dataframe(pd.DataFrame(preds, columns=["予測1", "予測2", "予測3", "予測4"]))

# ⑩ 高度予想：合計値・スキップ・ABCバランスを考慮
st.header("ナンバーズ4予想（AI風ロジック）")

if st.button("AI風ロジックで20通り生成"):
    # 合計値の平均・中央値・モードを取得
    total_sums = df_recent[[f"第{i}数字" for i in range(1, 5)]].sum(axis=1)
    avg = total_sums.mean()
    med = total_sums.median()
    mode_vals = total_sums.mode().tolist()

    # スキップ回数（最後に出てから何回出ていないか）
    recent_flat = []
    for _, row in df_recent.iterrows():
        recent_flat.extend([row[f"第{i}数字"] for i in range(1, 5)])
    skip_count = {i: None for i in range(10)}
    for idx in range(len(df_recent)):
        row = df_recent.iloc[idx]
        for d in range(1, 5):
            num = row[f"第{d}数字"]
            if skip_count[num] is None:
                skip_count[num] = idx

    # ABC分類関数
    def classify_abc(n):
        if n <= 3:
            return "A"
        elif n <= 6:
            return "B"
        else:
            return "C"

    # 予想生成
    def is_valid_combo(combo):
        total = sum(combo)
        if not (med - 4 <= total <= med + 4):  # 合計値を中央値±4以内に制限
            return False
        abc_counts = {"A": 0, "B": 0, "C": 0}
        for n in combo:
            abc_counts[classify_abc(n)] += 1
        if max(abc_counts.values()) >= 3:  # ABCが1種類に偏りすぎていればNG
            return False
        if all(skip_count[n] is not None and skip_count[n] < 3 for n in combo):
            return False  # 全部最近出ている数字だけ → NG
        return True

    predictions = []
    tries = 0
    while len(predictions) < 20 and tries < 1000:
        cand = sorted(random.sample(range(10), 4))
        if cand not in predictions and is_valid_combo(cand):
            predictions.append(cand)
        tries += 1

    if predictions:
        st.success("以下の条件で絞り込まれた予想を表示します：")
        st.markdown("- 合計値：中央値 ±4")
        st.markdown("- ABCバランス（偏りすぎNG）")
        st.markdown("- 最近出ていない数字を優先")
        st.dataframe(pd.DataFrame(predictions, columns=["予測1", "予測2", "予測3", "予測4"]))
    else:
        st.warning("条件に合致する予測が生成できませんでした。")
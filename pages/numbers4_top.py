import pandas as pd
import streamlit as st
import html
import random
from collections import Counter

# CSVパス
CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers4_24.csv"

# 最新の当選結果表示関数
def show_latest_results(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("未定義")
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])
        df = df.sort_values(by="抽せん日", ascending=False).reset_index(drop=True)

        # 最新1件
        latest = df.iloc[0]
        global df_recent
        df_recent = df.head(24)

        number_str = f"{latest['第1数字']}{latest['第2数字']}{latest['第3数字']}{latest['第4数字']}"

        st.header("① 最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(latest['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽せん日</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(latest['抽せん日'].strftime('%Y-%m-%d'))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {number_str}
                </td>
            </tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    except Exception as e:
        st.error("最新の当選結果の表示中にエラーが発生しました")
        st.error(str(e))

# ③ ランキング表示
st.header("③ 各桁の出現ランキング")
ranking_df = pd.DataFrame({
    "順位": [f"{i+1}位" for i in range(10)],
    "第1数字": df_recent["第1数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
    "第2数字": df_recent["第2数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
    "第3数字": df_recent["第3数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
    "第4数字": df_recent["第4数字"].value_counts().reindex(range(10), fill_value=0).sort_values(ascending=False).index[:10],
})
st.dataframe(ranking_df)

# ④ W/S/T カウント
st.subheader("④ シングル・ダブル・トリプル分析")
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
st.subheader("⑤ ひっぱり数字の回数")
hoppari = 0
for i in range(1, len(df_recent)):
    prev = set(df_recent.iloc[i - 1][[f"第{i}数字" for i in range(1, 5)]])
    curr = set(df_recent.iloc[i][[f"第{i}数字" for i in range(1, 5)]])
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
st.subheader("⑦ ペア（2つ組）出現回数")
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
st.subheader("⑧ 合計値の出現回数")
sum_counts = Counter()
for _, row in df_recent.iterrows():
    total = sum([row[f"第{i}数字"] for i in range(1, 5)])
    sum_counts[total] += 1
sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False)
st.dataframe(sum_df)

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
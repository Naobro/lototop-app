import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import streamlit as st
from auth import check_password
import streamlit.components.v1 as components

st.set_page_config(layout="centered")

st.title("ロト6 AI予想サイト")

import ssl
import pandas as pd
import random
from collections import Counter
ssl._create_default_https_context = ssl._create_unverified_context

st.markdown("""
<style>
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    white-space: nowrap;
    overflow-x: auto;
    max-width: 100%;
    text-align: center;
    color: #000;
    background-color: #fff;
}
th, td {
    border: 1px solid #ccc;
    padding: 8px;
    white-space: nowrap;
}
thead {
    background-color: #f2f2f2;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ✅ テーブル表示関数
def render_scrollable_table(df):
    st.markdown(f"""
    <div style='overflow-x:auto;'>
    {df.to_html(index=False, escape=False)}
    </div>
    """, unsafe_allow_html=True)

# ✅ データ取得・整形
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip()
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df[df["抽せん日"].notna()].copy()
for i in range(1, 7):
    df[f"第{i}数字"] = pd.to_numeric(df[f"第{i}数字"], errors='coerce')
df["ボーナス数字"] = pd.to_numeric(df["ボーナス数字"], errors="coerce")
df = df.dropna(subset=[f"第{i}数字" for i in range(1, 7)])

latest = df.iloc[-1]

# ✅ 整形関数
def format_count(val):
    try: return f"{int(float(val)):,}口"
    except: return "該当なし"

def format_yen(val):
    try: return f"{int(float(str(val).replace(',', '').replace('円',''))):,}円"
    except: return "該当なし"

# ✅ 表示① 最新結果
main_number_cells = ''.join([f"<td class='center'>{int(latest[f'第{i}数字'])}</td>" for i in range(1, 7)])
bonus_cell = f"<td colspan='6' class='center' style='color:red; font-weight:bold;'>{int(latest['ボーナス数字'])}</td>"

st.markdown(f"""
<table class='loto-table'>
<tr><th>回号</th><td colspan='6' class='center'>第{latest['回号']}回</td></tr>
<tr><th>抽せん日</th><td colspan='6' class='center'>{latest['抽せん日'].strftime('%Y年%m月%d日')}</td></tr>
<tr><th>本数字</th>{main_number_cells}</tr>
<tr><th>ボーナス数字</th>{bonus_cell}</tr>
<tr><th>1等</th><td colspan='3' class='right'>{format_count(latest['1等口数'])}</td><td colspan='3' class='right'>{format_yen(latest['1等賞金'])}</td></tr>
<tr><th>2等</th><td colspan='3' class='right'>{format_count(latest['2等口数'])}</td><td colspan='3' class='right'>{format_yen(latest['2等賞金'])}</td></tr>
<tr><th>3等</th><td colspan='3' class='right'>{format_count(latest['3等口数'])}</td><td colspan='3' class='right'>{format_yen(latest['3等賞金'])}</td></tr>
<tr><th>4等</th><td colspan='3' class='right'>{format_count(latest['4等口数'])}</td><td colspan='3' class='right'>{format_yen(latest['4等賞金'])}</td></tr>
<tr><th>5等</th><td colspan='3' class='right'>{format_count(latest['5等口数'])}</td><td colspan='3' class='right'>{format_yen(latest['5等賞金'])}</td></tr>
<tr><th>キャリーオーバー</th><td colspan='6' class='right'>{format_yen(latest['キャリーオーバー'])}</td></tr>
</table>
""", unsafe_allow_html=True)

# ✅ ② 直近24回の当選番号（ABC構成・ひっぱり・連続分析付き）
st.header("直近24回の当選番号")

df_recent = df.sort_values("回号", ascending=False).head(24).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")
df_recent = df_recent.sort_values(by="抽せん日", ascending=True).reset_index(drop=True)

all_numbers = df_recent[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
all_numbers = pd.to_numeric(all_numbers, errors="coerce")
counts = pd.Series(all_numbers).value_counts()

A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

abc_rows = []
abc_counts = {'A': 0, 'B': 0, 'C': 0}
cont_total = 0
pull_total = 0
nums_list = []

for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 7)]
    nums_list.append(nums)

for i in range(len(df_recent)):
    nums = nums_list[i]
    sorted_nums = sorted(nums)

    abc = []
    for n in sorted_nums:
        if n in B_set:
            abc.append("B"); abc_counts["B"] += 1
        elif n in A_set:
            abc.append("A"); abc_counts["A"] += 1
        else:
            abc.append("C"); abc_counts["C"] += 1
    abc_str = ",".join(abc)

    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_str = "あり" if cont else "なし"
    if cont:
        cont_total += 1

    if i == 0:
        pulls_str = "-"
    else:
        pulls = len(set(nums) & set(nums_list[i - 1]))
        pulls_str = f"{pulls}個" if pulls > 0 else "なし"
        if pulls > 0:
            pull_total += 1

    abc_rows.append({
        "抽せん日": df_recent.loc[i, "抽せん日"].strftime('%Y-%m-%d'),
        "回号": df_recent.loc[i, "回号"],
        **{f"第{i+1}数字": nums[i] for i in range(6)},
        "ABC構成": abc_str,
        "ひっぱり": pulls_str,
        "連続": cont_str,
    })

abc_df = pd.DataFrame(abc_rows).sort_values(by="抽せん日", ascending=False).reset_index(drop=True)
render_scrollable_table(abc_df)

total_abc = sum(abc_counts.values())
a_perc = round(abc_counts["A"] / total_abc * 100, 1)
b_perc = round(abc_counts["B"] / total_abc * 100, 1)
c_perc = round(abc_counts["C"] / total_abc * 100, 1)
pull_rate = round(pull_total / (len(df_recent) - 1) * 100, 1)
cont_rate = round(cont_total / len(df_recent) * 100, 1)

summary_df = pd.DataFrame({
    "分析項目": ["A数字割合", "B数字割合", "C数字割合", "ひっぱり率", "連続数字率"],
    "値": [f"{a_perc}%", f"{b_perc}%", f"{c_perc}%", f"{pull_rate}%", f"{cont_rate}%"]
})
st.subheader("出現傾向サマリー")
st.table(summary_df)

## ✅ ③ パターン分析（40〜43 も 30 に統合）
st.header("パターン分析")

def get_distribution(row):
    pattern = []
    for val in row:
        try:
            num = int(val)
            if 1 <= num <= 9:
                pattern.append("1")
            elif 10 <= num <= 19:
                pattern.append("10")
            elif 20 <= num <= 29:
                pattern.append("20")
            elif 30 <= num <= 43:
                pattern.append("30")
        except:
            pattern.append("不明")
    return '-'.join(sorted(pattern))

pattern_series = df_recent[[f"第{i}数字" for i in range(1, 7)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
render_scrollable_table(pattern_counts)

st.header("🎯 AIによる次回出現数字候補（20個：各位5個ずつ）")

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from collections import defaultdict, Counter
import numpy as np

df_ai = df.copy().dropna(subset=[f"第{i}数字" for i in range(1, 7)])
df_ai = df_ai.tail(min(len(df_ai), 100)).reset_index(drop=True)

X, y = [], []
for i in range(len(df_ai) - 1):
    prev_nums = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 7)]
    next_nums = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 7)]
    for target in next_nums:
        X.append(prev_nums)
        y.append(target)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
rf_probs = rf.predict_proba([X[-1]])[0]

mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
mlp.fit(X, y)
mlp_probs = mlp.predict_proba([X[-1]])[0]

transition = defaultdict(lambda: defaultdict(int))
for i in range(len(df_ai) - 1):
    curr = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 7)]
    next_ = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 7)]
    for c in curr:
        for n in next_:
            transition[c][n] += 1

last_draw = [df_ai.loc[len(df_ai)-1, f"第{j}数字"] for j in range(1, 7)]
markov_scores = defaultdict(int)
for c in last_draw:
    for n, cnt in transition[c].items():
        markov_scores[n] += cnt

score_dict = {n: 0 for n in range(1, 44)}
for i, s in enumerate(rf_probs):
    score_dict[i+1] += s
for i, s in enumerate(mlp_probs):
    score_dict[i+1] += s
for n, s in markov_scores.items():
    score_dict[n] += s

def which_kurai(n):
    if 1 <= n <= 9:
        return "1の位"
    elif 10 <= n <= 19:
        return "10の位"
    elif 20 <= n <= 29:
        return "20の位"
    elif 30 <= n <= 43:
        return "30の位"
    else:
        return "その他"

by_kurai = {"1の位":[], "10の位":[], "20の位":[], "30の位": []}
for n, s in sorted(score_dict.items(), key=lambda x: -x[1]):
    k = which_kurai(n)
    if k in by_kurai:
        by_kurai[k].append((n, s))

top20 = []
for k in ["1の位", "10の位", "20の位", "30の位"]:
    nums = [num for num, _ in by_kurai[k][:5]]
    top20.extend(nums)

assert len(top20) == 20

st.success(f"🧠 次回出現候補（AI予測・20個・各位5個ずつ）: {sorted(top20)}")

with st.expander("📊 モデル別候補を表示"):
    rf_top = list(np.argsort(rf_probs)[::-1][:15] + 1)
    mlp_top = list(np.argsort(mlp_probs)[::-1][:15] + 1)
    markov_top = sorted(markov_scores, key=markov_scores.get, reverse=True)[:15]
    st.write("🔹 ランダムフォレスト:", sorted(map(int, rf_top)))
    st.write("🔹 ニューラルネット:", sorted(map(int, mlp_top)))
    st.write("🔹 マルコフ連鎖:", sorted(map(int, markov_top)))

grouped6 = {"1の位": [], "10の位": [], "20の位": [], "30の位": []}
for n in top20:
    k = which_kurai(n)
    grouped6[k].append(n)

group_df6 = pd.DataFrame({k: grouped6[k] for k in grouped6})

st.markdown("### 🧮 候補数字の位別分類（1の位・10の位・20の位・30〜43の位・各5個）")
st.markdown(f"""
<div style='overflow-x: auto;'>
{group_df6.to_html(index=False, escape=False)}
</div>
""", unsafe_allow_html=True)

# ✅ A/B数字の位別分類（ロト6用：40〜43も30の位に分類）
st.header("A数字・B数字の位別分類")

def style_table(df):
    return df.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ]).to_html(escape=False, index=False)

latest = df.iloc[-1]
latest_numbers = [int(latest[f"第{i}数字"]) for i in range(1, 7)]

def highlight_number(n):
    return f"<span style='color:red; font-weight:bold'>{n}</span>" if n in latest_numbers else str(n)

def classify_numbers_loto6(numbers):
    bins = {'1の位': [], '10の位': [], '20の位': [], '30の位': []}
    for n in numbers:
        if 1 <= n <= 9:
            bins['1の位'].append(n)
        elif 10 <= n <= 19:
            bins['10の位'].append(n)
        elif 20 <= n <= 29:
            bins['20の位'].append(n)
        elif 30 <= n <= 43:
            bins['30の位'].append(n)
    return bins

A_bins = classify_numbers_loto6(A_set)
B_bins = classify_numbers_loto6(B_set)

digit_table = pd.DataFrame({
    "位": list(A_bins.keys()),
    "A数字": [', '.join([highlight_number(n) for n in sorted(A_bins[k])]) for k in A_bins],
    "B数字": [', '.join([highlight_number(n) for n in sorted(B_bins[k])]) for k in B_bins]
})

st.markdown(style_table(digit_table), unsafe_allow_html=True)

# ✅ ④各位の出現回数TOP5（変数名を position_top5_df に変更して衝突を回避）
st.header("各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 7):
    col = f'第{i}数字'
    col_values = pd.to_numeric(df_recent[col], errors="coerce")
    number_groups['1'].extend(col_values[col_values.between(1, 9)].dropna().astype(int).tolist())
    number_groups['10'].extend(col_values[col_values.between(10, 19)].dropna().astype(int).tolist())
    number_groups['20'].extend(col_values[col_values.between(20, 29)].dropna().astype(int).tolist())
    number_groups['30'].extend(col_values[col_values.between(30, 43)].dropna().astype(int).tolist())

position_top5_df = pd.DataFrame({
    '1の位': pd.Series(number_groups['1']).value_counts().head(5).index.tolist(),
    '10の位': pd.Series(number_groups['10']).value_counts().head(5).index.tolist(),
    '20の位': pd.Series(number_groups['20']).value_counts().head(5).index.tolist(),
    '30の位': pd.Series(number_groups['30']).value_counts().head(5).index.tolist()
})
render_scrollable_table(position_top5_df)

# ✅ ⑤ 各数字の出現回数TOP5
st.header("各数字の出現回数TOP5")
results = {'順位': ['1位', '2位', '3位', '4位', '5位']}
for i in range(1, 7):
    col = f'第{i}数字'
    col_values = pd.to_numeric(df_recent[col], errors="coerce").dropna().astype(int)
    counts = col_values.value_counts().sort_values(ascending=False)
    top5 = counts.head(5)
    results[col] = [f"{n}（{c}回）" for n, c in zip(top5.index, top5.values)]
    while len(results[col]) < 5:
        results[col].append("")
top5_df = pd.DataFrame(results)
render_scrollable_table(top5_df)

# --- ロト6の設定 ---
n_numbers = 6
max_ball = 43
df_recent = df.tail(24).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")
df_recent = df_recent.dropna(subset=["抽せん日"])

numbers = df_recent[[f"第{i}数字" for i in range(1, n_numbers + 1)]].values.flatten()
number_counts = pd.Series(numbers).value_counts().sort_values(ascending=False)

ranking_df = pd.DataFrame({
    "順位": range(1, len(number_counts) + 1),
    "数字": [f"{int(num)}（{count}）" for num, count in zip(number_counts.index, number_counts.values)]
})

left_df = ranking_df.head(22).reset_index(drop=True)
right_df = ranking_df.iloc[22:].reset_index(drop=True)

def format_html_table(df):
    return df.to_html(index=False, classes="loto-table", escape=False)

st.header("直近24回 出現回数ランキング（ロト6）")
left_col, right_col = st.columns(2)
with left_col:
    st.markdown("#### 🔵 ランキング（1位〜22位）")
    st.markdown(format_html_table(left_df), unsafe_allow_html=True)
with right_col:
    st.markdown("#### 🟢 ランキング（23位〜43位）")
    st.markdown(format_html_table(right_df), unsafe_allow_html=True)

# --- 🔁 連続数字ペア 出現ランキング ---
st.header("🔁 連続数字ペア 出現ランキング（ロト6）")

numbers_list = df_recent[[f"第{i}数字" for i in range(1, n_numbers + 1)]].values.tolist()
consecutive_pairs = []
for row in numbers_list:
    sorted_row = sorted(row)
    for a, b in zip(sorted_row, sorted_row[1:]):
        if b - a == 1:
            consecutive_pairs.append(f"{a}-{b}")

consec_counter = Counter(consecutive_pairs)
consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"])
consec_df = consec_df.sort_values(by="出現回数", ascending=False).reset_index(drop=True)

st.markdown(style_table(consec_df), unsafe_allow_html=True)

# ✅ ⑧ 基本予想（2通り×5パターン）
st.header("基本予想（パターン別 2通り×5種類）")
group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 40)),
    "40": list(range(40, 44)),
}
group_map = {n: g for g, nums in group_dict.items() for n in nums}
last_numbers = df_recent.iloc[0][[f"第{i}数字" for i in range(1, 7)]].tolist()

pattern_list = [
    ("1-10-10-20-20-30", ["1", "10", "10", "20", "20", "30"]),
    ("1-10-20-20-30-40", ["1", "10", "20", "20", "30", "40"]),
    ("10-10-10-20-30-30", ["10", "10", "10", "20", "30", "30"]),
    ("1-1-10-20-20-30",   ["1", "1", "10", "20", "20", "30"]),
    ("1-10-20-20-20-30",  ["1", "10", "20", "20", "20", "30"]),
]

def generate_from_group(group_key):
    cands = [n for n in group_dict[group_key] if n in A_set] * 6 + \
            [n for n in group_dict[group_key] if n in B_set] * 4
    return random.choice(cands) if cands else random.choice(group_dict[group_key])

for label, pattern in pattern_list:
    st.markdown(f"**パターン: {label}**")
    predictions = []
    for _ in range(2):
        nums = [generate_from_group(g) for g in pattern]
        if random.random() < 0.5:
            pulls = random.sample(last_numbers, k=random.choice([1, 2]))
            replace_indices = random.sample(range(6), k=len(pulls))
            for i, val in zip(replace_indices, pulls):
                if group_map.get(val) == pattern[i]:
                    nums[i] = val
        unique = sorted(set(nums))
        while len(unique) < 6:
            extra = random.randint(1, 43)
            if extra not in unique and group_map.get(extra) in pattern:
                g = group_map[extra]
                if unique.count(extra) < pattern.count(g):
                    unique.append(extra)
        unique = sorted(unique)[:6]
        predictions.append(unique)
    pred_df = pd.DataFrame(predictions, columns=[f"第{i}数字" for i in range(1, 7)])
    render_scrollable_table(pred_df)

st.header("セレクト予想")

group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 44)),
}

st.markdown("#### 🔢 候補にする数字群を選択")
use_position_groups = st.checkbox("各位の出現回数TOP5（1の位〜30の位）", value=True)
use_position_top5 = st.checkbox("各第n位のTOP5（第1〜第6数字ごと）", value=True)
use_A = st.checkbox("A数字", value=True)
use_B = st.checkbox("B数字", value=True)
use_C = st.checkbox("C数字")
use_last = st.checkbox("前回数字を除外", value=True)

select_manual = st.multiselect("任意で追加したい数字 (1-43)", list(range(1, 44)))

pattern_input = st.text_input("パターンを入力 (例: 1-10-20-20-30-30)", value="1-10-20-20-30-30")
pattern = pattern_input.strip().split("-")

last_numbers = latest[[f"第{i}数字" for i in range(1, 7)]].tolist() if use_last else []

candidate_set = set(select_manual)

if use_position_groups:
    number_groups = {'1': [], '10': [], '20': [], '30': []}
    for i in range(1, 7):
        col = f'第{i}数字'
        col_values = pd.to_numeric(df_recent[col], errors="coerce")
        number_groups['1'].extend(col_values[col_values.between(1, 9)].dropna().astype(int).tolist())
        number_groups['10'].extend(col_values[col_values.between(10, 19)].dropna().astype(int).tolist())
        number_groups['20'].extend(col_values[col_values.between(20, 29)].dropna().astype(int).tolist())
        number_groups['30'].extend(col_values[col_values.between(30, 43)].dropna().astype(int).tolist())
    for key in number_groups:
        top5 = pd.Series(number_groups[key]).value_counts().head(5).index.tolist()
        candidate_set.update(top5)

if use_position_top5:
    seen = set()
    for i in range(1, 7):
        col = f'第{i}数字'
        col_values = pd.to_numeric(df_recent[col], errors="coerce").dropna().astype(int)
        counts = col_values.value_counts().sort_values(ascending=False)
        for num in counts.index:
            if num not in seen:
                candidate_set.add(num)
                seen.add(num)
            if len(seen) >= 5:
                break

if use_A:
    candidate_set.update(A_set)
if use_B:
    candidate_set.update(B_set)
if use_C:
    C_numbers = sorted(list(set(range(1, 44)) - A_set - B_set))
    candidate_set.update(C_numbers)

candidate_set = sorted(set(candidate_set) - set(last_numbers))

def generate_select_prediction():
    prediction = []
    used = set()
    for group_key in pattern:
        group_nums = [n for n in group_dict.get(group_key, []) if n in candidate_set and n not in used]
        if not group_nums:
            return []
        chosen = random.choice(group_nums)
        prediction.append(chosen)
        used.add(chosen)
    return sorted(prediction) if len(prediction) == 6 else []

if st.button("🎯 セレクト予想を出す"):
    result = generate_select_prediction()
    if result:
        st.success(f"🎉 セレクト予想: {result}")
    else:
        st.error("条件に合致する数字が不足しています。候補を増やしてください。")

st.markdown("## 🆕 ロジック強化パート：出現頻度・引っ張り・連続重視")

df100 = df.tail(100)
freq_counts = pd.Series(df100[[f"第{i}数字" for i in range(1,7)]].values.flatten()).value_counts()

pairs = []
for row in df100.tail(24)[[f"第{i}数字" for i in range(1,7)]].values:
    row = sorted(row)
    for a,b in zip(row, row[1:]):
        if b - a == 1:
            pairs.append((a,b))
pair_counts = Counter(pairs)

improved_scores = {n: 0 for n in range(1,44)}
for n, cnt in freq_counts.items():
    improved_scores[n] += cnt * 1.5
for (a,b), cnt in pair_counts.items():
    improved_scores[a] += cnt * 1.0
    improved_scores[b] += cnt * 1.0

for n in improved_scores:
    improved_scores[n] += score_dict.get(n,0)

new_by_kurai = {"1の位":[], "10の位":[], "20の位":[], "30の位":[]}
for n,s in sorted(improved_scores.items(), key=lambda x: -x[1]):
    k = which_kurai(n)
    if k in new_by_kurai and len(new_by_kurai[k])<5:
        new_by_kurai[k].append(n)

new_top20 = sum([nums for nums in new_by_kurai.values()], [])

st.success(f"🧠 改善AI予測候補（20個・各位5個）：{sorted(new_top20)}")

common_with_prev = len(set(new_top20) & set(last_draw))
st.write(f"🔁 前回数字との共通数: {common_with_prev}個")

consec_included = sum(any(abs(n - m)==1 for m in new_top20) for n in new_top20)
st.write(f"🔗 候補内連続ペア含み数: {consec_included}個")

st.header("各数字の出現回数・出現率一覧")

def build_frequency_table(source_df, label_count, label_rate):
    total_draws = len(source_df)
    all_vals = source_df[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
    all_vals = pd.to_numeric(pd.Series(all_vals), errors="coerce").dropna().astype(int)
    count_map = all_vals.value_counts().to_dict()
    rows = []
    for num in range(1, 44):
        cnt = int(count_map.get(num, 0))
        rate = round(cnt / total_draws * 100, 1) if total_draws > 0 else 0
        rows.append({"数字": num, label_count: cnt, label_rate: rate})
    return pd.DataFrame(rows)

def add_sequential_rank(df_in, count_col, rate_col, rank_col):
    ranked = df_in.sort_values(
        by=[count_col, rate_col, "数字"],
        ascending=[False, False, True]
    ).reset_index(drop=True)
    ranked[rank_col] = range(1, len(ranked) + 1)
    return df_in.merge(ranked[["数字", rank_col]], on="数字", how="left")

def highlight_rank(val):
    try:
        v = int(val)
        if v <= 10:
            return "background-color:#fff3b0; color:#000; font-weight:bold;"
        elif v >= 34:
            return "background-color:#cfe2ff; color:#000; font-weight:bold;"
        return ""
    except:
        return ""

def render_rank_table(df_in):
    styled_html = (
        df_in.style
        .map(highlight_rank, subset=["100回ランク", "24回ランク"])
        .set_properties(**{"text-align": "center", "white-space": "nowrap"})
        .set_table_styles([
            {"selector": "table", "props": [("border-collapse", "collapse"), ("width", "100%"), ("font-size", "14px")]},
            {"selector": "th", "props": [("border", "1px solid #ccc"), ("padding", "8px"), ("background-color", "#f2f2f2"), ("text-align", "center")]},
            {"selector": "td", "props": [("border", "1px solid #ccc"), ("padding", "8px"), ("text-align", "center")]}
        ])
        .hide(axis="index")
        .to_html(escape=False)
    )
    st.markdown(f"<div style='overflow-x:auto;'>{styled_html}</div>", unsafe_allow_html=True)

df_all_sorted = df.sort_values("回号", ascending=True).reset_index(drop=True)
df_100 = df_all_sorted.tail(min(100, len(df_all_sorted))).copy()
df_24 = df_all_sorted.tail(min(24, len(df_all_sorted))).copy()

freq_100_df = build_frequency_table(df_100, "直近100回出現回数", "直近100回出現率")
freq_24_df = build_frequency_table(df_24, "直近24回出現回数", "直近24回出現率")

freq_summary_df = freq_100_df.merge(freq_24_df, on="数字")
freq_summary_df = add_sequential_rank(freq_summary_df, "直近100回出現回数", "直近100回出現率", "100回ランク")
freq_summary_df = add_sequential_rank(freq_summary_df, "直近24回出現回数", "直近24回出現率", "24回ランク")

freq_summary_df["直近100回出現率"] = freq_summary_df["直近100回出現率"].map(lambda x: f"{x:.1f}%")
freq_summary_df["直近24回出現率"] = freq_summary_df["直近24回出現率"].map(lambda x: f"{x:.1f}%")

render_rank_table(freq_summary_df[[
    "数字",
    "直近100回出現回数", "直近100回出現率", "100回ランク",
    "直近24回出現回数", "直近24回出現率", "24回ランク"
]])

st.header("各数字の出現間隔分析一覧")

def get_hit_positions(source_df, number):
    hit_positions = []
    for idx, row in source_df.reset_index(drop=True).iterrows():
        nums = [int(row[f"第{i}数字"]) for i in range(1, 7)]
        if number in nums:
            hit_positions.append(idx + 1)
    return hit_positions

def get_intervals_from_positions(positions):
    if len(positions) < 2:
        return []
    return [positions[i] - positions[i - 1] for i in range(1, len(positions))]

def format_avg_interval(intervals):
    if len(intervals) == 0:
        return "-"
    return str(round(sum(intervals) / len(intervals), 1))

def format_last5_intervals(intervals):
    if len(intervals) == 0:
        return "-"
    recent5 = list(reversed(intervals[-5:]))
    return "-".join(str(int(x)) for x in recent5)

def get_last_elapsed_count(source_df, number):
    source_df = source_df.reset_index(drop=True)
    latest_nums = [int(source_df.iloc[-1][f"第{i}数字"]) for i in range(1, 7)]
    if number in latest_nums:
        return "-"
    for idx in range(len(source_df) - 1, -1, -1):
        nums = [int(source_df.iloc[idx][f"第{i}数字"]) for i in range(1, 7)]
        if number in nums:
            return str(len(source_df) - (idx + 1))
    return "-"

def get_last_hit_date(source_df, number):
    source_df = source_df.reset_index(drop=True)
    for idx in range(len(source_df) - 1, -1, -1):
        nums = [int(source_df.iloc[idx][f"第{i}数字"]) for i in range(1, 7)]
        if number in nums:
            dt = pd.to_datetime(source_df.iloc[idx]["抽せん日"], errors="coerce")
            return dt.strftime("%Y-%m-%d") if pd.notna(dt) else "-"
    return "-"

df_interval_base = df.sort_values(["抽せん日", "回号"], ascending=True).reset_index(drop=True)
df_interval_100 = df_interval_base.tail(min(100, len(df_interval_base))).copy().reset_index(drop=True)

latest_draw_date = pd.to_datetime(df_interval_100.iloc[-1]["抽せん日"], errors="coerce")
if pd.notna(latest_draw_date):
    last_12m_start = latest_draw_date - pd.DateOffset(months=12)
    df_last12m = df_interval_100[df_interval_100["抽せん日"] >= last_12m_start].copy().reset_index(drop=True)
else:
    df_last12m = df_interval_100.copy()

df_monday = df_interval_100[df_interval_100["抽せん日"].dt.weekday == 0].copy().reset_index(drop=True)
df_thursday = df_interval_100[df_interval_100["抽せん日"].dt.weekday == 3].copy().reset_index(drop=True)

interval_rows = []

for num in range(1, 44):
    all_positions = get_hit_positions(df_interval_100, num)
    all_intervals = get_intervals_from_positions(all_positions)

    last12_positions = get_hit_positions(df_last12m, num)
    last12_intervals = get_intervals_from_positions(last12_positions)

    monday_positions = get_hit_positions(df_monday, num)
    monday_intervals = get_intervals_from_positions(monday_positions)

    thursday_positions = get_hit_positions(df_thursday, num)
    thursday_intervals = get_intervals_from_positions(thursday_positions)

    interval_rows.append({
        "数字": num,
        "直近100回平均間隔": format_avg_interval(all_intervals),
        "直近12ケ月平均間隔": format_avg_interval(last12_intervals),
        "月曜日平均間隔": format_avg_interval(monday_intervals),
        "木曜日平均間隔": format_avg_interval(thursday_intervals),
        "直近100回最大経過回数": str(max(all_intervals)) if len(all_intervals) > 0 else "-",
        "直近5回の出現間隔": format_last5_intervals(all_intervals),
        "最後の出現経過回数": get_last_elapsed_count(df_interval_100, num),
        "一番最近の出現日": get_last_hit_date(df_interval_100, num),
    })

interval_analysis_df = pd.DataFrame(interval_rows)
render_scrollable_table(interval_analysis_df)

# ============================================================
# 🤖 AI予想用コピーボタン（全データをMarkdown形式でコピー）
# ============================================================

def df_to_md(df: pd.DataFrame) -> str:
    """DataFrameをAIが読みやすいMarkdown表形式に変換する（HTMLタグは除去）"""
    import re
    def strip_html(val):
        return re.sub(r'<[^>]+>', '', str(val))

    cols = df.columns.tolist()
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep    = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows   = "\n".join(
        "| " + " | ".join(strip_html(v) for v in row.tolist()) + " |"
        for _, row in df.iterrows()
    )
    return "\n".join([header, sep, rows])

def build_ai_copy_text():
    latest_numbers_local = [int(latest[f"第{i}数字"]) for i in range(1, 7)]

    def mark_if_latest(n):
        return f"{n}*" if n in latest_numbers_local else str(n)

    lines = []
    lines.append(f"# ロト6 AI予想用データ（第{latest['回号']}回時点）")

    lines.append("\n## 1. 最新抽せん結果")
    lines.append(f"- 回号: 第{latest['回号']}回")
    lines.append(f"- 抽せん日: {latest['抽せん日'].strftime('%Y-%m-%d')}")
    lines.append(f"- 本数字: {', '.join(str(n) for n in latest_numbers_local)}")
    lines.append(f"- ボーナス数字: {int(latest['ボーナス数字'])}")
    lines.append(f"- 1等: {format_count(latest['1等口数'])} / {format_yen(latest['1等賞金'])}")
    lines.append(f"- 2等: {format_count(latest['2等口数'])} / {format_yen(latest['2等賞金'])}")
    lines.append(f"- 3等: {format_count(latest['3等口数'])} / {format_yen(latest['3等賞金'])}")
    lines.append(f"- 4等: {format_count(latest['4等口数'])} / {format_yen(latest['4等賞金'])}")
    lines.append(f"- 5等: {format_count(latest['5等口数'])} / {format_yen(latest['5等賞金'])}")
    lines.append(f"- キャリーオーバー: {format_yen(latest['キャリーオーバー'])}")

    lines.append("\n## 2. 直近24回の当選番号・ABC構成・ひっぱり・連続")
    lines.append(df_to_md(abc_df))

    lines.append("\n## 3. 出現傾向サマリー")
    lines.append(f"- A数字割合: {a_perc}%")
    lines.append(f"- B数字割合: {b_perc}%")
    lines.append(f"- C数字割合: {c_perc}%")
    lines.append(f"- ひっぱり率: {pull_rate}%")
    lines.append(f"- 連続数字率: {cont_rate}%")

    lines.append("\n## 4. パターン分析（直近24回）")
    lines.append(df_to_md(pattern_counts))

    lines.append("\n## 5. AIモデルによる次回候補（20個・各位5個）")
    lines.append(f"- 候補数字: {sorted(top20)}")
    lines.append(df_to_md(group_df6))

    lines.append("\n## 6. A数字・B数字の位別分類（※ * は最新当選数字と一致）")
    ab_rows = []
    for k in ["1の位", "10の位", "20の位", "30の位"]:
        ab_rows.append({
            "位": k,
            "A数字": ", ".join(mark_if_latest(n) for n in sorted(A_bins[k])),
            "B数字": ", ".join(mark_if_latest(n) for n in sorted(B_bins[k])),
        })
    lines.append(df_to_md(pd.DataFrame(ab_rows)))

    lines.append("\n## 7. 各位の出現回数TOP5")
    lines.append(df_to_md(position_top5_df))

    lines.append("\n## 8. 各数字（第1〜第6数字別）の出現回数TOP5")
    lines.append(df_to_md(top5_df))

    lines.append("\n## 9. 直近24回 出現回数ランキング（全43数字）")
    lines.append(df_to_md(ranking_df))

    lines.append("\n## 10. 連続数字ペア 出現ランキング")
    lines.append(df_to_md(consec_df))

    lines.append("\n## 11. 各数字の出現回数・出現率一覧（直近100回／24回）")
    freq_cols = [
        "数字",
        "直近100回出現回数", "直近100回出現率", "100回ランク",
        "直近24回出現回数", "直近24回出現率", "24回ランク"
    ]
    lines.append(df_to_md(freq_summary_df[freq_cols]))

    lines.append("\n## 12. 各数字の出現間隔分析")
    lines.append(df_to_md(interval_analysis_df))

    lines.append("\n## 13. 改善ロジックによるAI予測候補")
    lines.append(f"- 候補数字: {sorted(new_top20)}")
    lines.append(f"- 前回数字との共通数: {common_with_prev}個")
    lines.append(f"- 候補内連続ペア含み数: {consec_included}個")

    return "\n".join(lines)

ai_copy_text    = build_ai_copy_text()
escaped_ai_text = json.dumps(ai_copy_text)

ai_copy_button_html = f"""
<div style="margin:24px 0;">
  <button onclick="copyAIData()" style="
    background:#1a73e8;
    color:white;
    border:none;
    padding:14px 22px;
    font-size:16px;
    font-weight:bold;
    border-radius:8px;
    cursor:pointer;
  ">
    🤖 AI予想用データをコピー
  </button>
  <span id="ai-copy-status"
        style="margin-left:12px; color:green; font-weight:bold;">
  </span>
</div>
<script>
function copyAIData() {{
  const text = {escaped_ai_text};
  navigator.clipboard.writeText(text).then(function() {{
    document.getElementById('ai-copy-status').innerText = '✅ コピーしました';
    setTimeout(function() {{
      document.getElementById('ai-copy-status').innerText = '';
    }}, 3000);
  }}).catch(function(err) {{
    alert('コピーに失敗しました: ' + err);
  }});
}}
</script>
"""
components.html(ai_copy_button_html, height=90)

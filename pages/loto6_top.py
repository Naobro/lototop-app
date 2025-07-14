import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

st.set_page_config(layout="centered")
check_password()

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
    white-space: nowrap;       /* 折り返し防止 */
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

# 回号順にソートして上位24件（最新）を抽出
df_recent = df.sort_values("回号", ascending=False).head(24).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")
df_recent = df_recent.sort_values(by="抽せん日", ascending=True).reset_index(drop=True)

# 出現回数からABC分類セット作成（ロト6は6数字）
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
all_numbers = pd.to_numeric(all_numbers, errors="coerce")
counts = pd.Series(all_numbers).value_counts()

A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

# 分析用初期化
abc_rows = []
abc_counts = {'A': 0, 'B': 0, 'C': 0}
cont_total = 0
pull_total = 0
nums_list = []

# 数字だけのリスト作成（比較用）
for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 7)]
    nums_list.append(nums)

# 各回の分析
for i in range(len(df_recent)):
    nums = nums_list[i]
    sorted_nums = sorted(nums)

    # ABC構成
    abc = []
    for n in sorted_nums:
        if n in B_set:
            abc.append("B"); abc_counts["B"] += 1
        elif n in A_set:
            abc.append("A"); abc_counts["A"] += 1
        else:
            abc.append("C"); abc_counts["C"] += 1
    abc_str = ",".join(abc)

    # 連続数字分析
    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_str = "あり" if cont else "なし"
    if cont:
        cont_total += 1

    # ひっぱり分析（前回と共通する数字数）
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

# 表を新しい順に並べる
abc_df = pd.DataFrame(abc_rows).sort_values(by="抽せん日", ascending=False).reset_index(drop=True)
render_scrollable_table(abc_df)

# --- 出現傾向（ABC割合・ひっぱり率・連続率）テーブル ---
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
            elif 30 <= num <= 43:  # ← ここを修正
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

# --- 直近100回で学習用データ構築 ---
df_ai = df.copy().dropna(subset=[f"第{i}数字" for i in range(1, 7)])
df_ai = df_ai.tail(min(len(df_ai), 100)).reset_index(drop=True)

X, y = [], []
for i in range(len(df_ai) - 1):
    prev_nums = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 7)]
    next_nums = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 7)]
    for target in next_nums:
        X.append(prev_nums)
        y.append(target)

# --- RandomForest ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
rf_probs = rf.predict_proba([X[-1]])[0]

# --- Neural Network ---
mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
mlp.fit(X, y)
mlp_probs = mlp.predict_proba([X[-1]])[0]

# --- マルコフ連鎖スコア ---
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

# --- 全数字スコア合成 ---
score_dict = {n: 0 for n in range(1, 44)}
for i, s in enumerate(rf_probs):
    score_dict[i+1] += s
for i, s in enumerate(mlp_probs):
    score_dict[i+1] += s
for n, s in markov_scores.items():
    score_dict[n] += s

# --- 位ごとに分類 ---
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

# --- 各位ごとに上位5個（合計20個）を選ぶ ---
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

# --- 位ごとにテーブル整形 ---
grouped6 = {"1の位": [], "10の位": [], "20の位": [], "30の位": []}
for n in top20:
    k = which_kurai(n)
    grouped6[k].append(n)

group_df6 = pd.DataFrame({
    k: grouped6[k]
    for k in grouped6
})

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

# ✅ CSVの最後の行（最新の当選データ）を正しく使う
latest = df.iloc[-1]
latest_numbers = [int(latest[f"第{i}数字"]) for i in range(1, 7)]

def highlight_number(n):
    return f"<span style='color:red; font-weight:bold'>{n}</span>" if n in latest_numbers else str(n)

def classify_numbers_loto6(numbers):
    bins = {
        '1の位': [], '10の位': [], '20の位': [], '30の位': []
    }
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



# ✅ ④各位の出現回数TOP5
st.header("各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 7):
    col = f'第{i}数字'
    col_values = pd.to_numeric(df_recent[col], errors="coerce")
    number_groups['1'].extend(col_values[col_values.between(1, 9)].dropna().astype(int).tolist())
    number_groups['10'].extend(col_values[col_values.between(10, 19)].dropna().astype(int).tolist())
    number_groups['20'].extend(col_values[col_values.between(20, 29)].dropna().astype(int).tolist())
    number_groups['30'].extend(col_values[col_values.between(30, 43)].dropna().astype(int).tolist())

top5_df = pd.DataFrame({
    '1の位': pd.Series(number_groups['1']).value_counts().head(5).index.tolist(),
    '10の位': pd.Series(number_groups['10']).value_counts().head(5).index.tolist(),
    '20の位': pd.Series(number_groups['20']).value_counts().head(5).index.tolist(),
    '30の位': pd.Series(number_groups['30']).value_counts().head(5).index.tolist()
})
render_scrollable_table(top5_df)

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



import pandas as pd
from collections import Counter

# --- ロト6の設定 ---
n_numbers = 6  # ロト6は6個
max_ball = 43  # 数字は1〜43
df_recent = df.tail(24).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")
df_recent = df_recent.dropna(subset=["抽せん日"])

# --- 出現回数カウント ---
numbers = df_recent[[f"第{i}数字" for i in range(1, n_numbers + 1)]].values.flatten()
number_counts = pd.Series(numbers).value_counts().sort_values(ascending=False)

# --- ランキングDataFrame作成（数字の横に出現回数を括弧付きで表示）---
ranking_df = pd.DataFrame({
    "順位": range(1, len(number_counts) + 1),
    "数字": [f"{int(num)}（{count}）" for num, count in zip(number_counts.index, number_counts.values)]
})

# --- 左右分割：左22件・右21件 ---
left_df = ranking_df.head(22).reset_index(drop=True)
right_df = ranking_df.iloc[22:].reset_index(drop=True)

# --- 表示用テーブル関数 ---
def format_html_table(df):
    return df.to_html(index=False, classes="loto-table", escape=False)

# --- 出現回数ランキング表示 ---
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

# 集計＆整形
consec_counter = Counter(consecutive_pairs)
consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"])
consec_df = consec_df.sort_values(by="出現回数", ascending=False).reset_index(drop=True)

# 表示（style_table は既存の関数でOK）
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

# --- 数字グループ定義 ---
group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 44)),
}

# --- UI：選択条件 ---
st.markdown("#### 🔢 候補にする数字群を選択")
use_position_groups = st.checkbox("各位の出現回数TOP5（1の位〜30の位）", value=True)
use_position_top5 = st.checkbox("各第n位のTOP5（第1〜第6数字ごと）", value=True)
use_A = st.checkbox("A数字", value=True)
use_B = st.checkbox("B数字", value=True)
use_C = st.checkbox("C数字")
use_last = st.checkbox("前回数字を除外", value=True)

# --- UI：任意数字追加 ---
select_manual = st.multiselect("任意で追加したい数字 (1-43)", list(range(1, 44)))

# --- UI：パターン入力 ---
pattern_input = st.text_input("パターンを入力 (例: 1-10-20-20-30-30)", value="1-10-20-20-30-30")
pattern = pattern_input.strip().split("-")

# --- 除外対象（前回数字） ---
last_numbers = latest[[f"第{i}数字" for i in range(1, 7)]].tolist() if use_last else []

# --- 候補数字の生成 ---
candidate_set = set(select_manual)

# 各位の出現回数TOP5（1の位〜30の位）
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

# 各第n位のTOP5（第1〜6数字ごと）
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

# ABC分類
if use_A:
    candidate_set.update(A_set)
if use_B:
    candidate_set.update(B_set)
if use_C:
    C_numbers = sorted(list(set(range(1, 44)) - A_set - B_set))
    candidate_set.update(C_numbers)

# 最終候補から前回数字を除外
candidate_set = sorted(set(candidate_set) - set(last_numbers))

# --- パターンに沿って数字を選出 ---
def generate_select_prediction():
    prediction = []
    used = set()
    for group_key in pattern:
        group_nums = [n for n in group_dict.get(group_key, []) if n in candidate_set and n not in used]
        if not group_nums:
            return []  # 候補が足りないため予想失敗とする
        chosen = random.choice(group_nums)
        prediction.append(chosen)
        used.add(chosen)
    return sorted(prediction) if len(prediction) == 6 else []

# --- ボタンで実行 ---
if st.button("🎯 セレクト予想を出す"):
    result = generate_select_prediction()
    if result:
        st.success(f"🎉 セレクト予想: {result}")
    else:
        st.error("条件に合致する数字が不足しています。候補を増やしてください。")

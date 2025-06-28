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
# ✅ ② ABC分類
st.header("② 直近24回の当選番号（ABC分類）")

df_recent = df.sort_values("回号", ascending=False).head(24).copy()
digits = df_recent[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
digits = pd.to_numeric(digits, errors="coerce")
counts = pd.Series(digits).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

abc_rows = []
for _, row in df_recent.iterrows():
    nums = [row[f"第{i}数字"] for i in range(1, 7)]
    abc = [ "B" if n in B_set else "A" if n in A_set else "C" for n in nums ]
    abc_rows.append({
        "回号": row["回号"],
        **{f"第{i}数字": int(row[f"第{i}数字"]) for i in range(1, 7)},
        "ABC構成": ",".join(abc)
    })
abc_df = pd.DataFrame(abc_rows)
render_scrollable_table(abc_df)

# ✅ ③ パターン分析
st.header("③ パターン分析")

def get_distribution(row):
    pattern = []
    for val in row:
        try:
            num = int(val)
            if 1 <= num <= 9: pattern.append("1")
            elif 10 <= num <= 19: pattern.append("10")
            elif 20 <= num <= 29: pattern.append("20")
            elif 30 <= num <= 39: pattern.append("30")
            elif 40 <= num <= 43: pattern.append("40")
        except:
            pattern.append("不明")
    return '-'.join(sorted(pattern))

pattern_series = df_recent[[f"第{i}数字" for i in range(1, 7)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
render_scrollable_table(pattern_counts)

# ✅ ④ 各位の出現回数TOP5
st.header("④ 各位の出現回数TOP5")
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
st.header("⑤ 各数字の出現回数TOP5")
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

# ✅ ⑥ A・B・C数字分類
st.header("⑥ A・B・C数字（出現頻度分類）")
count_series = pd.Series(
    df_recent[[f'第{i}数字' for i in range(1, 7)]].values.flatten()
).dropna().astype(int).value_counts()
A_numbers = count_series[(count_series >= 3) & (count_series <= 4)].index.tolist()
B_numbers = count_series[count_series >= 5].index.tolist()
C_numbers = sorted(list(set(range(1, 44)) - set(A_numbers) - set(B_numbers)))

max_len = max(len(A_numbers), len(B_numbers), len(C_numbers))
abc_summary_df = pd.DataFrame({
    "A数字（3〜4回）": A_numbers + [""] * (max_len - len(A_numbers)),
    "B数字（5回以上）": B_numbers + [""] * (max_len - len(B_numbers)),
    "C数字（その他）": C_numbers + [""] * (max_len - len(C_numbers))
})
render_scrollable_table(abc_summary_df)

# ✅ ⑧ 基本予想（2通り×5パターン）
st.header("⑧ 基本予想（パターン別 2通り×5種類）")
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
# ✅ ⑨ セレクト予想ルーレット
st.header("⑨ セレクト予想ルーレット")

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

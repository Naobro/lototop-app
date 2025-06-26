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

import pandas as pd
import streamlit as st

# ✅ CSS（ラベル列：薄青、ラベル文字：赤、内容：黒、背景：白）
st.markdown("""
<style>
.loto-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 16px;
    background-color: #fff;
    color: #000;
}
.loto-table th {
    background-color: #e0ebf7;
    color: red;
    font-weight: bold;
    padding: 8px 10px;
    text-align: left;
    white-space: nowrap;
    border: 1px solid #ccc;
}
.loto-table td {
    background-color: #fff;
    color: #000;
    padding: 8px 10px;
    text-align: center;
    border: 1px solid #ccc;
}
</style>
""", unsafe_allow_html=True)

# ✅ データ読み込み
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip()
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df[df["抽せん日"].notna()].copy()

# 数値化（本数字とボーナス）
for i in range(1, 7):
    df[f"第{i}数字"] = pd.to_numeric(df[f'第{i}数字'], errors='coerce')
df["ボーナス数字"] = pd.to_numeric(df["ボーナス数字"], errors="coerce")
df = df.dropna(subset=[f"第{i}数字" for i in range(1, 7)])

# 最新の当選回を取得
latest = df.iloc[-1]

# フォーマッター関数
def format_count(val):
    try:
        return f"{int(float(val)):,}口"
    except:
        return "該当なし"

def format_yen(val):
    try:
        return f"{int(float(str(val).replace(',', '').replace('円',''))):,}円"
    except:
        return "該当なし"

# ✅ HTMLテーブル構築
main_number_cells = ''.join([f"<td>{int(latest[f'第{i}数字'])}</td>" for i in range(1, 7)])
bonus_cell = f"<td colspan='6' style='color:red; font-weight:bold;'>{int(latest['ボーナス数字']):02}</td>"

st.markdown(f"""
<table class='loto-table'>
<tr><th>回別</th><td colspan='6'>第{latest['回号']}回</td></tr>
<tr><th>抽せん日</th><td colspan='6'>{latest['抽せん日'].strftime('%Y年%m月%d日')}</td></tr>
<tr><th>本数字</th>{main_number_cells}</tr>
<tr><th>ボーナス数字</th>{bonus_cell}</tr>
<tr><th>1等</th><td colspan='3'>{format_count(latest['1等口数'])}</td><td colspan='3'>{format_yen(latest['1等賞金'])}</td></tr>
<tr><th>2等</th><td colspan='3'>{format_count(latest['2等口数'])}</td><td colspan='3'>{format_yen(latest['2等賞金'])}</td></tr>
<tr><th>3等</th><td colspan='3'>{format_count(latest['3等口数'])}</td><td colspan='3'>{format_yen(latest['3等賞金'])}</td></tr>
<tr><th>4等</th><td colspan='3'>{format_count(latest['4等口数'])}</td><td colspan='3'>{format_yen(latest['4等賞金'])}</td></tr>
<tr><th>5等</th><td colspan='3'>{format_count(latest['5等口数'])}</td><td colspan='3'>{format_yen(latest['5等賞金'])}</td></tr>
<tr><th>キャリーオーバー</th><td colspan='6'>{format_yen(latest['キャリーオーバー'])}</td></tr>
</table>
""", unsafe_allow_html=True)

# ✅ ② ABC分類
st.header("② 直近24回の当選番号（ABC分類）")

# ✅ 念のため当選数字を再数値化（不正値対策）
for i in range(1, 7):
    df[f"第{i}数字"] = pd.to_numeric(df[f"第{i}数字"], errors="coerce")
df["ボーナス数字"] = pd.to_numeric(df["ボーナス数字"], errors="coerce")

# ✅ 欠損のある行は除外
df = df.dropna(subset=[f"第{i}数字" for i in range(1, 7)])

# ✅ 直近24回
df_recent = df.sort_values("回号", ascending=False).head(24).copy()

# ✅ ABC分類のための頻度集計
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
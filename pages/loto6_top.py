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

# 表に左寄せスタイルを適用する関数
def style_table(df):
    return df.style.set_table_styles(
        [{'selector': 'th', 'props': [('text-align', 'left')]},
         {'selector': 'td', 'props': [('text-align', 'left')]}]
    ).to_html()

# SSL対策
ssl._create_default_https_context = ssl._create_unverified_context

# CSV読み込み
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"
df = pd.read_csv(url, encoding="utf-8")
df.columns = df.columns.str.strip()
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df[df["抽せん日"].notna()].copy()
df = df.sort_values("抽せん日", ascending=True).reset_index(drop=True)

int_cols = ['回号', '第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', 'ボーナス数字']
yen_cols = ['1等賞金', '2等賞金', '3等賞金', '4等賞金', '5等賞金', 'キャリーオーバー']
for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
for col in yen_cols:
    df[col] = df[col].astype(str).str.replace(",", "").replace("該当なし", "0")
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

def format_yen(val):
    return f"{val:,}円" if val > 0 else "該当なし"

def format_count(val):
    return f"{val:,}口" if val > 0 else "該当なし"

latest = df.iloc[-1]
main_numbers = ' '.join([f"<b style='font-size:16px'>{latest[f'第{i}数字']}</b>" for i in range(1, 7)])
bonus_number = f"<b style='font-size:14px; color:red'>({latest['ボーナス数字']:02})</b>"

# 表示開始
st.title("ロト6 AI予想サイト")
st.header("① 最新の当選番号")
st.markdown(f"""
<table style='width:100%; border-collapse:collapse; text-align:right; font-size:16px;'>
<tr><th>回号</th><td><b>第{latest['回号']}回</b></td><th>抽せん日</th><td>{latest['抽せん日'].strftime('%Y年%m月%d日')}</td></tr>
<tr><th>本数字</th><td colspan='3'>{main_numbers}</td></tr>
<tr><th>ボーナス数字</th><td colspan='3'>{bonus_number}</td></tr>
<tr><th>1等</th><td colspan='3'>{format_yen(latest['1等賞金'])}</td></tr>
</table>
""", unsafe_allow_html=True)

# ② 直近24回の当選番号（ABC分類）
st.header("② 直近24回の当選番号（ABC分類）")
df_recent = df.sort_values("回号", ascending=False).head(24).copy()
digits = df_recent[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
counts = pd.Series(digits).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

abc_rows = []
for _, row in df_recent.iterrows():
    nums = [row[f"第{i}数字"] for i in range(1, 7)]
    abc = [ "B" if n in B_set else "A" if n in A_set else "C" for n in nums ]
    abc_rows.append({
        "回号": row["回号"],
        **{f"第{i}数字": row[f"第{i}数字"] for i in range(1, 7)},
        "ABC構成": ",".join(abc)
    })
abc_df = pd.DataFrame(abc_rows)

# 表示スタイル調整
wide_table_css = """
<style>
.wide-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    table-layout: fixed;
    word-break: break-word;
}
.wide-table th, .wide-table td {
    border: 1px solid #ccc;
    padding: 12px;
    text-align: center;
    white-space: nowrap;
}
.wide-table thead {
    background-color: #f2f2f2;
    font-weight: bold;
}
</style>
"""

def wide_table(df):
    return df.to_html(index=False, escape=False, classes="wide-table")

st.markdown(wide_table_css, unsafe_allow_html=True)
st.markdown("<div style='overflow-x:auto;'>", unsafe_allow_html=True)
st.markdown(wide_table(abc_df), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ③ パターン分析
st.header("③ パターン分析")
def get_distribution(row):
    pattern = []
    for n in sorted(row):
        if 1 <= n <= 9:
            pattern.append("1")
        elif 10 <= n <= 19:
            pattern.append("10")
        elif 20 <= n <= 29:
            pattern.append("20")
        elif 30 <= n <= 39:
            pattern.append("30")
        elif 40 <= n <= 43:
            pattern.append("40")
    return '-'.join(pattern)

pattern_series = df_recent[[f"第{i}数字" for i in range(1, 7)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

# ④ 各位の出現回数TOP5
st.header("④ 各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 7):
    number_groups['1'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(1, 9)].values)
    number_groups['10'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(10, 19)].values)
    number_groups['20'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(20, 29)].values)
    number_groups['30'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(30, 43)].values)

top5_df = pd.DataFrame({
    '1の位': pd.Series(number_groups['1']).value_counts().head(5).index.tolist(),
    '10の位': pd.Series(number_groups['10']).value_counts().head(5).index.tolist(),
    '20の位': pd.Series(number_groups['20']).value_counts().head(5).index.tolist(),
    '30の位': pd.Series(number_groups['30']).value_counts().head(5).index.tolist()
})
st.markdown(style_table(top5_df), unsafe_allow_html=True)

# ⑤ 各数字の出現回数TOP5
st.header("⑤ 各数字の出現回数TOP5")
results = {'順位': ['1位', '2位', '3位', '4位', '5位']}
for i in range(1, 7):
    col = f'第{i}数字'
    counts = pd.Series(df_recent[col]).value_counts().sort_values(ascending=False)
    top5 = counts.head(5)
    results[col] = [f"{n}（{c}回）" for n, c in zip(top5.index, top5.values)]
    while len(results[col]) < 5:
        results[col].append("")
top5_df = pd.DataFrame(results)
st.markdown(style_table(top5_df), unsafe_allow_html=True)

# ⑥ A・B・C数字分類一覧
st.header("⑥ A・B・C数字（出現頻度分類）")
count_series = pd.Series(df_recent[[f'第{i}数字' for i in range(1, 7)]].values.flatten()).value_counts()
A_numbers = count_series[(count_series >= 3) & (count_series <= 4)].index.tolist()
B_numbers = count_series[count_series >= 5].index.tolist()
C_numbers = sorted(list(set(range(1, 44)) - set(A_numbers) - set(B_numbers)))

max_len = max(len(A_numbers), len(B_numbers), len(C_numbers))
A_pad = A_numbers + [""] * (max_len - len(A_numbers))
B_pad = B_numbers + [""] * (max_len - len(B_numbers))
C_pad = C_numbers + [""] * (max_len - len(C_numbers))

abc_df = pd.DataFrame({
    "A数字（3〜4回）": A_pad,
    "B数字（5回以上）": B_pad,
    "C数字（その他）": C_pad
})
st.markdown(style_table(abc_df), unsafe_allow_html=True)
# ⑧ 基本予想（パターンごとに2通り×5種類 = 合計10通り）
st.header("基本予想（パターン別 2通り×5種類）")

# A・B数字からグループ分け
group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 40)),
    "40": list(range(40, 44)),
}
group_map = {}
for g, nums in group_dict.items():
    for n in nums:
        group_map[n] = g

A_set = set(A_numbers)
B_set = set(B_numbers)

# 前回の数字（ひっぱり用）
last_numbers = df_recent.iloc[0][[f"第{i}数字" for i in range(1, 7)]].tolist()

# パターン構成とラベル
pattern_list = [
    ("1-10-10-20-20-30", ["1", "10", "10", "20", "20", "30"]),
    ("1-10-20-20-30-40", ["1", "10", "20", "20", "30", "40"]),
    ("10-10-10-20-30-30", ["10", "10", "10", "20", "30", "30"]),
    ("1-1-10-20-20-30",   ["1", "1", "10", "20", "20", "30"]),
    ("1-10-20-20-20-30",  ["1", "10", "20", "20", "20", "30"]),
]

# 予想生成ロジック
def generate_from_group(group_key):
    candidates = [n for n in group_dict[group_key] if n in A_set] * 6 + \
                 [n for n in group_dict[group_key] if n in B_set] * 4
    return random.choice(candidates) if candidates else random.choice(group_dict[group_key])

# 出力開始
for label, pattern in pattern_list:
    st.markdown(f"**パターン: {label}**")
    predictions = []

    for _ in range(2):  # 各パターンで2通り
        nums = [generate_from_group(g) for g in pattern]

        # 引っ張り50%
        if random.random() < 0.5:
            pulls = random.sample(last_numbers, k=random.choice([1, 2]))
            replace_indices = random.sample(range(6), k=len(pulls))
            for i, val in zip(replace_indices, pulls):
                val_group = group_map.get(val)
                if val_group == pattern[i]:  # グループ一致時のみ置換
                    nums[i] = val

        # 重複除去＋補充
        unique = sorted(set(nums))
        while len(unique) < 6:
            extra = random.randint(1, 43)
            if extra not in unique and group_map.get(extra) in pattern:
                group_counts = {g: pattern.count(g) for g in set(pattern)}
                current_counts = {g: sum(1 for n in unique if group_map.get(n) == g) for g in group_counts}
                for g in group_counts:
                    if current_counts.get(g, 0) < group_counts[g] and group_map.get(extra) == g:
                        unique.append(extra)
                        break
        unique = sorted(unique)[:6]
        predictions.append(unique)

    pred_df = pd.DataFrame(predictions, columns=[f"第{i}数字" for i in range(1, 7)])
    st.markdown(style_table(pred_df), unsafe_allow_html=True)
    remove_numbers = st.multiselect("除外したい数字", list(range(1, 44)))
axis_numbers = st.multiselect("起点としたい数字", list(range(1, 44)))
if st.button("予想を生成"):
    available_numbers = set(range(1, 44)) - set(remove_numbers)  # ロト6は1〜43
    ranges = [
        list(range(1, 14)),
        list(range(2, 18)),
        list(range(5, 23)),
        list(range(8, 28)),
        list(range(14, 34)),
        list(range(20, 37))
    ]

    def fill_numbers(selected, available_in_range):
        pool = list(available_in_range)
        random.shuffle(pool)
        for num in pool:
            if num not in selected:
                selected.append(num)
                break

    predictions = []
    for _ in range(20):
        selected = list(axis_numbers)
        used = set(selected)
        for r in ranges:
            available_in_range = set(r) & available_numbers - used
            fill_numbers(selected, available_in_range)
            used = set(selected)
        selected = selected[:6]  # ロト6は6数字
        selected.sort()
        predictions.append(selected)

    pred_df = pd.DataFrame(predictions, columns=[f"第{i}数字" for i in range(1, 7)])
    st.markdown(style_table(pred_df), unsafe_allow_html=True)
import ssl
import pandas as pd
import streamlit as st

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(layout="wide")
st.title("ロト6 AI予想サイト")
st.header("① 最新の当選番号")

# CSV読み込み
df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv")

# 日付列を整形
df['日付'] = pd.to_datetime(df['日付'], errors='coerce').dt.date

# 数値変換対象列
int_cols = ['回号', '第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', 'ボーナス数字',
            '1等口数', '2等口数', '3等口数', '4等口数', '5等口数']
yen_cols = ['1等賞金', '2等賞金', '3等賞金', '4等賞金', '5等賞金', 'キャリーオーバー']

for col in int_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

for col in yen_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", "").replace("該当なし", "0")
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# 最新データ
latest = df.iloc[-1]

# 整形関数
def format_yen(val):
    return f"{val:,}円" if val > 0 else "該当なし"

def format_count(val):
    return f"{val:,}口" if val > 0 else "該当なし"

# 本数字とボーナス
main_numbers = ' '.join([f"<b style='font-size:20px'>{latest[f'第{i}数字']}</b>" for i in range(1, 7)])
bonus_number = f"<b style='font-size:18px; color:red'>({latest['ボーナス数字']})</b>"

# 表示
st.markdown(f"""
<table style='width:100%; border-collapse:collapse; text-align:right; font-size:16px;'>
<tr><th>回号</th><td><b>第{latest['回号']}回</b></td><th>抽選日</th><td>{latest['日付']}</td></tr>
<tr><th>本数字</th><td colspan='3'>{main_numbers}</td></tr>
<tr><th>ボーナス数字</th><td colspan='3'>{bonus_number}</td></tr>
<tr><th>1等</th><td>{format_count(latest['1等口数'])}</td><td colspan='2'>{format_yen(latest['1等賞金'])}</td></tr>
<tr><th>2等</th><td>{format_count(latest['2等口数'])}</td><td colspan='2'>{format_yen(latest['2等賞金'])}</td></tr>
<tr><th>3等</th><td>{format_count(latest['3等口数'])}</td><td colspan='2'>{format_yen(latest['3等賞金'])}</td></tr>
<tr><th>4等</th><td>{format_count(latest['4等口数'])}</td><td colspan='2'>{format_yen(latest['4等賞金'])}</td></tr>
<tr><th>5等</th><td>{format_count(latest['5等口数'])}</td><td colspan='2'>{format_yen(latest['5等賞金'])}</td></tr>
<tr><th>キャリーオーバー</th><td colspan='3' style='text-align:right'>{format_yen(latest['キャリーオーバー'])}</td></tr>
</table>
""", unsafe_allow_html=True)
# ② 直近24回の当選番号（ABC構成・ひっぱり・連続分析付き）
st.header("② 直近24回の当選番号")

# 最新データから直近24回を取得
df_recent = df.tail(24).sort_values(by="日付", ascending=False)

# 出現回数でABC分類セット作成
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 7)]].values.flatten()
counts = pd.Series(all_numbers).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

# 各行のABC構成・ひっぱり・連続を分析
abc_rows = []
prev_numbers = set()
pull_total = 0
cont_total = 0
abc_counts = {'A': 0, 'B': 0, 'C': 0}

for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 7)]
    sorted_nums = sorted(nums)

    abc = []
    for n in sorted_nums:
        if n in B_set:
            abc.append('B')
            abc_counts['B'] += 1
        elif n in A_set:
            abc.append('A')
            abc_counts['A'] += 1
        else:
            abc.append('C')
            abc_counts['C'] += 1
    abc_str = ','.join(abc)

    pulls = len(set(nums) & prev_numbers)
    if pulls > 0:
        pull_total += 1
    prev_numbers = set(nums)

    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    if cont:
        cont_total += 1

    abc_rows.append({
        '抽選日': row['日付'].strftime('%Y-%m-%d'),
        '第1数字': row['第1数字'], '第2数字': row['第2数字'], '第3数字': row['第3数字'],
        '第4数字': row['第4数字'], '第5数字': row['第5数字'], '第6数字': row['第6数字'],
        'ABC構成': abc_str,
        'ひっぱり': f"{pulls}個" if pulls else "なし",
        '連続': "あり" if cont else "なし"
    })

abc_df = pd.DataFrame(abc_rows)

# 💡 横幅を広げるCSS（wide-tableクラス使用）
wide_table_css = """
<style>
.wide-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 16px;
    table-layout: auto;
}
.wide-table th, .wide-table td {
    border: 1px solid #ccc;
    padding: 14px 18px;
    white-space: nowrap;
    text-align: center;
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
st.markdown(wide_table(abc_df), unsafe_allow_html=True)

# --- 出現傾向（ABC割合・ひっぱり率・連続率）テーブル ---
total_abc = sum(abc_counts.values())
a_perc = round(abc_counts['A'] / total_abc * 100, 1)
b_perc = round(abc_counts['B'] / total_abc * 100, 1)
c_perc = round(abc_counts['C'] / total_abc * 100, 1)
pull_rate = round(pull_total / 24 * 100, 1)
cont_rate = round(cont_total / 24 * 100, 1)

summary_df = pd.DataFrame({
    "分析項目": ["A数字割合", "B数字割合", "C数字割合", "ひっぱり率", "連続数字率"],
    "値": [f"{a_perc}%", f"{b_perc}%", f"{c_perc}%", f"{pull_rate}%", f"{cont_rate}%" ]
})

# 💡 分析テーブル中央揃え用スタイル
center_css = """
<style>
.center-table {
    width: 50%;
    margin-left: auto;
    margin-right: auto;
    border-collapse: collapse;
    font-size: 16px;
}
.center-table th, .center-table td {
    border: 1px solid #ccc;
    padding: 12px 16px;
    text-align: center;
}
.center-table thead {
    background-color: #f2f2f2;
    font-weight: bold;
}
</style>
"""
def center_table(df):
    return df.to_html(index=False, escape=False, classes="center-table")

st.markdown("#### 🔎 出現傾向（ABC割合・ひっぱり率・連続率）")
st.markdown(center_css, unsafe_allow_html=True)
st.markdown(center_table(summary_df), unsafe_allow_html=True)
# ④ パターン分析
st.header("④ パターン分析")
patterns = df_recent[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].apply(
    lambda x: '-'.join([str((int(num)-1)//10*10+1) if 1<=int(num)<=9 else str((int(num)//10)*10) for num in sorted(x)]), axis=1)
pattern_counts = patterns.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

# ⑤ 各位の出現回数TOP5
st.header("⑤ 各位の出現回数TOP5")
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

# ⑥ 各数字の出現回数TOP5
st.header("⑥ 各数字の出現回数TOP5")
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

# ⑦ A・B・C数字（出現頻度で分類）
st.header("⑦ A・B・C数字（出現頻度分類）")
all_numbers = df_recent[[f'第{i}数字' for i in range(1, 7)]].values.flatten()
count_series = pd.Series(all_numbers).value_counts()

A_numbers = count_series[(count_series >= 3) & (count_series <= 4)].index.tolist()
B_numbers = count_series[count_series >= 5].index.tolist()
C_numbers = sorted(list(set(range(1, 44)) - set(A_numbers) - set(B_numbers)))

# 表示を整形
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
st.header("⑧ 基本予想（パターン別 2通り×5種類）")

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
# ⑧ セレクト予想
st.header("⑧ セレクト予想")
axis_numbers = st.multiselect("軸数字を選んでください (最大3個まで)", options=range(1, 44), max_selections=3)
remove_numbers = st.multiselect("削除数字を選んでください (最大20個まで)", options=range(1, 44), max_selections=20)

if st.button("予想を生成"):
    available_numbers = set(range(1, 44)) - set(remove_numbers)
    ranges = [
        list(range(1, 17)),
        list(range(2, 25)),
        list(range(6, 33)),
        list(range(12, 39)),
        list(range(19, 43)),
        list(range(27, 44))
    ]

    def fill_numbers(selected, available_in_range):
        candidates = [n for n in available_in_range if n in B_numbers] + \
                     [n for n in available_in_range if n in A_numbers] + \
                     [n for n in available_in_range if n not in B_numbers and n not in A_numbers]
        for num in candidates:
            if num not in selected:
                selected.append(num)
                return

    predictions = []
    for _ in range(20):
        selected = list(axis_numbers)
        for r in ranges:
            available_in_range = list(set(r) & available_numbers)
            fill_numbers(selected, available_in_range)
        selected = selected[:6]
        selected.sort()
        predictions.append(selected)

    pred_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"])
    st.markdown(style_table(pred_df), unsafe_allow_html=True)
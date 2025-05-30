# 【1/3】全コード：前半部（データ取得～出現傾向分析）
import pandas as pd
import random
import streamlit as st

st.set_page_config(layout="wide")
st.title("ミニロト AI予想サイト")

# CSS適用
st.markdown("""
<style>
table { width: 100%; border-collapse: collapse; text-align: center; font-size: 16px; }
th, td { border: 1px solid #ccc; padding: 8px; }
thead { background-color: #f2f2f2; font-weight: bold; }
.wide-table td { white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

def style_table(df):
    return df.to_html(index=False, escape=False, classes="wide-table")

# 読み込み
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(csv_path)
df = df.rename(columns={"日付": "抽せん日"})
df['抽せん日'] = pd.to_datetime(df['抽せん日'], errors='coerce')
df = df.dropna(subset=['抽せん日'])
df = df.sort_values(by="抽せん日", ascending=False)
df_recent = df.head(24)

# ① 最新の当選番号表示
df_latest = df.iloc[0]
st.header("① 最新の当選番号")
latest_html = f"""
<table>
<tr><th>回号</th><td>第{df_latest['回号']}回</td><th>抽選日</th><td>{df_latest['抽せん日'].strftime('%Y-%m-%d')}</td></tr>
<tr><th>本数字</th><td colspan='3'>{df_latest['第1数字']} {df_latest['第2数字']} {df_latest['第3数字']} {df_latest['第4数字']} {df_latest['第5数字']}</td></tr>
<tr><th>ボーナス</th><td colspan='3'>{df_latest['ボーナス数字']}</td></tr>
</table>
"""
st.markdown(latest_html, unsafe_allow_html=True)

# 賞金表示
def format_yen(val):
    return f"<b>{int(val):,}円</b>" if pd.notnull(val) else "-"
prize_html = f"""
<table><thead><tr><th>等級</th><th>口数</th><th>当選金額</th></tr></thead><tbody>
<tr><td>1等</td><td>{df_latest['1等口数']}口</td><td>{format_yen(df_latest['1等賞金'])}</td></tr>
<tr><td>2等</td><td>{df_latest['2等口数']}口</td><td>{format_yen(df_latest['2等賞金'])}</td></tr>
<tr><td>3等</td><td>{df_latest['3等口数']}口</td><td>{format_yen(df_latest['3等賞金'])}</td></tr>
<tr><td>4等</td><td>{df_latest['4等口数']}口</td><td>{format_yen(df_latest['4等賞金'])}</td></tr>
</tbody></table>
"""
st.markdown(prize_html, unsafe_allow_html=True)

# ② 直近24回 当選番号 + ABC + 引っ張り + 連続分析
st.header("② 直近24回の当選番号")
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts = pd.Series(all_numbers).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

abc_rows = []
prev_numbers = set()
pull_total = 0
cont_total = 0
abc_counts = {'A': 0, 'B': 0, 'C': 0}
for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 6)]
    sorted_nums = sorted(nums)
    abc = []
    for n in sorted_nums:
        if n in B_set:
            abc.append('B'); abc_counts['B'] += 1
        elif n in A_set:
            abc.append('A'); abc_counts['A'] += 1
        else:
            abc.append('C'); abc_counts['C'] += 1
    pulls = len(set(nums) & prev_numbers)
    pull_total += bool(pulls)
    prev_numbers = set(nums)
    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_total += cont
    abc_rows.append({
        '抽選日': row['抽せん日'].strftime('%Y-%m-%d'),
        **{f"第{i}数字": row[f"第{i}数字"] for i in range(1, 6)},
        'ABC構成': ','.join(abc),
        'ひっぱり': f"{pulls}個" if pulls else "なし",
        '連続': "あり" if cont else "なし"
    })
abc_df = pd.DataFrame(abc_rows)
st.markdown(style_table(abc_df), unsafe_allow_html=True)

# 出現傾向分析
total_abc = sum(abc_counts.values())
a_perc = round(abc_counts['A'] / total_abc * 100, 1)
b_perc = round(abc_counts['B'] / total_abc * 100, 1)
c_perc = round(abc_counts['C'] / total_abc * 100, 1)
pull_rate = round(pull_total / 24 * 100, 1)
cont_rate = round(cont_total / 24 * 100, 1)
st.markdown("#### 🔎 出現傾向（ABC割合・ひっぱり率・連続率）")
sum_df = pd.DataFrame({"分析項目": ["A割合", "B割合", "C割合", "ひっぱり率", "連続率"],
                       "値": [f"{a_perc}%", f"{b_perc}%", f"{c_perc}%", f"{pull_rate}%", f"{cont_rate}%"]})
st.markdown(style_table(sum_df), unsafe_allow_html=True)
# 【2/3】全コード：中盤（統計・ABC分類・基本予想）

# ③ 分布パターン
st.header("③ 分布パターン")
def get_distribution(row):
    pattern = []
    for n in sorted(row):
        if 1 <= n <= 9:
            pattern.append("1")
        elif 10 <= n <= 19:
            pattern.append("10")
        else:
            pattern.append("20")
    return '-'.join(pattern)
pattern_series = df_recent[[f"第{i}数字" for i in range(1, 6)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

# 各位の出現回数TOP5
st.header("④ 各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 6):
    number_groups['1'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(1, 9)].tolist()
    number_groups['10'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(10, 19)].tolist()
    number_groups['20'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(20, 29)].tolist()
    number_groups['30'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(30, 31)].tolist()

def pad_top_values(series, length=5):
    values = series.value_counts().head(length).index.tolist()
    return values + [""] * (length - len(values))

top5_df = pd.DataFrame({
    '1の位': pad_top_values(pd.Series(number_groups['1'])),
    '10の位': pad_top_values(pd.Series(number_groups['10'])),
    '20の位': pad_top_values(pd.Series(number_groups['20'])),
    '30の位': pad_top_values(pd.Series(number_groups['30']))
})
st.markdown(style_table(top5_df), unsafe_allow_html=True)

# 各数字の出現回数TOP3（位置別）
st.header("⑤ 各数字の出現回数TOP3（位置別）")
position_result = {'順位': ['1位', '2位', '3位']}
for i in range(1, 6):
    col = f'第{i}数字'
    counts = df_recent[col].value_counts().sort_values(ascending=False).head(3)
    position_result[col] = [f"{n}（{c}回）" for n, c in zip(counts.index, counts.values)] + [""] * (3 - len(counts))
st.markdown(style_table(pd.DataFrame(position_result)), unsafe_allow_html=True)

# ABC分類
st.header("⑥ A・B・C数字（出現頻度分類）")
A = counts[(counts >= 3) & (counts <= 4)].index.tolist()
B = counts[counts >= 5].index.tolist()
C = list(set(range(1, 32)) - set(A) - set(B))
max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))
abc_class_df = pd.DataFrame({"A数字（3〜4回）": A, "B数字（5回以上）": B, "C数字（その他）": C})
st.markdown(style_table(abc_class_df), unsafe_allow_html=True)

# ⑦ 基本予想（パターン上位＋電卓法）
st.header("⑦ 基本予想（人気パターン & 電卓式）")

# パターン上位ベース
pattern_pool = pattern_counts['パターン'].tolist()
pattern_weights = [3, 3, 2, 1, 1]  # 1位〜5位までに割り当てる個数
column_ranges = {
    1: list(range(1, 10)),    # 1〜9
    2: list(range(10, 19)),   # 10〜18
    3: list(range(19, 22)),   # 19〜21
    4: list(range(22, 28)),   # 22〜27
    5: list(range(28, 32))    # 28〜31
}
pattern_predictions = []
for i, p in enumerate(pattern_pool[:5]):
    for _ in range(pattern_weights[i]):
        pattern_parts = list(map(int, p.split('-')))
        nums = []
        for part in pattern_parts:
            pool = list(set(column_ranges[int(part)]) - set(nums))
            if pool:
                nums.append(random.choice(pool))
        nums = sorted(nums)
        if not (any(b - a == 1 for a, b in zip(nums, nums[1:])) and nums[2] - nums[0] == 2):  # 3連避け
            pattern_predictions.append(nums)

# 電卓式予想
def calculate_number_with_formula(numbers, weights):
    total = sum(numbers)
    predicted_numbers = [min(round(total / w), 31) for w in weights]
    return sorted(set(predicted_numbers))[:5]

calc_results = []
weights_list = [[2.5, 5, 3.2, 2.3, 1.8], [3, 2, 3, 2, 2]]
for weights in weights_list:
    numbers = random.sample(range(1, 32), 5)
    calc_results.append(calculate_number_with_formula(numbers, weights))

basic_df = pd.DataFrame(pattern_predictions[:8] + calc_results, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字"])
st.markdown(style_table(basic_df), unsafe_allow_html=True)
# 【3/3】全コード：後半部（セレクト予想・検証機能）
import itertools

# 出現パターン分析（1-10-20など）
def get_distribution(row):
    pattern = []
    for n in sorted(row):
        if 1 <= n <= 9:
            pattern.append("1")
        elif 10 <= n <= 19:
            pattern.append("10")
        else:
            pattern.append("20")
    return '-'.join(pattern)

pattern_series = df_recent[[f"第{i}数字" for i in range(1, 6)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.header("③ 分布パターンと頻出構成")
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

# 各位出現TOP5
st.header("④ 各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 6):
    number_groups['1'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(1, 9)].tolist()
    number_groups['10'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(10, 19)].tolist()
    number_groups['20'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(20, 29)].tolist()
    number_groups['30'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(30, 31)].tolist()

def pad_top(series):
    values = series.value_counts().head(5).index.tolist()
    return values + [""] * (5 - len(values))

top5_df = pd.DataFrame({
    '1の位': pad_top(pd.Series(number_groups['1'])),
    '10の位': pad_top(pd.Series(number_groups['10'])),
    '20の位': pad_top(pd.Series(number_groups['20'])),
    '30の位': pad_top(pd.Series(number_groups['30']))
})
st.markdown(style_table(top5_df), unsafe_allow_html=True)

# 位置別出現回数TOP3
st.header("⑤ 各数字の出現回数TOP3（位置別）")
position_result = {'順位': ['1位', '2位', '3位']}
for i in range(1, 6):
    col = f'第{i}数字'
    top3 = df_recent[col].value_counts().head(3)
    position_result[col] = [f"{n}（{c}回）" for n, c in zip(top3.index, top3.values)] + [""] * (3 - len(top3))
st.markdown(style_table(pd.DataFrame(position_result)), unsafe_allow_html=True)

# A/B/C分類表示
st.header("⑥ A・B・C数字（出現頻度分類）")
A = counts[(counts >= 3) & (counts <= 4)].index.tolist()
B = counts[counts >= 5].index.tolist()
C = list(set(range(1, 32)) - set(A) - set(B))
max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))
abc_class_df = pd.DataFrame({"A（3〜4回）": A, "B（5回以上）": B, "C（その他）": C})
st.markdown(style_table(abc_class_df), unsafe_allow_html=True)

# 基本予想（頻出パターン×ランダム）
st.header("⑦ 基本予想（出現構成 + 電卓法）")
pattern_weights = pattern_counts.head(5)['パターン'].tolist()
predicts = []

# 電卓法
weights = [4.1, 6.3, 5.7, 7.2, 5.5]
def calculate_number_with_formula(numbers):
    total = sum(numbers)
    pred = [min(round(total / w), 31) for w in weights]
    return sorted(set(pred))[:5]

# 10通り予測（上位5構成 + ランダム）
used_patterns = pattern_weights[:5] + random.choices(pattern_counts['パターン'][5:], k=5)
for p in used_patterns:
    parts = list(map(int, p.split('-')))
    nums = []
    for part in parts:
        pool = list(set(range(part, part+9)) - set(nums))
        if pool:
            nums.append(random.choice(pool))
    if len(nums) >= 5:
        nums = calculate_number_with_formula(nums)
    predicts.append(sorted(nums))

predict_df = pd.DataFrame(predicts, columns=["第1","第2","第3","第4","第5"])
st.markdown(style_table(predict_df), unsafe_allow_html=True)

# セレクト予想
st.header("⑧ セレクト予想")
axis = st.multiselect("軸数字（最大3）", list(range(1,32)), max_selections=3)
remove = st.multiselect("除外数字（最大20）", list(range(1,32)), max_selections=20)

def generate_selected(axis, remove, count=10):
    A_nums = [int(n) for n in abc_class_df['A（3〜4回）'] if n != '']
    B_nums = [int(n) for n in abc_class_df['B（5回以上）'] if n != '']
    C_nums = [int(n) for n in abc_class_df['C（その他）'] if n != '']
    ranges = [range(1,10), range(10,19), range(19,22), range(22,28), range(28,32)]
    full_pool = set(A_nums + B_nums + C_nums) - set(remove)

    def pick_by_range(pool):
        sel = []
        for r in ranges:
            choices = list(set(r) & pool)
            if choices:
                sel.append(random.choice(choices))
        return sel

    results = []
    for _ in range(count):
        nums = list(axis)
        pool = full_pool - set(nums)
        nums += pick_by_range(pool)
        nums = list(set(nums))[:5]
        while len(nums) < 5:
            pick = random.choice(list(pool))
            if pick not in nums:
                nums.append(pick)
        results.append(sorted(nums))
    return results

if st.button("予想を生成"):
    pred = generate_selected(axis, remove)
    st.markdown(style_table(pd.DataFrame(pred, columns=["第1","第2","第3","第4","第5"])), unsafe_allow_html=True)

# 検証機能
st.header("⑨ 予想検証機能")
uploaded = st.file_uploader("検証する予想CSVファイルをアップロード（5列・各行予想）")
if uploaded is not None:
    test_df = pd.read_csv(uploaded)
    win_numbers = set([df_latest[f"第{i}数字"] for i in range(1, 6)])
    def match_count(row):
        return len(set(row) & win_numbers)
    test_df['一致数'] = test_df.apply(match_count, axis=1)
    st.markdown("#### 検証結果：")
    st.markdown(style_table(test_df), unsafe_allow_html=True)
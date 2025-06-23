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
df = df.rename(columns={"抽せん日": "抽せん日"})
df['抽せん日'] = pd.to_datetime(df['抽せん日'], errors='coerce')
df = df.dropna(subset=['抽せん日'])
df = df.sort_values(by="抽せん日", ascending=False)
df_recent = df.head(24)

# 最新データの取得
df_latest = df.iloc[0]

st.header("① 最新の当選番号")

# 太字・赤字・大きなフォントの本数字とボーナス数字
main_numbers = ' '.join([f"<span style='color:red; font-weight:bold; font-size:24px'>{df_latest[f'第{i}数字']}</span>" for i in range(1, 6)])
bonus_number = f"<span style='color:red; font-weight:bold; font-size:24px'>{df_latest['ボーナス数字']}</span>"

latest_html = f"""
<table>
<tr><th>回号</th><td><b>第{df_latest['回号']}回</b></td><th>抽選日</th><td>{df_latest['抽せん日'].strftime('%Y-%m-%d')}</td></tr>
<tr><th>本数字</th><td colspan='3'>{main_numbers}</td></tr>
<tr><th>ボーナス</th><td colspan='3'>{bonus_number}</td></tr>
</table>
"""
st.markdown(latest_html, unsafe_allow_html=True)

# 賞金表示（右寄せ・整数化）
def format_number(val):
    if pd.isnull(val):
        return "-"
    return f"{int(val):,}"

prize_html = f"""
<table style="text-align:right;">
<thead><tr><th style='text-align:left;'>等級</th><th>口数</th><th>当選金額</th></tr></thead><tbody>
<tr><td style='text-align:left;'>1等</td><td>{format_number(df_latest['1等口数'])}口</td><td>{format_number(df_latest['1等賞金'])}円</td></tr>
<tr><td style='text-align:left;'>2等</td><td>{format_number(df_latest['2等口数'])}口</td><td>{format_number(df_latest['2等賞金'])}円</td></tr>
<tr><td style='text-align:left;'>3等</td><td>{format_number(df_latest['3等口数'])}口</td><td>{format_number(df_latest['3等賞金'])}円</td></tr>
<tr><td style='text-align:left;'>4等</td><td>{format_number(df_latest['4等口数'])}口</td><td>{format_number(df_latest['4等賞金'])}円</td></tr>
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

# A数字・B数字を取得（文字列→int変換）
A_nums = [int(n) for n in abc_class_df['A（3〜4回）'] if n != '']
B_nums = [int(n) for n in abc_class_df['B（5回以上）'] if n != '']

# 位別に分類
def classify_by_digit(nums):
    one_digit = sorted([n for n in nums if 1 <= n <= 9])
    ten_digit = sorted([n for n in nums if 10 <= n <= 19])
    twenty_digit = sorted([n for n in nums if 20 <= n <= 31])
    return one_digit, ten_digit, twenty_digit

a1, a10, a20 = classify_by_digit(A_nums)
b1, b10, b20 = classify_by_digit(B_nums)

# 表示用 DataFrame に整形
max_len = max(len(a1), len(a10), len(a20), len(b1), len(b10), len(b20))
def pad(lst):
    return lst + [''] * (max_len - len(lst))

digit_df = pd.DataFrame({
    "位": ["1の位"] * max_len + ["10の位"] * max_len + ["20/30の位"] * max_len,
    "A数字": pad(a1) + pad(a10) + pad(a20),
    "B数字": pad(b1) + pad(b10) + pad(b20),
})

st.header("⑥-A A数字・B数字の位別分類")
st.markdown(style_table(digit_df), unsafe_allow_html=True)

# 最新回（前回）の当選番号だけを表示
st.header("⑥-B 前回の当選番号（ひっぱり検討用）")

latest_numbers = [df_latest[f"第{i}数字"] for i in range(1, 6)]
latest_df = pd.DataFrame({
    "前回当選番号": latest_numbers
})

st.markdown(style_table(latest_df), unsafe_allow_html=True)

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

import pandas as pd
from collections import Counter

# CSV読み込み
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(csv_path)

# 整形処理
df.columns = df.columns.str.strip()
df = df.rename(columns={"抽せん日": "抽せん日"})
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df.dropna(subset=["抽せん日"])
df = df.sort_values(by="抽せん日", ascending=False).head(24)

# 本数字カラム抽出
number_cols = [col for col in df.columns if "第" in col and "数字" in col]
recent_numbers = df[number_cols].values

# カウント初期化
pull_counter = Counter()
total_counter = Counter()
last_numbers = set()

# 各回の数字出現とひっぱり記録
for row in recent_numbers:
    current_set = set(row)
    for num in row:
        total_counter[num] += 1
        if num in last_numbers:
            pull_counter[num] += 1
    last_numbers = current_set

# 結果整形
pull_stats = []
for num in sorted(total_counter):
    pulls = pull_counter.get(num, 0)
    total = total_counter[num]
    rate = pulls / total if total else 0
    pull_stats.append({
        "数字": num,
        "出現回数": total,
        "ひっぱり回数": pulls,
        "ひっぱり率": f"{rate:.1%}"
    })

# 出現回数順に並べ替え
pull_stats_df = pd.DataFrame(pull_stats).sort_values(by="出現回数", ascending=False)
print(pull_stats_df)

# 🔁 連続ペアの出現回数 & 🔄 ひっぱり回数とひっぱり率の分析
st.header("連続数字ペア & ひっぱり傾向")

from collections import Counter

# 最新24回の本数字を取得
recent_numbers = df.sort_values(by="抽せん日", ascending=False).head(24)
numbers_list = recent_numbers[[f"第{i}数字" for i in range(1, 6)]].values.tolist()

# 🔁 連続数字ペア（例: 25-26）
consecutive_pairs = []
for row in numbers_list:
    sorted_row = sorted(row)
    for a, b in zip(sorted_row, sorted_row[1:]):
        if b - a == 1:
            consecutive_pairs.append(f"{a}-{b}")
consec_counter = Counter(consecutive_pairs)

consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

# 🔄 ひっぱり分析（1回前に出た数字が次回にも出たか）
all_numbers = [set(row) for row in numbers_list]
pull_counter = Counter()
total_counter = Counter()

for i in range(1, len(all_numbers)):
    current = all_numbers[i]
    prev = all_numbers[i - 1]
    for num in current:
        total_counter[num] += 1
        if num in prev:
            pull_counter[num] += 1

# 出現回数がゼロで割るのを避けるため total_counter で存在する数字だけを対象に
pull_data = []
for num in sorted(total_counter.keys()):
    total = total_counter[num]
    pulls = pull_counter.get(num, 0)
    rate = f"{round(pulls / total * 100, 1)}%" if total > 0 else "-"
    pull_data.append([num, total, pulls, rate])

pull_df = pd.DataFrame(pull_data, columns=["数字", "出現回数", "ひっぱり回数", "ひっぱり率"])
pull_df = pull_df.sort_values(by="ひっぱり率", ascending=False)

# 表示
st.subheader("🔁 連続ペア 出現ランキング")
st.markdown(style_table(consec_df), unsafe_allow_html=True)

st.header("分布パターン")

def get_distribution(row):
    pattern = []
    for n in sorted(row):
        if 1 <= n <= 9:
            pattern.append("1")
        elif 10 <= n <= 19:
            pattern.append("10")
        else:  # ✅ 20〜31 をすべて 20 に分類
            pattern.append("20")
    return '-'.join(pattern)

pattern_series = df_recent[[f"第{i}数字" for i in range(1, 6)]].apply(get_distribution, axis=1)
pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

st.header("④ 各位の出現回数TOP5")

# 20〜31をまとめて1つのグループに
number_groups = {'1': [], '10': [], '20/30': []}
for i in range(1, 6):
    number_groups['1'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(1, 9)].tolist()
    number_groups['10'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(10, 19)].tolist()
    number_groups['20/30'] += df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(20, 31)].tolist()

def pad_top_values(series, length=5):
    values = series.value_counts().head(length).index.tolist()
    return values + [""] * (length - len(values))

top5_df = pd.DataFrame({
    '1の位': pad_top_values(pd.Series(number_groups['1'])),
    '10の位': pad_top_values(pd.Series(number_groups['10'])),
    '20/30の位': pad_top_values(pd.Series(number_groups['20/30']))
})
st.markdown(style_table(top5_df), unsafe_allow_html=True)

st.header("⑤ 各数字の出現回数TOP5（位置別）")

# ラベルを5行に拡張
position_result = {'順位': ['1位', '2位', '3位', '4位', '5位']}

for i in range(1, 6):
    col = f'第{i}数字'
    counts = df_recent[col].value_counts().sort_values(ascending=False).head(5)
    # 欠損時に空文字で補完
    top5 = [f"{n}（{c}回）" for n, c in zip(counts.index, counts.values)] + [""] * (5 - len(counts))
    position_result[col] = top5

# 表示
st.markdown(style_table(pd.DataFrame(position_result)), unsafe_allow_html=True)
# ABC分析用コード（完全動作版）
import pandas as pd
from collections import Counter

# CSV読込
df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv")

# 列名の空白除去
df.columns = df.columns.str.strip()

# 抽せん日変換
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")

# 直近24回分抽出
latest24 = df.sort_values("抽せん日", ascending=False).head(24)

# 本数字のみ取り出し
number_cols = [col for col in df.columns if "第" in col and "数字" in col]
flat_numbers = latest24[number_cols].values.flatten()

# 出現回数カウント
counts = Counter(flat_numbers)

# ABC分類ルール
A = [num for num, cnt in counts.items() if 3 <= cnt <= 4]
B = [num for num, cnt in counts.items() if cnt >= 5]
C = [num for num in range(1, 32) if num not in A + B]

# 表整形
max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))

abc_class_df = pd.DataFrame({
    "A数字（3〜4回）": sorted(A, key=lambda x: (x == "", x)),
    "B数字（5回以上）": sorted(B, key=lambda x: (x == "", x)),
    "C数字（その他）": sorted(C, key=lambda x: (x == "", x))
})

# Streamlit用：テーブル表示（style_table関数が必要）
# st.markdown(style_table(abc_class_df), unsafe_allow_html=True)
st.header("⑦ 基本予想（人気パターン & 電卓式）")

# パターン上位ベース
pattern_pool = pattern_counts['パターン'].tolist()
pattern_weights = [3, 3, 2, 1, 1]  # 1位〜5位までに割り当てる個数
column_ranges = {
    '1': list(range(1, 10)),     # 1〜9
    '10': list(range(10, 20)),   # 10〜19
    '20': list(range(20, 30)),   # 20〜29
    '30': list(range(30, 32))    # 30〜31
}

pattern_predictions = []
for i, p in enumerate(pattern_pool[:5]):
    for _ in range(pattern_weights[i]):
        pattern_parts = p.split('-')  # ← ここを修正
        nums = []
        for part in pattern_parts:
            pool = list(set(column_ranges[part]) - set(nums))  # partは文字列のまま使う
            if pool:
                nums.append(random.choice(pool))
        nums = sorted(nums)
        # 3連番禁止条件
        if not (any(b - a == 1 for a, b in zip(nums, nums[1:])) and nums[2] - nums[0] == 2):
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

# A/B/C分類表示
st.header("⑥ A・B・C数字（出現頻度分類）")

from collections import Counter

# 最新24回の本数字を取得
latest24_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()

# 出現回数をカウント → pandas.Series へ変換
counts = Counter(latest24_numbers)
counts_series = pd.Series(counts)

# ABC分類ルールに基づいて分類
A = counts_series[(counts_series >= 3) & (counts_series <= 4)].index.tolist()
B = counts_series[counts_series >= 5].index.tolist()
C = [num for num in range(1, 32) if num not in A + B]

# 表形式に整形
max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))

abc_class_df = pd.DataFrame({
    "A（3〜4回）": sorted(A, key=lambda x: (x == "", x)),
    "B（5回以上）": sorted(B, key=lambda x: (x == "", x)),
    "C（その他）": sorted(C, key=lambda x: (x == "", x))
})

st.markdown(style_table(abc_class_df), unsafe_allow_html=True)
# 基本予想（頻出パターン×ランダム）
import pandas as pd
import random
from collections import Counter
import streamlit as st

# ---- 必要な関数定義 ----
def calculate_number_with_formula(numbers):
    weights = [4.1, 6.3, 5.7, 7.2, 5.5]
    total = sum(numbers)
    pred = [min(round(total / w), 31) for w in weights]
    return sorted(set(pred))[:5]

def pad_pattern(pattern):
    parts = pattern.split('-')
    return parts + [''] * (5 - len(parts))

# ---- 分布パターン定義 ----
range_map = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 32)),
    
}

# ---- 分布パターンのランキング取得（1 / 10 / 20 の3区分に統一） ----
pattern_series = df_recent[[f"第{i}数字" for i in range(1, 6)]].apply(lambda row: '-'.join([
    "1" if 1 <= n <= 9 else
    "10" if 10 <= n <= 19 else
    "20"  # ✅ 20〜31 すべてを20に分類
    for n in sorted(row)
]), axis=1)

pattern_counts = pattern_series.value_counts().reset_index()
pattern_counts.columns = ["パターン", "出現回数"]

# ---- 上位3パターン（3個, 2個, 2個） + ランダム3個 ----
top_patterns = pattern_counts["パターン"].tolist()
used_patterns = (
    [top_patterns[0]] * 3 +
    [top_patterns[1]] * 2 +
    [top_patterns[2]] * 2 +
    random.sample(top_patterns[3:], 3)
)

# ---- ABC情報（A+Bのみ使用） ----
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts = pd.Series(all_numbers).value_counts()
A = counts[(counts >= 3) & (counts <= 4)].index.tolist()
B = counts[counts >= 5].index.tolist()
AB_pool = set(A + B)

# ---- 出現TOP5（位置別） ----
top_by_pos = {}
for i in range(1, 6):
    top_by_pos[i] = df_recent[f"第{i}数字"].value_counts().head(5).index.tolist()

# ---- パターンに基づく予想生成 ----
predicts = []
for p in used_patterns:
    nums = []
    used = set()
    parts = pad_pattern(p)
    for idx, part in enumerate(parts):
        pool = list(set(range_map[part]) & AB_pool - used)
        # 位置ごとのTOP数字優先
        if top_by_pos[idx + 1]:
            pool = sorted(pool, key=lambda x: x not in top_by_pos[idx + 1])
        if pool:
            pick = random.choice(pool)
            nums.append(pick)
            used.add(pick)
    # 保険：不足時にAB内から補充
    while len(nums) < 5:
        candidate = random.choice(list(AB_pool - used))
        nums.append(candidate)
        used.add(candidate)
    predicts.append(sorted(nums))

# ---- DataFrameにして表示 ----
predict_df = pd.DataFrame(predicts, columns=["第1", "第2", "第3", "第4", "第5"])
st.header("⑦ 基本予想（構成・出現・ABC優先）")
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
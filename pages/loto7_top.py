import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

st.set_page_config(layout="centered")
check_password()  # ✅ これが必須です

import ssl
import pandas as pd
import random

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
# ✅ 表示用関数（DataFrame → HTMLテーブル）
def style_table(df):
    return df.to_html(index=False, escape=False)

# 35行目以降に以下を追加
def load_data():
    df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv")
    df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
    df = df.sort_values(by="抽せん日").reset_index(drop=True)
    return df

df = load_data()
latest = df.iloc[-1]

# 最新の当選番号（①）
# タイトル
st.title("ロト7 AI予想サイト")
st.header(" 最新の当選番号")

# ✅ 最新データ取得
latest = df.iloc[-1]

# ✅ フォーマット関数（口数＋金額）
def format_count(val):
    try:
        return f"{int(float(val)):,}口"
    except:
        return "-"

def format_yen(val):
    try:
        return f"{int(float(val)):,}円"
    except:
        return "-"


# ✅ 本数字・ボーナス数字をセルで分割
main_number_cells = ''.join([f"<td class='center'>{int(latest[f'第{i}数字'])}</td>" for i in range(1, 8)])
bonus_cells = ''.join([
    f"<td class='center' style='color:red; font-weight:bold;'>{int(latest['BONUS数字1'])}</td>",
    f"<td class='center' style='color:red; font-weight:bold;'>{int(latest['BONUS数字2'])}</td>"
])

# ✅ HTML表示
st.markdown(f"""
<table class='loto-table'>
<tr><th>回号</th><td colspan='7' class='center'>第{latest['回号']}回</td></tr>
<tr><th>抽せん日</th><td colspan='7' class='center'>{latest['抽せん日'].strftime('%Y年%m月%d日')}</td></tr>
<tr><th>本数字</th>{main_number_cells}</tr>
<tr><th>ボーナス数字</th>{bonus_cells}</tr>
<tr><th>1等</th><td colspan='3' class='right'>{format_count(latest['1等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['1等賞金'])}</td></tr>
<tr><th>2等</th><td colspan='3' class='right'>{format_count(latest['2等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['2等賞金'])}</td></tr>
<tr><th>3等</th><td colspan='3' class='right'>{format_count(latest['3等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['3等賞金'])}</td></tr>
<tr><th>4等</th><td colspan='3' class='right'>{format_count(latest['4等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['4等賞金'])}</td></tr>
<tr><th>5等</th><td colspan='3' class='right'>{format_count(latest['5等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['5等賞金'])}</td></tr>
<tr><th>6等</th><td colspan='3' class='right'>{format_count(latest['6等口数'])}</td><td colspan='4' class='right'>{format_yen(latest['6等賞金'])}</td></tr>
<tr><th>キャリーオーバー</th><td colspan='7' class='right'>{format_yen(latest['キャリーオーバー'])}</td></tr>
</table>
""", unsafe_allow_html=True)
# ✅ ② 直近24回の当選番号（ABC構成・ひっぱり・連続分析付き）
st.header("② 直近24回の当選番号（ABC構成・ひっぱり・連続分析付き）")

# 最新データから直近24回を取得
df_recent = df.tail(24).sort_values(by="抽せん日", ascending=False).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")

# 出現回数でABC分類セット作成（7数字分に対応）
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
all_numbers = pd.to_numeric(all_numbers, errors="coerce")
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
    nums = [int(row[f"第{i}数字"]) for i in range(1, 8)]
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
        '抽せん日': row['抽せん日'].strftime('%Y-%m-%d'),
        '第1数字': row['第1数字'], '第2数字': row['第2数字'], '第3数字': row['第3数字'],
        '第4数字': row['第4数字'], '第5数字': row['第5数字'], '第6数字': row['第6数字'],
        '第7数字': row['第7数字'], 'ABC構成': abc_str,
        'ひっぱり': f"{pulls}個" if pulls else "なし",
        '連続': "あり" if cont else "なし"
    })

abc_df = pd.DataFrame(abc_rows)

# ✅ スクロール可能なテーブル表示（共通スタイルで）
st.markdown(abc_df.to_html(index=False), unsafe_allow_html=True)

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



st.markdown("#### 🔎 出現傾向（ABC割合・ひっぱり率・連続率）")

import pandas as pd
from collections import Counter
import streamlit as st

st.header("⑩ 連続数字ペア & ひっぱり傾向")

# 直近24回のデータを取得（dfは直近全データ）
latest_24 = df.tail(24)

# ロト7は本数字が7個
numbers_list = latest_24[[f"第{i}数字" for i in range(1, 8)]].values.tolist()

# 🔁 連続ペア（例: 25-26）
consecutive_pairs = []
for row in numbers_list:
    sorted_row = sorted(row)
    for a, b in zip(sorted_row, sorted_row[1:]):
        if b - a == 1:
            consecutive_pairs.append(f"{a}-{b}")
consec_counter = Counter(consecutive_pairs)
consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"])
consec_df = consec_df.sort_values(by="出現回数", ascending=False).reset_index(drop=True)

# 🔄 ひっぱり分析（前回からのひっぱり）
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

# 出現回数とひっぱり率計算
pull_data = []
for num in sorted(total_counter.keys()):
    total = total_counter[num]
    pulls = pull_counter.get(num, 0)
    rate = f"{round(pulls / total * 100, 1)}%" if total > 0 else "-"
    pull_data.append([num, total, pulls, rate])
pull_df = pd.DataFrame(pull_data, columns=["数字", "出現回数", "ひっぱり回数", "ひっぱり率"])
pull_df = pull_df.sort_values(by="ひっぱり率", ascending=False).reset_index(drop=True)

# 表示
st.subheader("🔁 連続ペア 出現ランキング")
st.markdown(style_table(consec_df), unsafe_allow_html=True)

st.subheader("🔄 ひっぱり回数とひっぱり率")
st.markdown(style_table(pull_df), unsafe_allow_html=True)

# ③ 出現回数ランキング（2列表示：左19件＋右18件）
st.header("③ 直近24回 出現回数ランキング")

# 出現回数カウント
numbers = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
number_counts = pd.Series(numbers).value_counts().sort_values(ascending=False)

# ランキングDataFrame作成
ranking_df = pd.DataFrame({
    "順位": range(1, len(number_counts) + 1),
    "出現回数": number_counts.values,
    "数字": number_counts.index
})

# 左右分割（左19行・右残り）
left_df = ranking_df.head(19).reset_index(drop=True)
right_df = ranking_df.iloc[19:].reset_index(drop=True)

# 表示用のHTML整形関数（CSS付きテーブル表示）
def format_html_table(df):
    return df.to_html(index=False, classes="loto-table", escape=False)

# 2列に分割して横並び表示
left_col, right_col = st.columns(2)
with left_col:
    st.markdown("#### 🔵 ランキング（1位〜19位）")
    st.markdown(format_html_table(left_df), unsafe_allow_html=True)
with right_col:
    st.markdown("#### 🟢 ランキング（20位〜）")
    st.markdown(format_html_table(right_df), unsafe_allow_html=True)

import pandas as pd
from collections import Counter

def analyze_loto(df: pd.DataFrame, n_numbers: int):
    df.columns = df.columns.str.strip()
    if "抽せん日" not in df.columns:
        df = df.rename(columns={"抽せん日": "抽せん日"})
    df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
    df = df.dropna(subset=["抽せん日"])
    df = df.sort_values(by="抽せん日", ascending=False).head(24)

    number_cols = [f"第{i}数字" for i in range(1, n_numbers + 1)]
    numbers_list = df[number_cols].values.tolist()

    # 🔁 連続ペア
    consecutive_pairs = []
    for row in numbers_list:
        sorted_row = sorted(row)
        for a, b in zip(sorted_row, sorted_row[1:]):
            if b - a == 1:
                consecutive_pairs.append(f"{a}-{b}")
    consec_counter = Counter(consecutive_pairs)
    consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"])
    consec_df = consec_df.sort_values(by="出現回数", ascending=False).reset_index(drop=True)

    # 🔄 ひっぱり回数と率
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

    pull_data = []
    for num in sorted(total_counter.keys()):
        total = total_counter[num]
        pulls = pull_counter.get(num, 0)
        rate = f"{round(pulls / total * 100, 1)}%" if total > 0 else "-"
        pull_data.append([num, total, pulls, rate])

    pull_df = pd.DataFrame(pull_data, columns=["数字", "出現回数", "ひっぱり回数", "ひっぱり率"])
    pull_df = pull_df.sort_values(by="ひっぱり率", ascending=False)

    return consec_df, pull_df

# ④ パターン分析
st.header(" パターン分析")
patterns = df_recent[[f"第{i}数字" for i in range(1, 8)]].apply(
    lambda x: '-'.join([str((int(n)-1)//10*10+1) if 1<=int(n)<=9 else str((int(n)//10)*10) for n in sorted(x)]), axis=1
)
pattern_counts = patterns.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

# ⑤ 各位の出現回数TOP5
st.header(" 各位の出現回数TOP5")
number_groups = {'1': [], '10': [], '20': [], '30': []}
for i in range(1, 8):
    number_groups['1'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(1, 9)].values)
    number_groups['10'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(10, 19)].values)
    number_groups['20'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(20, 29)].values)
    number_groups['30'].extend(df_recent[f'第{i}数字'][df_recent[f'第{i}数字'].between(30, 37)].values)

top5_df = pd.DataFrame({
    '1の位': pd.Series(number_groups['1']).value_counts().head(5).index.tolist(),
    '10の位': pd.Series(number_groups['10']).value_counts().head(5).index.tolist(),
    '20の位': pd.Series(number_groups['20']).value_counts().head(5).index.tolist(),
    '30の位': pd.Series(number_groups['30']).value_counts().head(5).index.tolist()
})
st.markdown(style_table(top5_df), unsafe_allow_html=True)

# ⑥ 各数字の出現回数TOP5
st.header(" 各数字の出現回数TOP5")

results = {'順位': ['1位', '2位', '3位', '4位', '5位']}
for i in range(1, 8):
    col = f'第{i}数字'
    counts = pd.Series(df_recent[col]).value_counts()
    counts = counts.sort_values(ascending=False).head(5)
    results[col] = [f"{num} ({cnt}回)" for num, cnt in counts.items()]
    
    # 5未満の場合の空埋め
    while len(results[col]) < 5:
        results[col].append("")

top5_df = pd.DataFrame(results)
st.markdown(style_table(top5_df), unsafe_allow_html=True)
# ⑦ A・B・C数字（出現頻度分類）
st.header(" A・B・C数字（出現頻度分類）")

# all_numbers を定義（直近24回の本数字をフラットに結合）
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()

# 出現回数から分類
counts = pd.Series(all_numbers).value_counts()
A = counts[(counts >= 3) & (counts <= 4)].index.tolist()
B = counts[counts >= 5].index.tolist()
C = list(set(range(1, 38)) - set(A) - set(B))

# 表の整形
max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))
abc_df = pd.DataFrame({
    "A数字（3〜4回）": A,
    "B数字（5回以上）": B,
    "C数字（その他）": C
})
st.markdown(style_table(abc_df), unsafe_allow_html=True)

import os
import pandas as pd
import random
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime
import matplotlib.font_manager as fm

# ✅ Mac用の日本語フォントを明示的に指定（AppleGothicが無難）
plt.rcParams['font.family'] = 'AppleGothic'  # または 'Hiragino Sans', 'YuGothic'

# --- 定数と準備 ---
RANGES = {
    "1": list(range(1, 14)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 38))
}

# キャッシュ用ファイルパス
latest_round = int(df.iloc[-1]['回号'])
cache_file = f"predictions/loto7_round{latest_round}.csv"
image_file = f"predictions/loto7_round{latest_round}_予想.png"

# 出現頻度でABC分類
recent_df = df.tail(24)
all_nums = recent_df[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
count_series = pd.Series(all_nums).value_counts()
B_numbers = count_series[count_series >= 5].index.tolist()
A_numbers = count_series[(count_series >= 3) & (count_series <= 4)].index.tolist()

# 前回の当選数字
last_numbers = [df.iloc[-2][f"第{i}数字"] for i in range(1, 8)]

# パターン分析
patterns = recent_df[[f"第{i}数字" for i in range(1, 8)]].apply(
    lambda x: '-'.join([str((int(n)-1)//10*10+1) if 1 <= int(n) <= 9 else str((int(n)//10)*10) for n in sorted(x)]),
    axis=1
)
pattern_counts = patterns.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
top_patterns = pattern_counts.head(3)['パターン'].tolist()
pattern_weights = [3, 2, 2]

# 数字候補の優先選択関数
def choose_number(pool, used):
    for group in [B_numbers, A_numbers]:
        candidates = [n for n in pool if n in group and n not in used]
        if candidates:
            return random.choice(candidates)
    candidates = [n for n in pool if n not in used]
    return random.choice(candidates) if candidates else random.randint(1, 37)

# --- 予想生成（キャッシュ or 新規） ---
if os.path.exists(cache_file):
    pred_df = pd.read_csv(cache_file)
else:
    os.makedirs("predictions", exist_ok=True)
    predictions = []
    for pattern, count in zip(top_patterns, pattern_weights):
        groups = pattern.split('-')
        for _ in range(count):
            selected = []
            used = set()
            for g in groups:
                num = choose_number(RANGES[g], used)
                selected.append(num)
                used.add(num)

            if random.random() < 0.3:
                pulled = random.choice(last_numbers)
                if pulled not in selected:
                    replace_index = random.randint(0, 6)
                    selected[replace_index] = pulled
            selected.sort()
            predictions.append(selected)

    # 残り3通りは完全ランダム構成
    for _ in range(3):
        selected = []
        used = set()
        for _ in range(7):
            num = choose_number(range(1, 38), used)
            selected.append(num)
            used.add(num)
        selected.sort()
        predictions.append(selected)

    pred_df = pd.DataFrame(predictions, columns=[f"第{i}数字" for i in range(1, 8)])
    pred_df.to_csv(cache_file, index=False)

# --- 表示と画像生成 ---
st.header("基本予想（パターン構成＋出現頻度＋レンジ構成＋引っ張り）")
st.markdown("この予想は最新の当選結果に基づいて固定され、当選番号が更新されるまで変わりません。")
st.dataframe(pred_df)

# 画像として保存（matplotlibで）
fig, ax = plt.subplots(figsize=(6, 6))
ax.axis('off')
table = ax.table(cellText=pred_df.values,
                 colLabels=pred_df.columns,
                 loc='center',
                 cellLoc='center')
table.scale(1, 2)
plt.title(f"{latest_round}回 ロト7予想", fontsize=16)
plt.savefig(image_file, bbox_inches='tight')

# --- ダウンロードボタン ---
with open(image_file, "rb") as f:
    st.download_button(
        label="📥 この予想を画像でダウンロード",
        data=f,
        file_name=f"{latest_round}回ロト7予想.png",
        mime="image/png"
    )

# ⑧ セレクト予想
st.header("セレクト予想")
axis_numbers = st.multiselect("軸数字を選んでください (最大3個まで)", options=range(1, 38), max_selections=3)
remove_numbers = st.multiselect("削除数字を選んでください (最大20個まで)", options=range(1, 38), max_selections=20)

if st.button("予想を生成"):
    available_numbers = set(range(1, 38)) - set(remove_numbers)
    ranges = [
        list(range(1, 14)),
        list(range(2, 18)),
        list(range(5, 23)),
        list(range(8, 28)),
        list(range(14, 34)),
        list(range(20, 37)),
        list(range(26, 38))
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
        selected = selected[:7]
        selected.sort()
        predictions.append(selected)

    pred_df = pd.DataFrame(predictions, columns=[f"第{i}数字" for i in range(1, 8)])
    st.markdown(style_table(pred_df), unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import random

st.header("⑨ セレクト予想ルーレット（ロト7）")

# --- 数字グループ定義（ロト7は1〜37） ---
group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 30)),
    "30": list(range(30, 38)),
}

# --- UI：選択条件 ---
st.markdown("#### 🔢 候補にする数字群を選択")
use_position_groups = st.checkbox("各位の出現回数TOP5（1の位〜30の位）", value=True)
use_position_top5 = st.checkbox("各第n位のTOP5（第1〜第7数字ごと）", value=True)
use_A = st.checkbox("A数字", value=True)
use_B = st.checkbox("B数字", value=True)
use_C = st.checkbox("C数字")
use_last = st.checkbox("前回数字を除外", value=True)

# --- UI：任意数字追加 ---
select_manual = st.multiselect("任意で追加したい数字 (1-37)", list(range(1, 38)))

# --- UI：パターン入力 ---
pattern_input = st.text_input("パターンを入力 (例: 1-10-20-20-30-30-1)", value="1-10-20-20-30-30-1")
pattern = pattern_input.strip().split("-")

# --- データ取得（ロト7のCSV） ---
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip()
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df[df["抽せん日"].notna()].copy()

for i in range(1, 8):
    df[f"第{i}数字"] = pd.to_numeric(df[f"第{i}数字"], errors="coerce")
df = df.dropna(subset=[f"第{i}数字" for i in range(1, 8)])
df_recent = df.sort_values("回号", ascending=False).head(24).copy()
latest = df_recent.iloc[0]

# --- 除外対象（前回数字） ---
last_numbers = latest[[f"第{i}数字" for i in range(1, 8)]].tolist() if use_last else []

# --- ABC分類（頻度ベース） ---
digits = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
counts = pd.Series(digits).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)
C_set = set(range(1, 38)) - A_set - B_set

# --- 候補生成 ---
candidate_set = set(select_manual)

if use_position_groups:
    number_groups = {'1': [], '10': [], '20': [], '30': []}
    for i in range(1, 8):
        col = f"第{i}数字"
        col_values = pd.to_numeric(df_recent[col], errors="coerce")
        number_groups['1'].extend(col_values[col_values.between(1, 9)].tolist())
        number_groups['10'].extend(col_values[col_values.between(10, 19)].tolist())
        number_groups['20'].extend(col_values[col_values.between(20, 29)].tolist())
        number_groups['30'].extend(col_values[col_values.between(30, 37)].tolist())
    for key in number_groups:
        top5 = pd.Series(number_groups[key]).value_counts().head(5).index.tolist()
        candidate_set.update(top5)

if use_position_top5:
    seen = set()
    for i in range(1, 8):
        col = f"第{i}数字"
        col_values = pd.to_numeric(df_recent[col], errors="coerce").dropna().astype(int)
        counts = col_values.value_counts()
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
    candidate_set.update(C_set)

candidate_set = sorted(set(candidate_set) - set(last_numbers))

# --- 予想生成 ---
def generate_select_prediction():
    prediction = []
    used = set()
    for group_key in pattern:
        group_nums = [n for n in group_dict.get(group_key, []) if n in candidate_set and n not in used]
        if not group_nums:
            return []  # 候補が足りない場合
        chosen = random.choice(group_nums)
        prediction.append(chosen)
        used.add(chosen)
    return sorted(prediction) if len(prediction) == 7 else []

# --- 実行ボタン ---
if st.button("🎯 セレクト予想を出す（ロト7）"):
    result = generate_select_prediction()
    if result:
        st.success(f"🎉 セレクト予想: {result}")
    else:
        st.error("条件に合致する数字が不足しています。候補を増やしてください。")
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

check_password()
st.set_page_config(layout="centered")

import ssl
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("ミニロト AI予想サイト")

## ✅ スマホで折り返さず横スクロール可能にするCSS（ミニロト・ロト6・ロト7共通）
st.markdown("""
<style>
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    white-space: nowrap;         /* 折り返し防止 */
    overflow-x: auto;            /* 横スクロール */
    max-width: 100%;
    text-align: center;
    color: #000;
    background-color: #fff;
    table-layout: auto;
}
th, td {
    border: 1px solid #ccc;
    padding: 8px;
    white-space: nowrap;         /* ← 各セルも明示的にnowrap */
}
thead {
    background-color: #f2f2f2;
    font-weight: bold;
}
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
# --- abc_class_df の生成（先に定義しておく） ---
latest24_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts = pd.Series(latest24_numbers).value_counts()
A = [str(n) for n in counts[(counts >= 3) & (counts <= 4)].index.tolist()]
B = [str(n) for n in counts[counts >= 5].index.tolist()]
C = [str(n) for n in range(1, 32) if str(n) not in A + B]

max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))

abc_class_df = pd.DataFrame({
    "A（3〜4回）": sorted(A),
    "B（5回以上）": sorted(B),
    "C（その他）": sorted(C)
})

# 最新データの取得
df_latest = df.iloc[0]

st.header("最新の当選番号")



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

# ✅ 本数字・ボーナス数字（セル分割）
main_number_cells = ''.join([f"<td class='center'>{int(df_latest[f'第{i}数字'])}</td>" for i in range(1, 6)])
bonus_cell = f"<td colspan='5' class='center' style='color:red; font-weight:bold;'>{int(df_latest['ボーナス数字'])}</td>"

# ✅ 表表示（キャリーオーバーなし）
st.markdown(f"""
<table class='loto-table'>
<tr><th>回号</th><td colspan='5' class='center'>第{df_latest['回号']}回</td></tr>
<tr><th>抽せん日</th><td colspan='5' class='center'>{df_latest['抽せん日'].strftime('%Y年%m月%d日')}</td></tr>
<tr><th>本数字</th>{main_number_cells}</tr>
<tr><th>ボーナス数字</th>{bonus_cell}</tr>
<tr><th>1等</th><td colspan='2' class='right'>{format_count(df_latest['1等口数'])}</td><td colspan='3' class='right'>{format_yen(df_latest['1等賞金'])}</td></tr>
<tr><th>2等</th><td colspan='2' class='right'>{format_count(df_latest['2等口数'])}</td><td colspan='3' class='right'>{format_yen(df_latest['2等賞金'])}</td></tr>
<tr><th>3等</th><td colspan='2' class='right'>{format_count(df_latest['3等口数'])}</td><td colspan='3' class='right'>{format_yen(df_latest['3等賞金'])}</td></tr>
<tr><th>4等</th><td colspan='2' class='right'>{format_count(df_latest['4等口数'])}</td><td colspan='3' class='right'>{format_yen(df_latest['4等賞金'])}</td></tr>
</table>
""", unsafe_allow_html=True)

# ② 直近24回 当選番号 + ABC + 引っ張り + 連続分析
st.header("直近24回の当選番号")

# 日付昇順にしてから処理（その後、表示時に降順に戻す）
df_recent = df.sort_values("抽せん日", ascending=True).tail(24).copy()
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
all_numbers = pd.to_numeric(all_numbers, errors="coerce")
counts = pd.Series(all_numbers).value_counts()

A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

abc_rows = []
pull_total = 0
cont_total = 0
abc_counts = {'A': 0, 'B': 0, 'C': 0}

nums_list = []
for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 6)]
    nums_list.append(nums)

# 分析処理（前から順に）
for i in range(len(df_recent)):
    nums = nums_list[i]
    sorted_nums = sorted(nums)

    # ABC構成
    abc = []
    for n in sorted_nums:
        if n in B_set:
            abc.append('B'); abc_counts['B'] += 1
        elif n in A_set:
            abc.append('A'); abc_counts['A'] += 1
        else:
            abc.append('C'); abc_counts['C'] += 1
    abc_str = ','.join(abc)

    # ひっぱり分析（前回の数字と比較）
    if i == 0:
        pulls_str = "-"
    else:
        pulls = len(set(nums) & set(nums_list[i - 1]))
        pulls_str = f"{pulls}個" if pulls > 0 else "なし"
        if pulls > 0:
            pull_total += 1

    # 連続数字分析
    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_str = "あり" if cont else "なし"
    if cont:
        cont_total += 1

    abc_rows.append({
        '抽せん日': df_recent.iloc[i]['抽せん日'].strftime('%Y-%m-%d'),
        **{f"第{i}数字": nums[i - 1] for i in range(1, 6)},
        'ABC構成': abc_str,
        'ひっぱり': pulls_str,
        '連続': cont_str,
    })

# 表を新しい順に表示
abc_df = pd.DataFrame(abc_rows).sort_values(by='抽せん日', ascending=False).reset_index(drop=True)
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

import streamlit as st
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

st.header("🎯 AIによる次回出現数字候補（1の位・10の位・20の位 各6個／計18個）")

# --- データ準備 ---
df_ai = df.copy().dropna(subset=[f"第{i}数字" for i in range(1, 6)])
df_ai = df_ai.tail(min(len(df_ai), 100)).reset_index(drop=True)

# --- 学習データ作成 ---
X, y = [], []
for i in range(len(df_ai) - 1):
    prev_nums = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 6)]
    next_nums = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 6)]
    for target in next_nums:
        X.append(prev_nums)
        y.append(target)

# --- AIモデル予測 ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
rf_probs = rf.predict_proba([X[-1]])[0]
rf_top = list(np.argsort(rf_probs)[::-1][:18] + 1)

mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
mlp.fit(X, y)
mlp_probs = mlp.predict_proba([X[-1]])[0]
mlp_top = list(np.argsort(mlp_probs)[::-1][:18] + 1)

# --- マルコフ連鎖 ---
transition = defaultdict(lambda: defaultdict(int))
for i in range(len(df_ai) - 1):
    curr = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 6)]
    next_ = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 6)]
    for c in curr:
        for n in next_:
            transition[c][n] += 1

last_draw = [df_ai.loc[len(df_ai)-1, f"第{j}数字"] for j in range(1, 6)]
markov_scores = defaultdict(int)
for c in last_draw:
    for n, cnt in transition[c].items():
        markov_scores[n] += cnt
markov_top = sorted(markov_scores, key=markov_scores.get, reverse=True)[:18]

# --- 直近24回の出現ランキングを加点 ---
latest_24 = df_ai.head(24)
flat_24 = latest_24[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
rank_24 = Counter(flat_24)

# --- 全モデル候補を集計 ---
all_candidates = rf_top + mlp_top + markov_top
counter = Counter(all_candidates)

# --- 加点（AI候補のスコア＋直近24回出現回数*1.5） ---
score_dict = defaultdict(float)
for n in range(1, 32):
    score_dict[n] = counter[n] + rank_24[n] * 1.5

# --- 位ごとにスコア順で抽出 ---
digit_bins = {
    "1の位": [],
    "10の位": [],
    "20の位": [],
}
for n in range(1, 32):
    if 1 <= n <= 9:
        digit_bins["1の位"].append((n, score_dict[n]))
    elif 10 <= n <= 19:
        digit_bins["10の位"].append((n, score_dict[n]))
    elif 20 <= n <= 31:
        digit_bins["20の位"].append((n, score_dict[n]))

top_1 = [n for n, _ in sorted(digit_bins["1の位"], key=lambda x: -x[1])[:6]]
top_10 = [n for n, _ in sorted(digit_bins["10の位"], key=lambda x: -x[1])[:6]]
top_20 = [n for n, _ in sorted(digit_bins["20の位"], key=lambda x: -x[1])[:6]]

top18 = sorted(top_1 + top_10 + top_20)

# --- 表示 ---
st.success(f"🧠 次回出現候補（AI予測・各位6個ずつ）: {top18}")

# --- モデル別候補表示（展開式） ---
with st.expander("📊 モデル別候補を表示"):
    st.write("🔹 ランダムフォレスト:", ", ".join(map(str, sorted(rf_top))))
    st.write("🔹 ニューラルネット:", ", ".join(map(str, sorted(mlp_top))))
    st.write("🔹 マルコフ連鎖:", ", ".join(map(str, sorted(markov_top))))
    st.write("🔹 直近24回出現ランキング:", ", ".join(f"{k}({v})" for k, v in rank_24.most_common()))

# --- 位別分類表示 ---
grouped = {
    "1の位": top_1,
    "10の位": top_10,
    "20の位": top_20,
}
max_len = max(len(v) for v in grouped.values())
group_df = pd.DataFrame({
    k: grouped[k] + [""] * (max_len - len(grouped[k]))
    for k in grouped
})
group_df = group_df.applymap(lambda x: str(int(x)) if str(x).isdigit() else "")

st.markdown("### 🧮 候補数字の位別分類（1の位・10の位・20の位）")
st.markdown(f"""
<div style='overflow-x: auto;'>
{group_df.to_html(index=False, escape=False)}
</div>
""", unsafe_allow_html=True)

st.header("A数字・B数字の位別分類（ミニロト）")

def style_table(df: pd.DataFrame) -> str:
    # ★ DataFrame → Styler に変換してスタイルを適用（set_table_stylesはStyler専用）
    return (
        df.style
          .set_table_styles([
              {'selector': 'th', 'props': [('text-align', 'center')]},
              {'selector': 'td', 'props': [('text-align', 'center')]}
          ], overwrite=False)
          .hide_index()
          .to_html()  # .render()でも可
    )

# --- 最新行が先頭に来ている前提で最新行を取得 ---
df = df.reset_index(drop=True)
latest = df.iloc[0]
latest_numbers = {
    int(latest[f"第{i}数字"]) for i in range(1, 6)
    if pd.notnull(latest.get(f"第{i}数字"))
}

def highlight_number(n: int) -> str:
    return f"<span style='color:red; font-weight:bold'>{n}</span>" if n in latest_numbers else str(n)

def classify_numbers_mini_loto(numbers: list[int]) -> dict[str, list[int]]:
    bins = {'1の位': [], '10の位': [], '20の位': []}
    for n in numbers:
        n = int(n)
        if 1 <= n <= 9:
            bins['1の位'].append(n)
        elif 10 <= n <= 19:
            bins['10の位'].append(n)
        elif 20 <= n <= 31:
            bins['20の位'].append(n)
    return bins

A_bins = classify_numbers_mini_loto(A_set)
B_bins = classify_numbers_mini_loto(B_set)

digit_table = pd.DataFrame({
    "位": list(A_bins.keys()),
    "A数字": [
        ', '.join(highlight_number(n) for n in sorted(A_bins[k]))
        for k in A_bins
    ],
    "B数字": [
        ', '.join(highlight_number(n) for n in sorted(B_bins[k]))
        for k in B_bins
    ]
})

html = style_table(digit_table)
st.markdown(html, unsafe_allow_html=True)




st.header("各位の出現回数TOP5")

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

st.header("各数字の出現回数TOP5（位置別）")

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

A = [str(n) for n in A]
B = [str(n) for n in B]
C = [str(n) for n in C]

abc_class_df = pd.DataFrame({
    "A（3〜4回）": sorted(A),
    "B（5回以上）": sorted(B),
    "C（その他）": sorted(C)
})

# Streamlit用：テーブル表示（style_table関数が必要）
# st.markdown(style_table(abc_class_df), unsafe_allow_html=True)
# --- ⑦ 基本予想（構成・出現・ABC優先） ---
st.header("基本予想（構成・出現・ABC優先）")

import random

# 構成パターン（位の区分）
structure_patterns = [
    ['1', '10', '10', '20', '20'],
    ['1', '1', '10', '20', '20'],
    ['1', '1', '1', '20', '20'],
    ['1', '10', '20', '20', '20'],
    ['10', '10', '20', '20', '20'],
    ['10', '10', '10', '20', '20']
]

# 数字範囲マップ
range_map = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 32))
}

# ABC分類からA/Bを抽出（df_recentから取得）
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts = pd.Series(all_numbers).value_counts()
A = counts[(counts >= 3) & (counts <= 4)].index.tolist()
B = counts[counts >= 5].index.tolist()
AB_pool = set(A + B)

# 各位の出現回数TOP5
top_by_pos = {}
for i in range(1, 6):
    top_by_pos[i] = df_recent[f"第{i}数字"].value_counts().head(5).index.tolist()

# ランダム固定（再現性確保）
random.seed(42)

# 20通り生成（6パターンを繰り返し使用）
predicts = []
while len(predicts) < 20:
    p = random.choice(structure_patterns)
    nums = []
    used = set()
    for idx, part in enumerate(p):
        pool = list(set(range_map[part]) & AB_pool - used)
        # 出現上位を優先
        if top_by_pos[idx + 1]:
            pool = sorted(pool, key=lambda x: x not in top_by_pos[idx + 1])
        if pool:
            pick = random.choice(pool)
            nums.append(pick)
            used.add(pick)
    # 不足時に補完（A/Bから）
    while len(nums) < 5:
        candidate = random.choice(list(AB_pool - used))
        nums.append(candidate)
        used.add(candidate)
    predicts.append(sorted(nums))

# 表に変換して表示
predict_df = pd.DataFrame(predicts, columns=["第1", "第2", "第3", "第4", "第5"])
st.markdown(style_table(predict_df), unsafe_allow_html=True)

# セレクト予想
st.header("セレクト予想")
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
import streamlit as st
import pandas as pd
import random

st.header("セレクト予想ルーレット（ミニロト）")

# --- 数字グループ定義（ミニロトは1〜31） ---
group_dict = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 32)),  # ✅ 20〜31まで含める
}

# --- UI：選択条件 ---
st.markdown("#### 🔢 候補にする数字群を選択")
use_position_groups = st.checkbox("各位の出現回数TOP5（1の位〜30の位）", value=True)
use_position_top5 = st.checkbox("各第n位のTOP5（第1〜第5数字ごと）", value=True)
use_A = st.checkbox("A数字", value=True)
use_B = st.checkbox("B数字", value=True)
use_C = st.checkbox("C数字")
use_last = st.checkbox("前回数字を除外", value=True)

# --- UI：任意数字追加 ---
select_manual = st.multiselect("任意で追加したい数字 (1-31)", list(range(1, 32)))

# --- UI：パターン入力 ---
pattern_input = st.text_input("パターンを入力 (例: 1-10-20-30-10)", value="1-10-20-30-10")
pattern = pattern_input.strip().split("-")

# --- データ取得（ミニロトCSV） ---
url = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip()
df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
df = df[df["抽せん日"].notna()].copy()

for i in range(1, 6):
    df[f"第{i}数字"] = pd.to_numeric(df[f"第{i}数字"], errors="coerce")
df = df.dropna(subset=[f"第{i}数字" for i in range(1, 6)])
df_recent = df.sort_values("回号", ascending=False).head(24).copy()
latest = df_recent.iloc[0]

# --- 除外対象（前回数字） ---
last_numbers = latest[[f"第{i}数字" for i in range(1, 6)]].tolist() if use_last else []

# --- ABC分類（頻度ベース） ---
digits = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts = pd.Series(digits).value_counts()
A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)
C_set = set(range(1, 32)) - A_set - B_set

# --- 候補生成 ---
candidate_set = set(select_manual)

if use_position_groups:
    number_groups = {'1': [], '10': [], '20': []}  # ← '30' を削除
    for i in range(1, 6):
        col = f"第{i}数字"
        col_values = pd.to_numeric(df_recent[col], errors="coerce")
        number_groups['1'].extend(col_values[col_values.between(1, 9)].tolist())
        number_groups['10'].extend(col_values[col_values.between(10, 19)].tolist())
        number_groups['20'].extend(col_values[col_values.between(20, 31)].tolist())  # ✅ 20〜31を1グループに統合

    for key in number_groups:
        top5 = pd.Series(number_groups[key]).value_counts().head(5).index.tolist()
        candidate_set.update(top5)

if use_position_top5:
    seen = set()
    for i in range(1, 6):
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
    return sorted(prediction) if len(prediction) == 5 else []

# --- 実行ボタン ---
if st.button("🎯 セレクト予想を出す（ミニロト）"):
    result = generate_select_prediction()
    if result:
        st.success(f"🎉 セレクト予想: {result}")
    else:
        st.error("条件に合致する数字が不足しています。候補を増やしてください。")
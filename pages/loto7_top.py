import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from auth import check_password

st.set_page_config(layout="centered")


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
st.header("直近24回の当選番号")

# 日付昇順にしてから処理し、あとで降順に並べ直す
df_recent = df.tail(24).copy()
df_recent["抽せん日"] = pd.to_datetime(df_recent["抽せん日"], errors="coerce")
df_recent = df_recent.sort_values(by="抽せん日", ascending=True).reset_index(drop=True)

# 出現回数でABC分類セット作成（7数字分に対応）
all_numbers = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
all_numbers = pd.to_numeric(all_numbers, errors="coerce")
counts = pd.Series(all_numbers).value_counts()

A_set = set(counts[(counts >= 3) & (counts <= 4)].index)
B_set = set(counts[counts >= 5].index)

# 分析処理
abc_rows = []
abc_counts = {'A': 0, 'B': 0, 'C': 0}
cont_total = 0
pull_total = 0

nums_list = []
for _, row in df_recent.iterrows():
    nums = [int(row[f"第{i}数字"]) for i in range(1, 8)]
    nums_list.append(nums)

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

    # 連続
    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_str = "あり" if cont else "なし"
    if cont:
        cont_total += 1

    # ひっぱり（1回目は比較対象がない）
    if i == 0:
        pulls_str = "-"
    else:
        pulls = len(set(nums) & set(nums_list[i - 1]))
        pulls_str = f"{pulls}個" if pulls > 0 else "なし"
        if pulls > 0:
            pull_total += 1

    abc_rows.append({
        '抽せん日': df_recent.loc[i, "抽せん日"].strftime('%Y-%m-%d'),
        '第1数字': nums[0], '第2数字': nums[1], '第3数字': nums[2],
        '第4数字': nums[3], '第5数字': nums[4], '第6数字': nums[5],
        '第7数字': nums[6], 'ABC構成': abc_str,
        'ひっぱり': pulls_str,
        '連続': cont_str
    })

# 表を最新が上になるように並べ替え
abc_df = pd.DataFrame(abc_rows).sort_values(by="抽せん日", ascending=False)

# 表示
st.markdown(abc_df.to_html(index=False), unsafe_allow_html=True)

# --- 出現傾向（ABC割合・ひっぱり率・連続率）テーブル ---
total_abc = sum(abc_counts.values())
a_perc = round(abc_counts['A'] / total_abc * 100, 1)
b_perc = round(abc_counts['B'] / total_abc * 100, 1)
c_perc = round(abc_counts['C'] / total_abc * 100, 1)
pull_rate = round(pull_total / (len(df_recent) - 1) * 100, 1)
cont_rate = round(cont_total / len(df_recent) * 100, 1)

summary_df = pd.DataFrame({
    "分析項目": ["A数字割合", "B数字割合", "C数字割合", "ひっぱり率", "連続数字率"],
    "値": [f"{a_perc}%", f"{b_perc}%", f"{c_perc}%", f"{pull_rate}%", f"{cont_rate}%"]
})
st.subheader("出現傾向サマリー")
st.table(summary_df)

# ④ パターン分析
st.header(" パターン分析")
patterns = df_recent[[f"第{i}数字" for i in range(1, 8)]].apply(
    lambda x: '-'.join([str((int(n)-1)//10*10+1) if 1<=int(n)<=9 else str((int(n)//10)*10) for n in sorted(x)]), axis=1
)
pattern_counts = patterns.value_counts().reset_index()
pattern_counts.columns = ['パターン', '出現回数']
st.markdown(style_table(pattern_counts), unsafe_allow_html=True)

st.header("🎯 AIによる次回出現数字候補（22個に絞り込み）")

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from collections import defaultdict, Counter
import numpy as np
import pandas as pd

# --- 直近100回のデータで学習用データ構築（ロト7は第1〜第7数字） ---
df_ai = df.copy().dropna(subset=[f"第{i}数字" for i in range(1, 8)])
df_ai = df_ai.tail(min(len(df_ai), 100)).reset_index(drop=True)
X, y = [], []
for i in range(len(df_ai) - 1):
    prev_nums = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 8)]
    next_nums = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 8)]
    for target in next_nums:
        X.append(prev_nums)
        y.append(target)

# --- ランダムフォレスト ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
rf_probs = rf.predict_proba([X[-1]])[0]
rf_top = list(np.argsort(rf_probs)[::-1][:15] + 1)

# --- ニューラルネットワーク ---
mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
mlp.fit(X, y)
mlp_probs = mlp.predict_proba([X[-1]])[0]
mlp_top = list(np.argsort(mlp_probs)[::-1][:15] + 1)

# --- マルコフ連鎖（簡易実装） ---
transition = defaultdict(lambda: defaultdict(int))
for i in range(len(df_ai) - 1):
    curr = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 8)]
    next_ = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 8)]
    for c in curr:
        for n in next_:
            transition[c][n] += 1

last_draw = [df_ai.loc[len(df_ai)-1, f"第{j}数字"] for j in range(1, 8)]
markov_scores = defaultdict(int)
for c in last_draw:
    for n, cnt in transition[c].items():
        markov_scores[n] += cnt
markov_top = sorted(markov_scores, key=markov_scores.get, reverse=True)[:15]

# --- 候補を重複頻度で集計し、上位22個を抽出 ---
all_candidates = rf_top + mlp_top + markov_top
counter = Counter(all_candidates)
top22 = [num for num, _ in counter.most_common(22)]
top22 = sorted(set(top22))[:22]
top22 = list(map(int, top22))  # np.int64 → int

# --- 表示 ---
st.success(f"🧠 次回出現候補（AI予測・22個）: {sorted(top22)}")

# --- モデル別候補（テーブル崩れ防止のため文字列で出力） ---
with st.expander("📊 モデル別候補を表示"):
    st.write("🔹 ランダムフォレスト:", ", ".join(map(str, sorted(map(int, rf_top)))))
    st.write("🔹 ニューラルネット:", ", ".join(map(str, sorted(map(int, mlp_top)))))
    st.write("🔹 マルコフ連鎖:", ", ".join(map(str, sorted(map(int, markov_top)))))

# --- 候補数字を位ごとに分類 ---
grouped = {
    "1の位": [],
    "10の位": [],
    "20の位": [],
    "30の位": [],
}
for n in top22:
    if 1 <= n <= 9:
        grouped["1の位"].append(n)
    elif 10 <= n <= 19:
        grouped["10の位"].append(n)
    elif 20 <= n <= 29:
        grouped["20の位"].append(n)
    elif 30 <= n <= 37:
        grouped["30の位"].append(n)

# --- 表形式に整形（整数で表示するため文字列に変換） ---
max_len = max(len(v) for v in grouped.values())
group_df = pd.DataFrame({
    k: grouped[k] + [None] * (max_len - len(grouped[k]))
    for k in grouped
})

# 数値を整数の文字列に変換し、小数点を消す（Noneは空文字に）

if isinstance(group_df, pd.Series):
    group_df = group_df.map(lambda x: str(int(x)) if pd.notnull(x) else "")
else:
    group_df = group_df.apply(lambda col: col.map(lambda x: str(int(x)) if pd.notnull(x) else ""))

st.markdown("### 🧮 候補数字の位別分類（1の位・10の位・20の位・30の位）")
st.markdown(f"""
<div style='overflow-x: auto;'>
{group_df.to_html(index=False, escape=False)}
</div>
""", unsafe_allow_html=True)






# ✅ A/B数字の位別分類（ロト7用：最大37まで）

st.header("A数字・B数字の位別分類")

def style_table(df):
    return df.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ]).to_html(escape=False, index=False)

# 最新当選番号（ロト7は第1〜第7数字）※正しい行
latest_numbers = [int(df.iloc[-1][f"第{i}数字"]) for i in range(1, 8)]

def highlight_number(n):
    return f"<span style='color:red; font-weight:bold'>{n}</span>" if n in latest_numbers else str(n)

def classify_numbers_loto7(numbers):
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
        elif 30 <= n <= 37:  # ロト7は最大37まで
            bins['30の位'].append(n)
    return bins

A_bins = classify_numbers_loto7(A_set)
B_bins = classify_numbers_loto7(B_set)

digit_table = pd.DataFrame({
    "位": list(A_bins.keys()),
    "A数字": [', '.join([highlight_number(n) for n in sorted(A_bins[k])]) for k in A_bins],
    "B数字": [', '.join([highlight_number(n) for n in sorted(B_bins[k])]) for k in B_bins]
})

st.markdown(style_table(digit_table), unsafe_allow_html=True)

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


import pandas as pd
from collections import Counter
import streamlit as st


# ③ 出現回数ランキング（2列表示：左19件＋右残り）
st.header("直近24回 出現回数ランキング")

# 出現回数カウント
numbers = df_recent[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
number_counts = pd.Series(numbers).value_counts().sort_values(ascending=False)

# ランキングDataFrame作成（数字の横に出現回数を括弧付きで表示）
ranking_df = pd.DataFrame({
    "順位": range(1, len(number_counts) + 1),
    "数字": [f"{int(num)}（{count}）" for num, count in zip(number_counts.index, number_counts.values)]
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







st.header("🔁 連続数字ペア 出現ランキング")

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

# 集計＆整形
consec_counter = Counter(consecutive_pairs)
consec_df = pd.DataFrame(consec_counter.items(), columns=["連続ペア", "出現回数"])
consec_df = consec_df.sort_values(by="出現回数", ascending=False).reset_index(drop=True)

# 表示
st.markdown(style_table(consec_df), unsafe_allow_html=True)
import os
import pandas as pd
import random
import streamlit as st


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

st.markdown("### 🧮 候補数字の位別分類（1の位・10の位・20の位・30の位）")

st.header("A数字・B数字の位別分類")

st.markdown("### 🧮 候補数字の位別分類（1の位・10の位・20の位・30の位）")
st.markdown(f"""
<div style='overflow-x: auto;'>
{group_df.to_html(index=False, escape=False)}
</div>
""", unsafe_allow_html=True)

st.header("各数字の出現回数・出現率一覧")

def render_scrollable_table(df):
    st.markdown(f"""
    <div style='overflow-x:auto;'>
    {df.to_html(index=False, escape=False)}
    </div>
    """, unsafe_allow_html=True)

def build_frequency_table(source_df, label_count, label_rate):
    total_draws = len(source_df)
    all_vals = source_df[[f"第{i}数字" for i in range(1, 8)]].values.flatten()
    all_vals = pd.to_numeric(pd.Series(all_vals), errors="coerce").dropna().astype(int)
    count_map = all_vals.value_counts().to_dict()

    rows = []
    for num in range(1, 38):
        cnt = int(count_map.get(num, 0))
        rate = round(cnt / total_draws * 100, 1) if total_draws > 0 else 0
        rows.append({
            "数字": num,
            label_count: cnt,
            label_rate: rate
        })
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
        elif v >= 28:
            return "background-color:#cfe2ff; color:#000; font-weight:bold;"
        return ""
    except:
        return ""

def render_rank_table(df_in):
    styled_html = (
        df_in.style
        .map(highlight_rank, subset=["100回ランク", "24回ランク"])
        .set_properties(**{
            "text-align": "center",
            "white-space": "nowrap"
        })
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
        nums = [int(row[f"第{i}数字"]) for i in range(1, 8)]
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
    latest_nums = [int(source_df.iloc[-1][f"第{i}数字"]) for i in range(1, 8)]
    if number in latest_nums:
        return "-"
    for idx in range(len(source_df) - 1, -1, -1):
        nums = [int(source_df.iloc[idx][f"第{i}数字"]) for i in range(1, 8)]
        if number in nums:
            return str(len(source_df) - (idx + 1))
    return "-"

def get_last_hit_date(source_df, number):
    source_df = source_df.reset_index(drop=True)
    for idx in range(len(source_df) - 1, -1, -1):
        nums = [int(source_df.iloc[idx][f"第{i}数字"]) for i in range(1, 8)]
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

interval_rows = []

for num in range(1, 38):
    all_positions = get_hit_positions(df_interval_100, num)
    all_intervals = get_intervals_from_positions(all_positions)

    last12_positions = get_hit_positions(df_last12m, num)
    last12_intervals = get_intervals_from_positions(last12_positions)

    interval_rows.append({
        "数字": num,
        "直近100回平均間隔": format_avg_interval(all_intervals),
        "直近12ケ月平均間隔": format_avg_interval(last12_intervals),
        "直近100回最大経過回数": str(max(all_intervals)) if len(all_intervals) > 0 else "-",
        "直近5回の出現間隔": format_last5_intervals(all_intervals),
        "最後の出現経過回数": get_last_elapsed_count(df_interval_100, num),
        "一番最近の出現日": get_last_hit_date(df_interval_100, num),
    })

interval_analysis_df = pd.DataFrame(interval_rows)
render_scrollable_table(interval_analysis_df)

st.header("A数字・B数字の位別分類")

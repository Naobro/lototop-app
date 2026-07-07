import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

try:
    from auth import check_password
except ImportError:
    pass

st.set_page_config(layout="wide")

import ssl
import pandas as pd
import numpy as np
import random
import json
from collections import defaultdict, Counter
import streamlit.components.v1 as components
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"

# ============================================
# 共通スタイル
# ============================================

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
    table-layout: auto;
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


def style_table(df):
    return df.to_html(index=False, escape=False, classes="wide-table")


def style_table_with_index(df):
    return (
        df.style
        .set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]},
            {'selector': 'td', 'props': [('text-align', 'center')]}
        ], overwrite=False)
        .hide(axis="index")
        .to_html()
    )


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


# ============================================
# データ読み込み（共通・キャッシュ化）
# ============================================

@st.cache_data(ttl=600)
def load_df(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
    df = df.dropna(subset=["抽せん日"])
    for i in range(1, 6):
        df[f"第{i}数字"] = pd.to_numeric(df[f"第{i}数字"], errors="coerce")
    df = df.dropna(subset=[f"第{i}数字" for i in range(1, 6)])
    df = df.sort_values(by="抽せん日", ascending=False).reset_index(drop=True)
    return df


# ============================================
# AI予測ロジック（コピーテキスト生成・画面表示 共通）
# ============================================

def run_ai_prediction(df):
    """RF・NN・マルコフ連鎖・改善ロジックによるミニロト予測を実行し結果を返す"""
    try:
        df_ai = df.copy().dropna(subset=[f"第{i}数字" for i in range(1, 6)])
        # ★ df は既に降順（最新が先頭）なので head() で直近100回を取得する
        df_ai = df_ai.head(min(len(df_ai), 100)).reset_index(drop=True)

        X, y = [], []
        for i in range(len(df_ai) - 1):
            prev_nums = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 6)]
            next_nums = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 6)]
            for target in next_nums:
                X.append(prev_nums)
                y.append(target)

        if len(X) == 0:
            return None

        # ランダムフォレスト（classes_を参照して正確に数字と確率を対応付ける）
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        rf_probs = rf.predict_proba([X[-1]])[0]
        rf_pairs = sorted(zip(rf.classes_, rf_probs), key=lambda x: x[1], reverse=True)[:18]
        rf_top = sorted([int(c) for c, _ in rf_pairs])

        # ニューラルネット
        mlp = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
        mlp.fit(X, y)
        mlp_probs = mlp.predict_proba([X[-1]])[0]
        mlp_pairs = sorted(zip(mlp.classes_, mlp_probs), key=lambda x: x[1], reverse=True)[:18]
        mlp_top = sorted([int(c) for c, _ in mlp_pairs])

        # マルコフ連鎖
        transition = defaultdict(lambda: defaultdict(int))
        for i in range(len(df_ai) - 1):
            curr = [df_ai.loc[i + 1, f"第{j}数字"] for j in range(1, 6)]
            next_ = [df_ai.loc[i, f"第{j}数字"] for j in range(1, 6)]
            for c in curr:
                for n in next_:
                    transition[c][n] += 1
        last_draw = [df_ai.loc[0, f"第{j}数字"] for j in range(1, 6)]
        markov_scores = defaultdict(int)
        for c in last_draw:
            for n, cnt in transition[c].items():
                markov_scores[n] += cnt
        markov_top = sorted(sorted(markov_scores, key=markov_scores.get, reverse=True)[:18])

        # 直近24回出現ランキング
        latest_24 = df_ai.head(24)
        flat_24 = latest_24[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
        rank_24 = Counter(flat_24)

        # 合算スコア
        all_candidates = rf_top + mlp_top + markov_top
        counter = Counter(all_candidates)
        score_dict = defaultdict(float)
        for n in range(1, 32):
            score_dict[n] = counter[n] + rank_24[n] * 1.5

        # 改善ロジック（頻出・連続ペア加点）
        freq_counts = pd.Series(
            df.head(100)[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
        ).value_counts()
        pairs = []
        df_recent24 = df.head(24)
        for row in df_recent24[[f"第{i}数字" for i in range(1, 6)]].values:
            row_sorted = sorted(row)
            for a, b in zip(row_sorted, row_sorted[1:]):
                if b - a == 1:
                    pairs.append((a, b))
        pair_counts = Counter(pairs)
        improved_scores = {n: 0 for n in range(1, 32)}
        for n, cnt in freq_counts.items():
            improved_scores[int(n)] += cnt * 1.5
        for (a, b), cnt in pair_counts.items():
            improved_scores[int(a)] += cnt
            improved_scores[int(b)] += cnt
        for n in improved_scores:
            improved_scores[n] += score_dict.get(n, 0)

        new_bins = {"1の位": [], "10の位": [], "20の位": []}
        for n, sc in sorted(improved_scores.items(), key=lambda x: -x[1]):
            if 1 <= n <= 9 and len(new_bins["1の位"]) < 6:
                new_bins["1の位"].append(n)
            elif 10 <= n <= 19 and len(new_bins["10の位"]) < 6:
                new_bins["10の位"].append(n)
            elif 20 <= n <= 31 and len(new_bins["20の位"]) < 6:
                new_bins["20の位"].append(n)
        new_top18 = sorted(sum(new_bins.values(), []))

        return {
            "rf_top": rf_top,
            "mlp_top": mlp_top,
            "markov_top": markov_top,
            "rank_24": rank_24,
            "new_top18": new_top18,
            "new_bins": new_bins,
            "last_draw": [int(x) for x in last_draw],
        }
    except Exception as e:
        return {"error": str(e)}


def build_ai_export_text(csv_path):
    """コピーボタン用：最新当選番号・直近24回・AB数字・AI予測をすべてテキスト化"""
    try:
        df = load_df(csv_path)
        latest = df.iloc[0]
        latest_round = int(latest["回号"])
        next_round = latest_round + 1
        latest_nums = [int(latest[f"第{i}数字"]) for i in range(1, 6)]
        bonus = int(latest["ボーナス数字"])

        text = "【ミニロト 直近データ（AI貼り付け用）】\n"
        text += f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"最新回号: 第{latest_round}回 / 次回: 第{next_round}回\n"
        text += f"最新当選番号: {' '.join(map(str, latest_nums))}  ボーナス:{bonus}\n\n"

        df24 = df.head(24)
        text += "=== 直近24回の当選番号 ===\n"
        text += "回号  抽せん日  第1 第2 第3 第4 第5  ボーナス\n"
        for _, row in df24.iterrows():
            nums_str = " ".join(str(int(row[f"第{i}数字"])) for i in range(1, 6))
            text += (f"{int(row['回号'])}  {row['抽せん日'].strftime('%Y-%m-%d')}  "
                     f"{nums_str}  {int(row['ボーナス数字'])}\n")

        all_nums = df24[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
        counts = Counter(all_nums)
        A_list = sorted([int(n) for n, c in counts.items() if 3 <= c <= 4])
        B_list = sorted([int(n) for n, c in counts.items() if c >= 5])
        C_list = sorted([n for n in range(1, 32) if n not in A_list + B_list])
        text += "\n=== AB数字分類（直近24回）===\n"
        text += "A（3〜4回出現）: " + ", ".join(map(str, A_list)) + "\n"
        text += "B（5回以上出現）: " + ", ".join(map(str, B_list)) + "\n"
        text += "C（その他）: " + ", ".join(map(str, C_list)) + "\n"

        text += "\n=== 各位出現ランキング（直近24回）===\n"
        bins = {"1の位 (1-9)": range(1, 10), "10の位 (10-19)": range(10, 20), "20の位 (20-31)": range(20, 32)}
        flat24 = list(all_nums)
        for bin_name, bin_range in bins.items():
            bin_nums = [n for n in flat24 if n in bin_range]
            top5 = Counter(bin_nums).most_common(5)
            text += f"{bin_name}: " + ", ".join(f"{int(n)}({c}回)" for n, c in top5) + "\n"

        A_set_txt = set(A_list)
        B_set_txt = set(B_list)
        abc_counts = {"A": 0, "B": 0, "C": 0}
        for n in flat24:
            n = int(n)
            if n in B_set_txt:
                abc_counts["B"] += 1
            elif n in A_set_txt:
                abc_counts["A"] += 1
            else:
                abc_counts["C"] += 1
        total_abc = sum(abc_counts.values())
        text += "\n=== ABC出現割合（直近24回・全数字）===\n"
        for k in ["A", "B", "C"]:
            pct = abc_counts[k] / total_abc * 100 if total_abc > 0 else 0
            text += f"{k}: {abc_counts[k]}個 ({pct:.1f}%)\n"

        nums_list_24 = [
            [int(row[f"第{i}数字"]) for i in range(1, 6)]
            for _, row in df24.iterrows()
        ]
        pull_total = sum(
            1 for i in range(1, len(nums_list_24))
            if set(nums_list_24[i]) & set(nums_list_24[i - 1])
        )
        text += "\n=== ひっぱり傾向（直近24回）===\n"
        text += f"ひっぱりあり回数: {pull_total}回 / 24回 ({pull_total/24*100:.1f}%)\n"

        consec_pairs = []
        for row in nums_list_24:
            for a, b in zip(sorted(row), sorted(row)[1:]):
                if b - a == 1:
                    consec_pairs.append(f"{a}-{b}")
        consec_counter = Counter(consec_pairs)
        text += "\n=== 連続数字ペア（直近24回・上位10）===\n"
        for pair, cnt in consec_counter.most_common(10):
            text += f"{pair}: {cnt}回\n"

        text += "\n" + "=" * 50 + "\n"
        text += "=== AI予測候補（次回） ===\n"
        text += "※ RF=ランダムフォレスト / NN=ニューラルネット / MC=マルコフ連鎖\n\n"
        ai_result = run_ai_prediction(df)
        if ai_result and "error" not in ai_result:
            text += f"ランダムフォレスト TOP18: {ai_result['rf_top']}\n"
            text += f"ニューラルネット  TOP18: {ai_result['mlp_top']}\n"
            text += f"マルコフ連鎖      TOP18: {ai_result['markov_top']}\n"
            text += "\n=== 改善AI予測（頻出・連続ペア加点）===\n"
            text += f"合算スコアTOP18: {ai_result['new_top18']}\n"
            text += "位別内訳:\n"
            for k, v in ai_result["new_bins"].items():
                text += f"  {k}: {sorted(v)}\n"
            text += f"\n前回当選との共通数: {len(set(ai_result['new_top18']) & set(ai_result['last_draw']))}個\n"
            text += "\n=== 直近24回出現ランキング（全数字）===\n"
            for num, cnt in ai_result["rank_24"].most_common():
                text += f"  {int(num)}: {int(cnt)}回\n"
        else:
            text += f"[AI予測生成エラー: {ai_result.get('error', '不明') if ai_result else '不明'}]\n"
        text += "=" * 50 + "\n"

        text += "\n（出典: https://naobillionaire.synergy.cfbx.jp/ ）\n"
        return text
    except Exception as e:
        return f"データ取得エラー: {e}"


def render_copy_button(text):
    safe = json.dumps(text)
    components.html(f"""
    <div style="font-family:sans-serif; margin-bottom:10px;">
      <button id="copyBtn" style="
          width:100%; padding:16px; font-size:18px; font-weight:bold;
          color:#fff; background:#1a5490; border:none; border-radius:10px;
          cursor:pointer; box-shadow:0 3px 8px rgba(0,0,0,0.2);">
          📋 AIに渡すデータをコピー
      </button>
      <span id="copyMsg" style="display:block; margin-top:8px; color:#2e7d32; font-weight:bold;"></span>
    </div>
    <script>
      const data = {safe};
      const btn = document.getElementById("copyBtn");
      const msg = document.getElementById("copyMsg");
      btn.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(data);
          msg.textContent = "✅ コピーしました！AI（Claude/ChatGPT/Gemini）に貼り付けてください";
        }} catch (e) {{
          const ta = document.createElement("textarea");
          ta.value = data;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
          msg.textContent = "✅ コピーしました！";
        }}
      }});
    </script>
    """, height=110)


# ============================================
# ★ タイトル＆最上部コピーボタン
# ============================================

st.title("ミニロト AI予想サイト")
_ai_export_text = build_ai_export_text(CSV_PATH)
render_copy_button(_ai_export_text)
with st.expander("コピーされる内容を確認する"):
    st.code(_ai_export_text, language="text")
st.markdown("---")


# ============================================
# データ読み込み
# ============================================

df = load_df(CSV_PATH)
df_recent = df.head(24).copy()

latest24_numbers = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts_abc = pd.Series(latest24_numbers).value_counts()
A_set = set(counts_abc[(counts_abc >= 3) & (counts_abc <= 4)].index)
B_set = set(counts_abc[counts_abc >= 5].index)

A = sorted([str(int(n)) for n in A_set])
B = sorted([str(int(n)) for n in B_set])
C = sorted([str(n) for n in range(1, 32) if n not in A_set and n not in B_set])

max_len = max(len(A), len(B), len(C))
A += [""] * (max_len - len(A))
B += [""] * (max_len - len(B))
C += [""] * (max_len - len(C))

abc_class_df = pd.DataFrame({
    "A（3〜4回）": A,
    "B（5回以上）": B,
    "C（その他）": C
})


# ============================================
# ① 最新当選番号
# ============================================

df_latest = df.iloc[0]

st.header("最新の当選番号")

main_number_cells = ''.join([
    f"<td class='center'>{int(df_latest[f'第{i}数字'])}</td>"
    for i in range(1, 6)
])
bonus_cell = (
    f"<td colspan='5' class='center' style='color:red; font-weight:bold;'>"
    f"{int(df_latest['ボーナス数字'])}</td>"
)

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


# ============================================
# ② 直近24回 + ABC + ひっぱり + 連続分析
# ============================================

st.header("直近24回の当選番号")

df_recent_asc = df.sort_values("抽せん日", ascending=True).tail(24).copy()
all_numbers_asc = pd.to_numeric(
    df_recent_asc[[f"第{i}数字" for i in range(1, 6)]].values.flatten(), errors="coerce"
)
counts_asc = pd.Series(all_numbers_asc).value_counts()
A_set_asc = set(counts_asc[(counts_asc >= 3) & (counts_asc <= 4)].index)
B_set_asc = set(counts_asc[counts_asc >= 5].index)

abc_rows = []
pull_total = 0
cont_total = 0
abc_counts_table = {'A': 0, 'B': 0, 'C': 0}
nums_list_asc = [
    [int(row[f"第{i}数字"]) for i in range(1, 6)]
    for _, row in df_recent_asc.iterrows()
]

for i in range(len(df_recent_asc)):
    nums = nums_list_asc[i]
    sorted_nums = sorted(nums)
    abc = []
    for n in sorted_nums:
        if n in B_set_asc:
            abc.append('B'); abc_counts_table['B'] += 1
        elif n in A_set_asc:
            abc.append('A'); abc_counts_table['A'] += 1
        else:
            abc.append('C'); abc_counts_table['C'] += 1
    abc_str = ','.join(abc)
    if i == 0:
        pulls_str = "-"
    else:
        pulls = len(set(nums) & set(nums_list_asc[i - 1]))
        pulls_str = f"{pulls}個" if pulls > 0 else "なし"
        if pulls > 0:
            pull_total += 1
    cont = any(b - a == 1 for a, b in zip(sorted_nums, sorted_nums[1:]))
    cont_str = "あり" if cont else "なし"
    if cont:
        cont_total += 1
    abc_rows.append({
        '抽せん日': df_recent_asc.iloc[i]['抽せん日'].strftime('%Y-%m-%d'),
        **{f"第{i}数字": nums[i - 1] for i in range(1, 6)},
        'ABC構成': abc_str,
        'ひっぱり': pulls_str,
        '連続': cont_str,
    })

abc_df = pd.DataFrame(abc_rows).sort_values(by='抽せん日', ascending=False).reset_index(drop=True)
st.markdown(style_table(abc_df), unsafe_allow_html=True)

total_abc_val = sum(abc_counts_table.values())
a_perc = round(abc_counts_table['A'] / total_abc_val * 100, 1) if total_abc_val > 0 else 0
b_perc = round(abc_counts_table['B'] / total_abc_val * 100, 1) if total_abc_val > 0 else 0
c_perc = round(abc_counts_table['C'] / total_abc_val * 100, 1) if total_abc_val > 0 else 0
pull_rate = round(pull_total / 24 * 100, 1)
cont_rate = round(cont_total / 24 * 100, 1)

st.markdown("#### 🔎 出現傾向（ABC割合・ひっぱり率・連続率）")
sum_df = pd.DataFrame({
    "分析項目": ["A割合", "B割合", "C割合", "ひっぱり率", "連続率"],
    "値": [f"{a_perc}%", f"{b_perc}%", f"{c_perc}%", f"{pull_rate}%", f"{cont_rate}%"]
})
st.markdown(style_table(sum_df), unsafe_allow_html=True)


# ============================================
# 分布パターン
# ============================================

st.header("分布パターン")

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


# ============================================
# AI予測セクション
# ============================================

st.header("🎯 AIによる次回出現数字候補（1の位・10の位・20の位 各6個／計18個）")

ai_result = run_ai_prediction(df)

if ai_result and "error" not in ai_result:
    rf_top = ai_result["rf_top"]
    mlp_top = ai_result["mlp_top"]
    markov_top = ai_result["markov_top"]
    rank_24 = ai_result["rank_24"]
    new_top18 = ai_result["new_top18"]
    new_bins = ai_result["new_bins"]
    last_draw = ai_result["last_draw"]

    st.markdown("## 🆕 改善AI予測（頻出・ひっぱり・連続を重視）")
    st.success(f"🧠 改善AI予測候補（18個：各位上位6個）: {new_top18}")
    common_prev = len(set(new_top18) & set(last_draw))
    st.write(f"🔁 前回当せん数字との共通数: {common_prev}個")
    consec_count = sum(any(abs(n - m) == 1 for m in new_top18) for n in new_top18)
    st.write(f"🔗 候補内に含まれる連続ペア数: {consec_count}個")

    with st.expander("📊 モデル別候補を表示"):
        st.write("🔹 ランダムフォレスト:", ", ".join(map(str, rf_top)))
        st.write("🔹 ニューラルネット:", ", ".join(map(str, mlp_top)))
        st.write("🔹 マルコフ連鎖:", ", ".join(map(str, markov_top)))
        st.write("🔹 直近24回出現ランキング:", ", ".join(f"{int(k)}({int(v)})" for k, v in rank_24.most_common()))

    max_bin_len = max(len(v) for v in new_bins.values())
    group_df = pd.DataFrame({
        k: new_bins[k] + [""] * (max_bin_len - len(new_bins[k]))
        for k in new_bins
    })
    st.markdown("### 🧮 候補数字の位別分類")
    st.markdown(style_table(group_df), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🤖 AI分析用データエクスポート")
    st.info("以下をコピー → AI（Claude/ChatGPT/Gemini）に貼り付け")

    tab1, tab2, tab3 = st.tabs(["📋 簡単コピー", "📊 JSON形式", "📝 詳細分析用"])

    with tab1:
        try:
            simple_text = "【ミニロト AI予測データ】\n\n"
            simple_text += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            simple_text += f"次回: 第{int(df.iloc[0]['回号']) + 1}回\n\n"
            simple_text += f"改善AI予測TOP18: {new_top18}\n"
            simple_text += "位別内訳:\n"
            for k, v in new_bins.items():
                simple_text += f"  {k}: {sorted(v)}\n"
            simple_text += f"\nRF TOP18: {rf_top}\n"
            simple_text += f"NN TOP18: {mlp_top}\n"
            simple_text += f"マルコフ TOP18: {markov_top}\n"
            st.code(simple_text, language='text')
        except Exception as e:
            st.error(f"簡単コピー生成エラー: {e}")

    with tab2:
        try:
            prediction_data = {
                "meta": {
                    "generated_at": datetime.now().isoformat(),
                    "current_round": int(df.iloc[0]["回号"]),
                    "next_round": int(df.iloc[0]["回号"]) + 1,
                    "previous_winning": last_draw,
                    "previous_bonus": int(df.iloc[0]["ボーナス数字"])
                },
                "predictions": {
                    "improved_top18": new_top18,
                    "by_digit": new_bins,
                    "rf_top18": rf_top,
                    "mlp_top18": mlp_top,
                    "markov_top18": markov_top,
                }
            }
            json_str = json.dumps(prediction_data, ensure_ascii=False, indent=2)
            st.code(json_str, language='json')
            st.download_button(
                label="📥 JSONファイルダウンロード",
                data=json_str,
                file_name=f"miniloto_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"JSON生成エラー: {e}")

    with tab3:
        try:
            st.code(_ai_export_text, language='text')
        except Exception as e:
            st.error(f"詳細分析生成エラー: {e}")
else:
    st.error(f"AI予測エラー: {ai_result.get('error', '不明') if ai_result else '不明'}")


# ============================================
# A・B数字の位別分類
# ============================================

st.header("A数字・B数字の位別分類（ミニロト）")

latest_numbers = {
    int(df.iloc[0][f"第{i}数字"]) for i in range(1, 6)
    if pd.notnull(df.iloc[0].get(f"第{i}数字"))
}

def highlight_number(n: int) -> str:
    return f"<span style='color:red; font-weight:bold'>{n}</span>" if n in latest_numbers else str(n)

def classify_numbers_mini_loto(numbers):
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
    "A数字": [', '.join(highlight_number(n) for n in sorted(A_bins[k])) for k in A_bins],
    "B数字": [', '.join(highlight_number(n) for n in sorted(B_bins[k])) for k in B_bins]
})
st.markdown(style_table_with_index(digit_table), unsafe_allow_html=True)


# ============================================
# 各位の出現回数TOP5
# ============================================

st.header("各位の出現回数TOP5")

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


# ============================================
# 各数字の出現回数TOP5（位置別）
# ============================================

st.header("各数字の出現回数TOP5（位置別）")

position_result = {'順位': ['1位', '2位', '3位', '4位', '5位']}
for i in range(1, 6):
    col = f'第{i}数字'
    counts_pos = df_recent[col].value_counts().sort_values(ascending=False).head(5)
    top5 = [f"{n}（{c}回）" for n, c in zip(counts_pos.index, counts_pos.values)] + [""] * (5 - len(counts_pos))
    position_result[col] = top5
st.markdown(style_table(pd.DataFrame(position_result)), unsafe_allow_html=True)


# ============================================
# 各数字の出現回数・出現率一覧
# ============================================

st.header("各数字の出現回数・出現率一覧")

number_range = range(1, 32)
recent100 = df.head(100)
recent24_freq = df.head(24)
flat100 = recent100[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
flat24_freq = recent24_freq[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
count100 = pd.Series(flat100).value_counts()
count24_freq = pd.Series(flat24_freq).value_counts()

freq_rows = []
for num in number_range:
    c100 = int(count100.get(num, 0))
    c24 = int(count24_freq.get(num, 0))
    freq_rows.append({
        "数字": num,
        "直近100回出現回数": c100,
        "直近100回出現率": round(c100 / 100 * 100, 1),
        "直近24回出現回数": c24,
        "直近24回出現率": round(c24 / 24 * 100, 1),
    })
freq_summary_df = pd.DataFrame(freq_rows)
freq_summary_df["100回ランク"] = freq_summary_df["直近100回出現回数"].rank(method="min", ascending=False).astype(int)
freq_summary_df["24回ランク"] = freq_summary_df["直近24回出現回数"].rank(method="min", ascending=False).astype(int)

def highlight_rank(val):
    try:
        val = int(val)
        if val <= 5:
            return "background-color:#ff4d4d;color:white;font-weight:bold;"
        if val <= 10:
            return "background-color:#ffcc00;font-weight:bold;"
        if val >= 25:
            return "background-color:#87cefa;font-weight:bold;"
        return ""
    except:
        return ""

styled = (
    freq_summary_df[[
        "数字", "直近100回出現回数", "直近100回出現率",
        "100回ランク", "直近24回出現回数", "直近24回出現率", "24回ランク"
    ]].style
    .map(highlight_rank, subset=["100回ランク", "24回ランク"])
    .format({"直近100回出現率": "{:.1f}%", "直近24回出現率": "{:.1f}%"})
)
st.markdown(styled.to_html(), unsafe_allow_html=True)


# ============================================
# 各数字の出現間隔分析一覧
# ============================================

st.header("各数字の出現間隔分析一覧")

df_interval = df.reset_index(drop=True)
interval_rows = []
for target in range(1, 32):
    hit_idx = [
        idx for idx, row in df_interval.iterrows()
        if target in [row[f"第{i}数字"] for i in range(1, 6)]
    ]
    if len(hit_idx) >= 2:
        intervals = [hit_idx[i] - hit_idx[i - 1] for i in range(1, len(hit_idx))]
        avg100 = round(sum(intervals) / len(intervals), 1)
        recent5 = "-".join(map(str, intervals[:5]))
        max_gap = max(intervals)
    else:
        avg100 = "-"
        recent5 = "-"
        max_gap = "-"
    if len(hit_idx) > 0:
        last_gap = hit_idx[0]
        latest_date = df_interval.iloc[hit_idx[0]]["抽せん日"].strftime("%Y-%m-%d")
    else:
        last_gap = "-"
        latest_date = "-"
    interval_rows.append({
        "数字": target,
        "直近100回平均間隔": avg100,
        "直近100回最大経過回数": max_gap,
        "直近5回の出現間隔": recent5,
        "最後の出現経過回数": last_gap,
        "一番最近の出現日": latest_date
    })
interval_df = pd.DataFrame(interval_rows)
st.markdown(interval_df.to_html(index=False), unsafe_allow_html=True)


# ============================================
# 連続数字ペア & ひっぱり傾向
# ============================================

st.header("連続数字ペア & ひっぱり傾向")

numbers_list_recent = df.head(24)[[f"第{i}数字" for i in range(1, 6)]].values.tolist()

consecutive_pairs = []
for row in numbers_list_recent:
    sorted_row = sorted(row)
    for a, b in zip(sorted_row, sorted_row[1:]):
        if b - a == 1:
            consecutive_pairs.append(f"{int(a)}-{int(b)}")
consec_counter = Counter(consecutive_pairs)
consec_df = pd.DataFrame(
    consec_counter.items(), columns=["連続ペア", "出現回数"]
).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

all_numbers_pull = [set(row) for row in numbers_list_recent]
pull_counter_num = Counter()
total_counter_num = Counter()
for i in range(1, len(all_numbers_pull)):
    current = all_numbers_pull[i]
    prev = all_numbers_pull[i - 1]
    for num in current:
        total_counter_num[num] += 1
        if num in prev:
            pull_counter_num[num] += 1

pull_data = []
for num in sorted(total_counter_num.keys()):
    total = total_counter_num[num]
    pulls = pull_counter_num.get(num, 0)
    rate = f"{round(pulls / total * 100, 1)}%" if total > 0 else "-"
    pull_data.append([int(num), total, pulls, rate])
pull_df = pd.DataFrame(pull_data, columns=["数字", "出現回数", "ひっぱり回数", "ひっぱり率"])
pull_df = pull_df.sort_values(by="ひっぱり率", ascending=False)

st.subheader("🔁 連続ペア 出現ランキング")
st.markdown(style_table(consec_df), unsafe_allow_html=True)
st.subheader("🔄 ひっぱり回数とひっぱり率")
st.markdown(style_table(pull_df), unsafe_allow_html=True)


# ============================================
# 基本予想（構成・出現・ABC優先）
# ============================================

st.header("基本予想（構成・出現・ABC優先）")

structure_patterns = [
    ['1', '10', '10', '20', '20'],
    ['1', '1', '10', '20', '20'],
    ['1', '1', '1', '20', '20'],
    ['1', '10', '20', '20', '20'],
    ['10', '10', '20', '20', '20'],
    ['10', '10', '10', '20', '20']
]
range_map = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 32))
}
all_numbers_base = df_recent[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts_base = pd.Series(all_numbers_base).value_counts()
A_base = counts_base[(counts_base >= 3) & (counts_base <= 4)].index.tolist()
B_base = counts_base[counts_base >= 5].index.tolist()
AB_pool = set([int(n) for n in A_base + B_base])
top_by_pos = {}
for i in range(1, 6):
    top_by_pos[i] = df_recent[f"第{i}数字"].value_counts().head(5).index.tolist()

random.seed(42)
predicts = []
while len(predicts) < 20:
    p = random.choice(structure_patterns)
    nums = []
    used = set()
    for idx, part in enumerate(p):
        pool = list(set(range_map[part]) & AB_pool - used)
        if top_by_pos[idx + 1]:
            pool = sorted(pool, key=lambda x: x not in top_by_pos[idx + 1])
        if pool:
            pick = random.choice(pool)
            nums.append(pick)
            used.add(pick)
    while len(nums) < 5:
        candidate = random.choice(list(AB_pool - used))
        nums.append(candidate)
        used.add(candidate)
    predicts.append(sorted(nums))

predict_df = pd.DataFrame(predicts, columns=["第1", "第2", "第3", "第4", "第5"])
st.markdown(style_table(predict_df), unsafe_allow_html=True)


# ============================================
# セレクト予想
# ============================================

st.header("セレクト予想")
axis = st.multiselect("軸数字（最大3）", list(range(1, 32)), max_selections=3)
remove = st.multiselect("除外数字（最大20）", list(range(1, 32)), max_selections=20)

def generate_selected(axis, remove, count=10):
    A_nums = [int(n) for n in abc_class_df['A（3〜4回）'] if n != '']
    B_nums = [int(n) for n in abc_class_df['B（5回以上）'] if n != '']
    C_nums = [int(n) for n in abc_class_df['C（その他）'] if n != '']
    ranges = [range(1, 10), range(10, 19), range(19, 22), range(22, 28), range(28, 32)]
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
    st.markdown(style_table(pd.DataFrame(pred, columns=["第1", "第2", "第3", "第4", "第5"])), unsafe_allow_html=True)


# ============================================
# セレクト予想ルーレット
# ============================================

st.header("セレクト予想ルーレット（ミニロト）")

group_dict_roulette = {
    "1": list(range(1, 10)),
    "10": list(range(10, 20)),
    "20": list(range(20, 32)),
}

st.markdown("#### 🔢 候補にする数字群を選択")
use_position_groups = st.checkbox("各位の出現回数TOP5（1の位〜30の位）", value=True)
use_position_top5 = st.checkbox("各第n位のTOP5（第1〜第5数字ごと）", value=True)
use_A = st.checkbox("A数字", value=True)
use_B = st.checkbox("B数字", value=True)
use_C = st.checkbox("C数字")
use_last = st.checkbox("前回数字を除外", value=True)
select_manual = st.multiselect("任意で追加したい数字 (1-31)", list(range(1, 32)))
pattern_input = st.text_input("パターンを入力 (例: 1-10-20-30-10)", value="1-10-20-30-10")
pattern = pattern_input.strip().split("-")

latest_roulette = df.iloc[0]
last_numbers_roulette = (
    latest_roulette[[f"第{i}数字" for i in range(1, 6)]].tolist() if use_last else []
)

digits_roulette = df.head(24)[[f"第{i}数字" for i in range(1, 6)]].values.flatten()
counts_roulette = pd.Series(digits_roulette).value_counts()
A_set_r = set(counts_roulette[(counts_roulette >= 3) & (counts_roulette <= 4)].index)
B_set_r = set(counts_roulette[counts_roulette >= 5].index)
C_set_r = set(range(1, 32)) - A_set_r - B_set_r

candidate_set = set(select_manual)
df_recent_r = df.head(24).copy()

if use_position_groups:
    number_groups_r = {'1': [], '10': [], '20': []}
    for i in range(1, 6):
        col = f"第{i}数字"
        col_values = pd.to_numeric(df_recent_r[col], errors="coerce")
        number_groups_r['1'].extend(col_values[col_values.between(1, 9)].tolist())
        number_groups_r['10'].extend(col_values[col_values.between(10, 19)].tolist())
        number_groups_r['20'].extend(col_values[col_values.between(20, 31)].tolist())
    for key in number_groups_r:
        top5 = pd.Series(number_groups_r[key]).value_counts().head(5).index.tolist()
        candidate_set.update(top5)

if use_position_top5:
    seen = set()
    for i in range(1, 6):
        col = f"第{i}数字"
        col_values = pd.to_numeric(df_recent_r[col], errors="coerce").dropna().astype(int)
        counts_r = col_values.value_counts()
        for num in counts_r.index:
            if num not in seen:
                candidate_set.add(num)
                seen.add(num)
            if len(seen) >= 5:
                break

if use_A:
    candidate_set.update(A_set_r)
if use_B:
    candidate_set.update(B_set_r)
if use_C:
    candidate_set.update(C_set_r)

candidate_set = sorted(set(candidate_set) - set(last_numbers_roulette))

def generate_select_prediction_roulette():
    prediction = []
    used = set()
    for group_key in pattern:
        group_nums = [
            n for n in group_dict_roulette.get(group_key, [])
            if n in candidate_set and n not in used
        ]
        if not group_nums:
            return []
        chosen = random.choice(group_nums)
        prediction.append(chosen)
        used.add(chosen)
    return sorted(prediction) if len(prediction) == 5 else []

if st.button("🎯 セレクト予想を出す（ミニロト）"):
    result = generate_select_prediction_roulette()
    if result:
        st.success(f"🎉 セレクト予想: {result}")
    else:
        st.error("条件に合致する数字が不足しています。候補を増やしてください。")

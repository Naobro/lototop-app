import streamlit as st
from auth import check_password  # type: ignore

check_password()
st.set_page_config(layout="centered")

import ssl
import pandas as pd
import random
from collections import Counter
import html
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from collections import defaultdict

# ✅ 外部モジュール読み込みはこれでOK。以下2行は完全に不要なので削除済み
# import sys
# from numbers3_ai import show_ai_predictions


# 最新の当選結果表示関数
def show_latest_results(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.replace("(", "（").replace(")", "）") for col in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.fillna("未定義")
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")
        df = df.dropna(subset=["抽せん日"])

        latest = df.sort_values(by="抽せん日", ascending=False).iloc[0]

        number_str = f"{latest['第1数字']}{latest['第2数字']}{latest['第3数字']}"

        st.header("① 最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(latest['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽せん日</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(latest['抽せん日'].strftime('%Y-%m-%d'))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {number_str}
                </td>
            </tr>
            <tr>
    <td style="padding: 10px; font-weight: bold; text-align: left;">ストレート</td>
    <td colspan="2">{html.escape(str(latest['ストレート口数']))}口</td>
    <td>{html.escape(str(latest['ストレート当選金額']))}円</td>
</tr>
<tr>
    <td style="padding: 10px; font-weight: bold; text-align: left;">ボックス</td>
    <td colspan="2">{html.escape(str(latest['ボックス口数']))}口</td>
    <td>{html.escape(str(latest['ボックス当選金額']))}円</td>
</tr>
<tr>
    <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ストレート</td>
    <td colspan="2">{html.escape(str(latest['セット（ストレート）口数']))}口</td>
    <td>{html.escape(str(latest['セット（ストレート）当選金額']))}円</td>
</tr>
<tr>
    <td style="padding: 10px; font-weight: bold; text-align: left;">セット・ボックス</td>
    <td colspan="2">{html.escape(str(latest['セット（ボックス）口数']))}口</td>
    <td>{html.escape(str(latest['セット（ボックス）当選金額']))}円</td>
</tr>
<tr>
    <td style="padding: 10px; font-weight: bold; text-align: left;">ミニ</td>
    <td colspan="2">{html.escape(str(latest['ミニ口数']))}口</td>
    <td>{html.escape(str(latest['ミニ当選金額']))}円</td>
</tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.error(f"エラー詳細: {type(e)}")
CSV_PATH = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"

# Streamlit表示
def show_page():
    st.title("ナンバーズ3 - 当選予想ページ")
    show_latest_results(CSV_PATH)

# 実行
# ✅ 修正後（この1行だけにする）
show_page()

import pandas as pd
import streamlit as st

import pandas as pd
import streamlit as st

import pandas as pd
import streamlit as st

st.header("② 直近24回の当選番号（ABC分類付き）")

def generate_recent_numbers3_table(csv_path):
    try:
        # CSV読み込みと整形
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["第1数字", "第2数字", "第3数字"])
        df[["第1数字", "第2数字", "第3数字"]] = df[["第1数字", "第2数字", "第3数字"]].astype(int)
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce").dt.strftime("%Y-%m-%d")

        # 直近24回に絞る
        df_recent = df.sort_values("回号", ascending=False).head(24).reset_index(drop=True)

        # ABC分類マップ（直近24回のみ）
        def get_abc_rank_map(series):
            counts = series.value_counts().sort_values(ascending=False)
            digits = counts.index.tolist()
            abc_map = {}
            for i, num in enumerate(digits[:10]):
                if i < 4:
                    abc_map[num] = "A"
                elif i < 7:
                    abc_map[num] = "B"
                else:
                    abc_map[num] = "C"
            return abc_map

        abc_map_1 = get_abc_rank_map(df_recent["第1数字"])
        abc_map_2 = get_abc_rank_map(df_recent["第2数字"])
        abc_map_3 = get_abc_rank_map(df_recent["第3数字"])

        # ABC分類（Aだけ赤色HTMLで装飾）
        def abc_with_color(d1, d2, d3):
            def colorize(x):
                return f'<span style="color:red;font-weight:bold">{x}</span>' if x == "A" else x
            a1 = colorize(abc_map_1.get(d1, "-"))
            a2 = colorize(abc_map_2.get(d2, "-"))
            a3 = colorize(abc_map_3.get(d3, "-"))
            return f"{a1},{a2},{a3}"

        df_recent["ABC分類"] = df_recent.apply(
            lambda row: abc_with_color(row["第1数字"], row["第2数字"], row["第3数字"]),
            axis=1
        )

        # 表示用テーブル（HTML形式）
        df_display = df_recent[["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "ABC分類"]]
        st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# 実行
recent_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_recent_numbers3_table(recent_csv_path)
# **③ ランキングの作成**
st.header("ランキング")

def generate_ranking(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のみを抽出（回号の降順）
        df = df.sort_values("回号", ascending=False).head(24)

        def rank_counts(series):
            counts = series.value_counts().sort_values(ascending=False)
            df_rank = counts.reset_index()
            df_rank.columns = ["数字", "出現回数"]
            df_rank["順位"] = df_rank["出現回数"].rank(method="dense", ascending=False).astype(int)
            return df_rank.sort_values(["順位", "数字"]).reset_index(drop=True)

        def expand_top_ranks(ranking_df, max_rank=5):
            return ranking_df[ranking_df["順位"] <= max_rank].sort_values(["順位", "数字"]).reset_index(drop=True)

        top_1st = expand_top_ranks(rank_counts(df["第1数字"]))
        top_2nd = expand_top_ranks(rank_counts(df["第2数字"]))
        top_3rd = expand_top_ranks(rank_counts(df["第3数字"]))

        max_len = max(len(top_1st), len(top_2nd), len(top_3rd))
        fill = lambda lst: lst + [""] * (max_len - len(lst))

        combined_df = pd.DataFrame({
            "順位": [f"{i+1}位" for i in range(max_len)],
            "第1桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_1st.iterrows()]),
            "第2桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_2nd.iterrows()]),
            "第3桁目": fill([f"{row['数字']}（{row['出現回数']}回）" for _, row in top_3rd.iterrows()])
        })

        # スタイル適用：上位3位まで黄色、文字を中央揃え
        def highlight(row):
            if row["順位"] in ["1位", "2位", "3位"]:
                return ['background-color: gold; color: black; font-weight: bold; text-align: center'] * len(row)
            return ['text-align: center'] * len(row)

        st.write(combined_df.style.apply(highlight, axis=1).set_properties(**{'text-align': 'center'}))

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVパス指定
ranking_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_ranking(ranking_csv_path)

# **④分析セクション**
st.header("分析セクション")

import pandas as pd
import streamlit as st
from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import itertools

# ====================== AI予測関数 ======================
def show_ai_predictions(csv_path):
    st.header("🎯 AIによる次回数字予測")

    try:
        df = pd.read_csv(csv_path)
        st.write("✅ CSV読み込み成功")

        # カラム名の正規化（全角→半角）
        df.columns = [col.replace('（', '(').replace('）', ')') for col in df.columns]
        required_cols = ["第1数字", "第2数字", "第3数字"]
        if not all(col in df.columns for col in required_cols):
            st.error("必要なカラム（第1数字〜第3数字）が見つかりません")
            st.write("現在のカラム:", df.columns.tolist())
            return

        # 数値化＆直近最大100回に制限
        df = df.dropna(subset=required_cols)
        df[required_cols] = df[required_cols].astype(int)
        df = df.tail(min(len(df), 100)).reset_index(drop=True)

        # 入力と出力データ作成
        X, y1, y2, y3 = [], [], [], []
        for i in range(len(df) - 1):
            prev = df.iloc[i + 1]
            curr = df.iloc[i]
            X.append([prev["第1数字"], prev["第2数字"], prev["第3数字"]])
            y1.append(curr["第1数字"])
            y2.append(curr["第2数字"])
            y3.append(curr["第3数字"])

        # ================== モデル学習 ==================
        rf = RandomForestClassifier(n_estimators=100, random_state=0)
        nn = MLPClassifier(max_iter=500, random_state=0)
        rf.fit(X, y1)
        nn.fit(X, y1)
        rf_y2 = RandomForestClassifier(n_estimators=100, random_state=0)
        rf_y2.fit(X, y2)
        nn_y2 = MLPClassifier(max_iter=500, random_state=0)
        nn_y2.fit(X, y2)
        rf_y3 = RandomForestClassifier(n_estimators=100, random_state=0)
        rf_y3.fit(X, y3)
        nn_y3 = MLPClassifier(max_iter=500, random_state=0)
        nn_y3.fit(X, y3)

        latest = df.iloc[0]
        latest_input = [[latest["第1数字"], latest["第2数字"], latest["第3数字"]]]

        def get_top3(model, X_input):
            probs = model.predict_proba(X_input)[0]
            top_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:3]
            return top_indices

        # ================== 各モデルTOP3表示 ==================
        rf_top3 = [
            get_top3(rf, latest_input),
            get_top3(rf_y2, latest_input),
            get_top3(rf_y3, latest_input)
        ]
        nn_top3 = [
            get_top3(nn, latest_input),
            get_top3(nn_y2, latest_input),
            get_top3(nn_y3, latest_input)
        ]

        def markov_chain_prediction(series):
            transitions = defaultdict(Counter)
            for i in range(len(series) - 1):
                curr, next_ = series[i], series[i + 1]
                transitions[curr][next_] += 1
            last = series[0]
            next_counts = transitions.get(last, {})
            return [num for num, _ in next_counts.most_common(3)]

        mc_top3 = [
            markov_chain_prediction(df["第1数字"].tolist()),
            markov_chain_prediction(df["第2数字"].tolist()),
            markov_chain_prediction(df["第3数字"].tolist())
        ]

        # ✅ モデル別TOP3表示
        def show_model_table(title, data):
            st.subheader(title)
            df_model = pd.DataFrame({
                "第1数字": data[0],
                "第2数字": data[1],
                "第3数字": data[2]
            })
            df_model.index = [f"{i+1}番目" for i in range(3)]
            st.dataframe(df_model.style.set_properties(**{'text-align': 'center'}), use_container_width=True)

        show_model_table("🌲 ランダムフォレスト TOP3", rf_top3)
        show_model_table("🧠 ニューラルネット TOP3", nn_top3)
        show_model_table("🔁 マルコフ連鎖 TOP3", mc_top3)

        # ================== TOP5統合（3モデル合算） ==================
        final_top5 = []
        for i in range(3):  # 第1,2,3桁
            combined = rf_top3[i] + nn_top3[i] + mc_top3[i]
            freq = Counter(combined)
            top5 = [num for num, _ in freq.most_common()]
            final_top5.append(sorted(set(top5))[:5])  # ユニーク化＋ソート

        final_top3 = [lst[:3] for lst in final_top5]

        # ================== 組合せ表示 ==================
        comb_5x5x5 = list(itertools.product(*final_top5))
        df_5 = pd.DataFrame(comb_5x5x5, columns=["第1数字", "第2数字", "第3数字"])
        st.subheader("🎯 最終候補：AI統合 125通り（5×5×5）")
        st.dataframe(df_5, use_container_width=True)

        comb_3x3x3 = list(itertools.product(*final_top3))
        df_3 = pd.DataFrame(comb_3x3x3, columns=["第1数字", "第2数字", "第3数字"])
        st.subheader("🔍 絞り込んだ27通り（3×3×3）")
        st.dataframe(df_3, use_container_width=True)

    except Exception as e:
        st.error("AI予測の実行中にエラーが発生しました")
        st.exception(e)

# ====================== Streamlit呼び出し ======================
def show_page():
    show_ai_predictions("data/n3.csv")

show_page()

# **ナンバーズ3 直近24回のWとSの回数**
st.subheader("直近24回のWとSの回数")

def generate_w_and_s(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # WとSの回数をカウント
        w_count = 0
        s_count = 0

        # 各回の当選番号を調べる
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            
            # 重複が2個ある場合W（ダブル）
            if len(set(numbers)) == 2:  # 2つの異なる数字がある
                w_count += 1
            # すべて異なる場合S（シングル）
            elif len(set(numbers)) == 3:  # 3つすべて異なる数字
                s_count += 1

        # WとSの回数をデータフレームで表示
        result_df = pd.DataFrame({
            "分析項目": ["W（ダブル）", "S（シングル）"],
            "回数": [w_count, s_count]
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_w_and_s(csv_path)

# **ナンバーズ3 直近24回のひっぱり数字の回数**
st.subheader("直近24回のひっぱり回数")

def generate_hoppari_numbers(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # ひっぱり数字の回数をカウント
        hoppari_count = 0

        # 各回の当選番号を調べる
        for i in range(1, len(df_recent)):
            current_numbers = {df_recent.iloc[i]['第1数字'], df_recent.iloc[i]['第2数字'], df_recent.iloc[i]['第3数字']}
            previous_numbers = {df_recent.iloc[i-1]['第1数字'], df_recent.iloc[i-1]['第2数字'], df_recent.iloc[i-1]['第3数字']}
            
            # 現在の回と前回の当選番号に共通する数字があれば「ひっぱり数字」
            if len(current_numbers.intersection(previous_numbers)) > 0:
                hoppari_count += 1

        # ひっぱり数字の回数を表示
        result_df = pd.DataFrame({
            "分析項目": ["ひっぱり数字"],
            "回数": [hoppari_count]
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_hoppari_numbers(csv_path)

# **ナンバーズ3 直近24回の数字の分布（範囲ごとの分布）**
st.subheader("直近24回の数字の分布（範囲ごとの分布）")

def generate_range_distribution(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # 範囲ごとのカウント
        range_counts = {'A (0-2)': 0, 'B (3-5)': 0, 'C (6-9)': 0}

        # 各回の当選番号を調べ、範囲に分けてカウント
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            for num in numbers:
                if 0 <= num <= 2:
                    range_counts['A (0-2)'] += 1
                elif 3 <= num <= 5:
                    range_counts['B (3-5)'] += 1
                elif 6 <= num <= 9:
                    range_counts['C (6-9)'] += 1

        # 範囲ごとの分布をデータフレームで表示
        result_df = pd.DataFrame({
            "範囲": list(range_counts.keys()),
            "出現回数": list(range_counts.values())
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_range_distribution(csv_path)


        
# **組み合わせパターン（ペア）のカウント**
st.subheader("直近24回の組み合わせパターン（ペア）のカウント")

def generate_combinations(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # ペアのカウント
        pair_counts = Counter()

        # 各回の当選番号を調べる
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字']]
            # ペア（2つの数字の組み合わせ）
            for i in range(len(numbers)):
                for j in range(i + 1, len(numbers)):
                    pair = tuple(sorted([numbers[i], numbers[j]]))  # ペアをソートして重複を避ける
                    pair_counts[pair] += 1

        # 結果をデータフレームで表示
        pair_df = pd.DataFrame(pair_counts.items(), columns=["ペア", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

        st.write("ペアの出現回数：")
        st.write(pair_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_combinations(csv_path)

# **数字の合計値の分析**
st.subheader("直近24回の数字の合計値の分析")

def generate_sum_analysis(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # 合計値のカウント
        sum_counts = Counter()

        # 各回の当選番号の合計を計算
        for _, row in df_recent.iterrows():
            total = row['第1数字'] + row['第2数字'] + row['第3数字']
            sum_counts[total] += 1

        # 結果をデータフレームで表示
        sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

        st.write("数字の合計値の出現回数：")
        st.write(sum_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv"
generate_sum_analysis(csv_path)

# **予測セクション**
st.header("ナンバーズ3 予測")
st.write("軸数字を1つ選択")

# ① ランダム予測（軸数字を必ず含む）
def generate_random_predictions(n, axis_number):
    predictions = []
    for _ in range(n):
        # ランダム予測：軸数字を含んだ予測
        prediction = [axis_number, random.choice([i for i in range(10) if i != axis_number]), random.choice([i for i in range(10) if i != axis_number])]
        prediction = sorted(prediction)  # 順番を無視するためにソート
        if prediction not in predictions:  # 重複を排除
            predictions.append(prediction)
    return predictions

# **予測のボタン処理**
axis_number = st.selectbox("軸数字を選択 (0〜9)", list(range(10)), key="axis_number")
num_predictions = 20  # 予測数を20に固定

# ランダム予測ボタン
if st.button("20パターン予測", key="random_predict_button"):
    random_predictions = generate_random_predictions(num_predictions, axis_number)
    st.write(f"ランダム予測 (20パターン)：")
    df_random_predictions = pd.DataFrame(random_predictions, columns=[f'予測番号{i+1}' for i in range(3)])
    st.dataframe(df_random_predictions)


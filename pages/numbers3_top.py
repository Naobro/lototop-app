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

import pandas as pd
import streamlit as st
from collections import Counter

def show_ai_predictions(csv_path):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.exceptions import NotFittedError
    from collections import defaultdict, Counter
    import itertools

    st.header("AIによる次回数字予測")

    try:
        df = pd.read_csv(csv_path)
        # ✅ カラム名の全角→半角カッコ変換
        df.columns = [col.replace('（', '(').replace('）', ')') for col in df.columns]

        df = df.dropna(subset=["第1数字", "第2数字", "第3数字"])
        df[["第1数字", "第2数字", "第3数字"]] = df[["第1数字", "第2数字", "第3数字"]].astype(int)

        # 学習データ作成
        X, y1, y2, y3 = [], [], [], []
        for i in range(len(df) - 1):
            prev = df.iloc[i + 1]
            curr = df.iloc[i]
            X.append([prev["第1数字"], prev["第2数字"], prev["第3数字"]])
            y1.append(curr["第1数字"])
            y2.append(curr["第2数字"])
            y3.append(curr["第3数字"])
        X = pd.DataFrame(X)
        latest = [int(df.iloc[0][f"第{i}数字"]) for i in range(1, 4)]

        # TOP候補取得関数
        def get_top_n(model, x, n=3):
            try:
                probs = model.predict_proba([x])[0]
                return [str(i) for i, _ in sorted(enumerate(probs), key=lambda x: -x[1])[:n]]
            except (AttributeError, NotFittedError):
                pred = model.predict([x])[0]
                return [str(pred)]

        # モデル定義
        rf_model = RandomForestClassifier(n_estimators=100)
        nn_model = MLPClassifier(hidden_layer_sizes=(50,), max_iter=1000)

        rf_top5 = [
            get_top_n(rf_model.fit(X, y1), latest, 5),
            get_top_n(rf_model.fit(X, y2), latest, 5),
            get_top_n(rf_model.fit(X, y3), latest, 5)
        ]
        nn_top5 = [
            get_top_n(nn_model.fit(X, y1), latest, 5),
            get_top_n(nn_model.fit(X, y2), latest, 5),
            get_top_n(nn_model.fit(X, y3), latest, 5)
        ]

        # マルコフ連鎖
        def markov_top_n(col, n=5):
            transition = defaultdict(list)
            values = df[col].astype(str).tolist()
            for i in range(len(values) - 1):
                transition[values[i]].append(values[i + 1])
            last = values[0]
            count = Counter(transition[last])
            return [v for v, _ in count.most_common(n)]

        mc_top5 = [
            markov_top_n("第1数字", 5),
            markov_top_n("第2数字", 5),
            markov_top_n("第3数字", 5)
        ]

        # 表形式表示（TOP3のみ）
        rf_top3 = [lst[:3] for lst in rf_top5]
        nn_top3 = [lst[:3] for lst in nn_top5]
        mc_top3 = [lst[:3] for lst in mc_top5]

        result_df = pd.DataFrame([
            ["🌲 ランダムフォレスト"] + [", ".join(rf_top3[i]) for i in range(3)],
            ["🧠 ニューラルネット"] + [", ".join(nn_top3[i]) for i in range(3)],
            ["🔁 マルコフ連鎖"] + [", ".join(mc_top3[i]) for i in range(3)],
        ], columns=["モデル名", "第1数字候補", "第2数字候補", "第3数字候補"])

        st.subheader("🔍 AIモデル予測（次に来る数字の上位3候補）")
        st.dataframe(result_df, use_container_width=True)

        # 共通数字
        st.subheader("✅ 3手法で一致した数字")
        for i, k in enumerate(["第1数字", "第2数字", "第3数字"]):
            common = set(rf_top3[i]) & set(nn_top3[i]) & set(mc_top3[i])
            if common:
                st.markdown(f"**{k}**：{'、'.join(sorted(common))}")
            else:
                st.markdown(f"**{k}**：一致なし")

        # ✅ 各モデルの5候補をまとめた最終候補（int型で昇順）
        final_top5 = []
        for i in range(3):
            combined = list(set(rf_top5[i] + nn_top5[i] + mc_top5[i]))
            combined_int = sorted(set(map(int, combined)))[:5]
            final_top5.append(combined_int)
        final_top3 = [lst[:3] for lst in final_top5]

        # 🔢 5x5x5組合せ
        comb_5x5x5 = list(itertools.product(*final_top5))
        df_5 = pd.DataFrame(comb_5x5x5, columns=["第1数字", "第2数字", "第3数字"])
        st.subheader("🎯 このサイトが推す125通り（5×5×5）")
        st.dataframe(df_5, use_container_width=True)

        # 🔍 3x3x3組合せ
        comb_3x3x3 = list(itertools.product(*final_top3))
        df_3 = pd.DataFrame(comb_3x3x3, columns=["第1数字", "第2数字", "第3数字"])
        st.subheader("🔍 絞り込んだ27通り（3×3×3）")
        st.dataframe(df_3, use_container_width=True)

    except Exception as e:
        st.error("AI予測の実行中にエラーが発生しました")
        st.exception(e)
        
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


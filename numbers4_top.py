import pandas as pd
import streamlit as st
import html

# **最新の当選番号テーブルを生成**
def generate_numbers4_table(latest_csv):
    try:
        # CSVファイルを読み込む
        df_latest = pd.read_csv(latest_csv)

        # カラム名にスペースを除去
        df_latest.columns = df_latest.columns.str.strip()  # カラム名の余分なスペースを削除

        # データの行を取得
        str_result = df_latest[df_latest['タイプ'] == 'ストレート'].iloc[0]  # ストレートの結果
        box_result = df_latest[df_latest['タイプ'] == 'ボックス'].iloc[0]  # ボックスの結果
        set_str_result = df_latest[df_latest['タイプ'] == 'セット・ストレート'].iloc[0]  # セット・ストレートの結果
        set_box_result = df_latest[df_latest['タイプ'] == 'セット・ボックス'].iloc[0]  # セット・ボックスの結果

        # Streamlitページのタイトル
        st.title("ナンバーズ4 最新の当選番号")

        # 最新の当選番号テーブルを生成
        st.header("① 最新の当選番号")
        table_html = f"""
        <table style="width: 80%; margin: 0 auto; border-collapse: collapse; text-align: right;">
            <tr>
                <td style="padding: 10px; font-weight: bold;text-align: left;">回号</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(str_result['回号']))}回</td>
                <td style="padding: 10px; font-weight: bold;">抽選日</td>
                <td style="padding: 10px; font-size: 20px;">{html.escape(str(str_result['抽選日']))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">当選番号</td>
                <td colspan="3" style="padding: 10px; font-size: 24px; font-weight: bold; color: red; text-align: right;">
                    {html.escape(str(str_result['当選番号']))}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ストレート</td>
                <td style="padding: 10px; text-align: right;" colspan="2">{html.escape(str(str_result['当選口数']))}</td>
                <td style="padding: 10px; text-align: right;">{html.escape(str(str_result['当選金額']))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">ボックス</td>
                <td style="padding: 10px; text-align: right;" colspan="2">{html.escape(str(box_result['当選口数']))}</td>
                <td style="padding: 10px; text-align: right;">{html.escape(str(box_result['当選金額']))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット-ストレート</td>
                <td style="padding: 10px; text-align: right;" colspan="2">{html.escape(str(set_str_result['当選口数']))}</td>
                <td style="padding: 10px; text-align: right;">{html.escape(str(set_str_result['当選金額']))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; text-align: left;">セット-ボックス</td>
                <td style="padding: 10px; text-align: right;" colspan="2">{html.escape(str(set_box_result['当選口数']))}</td>
                <td style="padding: 10px; text-align: right;">{html.escape(str(set_box_result['当選金額']))}</td>
            </tr>
        </table>
        """

        # 最新の当選番号テーブルを表示
        st.markdown(table_html, unsafe_allow_html=True)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
latest_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers_4_latest.csv"
generate_numbers4_table(latest_csv_path)

import pandas as pd
import streamlit as st
import html

# **② 直近24回の当選番号**を表示
st.header("② 直近24回の当選番号")

def generate_recent_numbers4_table(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["抽せん日"] = pd.to_datetime(df["抽せん日"], errors="coerce")  # 日付に変換
        df = df.dropna(subset=["抽せん日"])  # 日付が無効な行を削除
        df_recent = df.tail(24).sort_values(by="抽せん日", ascending=False)  # 直近24回を取得

        # データフレームの内容を表示
        st.write(df_recent)  # データフレームを表示
        
        # 正しいHTML構造に修正
        table_html = """
        <table style="width: 100%; margin: 0 auto; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="padding: 10px; font-weight: bold; text-align: left;">回号</th>
                    <th style="padding: 10px; font-weight: bold; text-align: left;">抽選日</th>
                    <th style="padding: 10px; font-weight: bold; text-align: left;">当選番号</th>
                </tr>
            </thead>
            <tbody>
        """

        # テーブルの行を追加
        for _, row in df_recent.iterrows():
            table_html += f"""
            <tr>
                <td style="padding: 10px; text-align: left;">{html.escape(str(row['回号']))}</td>
                <td style="padding: 10px; text-align: left;">{html.escape(row['抽せん日'].strftime('%Y-%m-%d'))}</td>
                <td style="padding: 10px; text-align: right;">
                    {html.escape(str(row['第1数字']))}-{html.escape(str(row['第2数字']))}-{html.escape(str(row['第3数字']))}-{html.escape(str(row['第4数字']))}
                </td>
            </tr>
            """
        
        table_html += "</tbody></table>"  # テーブルの閉じタグを忘れずに追加

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
recent_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_recent_numbers4_table(recent_csv_path)

# **ナンバーズ4 ランキングの作成**
st.header("ナンバーズ4 ランキング")

def generate_ranking_numbers4(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)
        df["第4数字"] = df["第4数字"].astype(int)

        # 各数字の出現回数をカウント
        count_1st = df["第1数字"].value_counts().sort_values(ascending=False)
        count_2nd = df["第2数字"].value_counts().sort_values(ascending=False)
        count_3rd = df["第3数字"].value_counts().sort_values(ascending=False)
        count_4th = df["第4数字"].value_counts().sort_values(ascending=False)

        # 数字1から9までを揃えて0で埋める
        all_numbers = range(0, 10)  # ナンバーズ4の場合、0から9の数字が使用される
        count_1st = count_1st.reindex(all_numbers).fillna(0).astype(int)
        count_2nd = count_2nd.reindex(all_numbers).fillna(0).astype(int)
        count_3rd = count_3rd.reindex(all_numbers).fillna(0).astype(int)
        count_4th = count_4th.reindex(all_numbers).fillna(0).astype(int)

        # データフレームを作成
        ranking_df = pd.DataFrame({
            "順位": [f"{i+1}位" for i in range(10)],
            "第1数字": [f"{num}({count})" for num, count in zip(count_1st.index[:10], count_1st.values[:10])],
            "第2数字": [f"{num}({count})" for num, count in zip(count_2nd.index[:10], count_2nd.values[:10])],
            "第3数字": [f"{num}({count})" for num, count in zip(count_3rd.index[:10], count_3rd.values[:10])],
            "第4数字": [f"{num}({count})" for num, count in zip(count_4th.index[:10], count_4th.values[:10])],
        })

        # それぞれの列を出現回数順に並べ替える
        ranking_df["第1数字"] = count_1st.sort_values(ascending=False).index[:10]
        ranking_df["第2数字"] = count_2nd.sort_values(ascending=False).index[:10]
        ranking_df["第3数字"] = count_3rd.sort_values(ascending=False).index[:10]
        ranking_df["第4数字"] = count_4th.sort_values(ascending=False).index[:10]

        # 順位列を最初に移動
        ranking_df = ranking_df[["順位", "第1数字", "第2数字", "第3数字", "第4数字"]]

        # 上位5位まで目立つ色で塗りつぶし、文字を赤文字で太字に
        def highlight_top5(row):
            if row["順位"] in ["1位", "2位", "3位", "4位", "5位"]:
                return ['background-color: yellow; color: black; font-weight: bold; text-align: center'] * len(row)
            return ['text-align: center'] * len(row)

        # ランキングテーブルを表示
        st.write(ranking_df.style.apply(highlight_top5, axis=1).set_properties(**{'text-align': 'center'}))

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
ranking_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_ranking_numbers4(ranking_csv_path)
# **④分析セクション**
st.header("④分析セクション")
from collections import Counter  # これを追加

# **直近24回のW（ダブル）、S（シングル）、T（トリプル）の回数（ナンバーズ4）**
st.subheader("直近24回のW（ダブル）、S（シングル）、T（トリプル）の回数")

def generate_w_s_t(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)
        df["第4数字"] = df["第4数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # 各回のシングル、ダブル、トリプルのカウント
        single_count = 0
        double_count = 0
        triple_count = 0

        # 各回の当選番号を調べる
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字'], row['第4数字']]
            
            # トリプル：同じ数字が3つ以上
            number_counts = Counter(numbers)
            if 3 in number_counts.values():  # 3つ同じ数字がある場合はトリプル
                triple_count += 1
            elif len(set(numbers)) == 3:  # ダブル：同じ数字が2つ、異なる数字が1つ
                double_count += 1
            elif len(set(numbers)) == 4:  # シングル：全て異なる数字
                single_count += 1

        # 結果をデータフレームで表示
        result_df = pd.DataFrame({
            "分析項目": ["シングル", "ダブル", "トリプル"],
            "回数": [single_count, double_count, triple_count]
        })
        st.write(result_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_w_s_t(csv_path)
# **ナンバーズ4 直近24回のひっぱり数字の回数**
st.subheader("直近24回のひっぱり回数")

def generate_hoppari_numbers(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)
        df["第4数字"] = df["第4数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # ひっぱり数字の回数をカウント
        hoppari_count = 0

        # 各回の当選番号を調べる
        for i in range(1, len(df_recent)):
            current_numbers = {df_recent.iloc[i]['第1数字'], df_recent.iloc[i]['第2数字'], df_recent.iloc[i]['第3数字'], df_recent.iloc[i]['第4数字']}
            previous_numbers = {df_recent.iloc[i-1]['第1数字'], df_recent.iloc[i-1]['第2数字'], df_recent.iloc[i-1]['第3数字'], df_recent.iloc[i-1]['第4数字']}
            
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
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_hoppari_numbers(csv_path)

# **ナンバーズ4 直近24回の数字の分布（範囲ごとの分布）**
st.subheader("直近24回の数字の分布（範囲ごとの分布）")

def generate_range_distribution(csv_path):
    try:
        # CSVを読み込む
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")  # 欠損値を"未定義"で埋める
        df["第1数字"] = df["第1数字"].astype(int)
        df["第2数字"] = df["第2数字"].astype(int)
        df["第3数字"] = df["第3数字"].astype(int)
        df["第4数字"] = df["第4数字"].astype(int)

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # 範囲ごとのカウント
        range_counts = {'A (0-2)': 0, 'B (3-5)': 0, 'C (6-9)': 0}

        # 各回の当選番号を調べ、範囲に分けてカウント
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字'], row['第4数字']]
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
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_range_distribution(csv_path)
import pandas as pd
from collections import Counter
import streamlit as st

from collections import Counter  # これを追加

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
        df["第4数字"] = df["第4数字"].astype(int)  # 第4数字を追加

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # ペアのカウント
        pair_counts = Counter()

        # 各回の当選番号を調べる
        for _, row in df_recent.iterrows():
            numbers = [row['第1数字'], row['第2数字'], row['第3数字'], row['第4数字']]  # 4つの数字を取得
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
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
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
        df["第4数字"] = df["第4数字"].astype(int)  # 第4数字を追加

        # 直近24回のデータを取得
        df_recent = df.tail(24)

        # 合計値のカウント
        sum_counts = Counter()

        # 各回の当選番号の合計を計算
        for _, row in df_recent.iterrows():
            total = row['第1数字'] + row['第2数字'] + row['第3数字'] + row['第4数字']  # 4つの数字の合計
            sum_counts[total] += 1

        # 結果をデータフレームで表示
        sum_df = pd.DataFrame(sum_counts.items(), columns=["合計値", "出現回数"]).sort_values(by="出現回数", ascending=False).reset_index(drop=True)

        st.write("数字の合計値の出現回数：")
        st.write(sum_df)

    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVのパス
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/numbers4_24.csv"
generate_sum_analysis(csv_path)
import streamlit as st

import pandas as pd

# **ナンバーズ4 予測セクション**
st.header("ナンバーズ4 予測")
st.write("軸数字を1つ選択")

# ① ランダム予測（軸数字を必ず含む）
def generate_random_predictions(n, axis_number):
    predictions = []
    for _ in range(n):
        # ランダム予測：軸数字を含んだ予測
        prediction = [axis_number, random.choice([i for i in range(10) if i != axis_number]), 
                      random.choice([i for i in range(10) if i != axis_number]),
                      random.choice([i for i in range(10) if i != axis_number])]
        prediction = sorted(prediction)  # 順番を無視するためにソート
        if prediction not in predictions:  # 重複を排除
            predictions.append(prediction)
    return predictions

# **予測のボタン処理**
axis_number = st.selectbox("軸数字を選択 (0〜9)", list(range(10)), key="axis_number")
num_predictions = 20  # 予測数を20に固定

if st.button("20パターン予測", key="random_predict_button"):
    random_predictions = generate_random_predictions(num_predictions, axis_number)
    st.write(f"ランダム予測 (20パターン)：")
    df_random_predictions = pd.DataFrame(random_predictions, columns=[f'予測番号{i+1}' for i in range(4)])
    st.dataframe(df_random_predictions)
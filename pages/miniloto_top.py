import pandas as pd
import streamlit as st

# **ページのタイトル**
st.title("ミニロト AI予想サイト")

# CSVファイルのパス
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(csv_path)

# **① 最新の当選番号**を表示
st.header("① 最新の当選番号")

def generate_miniloto_table(latest_csv, prizes_csv):
    try:
        # 最新の抽選結果を読み込む
        df_latest = pd.read_csv(latest_csv)

        # データフレームが空でないことを確認
        if len(df_latest) > 0:
            latest_result = df_latest.iloc[0]
        else:
            return "データフレームが空です。"

        # 賞金情報を読み込む
        df_prizes = pd.read_csv(prizes_csv)

        # HTMLテーブルの生成
        table_html = f"""
        <table class='custom-table' style="width: 100%; border-collapse: collapse; text-align: right;">
            <tr>
                <th rowspan="2" style="width:15%;">回号</th>
                <td rowspan="2" class="center-align" style="font-weight: bold; font-size: 20px; text-align: right;">第{latest_result['回号'].replace('回回', '回')}</td>
                <th style="width:15%;">抽選日</th>
                <td class="center-align" style="text-align: right;">{latest_result['抽せん日'].replace('抽選', '')}</td>
            </tr>
            <tr>
                <th>本数字</th>
                <td class="center-align" style="font-size: 18px; font-weight: bold; color: #ff6347; text-align: right;">{latest_result['本数字']}</td>
            </tr>
            <tr>
                <th>ボーナス数字</th>
                <td colspan="3" class="center-align" style="font-size: 18px; font-weight: bold; color: #ff6347; text-align: right;">
                    <span class="bold-red">({latest_result['ボーナス数字']})</span>
                </td>
            </tr>
        </table>
        """

        # 賞金情報（1等〜4等）のテーブルを生成
        prize_table_html = """
        <table class='custom-table' style="width: 100%; border-collapse: collapse; text-align: right;">
            <thead>
                <tr>
                    <th>等級</th>
                    <th>口数</th>
                    <th>当選金額</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1等</td>
                    <td class="center-align">{}</td>
                    <td class="center-align">{}</td>
                </tr>
                <tr>
                    <td>2等</td>
                    <td class="center-align">{}</td>
                    <td class="center-align">{}</td>
                </tr>
                <tr>
                    <td>3等</td>
                    <td class="center-align">{}</td>
                    <td class="center-align">{}</td>
                </tr>
                <tr>
                    <td>4等</td>
                    <td class="center-align">{}</td>
                    <td class="center-align">{}</td>
                </tr>
            </tbody>
        </table>
        """.format(
            df_prizes.iloc[0]['口数'], df_prizes.iloc[0]['当選金額'],
            df_prizes.iloc[1]['口数'], df_prizes.iloc[1]['当選金額'],
            df_prizes.iloc[2]['口数'], df_prizes.iloc[2]['当選金額'],
            df_prizes.iloc[3]['口数'], df_prizes.iloc[3]['当選金額']
        )

        return table_html + prize_table_html

    except FileNotFoundError:
        return "CSVファイルが見つかりませんでした。パスを確認してください。"
    except Exception as e:
        return f"エラーが発生しました: {e}"

# **最新の当選番号**を表示
table = generate_miniloto_table(
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_latest.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_prizes.csv"
)
st.markdown(table, unsafe_allow_html=True)

import pandas as pd
import streamlit as st

# **② 直近24回の当選番号**を表示
st.header("② 直近24回の当選番号")

def generate_recent_miniloto_table(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        
        # '抽せん日' カラムを日付型に変換
        df['抽せん日'] = pd.to_datetime(df['抽せん日'], errors="coerce")
        
        # 無効な日付を削除
        df = df.dropna(subset=["抽せん日"])
        
        # 直近24回分を取得
        df_recent = df.tail(24).sort_values(by="抽せん日", ascending=False)

        # テーブルの作成
        table_html = "<table border='1' style='width: 100%; border-collapse: collapse; text-align: right;'>"
        table_html += "<thead><tr><th>抽選日</th><th>第1数字</th><th>第2数字</th><th>第3数字</th><th>第4数字</th><th>第5数字</th></tr></thead><tbody>"

        # データの行をテーブルに追加
        for _, row in df_recent.iterrows():
            table_html += f"<tr><td>{row['抽せん日'].strftime('%Y-%m-%d')}</td><td>{row['第1数字']}</td><td>{row['第2数字']}</td><td>{row['第3数字']}</td><td>{row['第4数字']}</td><td>{row['第5数字']}</td></tr>"

        table_html += "</tbody></table>"

        # HTMLとして表示
        st.markdown(table_html, unsafe_allow_html=True)
    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

# CSVファイルのパスを指定
recent_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
generate_recent_miniloto_table(recent_csv_path)

import pandas as pd
import streamlit as st

# **③ ランキング**を表示
st.header("③ 直近24回 出現回数 ランキング")

def generate_ranking_table(csv_path):
    df = pd.read_csv(csv_path)
    
    # '第1数字' から '第5数字' を使って出現回数を数える
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].values.flatten()

    # 数字の出現回数をカウント
    number_counts = pd.Series(numbers).value_counts().sort_values(ascending=False)

    ranking_df = pd.DataFrame({
        '順位': range(1, len(number_counts) + 1),
        '数字': number_counts.index,
        '出現回数': number_counts.values
    })

    ranking_html = "<table border='1' style='width: 100%; border-collapse: collapse; text-align: right;'>"
    ranking_html += "<thead><tr><th>順位</th><th>出現回数</th><th>数字</th></tr></thead><tbody>"

    for _, row in ranking_df.iterrows():
        ranking_html += f"<tr><td>{row['順位']}</td><td>{row['出現回数']}</td><td>{row['数字']}</td></tr>"

    ranking_html += "</tbody></table>"

    st.markdown(ranking_html, unsafe_allow_html=True)

# ランキング表示
ranking_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
generate_ranking_table(ranking_csv_path)

import pandas as pd
import streamlit as st

# **④ 分析**セクション
st.header("④ 分析セクション")

# パターン分析の表示
def analyze_number_patterns(csv_path):
    df = pd.read_csv(csv_path)

    # パターンを取得 (1-9は1、10-19は10...に分類)
    # '第1数字', '第2数字', '第3数字', '第4数字', '第5数字' を使ってパターンを分析
    patterns = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].apply(
        lambda x: '-'.join([str((int(num) - 1) // 10 * 10 + 1) if 1 <= int(num) <= 9 else str((int(num) // 10) * 10) for num in sorted(x)]), axis=1)

    # パターンごとの出現回数をカウント
    pattern_counts = patterns.value_counts().reset_index()
    pattern_counts.columns = ['パターン', '出現回数']

    st.write("出現したパターンとその回数:1→1〜9,10→10〜19,20→20〜29,30→30〜31")
    st.write(pattern_counts)

# CSVファイルのパスを指定して関数を呼び出し
analyze_number_patterns("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv")

import pandas as pd
import streamlit as st

# CSVファイルのURL
url = 'https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv'

# URLからミニロトのデータを読み込む
df = pd.read_csv(url)

# A数字とB数字の関数
def generate_AB_numbers(df):
    # ミニロトのデータは1〜31の範囲なので、数字が31以上の場合を除外する
    number_groups = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].values.flatten()
    number_groups = [num for num in number_groups if num <= 31]  # 31を超える数字を除外

    # 出現回数を計算
    number_counts = pd.Series(number_groups).value_counts()

    # A数字: 直近24回で出現回数3〜4回の数字を抽出
    A_numbers = number_counts[(number_counts >= 3) & (number_counts <= 4)].index.tolist()

    # B数字: 直近24回で出現回数5回以上の数字を抽出
    B_numbers = number_counts[number_counts >= 5].index.tolist()

    # A数字とB数字を横並びにして表示するためのDataFrameを作成
    AB_numbers_df = pd.DataFrame({
        'A数字　出現回数3〜4回': [', '.join(map(str, A_numbers))],
        'B数字　出現回数5回以上': [', '.join(map(str, B_numbers))]
    })

    # 横並びにして表示
    st.write("A数字とB数字:")
    st.table(AB_numbers_df)

# A数字とB数字のテーブルを表示
generate_AB_numbers(df)

import pandas as pd
import streamlit as st

# CSVファイルのURL
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(csv_path)

# A数字とB数字の関数
def generate_AB_numbers(df):
    # ミニロトのデータは1〜31の範囲なので、数字が31以上の場合を除外する
    number_groups = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].values.flatten()
    number_groups = [num for num in number_groups if num <= 31]  # 31を超える数字を除外

    # 出現回数を計算
    number_counts = pd.Series(number_groups).value_counts()

    # A数字: 直近24回で出現回数3〜4回の数字を抽出
    A_numbers = number_counts[(number_counts >= 3) & (number_counts <= 4)].index.tolist()

    # B数字: 直近24回で出現回数5回以上の数字を抽出
    B_numbers = number_counts[number_counts >= 5].index.tolist()

    # C数字: AとBに含まれないその他の数字
    all_numbers = set(range(1, 32))  # ミニロトは1〜31まで
    C_numbers = list(all_numbers - set(A_numbers) - set(B_numbers))

    return A_numbers, B_numbers, C_numbers

import pandas as pd
import streamlit as st


# CSVファイルのURL
csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"
df = pd.read_csv(csv_path)

# A数字とB数字の関数
def generate_AB_numbers(df):
    # ミニロトのデータは1〜31の範囲なので、数字が31以上の場合を除外する
    number_groups = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].values.flatten()
    number_groups = [num for num in number_groups if num <= 31]  # 31を超える数字を除外

    # 出現回数を計算
    number_counts = pd.Series(number_groups).value_counts()

    # A数字: 直近24回で出現回数3〜4回の数字を抽出
    A_numbers = number_counts[(number_counts >= 3) & (number_counts <= 4)].index.tolist()

    # B数字: 直近24回で出現回数5回以上の数字を抽出
    B_numbers = number_counts[number_counts >= 5].index.tolist()

    # C数字: AとBに含まれないその他の数字
    all_numbers = set(range(1, 32))  # ミニロトは1〜31まで
    C_numbers = list(all_numbers - set(A_numbers) - set(B_numbers))

    return A_numbers, B_numbers, C_numbers

# 直近10回の当選番号を取得する関数
def generate_recent_miniloto_table(csv_path, recent_count=10):
    df = pd.read_csv(csv_path)
    
    # '抽せん日' カラムを日付型に変換
    df['抽せん日'] = pd.to_datetime(df['抽せん日'], errors="coerce")
    
    # 無効な日付を削除
    df = df.dropna(subset=["抽せん日"])
    
    # 直近のn回分を取得
    df_recent = df.tail(recent_count).sort_values(by="抽せん日", ascending=False)
    
    return df_recent

# 直近10回の当選番号をA、B、Cに分類する関数
def categorize_numbers(df_recent, A_numbers, B_numbers, C_numbers):
    categorized_data = []
    
    for _, row in df_recent.iterrows():
        # 当選番号を取り出し
        numbers = [row['第1数字'], row['第2数字'], row['第3数字'], row['第4数字'], row['第5数字']]
        
        # グループを分類
        groups = []
        for num in numbers:
            if num in B_numbers:
                groups.append('B')
            elif num in A_numbers:
                groups.append('A')
            else:
                groups.append('C')
        
        categorized_data.append(groups)
    
    return categorized_data

# A、B、Cグループを取得
A_numbers, B_numbers, C_numbers = generate_AB_numbers(df)

# 直近10回の当選番号を取得
df_recent = generate_recent_miniloto_table(csv_path)

# 直近10回の当選番号をA、B、Cに分類
categorized_data = categorize_numbers(df_recent, A_numbers, B_numbers, C_numbers)

# **直近10回の当選番号とグループを表示**
st.header("② 直近10回の当選番号（A, B, C グループ）")

# テーブル形式で表示
table_data = {
    "抽選日": df_recent['抽せん日'].dt.strftime('%Y-%m-%d'),
    "第1数字": df_recent['第1数字'],
    "第2数字": df_recent['第2数字'],
    "第3数字": df_recent['第3数字'],
    "第4数字": df_recent['第4数字'],
    "第5数字": df_recent['第5数字'],
    "グループ": [' | '.join(groups) for groups in categorized_data]
}

table_df = pd.DataFrame(table_data)

st.table(table_df)

import random
import pandas as pd
import streamlit as st

# **範囲の設定**
column_ranges = {
    1: list(range(1, 10)),    # 一列目 (1〜9)
    2: list(range(10, 19)),   # 二列目 (10〜18)
    3: list(range(19, 22)),   # 三列目 (19〜21)
    4: list(range(22, 28)),   # 四列目 (22〜27)
    5: list(range(28, 32))    # 五列目 (28〜31)
}

# **直近24回のデータから3回以上出現した数字を抽出する関数**
def get_numbers_with_multiple_occurrences(df, min_occurrences=3):
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字']].values.flatten()
    number_counts = pd.Series(numbers).value_counts()
    return number_counts[number_counts >= min_occurrences].index.tolist()

# **前回の当選番号を取得する関数**
def get_previous_numbers(df):
    # 最新のデータから前回の抽選番号を取得
    latest_result = df.iloc[0]  # 最新の行
    previous_result = df.iloc[1]  # 1行前（前回の抽選結果）
    
    # 前回の当選番号をリストとして取得
    return [previous_result['第1数字'], previous_result['第2数字'], previous_result['第3数字'], previous_result['第4数字'], previous_result['第5数字']]

# **前回の当選番号の前後の数字を取得する関数**
def get_neighbouring_numbers(previous_numbers):
    neighbouring_numbers = []
    for num in previous_numbers:
        if num > 1:
            neighbouring_numbers.append(num - 1)  # 前の数字
        if num < 31:
            neighbouring_numbers.append(num + 1)  # 次の数字
    return list(set(neighbouring_numbers))  # 重複を排除して返す

# **その他の数字を取得する関数**
def get_other_numbers(excluded_numbers, all_numbers_range=range(1, 32)):
    # 除外された数字を取り除いた残りの数字を返す
    return list(set(all_numbers_range) - set(excluded_numbers))

# **範囲ごとに出現した数字をフィルタリングして選ぶ関数**
def get_numbers_by_range(available_numbers, ranges):
    selected_numbers = []
    
    for number_range in ranges:
        # それぞれの範囲に該当する数字をフィルタリング
        available_in_range = list(set(number_range) & set(available_numbers))
        if available_in_range:
            selected_numbers.append(random.choice(available_in_range))
    
    return selected_numbers

# **予測生成関数**
def generate_miniloto_prediction(axis_numbers, remove_numbers, df, prediction_count=10):
    # 使用する数字のリスト
    available_numbers = set(range(1, 32)) - set(remove_numbers)  # 削除した数字を除外
    predictions = []

    # A〜Dの数字を抽出
    A_numbers = get_numbers_with_multiple_occurrences(df)  # 3回または4回出現した数字
    B_numbers = get_numbers_with_multiple_occurrences(df, 5)  # 5回以上出現した数字
    C_numbers = get_previous_numbers(df)  # 前回の当選番号
    D_numbers = get_neighbouring_numbers(C_numbers)  # 前回の当選番号の前後の数字
    E_numbers = get_other_numbers(A_numbers + B_numbers + C_numbers + D_numbers)  # その他の数字

    # 各範囲を定義（ミニロト用）
    ranges = [
        list(range(1, 10)),   # 第1数字（1〜9）
        list(range(10, 19)),  # 第2数字（10〜18）
        list(range(19, 22)),  # 第3数字（19〜21）
        list(range(22, 28)),  # 第4数字（22〜27）
        list(range(28, 32))   # 第5数字（28〜31）
    ]

    for _ in range(prediction_count):
        prediction = list(axis_numbers)  # 軸数字を追加
        
        # 残りの数字を基準に基づいて選ぶ
        remaining_numbers = list(available_numbers - set(prediction))
        
        # 各範囲に対応する数字を選ぶ
        selected_range_numbers = get_numbers_by_range(remaining_numbers, ranges)
        
        prediction.extend(selected_range_numbers)
        
        # 必要な数字数をランダムに補う
        while len(prediction) < 5:
            prediction.append(random.choice(remaining_numbers))
        
        prediction = [int(num) for num in prediction]  # 小数点を整数に変換
        prediction.sort()

        # 予測結果が5個かどうか確認
        if len(prediction) != 5:
            print(f"予測が5個でない: {prediction} (個数: {len(prediction)})")  # エラーチェック用
        
        predictions.append(prediction)
    
    return predictions

# **予測結果を表示する関数**
def display_predictions(predictions):
    predictions = [pred[:5] for pred in predictions]  # 5個の数字に切り取る
    prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字"])
    st.table(prediction_df)

# **予測セクション**
st.header("② セレクト予想")

# 軸数字（最大3個）と削除数字（最大20個）を選択
axis_numbers = st.multiselect("軸数字を選んでください (最大3個まで)", options=range(1, 32), max_selections=3)
remove_numbers = st.multiselect("削除数字を選んでください (最大20個まで)", options=range(1, 32), max_selections=20)

# ボタンを押して予想を生成
if st.button("予想を生成"):
    if axis_numbers or remove_numbers:  # 軸数字か削除数字が選択されていれば予想生成
        select_predictions = generate_miniloto_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(select_predictions)
    else:
        # どちらも選択されていない場合、完全にランダムな予想を生成
        random_predictions = generate_miniloto_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/miniloto_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(random_predictions)
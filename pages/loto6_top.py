import ssl
import certifi
import pandas as pd
import streamlit as st
import urllib.request
import random


# ① 最新の当選番号を表示
st.header("① 最新の当選番号")

def generate_loto6_table(latest_csv, prizes_csv, carryover_csv):
    try:
        df_latest = pd.read_csv(latest_csv)
        latest_result = df_latest.iloc[0]

        df_carryover = pd.read_csv(carryover_csv)
        carryover_result = df_carryover.iloc[0]

        df_prizes = pd.read_csv(prizes_csv)
        prizes_result = df_prizes.iloc[0]

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
            <tr>
                <th>1等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{prizes_result['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{prizes_result['当選金額']}</td>
            </tr>
            <tr>
                <th>2等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{df_prizes.iloc[1]['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{df_prizes.iloc[1]['当選金額']}</td>
            </tr>
            <tr>
                <th>3等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{df_prizes.iloc[2]['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{df_prizes.iloc[2]['当選金額']}</td>
            </tr>
            <tr>
                <th>4等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{df_prizes.iloc[3]['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{df_prizes.iloc[3]['当選金額']}</td>
            </tr>
            <tr>
                <th>5等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{df_prizes.iloc[4]['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{df_prizes.iloc[4]['当選金額']}</td>
            </tr>
            <tr>
                <th>キャリーオーバー</th>
                <td colspan="3" class="right-align" style="text-align: right;">{carryover_result['キャリーオーバー']}</td>
            </tr>
        </table>
        """
        return table_html
    except FileNotFoundError:
        return "CSVファイルが見つかりませんでした。パスを確認してください。"
    except Exception as e:
        return f"エラーが発生しました: {e}"

# 最新の当選番号を表示
table = generate_loto6_table(
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_latest.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_prizes.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_carryover.csv"
)
st.markdown(table, unsafe_allow_html=True)


import pandas as pd
import streamlit as st

# CSVファイルを読み込んで直近24回を抽出する関数
def get_recent_loto6_data(csv_path):
    df = pd.read_csv(csv_path)
    df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
    df = df.dropna(subset=["日付"])  # 日付が無効な行を削除
    df = df.sort_values(by="日付", ascending=False)  # 日付で降順に並べ替え
    df_recent = df.head(24)  # 上から24回分を取得
    return df_recent

# 直近24回の当選番号を表示
st.header("② 直近24回の当選番号")

def generate_recent_loto6_table(csv_path):
    df_recent = get_recent_loto6_data(csv_path)

    table_html = "<table border='1' style='width: 100%; border-collapse: collapse; text-align: right;'>"
    table_html += "<thead><tr><th>抽選日</th><th>第1数字</th><th>第2数字</th><th>第3数字</th><th>第4数字</th><th>第5数字</th><th>第6数字</th></tr></thead><tbody>"

    for _, row in df_recent.iterrows():
        table_html += f"<tr><td>{row['日付'].strftime('%Y-%m-%d')}</td><td>{row['第1数字']}</td><td>{row['第2数字']}</td><td>{row['第3数字']}</td><td>{row['第4数字']}</td><td>{row['第5数字']}</td><td>{row['第6数字']}</td></tr>"

    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)

recent_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"
generate_recent_loto6_table(recent_csv_path)

# ③ 直近24回 出現回数 ランキング
st.header("③ 直近24回 出現回数 ランキング")

def generate_ranking_table(csv_path):
    df_recent = get_recent_loto6_data(csv_path)
    numbers = df_recent[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].values.flatten()

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

generate_ranking_table(recent_csv_path)

# ④ 分析セクション
st.header("④ 分析セクション")

def analyze_number_patterns(csv_path):
    df_recent = get_recent_loto6_data(csv_path)

    # パターンを取得 (1-9は1、10-19は10...に分類)
    patterns = df_recent[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].apply(
        lambda x: '-'.join([str((int(num) - 1) // 10 * 10 + 1) if 1 <= int(num) <= 9 else str((int(num) // 10) * 10) for num in sorted(x)]), axis=1)

    # パターンごとの出現回数をカウント
    pattern_counts = patterns.value_counts().reset_index()
    pattern_counts.columns = ['パターン', '出現回数']

    st.write("出現したパターンとその回数:")
    st.write(pattern_counts)

analyze_number_patterns(recent_csv_path)

# ⑤ 各位の出現回数TOP5
st.header("各位の出現回数TOP5")

def get_top5_numbers(df):
    # 1の位、10の位、20の位、30の位のリスト作成
    number_groups = {'1': [], '10': [], '20': [], '30': []}

    # 直近24回分の数字を取得して各位に分類
    for i in range(1, 7):
        number_groups['1'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(1, 9)].values)
        number_groups['10'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(10, 19)].values)
        number_groups['20'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(20, 29)].values)
        number_groups['30'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(30, 43)].values)

    # 各位のTOP5を計算
    top5_1 = pd.Series(number_groups['1']).value_counts()
    top5_10 = pd.Series(number_groups['10']).value_counts()
    top5_20 = pd.Series(number_groups['20']).value_counts()
    top5_30 = pd.Series(number_groups['30']).value_counts()

    # 各位のTOP5を表示
    top5_df = pd.DataFrame({
        '1の位': top5_1.head(5).index.tolist(),
        '10の位': top5_10.head(5).index.tolist(),
        '20の位': top5_20.head(5).index.tolist(),
        '30の位': top5_30.head(5).index.tolist()
    })

    st.write(top5_df)

df_recent = get_recent_loto6_data(recent_csv_path)
get_top5_numbers(df_recent)


# **⑥ 各数字の出現回数TOP3**
st.header("各数字の出現回数TOP3")

def get_top3_numbers_by_position(df):
    # ロト6では第6数字までの対応
    results = {'順位': ['1位', '2位', '3位'], '第1数字': [], '第2数字': [], '第3数字': [], '第4数字': [], '第5数字': [], '第6数字': []}

    # 第1数字から第6数字までループ
    for i in range(1, 7):
        col_name = f'第{i}数字'

        # 出現回数をカウント
        number_counts = pd.Series(df[col_name]).value_counts()

        # 出現回数が1回より多い数字のみを抽出
        number_counts = number_counts[number_counts > 1]

        # 出現回数でソート
        sorted_counts = number_counts.sort_values(ascending=False)

        # 順位ごとの表示
        rank = 1
        prev_count = None
        same_rank_numbers = []

        # 出現回数に基づいて順位付け
        for number, count in sorted_counts.items():
            if prev_count == count:
                same_rank_numbers.append(number)
            else:
                if same_rank_numbers:
                    results[f'第{i}数字'].append(f"{', '.join(map(str, same_rank_numbers))} ({prev_count}回)")
                same_rank_numbers = [number]
                prev_count = count
                rank += 1

        # 最後の順位も追加
        if same_rank_numbers:
            results[f'第{i}数字'].append(f"{', '.join(map(str, same_rank_numbers))} ({prev_count}回)")

        # 空のセルは空欄にする
        while len(results[f'第{i}数字']) < 3:
            results[f'第{i}数字'].append("")

    # 各位の出現回数を合わせる（長さを同じにするための調整）
    max_length = max(len(v) for v in results.values())  # 最大長を取得
    for key in results:
        while len(results[key]) < max_length:
            results[key].append("")

    # データフレームに変換
    top3_df = pd.DataFrame(results)

    # インデックス（左側の列）を削除
    top3_df.index = [''] * len(top3_df)

    # テーブルを表示
    st.header("第1数字〜第6数字 各数字の出現回数TOP3")
    st.table(top3_df)

# データの読み込み
df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv")

# 出現回数TOP3を表示
get_top3_numbers_by_position(df)

# A数字とB数字の関数
def generate_AB_numbers(df):
    # A数字: 直近24回で出現回数3〜4回の数字を抽出
    number_groups = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].values.flatten()
    number_counts = pd.Series(number_groups).value_counts()
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

import ssl
import pandas as pd
import random
import streamlit as st

# SSL証明書の検証を無効にする
ssl._create_default_https_context = ssl._create_unverified_context

# **予測結果を表示する関数**
def display_predictions(predictions):
    # 各予測が6個の数字になることを確認
    predictions = [pred[:6] for pred in predictions]  # 6個の数字に切り取る
    prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"])
    st.table(prediction_df)

# **直近24回のデータから3回以上出現した数字を抽出する関数**
def get_numbers_with_multiple_occurrences(df, min_occurrences=3):
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].values.flatten()
    number_counts = pd.Series(numbers).value_counts()
    return number_counts[number_counts >= min_occurrences].index.tolist()

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
def generate_select_prediction(axis_numbers, remove_numbers, df, prediction_count=10):
    # 使用する数字のリスト
    available_numbers = set(range(1, 44)) - set(remove_numbers)  # 削除した数字を除外
    predictions = []

    # 各範囲を定義（ロト6用）
    ranges = [
        list(range(1, 17)),   # 第1数字（1〜16）
        list(range(2, 25)),   # 第2数字（2〜24）
        list(range(6, 33)),   # 第3数字（6〜32）
        list(range(12, 39)),  # 第4数字（12〜38）
        list(range(19, 43)),  # 第5数字（19〜42）
        list(range(27, 44))   # 第6数字（27〜43）
    ]
    
    for _ in range(prediction_count):
        prediction = list(axis_numbers)  # 軸数字を追加
        
        # 残りの数字を基準に基づいて選ぶ
        remaining_numbers = list(available_numbers - set(prediction))
        
        # 各範囲に対応する数字を選ぶ
        selected_range_numbers = get_numbers_by_range(remaining_numbers, ranges)
        
        prediction.extend(selected_range_numbers)
        
        # 必要な数字数をランダムに補う
        while len(prediction) < 6:
            prediction.append(random.choice(remaining_numbers))
        
        prediction.sort()

        # 予測結果が6個かどうか確認
        if len(prediction) != 6:
            print(f"予測が6個でない: {prediction} (個数: {len(prediction)})")  # エラーチェック用
        
        predictions.append(prediction)

    return predictions

# **予測セクション**
st.header("② セレクト予想")

# 軸数字（最大3個）と削除数字（最大20個）を選択
axis_numbers = st.multiselect("軸数字を選んでください (最大3個まで)", options=range(1, 44), max_selections=3)
remove_numbers = st.multiselect("削除数字を選んでください (最大20個まで)", options=range(1, 44), max_selections=20)

# ボタンを押して予想を生成
if st.button("予想を生成"):
    if axis_numbers or remove_numbers:  # 軸数字か削除数字が選択されていれば予想生成
        select_predictions = generate_select_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(select_predictions)
    else:
        # どちらも選択されていない場合、完全にランダムな予想を生成
        random_predictions = generate_select_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto6_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(random_predictions)
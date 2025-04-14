import ssl
import pandas as pd
import random
import streamlit as st

# SSL証明書の検証を無効にする
ssl._create_default_https_context = ssl._create_unverified_context

# CSVを読み込む
df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv")

# **ページのタイトル**
st.title("ロト7 AI予想サイト")

# **① 最新の当選番号**
st.header("①最新の当選番号")

# **最新の当選番号テーブルを生成**
def generate_loto7_table(latest_csv, prizes_csv, carryover_csv):
    try:
        # 最新の抽選結果を読み込む
        df_latest = pd.read_csv(latest_csv)
        latest_result = df_latest.iloc[0]  # 最新の結果を取得

        # キャリーオーバーを読み込む
        df_carryover = pd.read_csv(carryover_csv)
        carryover_result = df_carryover.iloc[0]  # 最新のキャリーオーバーを取得

        # 当選口数と金額を読み込む
        df_prizes = pd.read_csv(prizes_csv)
        prizes_result = df_prizes.iloc[0]  # 1等の結果を取得

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
                <th>6等</th>
                <td colspan="2" class="center-align" style="text-align: right;">{df_prizes.iloc[5]['口数'].replace('口', '')}口</td>
                <td class="right-align" style="text-align: right;">{df_prizes.iloc[5]['当選金額']}</td>
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

# **最新の当選番号**を表示
table = generate_loto7_table(
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_latest.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_prizes.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_carryover.csv"
)
st.markdown(table, unsafe_allow_html=True)

# **② 直近24回の当選番号**
st.header("② 直近24回の当選番号")

def generate_recent_loto7_table(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
        df = df.dropna(subset=["日付"])
        df_recent = df.tail(24).sort_values(by="日付", ascending=False)

        table_html = "<table border='1' style='width: 100%; border-collapse: collapse; text-align: right;'>"
        table_html += "<thead><tr><th>抽選日</th><th>第1数字</th><th>第2数字</th><th>第3数字</th><th>第4数字</th><th>第5数字</th><th>第6数字</th><th>第7数字</th></tr></thead><tbody>"

        for _, row in df_recent.iterrows():
            table_html += f"<tr><td>{row['日付'].strftime('%Y-%m-%d')}</td><td>{row['第1数字']}</td><td>{row['第2数字']}</td><td>{row['第3数字']}</td><td>{row['第4数字']}</td><td>{row['第5数字']}</td><td>{row['第6数字']}</td><td>{row['第7数字']}</td></tr>"

        table_html += "</tbody></table>"

        st.markdown(table_html, unsafe_allow_html=True)
    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

recent_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv"
generate_recent_loto7_table(recent_csv_path)

# **③ ランキング**
st.header("③ 直近24回 出現回数 ランキング")

def generate_ranking_table(csv_path):
    df = pd.read_csv(csv_path)
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', '第7数字']].values.flatten()

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

ranking_csv_path = "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv"
generate_ranking_table(ranking_csv_path)

# **④ 分析セクション**
st.header("④ 分析セクション")

# パターン分析の表示
def analyze_number_patterns(csv_path):
    df = pd.read_csv(csv_path)

    patterns = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', '第7数字']].apply(
        lambda x: '-'.join([str((int(num) - 1) // 10 * 10 + 1) if 1 <= int(num) <= 9 else str((int(num) // 10) * 10) for num in sorted(x)]), axis=1)

    pattern_counts = patterns.value_counts().reset_index()
    pattern_counts.columns = ['パターン', '出現回数']

    st.write("出現したパターンとその回数:1→1〜9,10→10〜19,20→20〜29,30→30〜37,")
    st.write(pattern_counts)

analyze_number_patterns("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv")

# **⑤ 各位の出現回数TOP5**
st.header("各位の出現回数TOP5")

def get_top5_numbers(df):
    number_groups = {'1': [], '10': [], '20': [], '30': []}

    for i in range(1, 8):  # ロト7は7つの数字がある
        number_groups['1'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(1, 9)].values)
        number_groups['10'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(10, 19)].values)
        number_groups['20'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(20, 29)].values)
        number_groups['30'].extend(df[f'第{i}数字'][df[f'第{i}数字'].between(30, 37)].values)

    top5_1 = pd.Series(number_groups['1']).value_counts()
    top5_10 = pd.Series(number_groups['10']).value_counts()
    top5_20 = pd.Series(number_groups['20']).value_counts()
    top5_30 = pd.Series(number_groups['30']).value_counts()

    top5_df = pd.DataFrame({
        '1の位': top5_1.head(5).index.tolist(),
        '10の位': top5_10.head(5).index.tolist(),
        '20の位': top5_20.head(5).index.tolist(),
        '30の位': top5_30.head(5).index.tolist()
    })

    st.write(top5_df)

get_top5_numbers(df)

# **⑥ 各数字の出現回数TOP3**
st.header("各数字の出現回数TOP3")

def get_top3_numbers_by_position(df):
    results = {'順位': ['1位', '2位', '3位'], '第1数字': [], '第2数字': [], '第3数字': [], '第4数字': [], '第5数字': [], '第6数字': [], '第7数字': []}

    for i in range(1, 8):
        col_name = f'第{i}数字'

        number_counts = pd.Series(df[col_name]).value_counts()
        number_counts = number_counts[number_counts > 1]
        sorted_counts = number_counts.sort_values(ascending=False)

        rank = 1
        prev_count = None
        same_rank_numbers = []

        for number, count in sorted_counts.items():
            if prev_count == count:
                same_rank_numbers.append(number)
            else:
                if same_rank_numbers:
                    results[f'第{i}数字'].append(f"{', '.join(map(str, same_rank_numbers))} ({prev_count}回)")
                same_rank_numbers = [number]
                prev_count = count
                rank += 1

        if same_rank_numbers:
            results[f'第{i}数字'].append(f"{', '.join(map(str, same_rank_numbers))} ({prev_count}回)")

        while len(results[f'第{i}数字']) < 3:
            results[f'第{i}数字'].append("")

    max_length = max(len(v) for v in results.values())
    for key in results:
        while len(results[key]) < max_length:
            results[key].append("")

    top3_df = pd.DataFrame(results)
    top3_df.index = [''] * len(top3_df)
    
    st.header("第1数字〜第7数字 各数字の出現回数TOP3")
    st.table(top3_df)

get_top3_numbers_by_position(df)

import ssl
import pandas as pd
import random
import streamlit as st

# SSL証明書の検証を無効にする
ssl._create_default_https_context = ssl._create_unverified_context

# **予測結果を表示する関数**
def display_predictions(predictions):
    # 各予測が7個の数字になることを確認
    predictions = [pred[:7] for pred in predictions]  # 7個の数字に切り取る
    prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字", "第7数字"])
    st.table(prediction_df)

# **直近24回のデータから3回以上出現した数字を抽出する関数**
def get_numbers_with_multiple_occurrences(df, min_occurrences=3):
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', '第7数字']].values.flatten()
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
    available_numbers = set(range(1, 38)) - set(remove_numbers)  # 削除した数字を除外
    predictions = []

    # 各範囲を定義
    ranges = [
        list(range(1, 14)),   # 第1数字（1〜13）
        list(range(2, 18)),   # 第2数字（2〜17）
        list(range(5, 23)),   # 第3数字（5〜22）
        list(range(8, 28)),   # 第4数字（8〜27）
        list(range(14, 34)),  # 第5数字（14〜33）
        list(range(20, 37)),  # 第6数字（20〜36）
        list(range(26, 38))   # 第7数字（26〜37）
    ]
    
    for _ in range(prediction_count):
        prediction = list(axis_numbers)  # 軸数字を追加

        # 残りの数字を基準に基づいて選ぶ
        remaining_numbers = list(available_numbers - set(prediction))
        
        # 各範囲に対応する数字を選ぶ
        selected_range_numbers = get_numbers_by_range(remaining_numbers, ranges)

        # 重複しないように追加
        for num in selected_range_numbers:
            if num not in prediction:
                prediction.append(num)

        # 必要な数字数をランダムに補う
        while len(prediction) < 7:
            random_num = random.choice(remaining_numbers)
            if random_num not in prediction:  # 同じ数字が選ばれないようにする
                prediction.append(random_num)

        prediction.sort()

        # 予測結果が7個かどうか確認
        if len(prediction) != 7:
            print(f"予測が7個でない: {prediction} (個数: {len(prediction)})")  # エラーチェック用
        
        predictions.append(prediction)

    # 重複した数字があるか確認
    for pred in predictions:
        if len(pred) != len(set(pred)):
            print(f"重複した数字がある予測: {pred}")
    
    return predictions

import pandas as pd
import streamlit as st

# ロト7のA数字とB数字の関数
def generate_AB_numbers_loto7(df):
    # A数字: 直近24回で出現回数3〜4回の数字を抽出
    # 第1数字から第7数字までを考慮する
    number_groups = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字', '第7数字']].values.flatten()
    number_counts = pd.Series(number_groups).value_counts()
    
    # A数字: 出現回数3〜4回
    A_numbers = number_counts[(number_counts >= 3) & (number_counts <= 4)].index.tolist()

    # B数字: 出現回数5回以上
    B_numbers = number_counts[number_counts >= 5].index.tolist()

    # A数字とB数字を横並びにして表示するためのDataFrameを作成
    AB_numbers_df = pd.DataFrame({
        'A数字（出現回数3〜4回）': [', '.join(map(str, A_numbers))],
        'B数字（出現回数5回以上）': [', '.join(map(str, B_numbers))]
    })

    # 横並びにして表示
    st.write("A数字とB数字:")
    st.table(AB_numbers_df)

# ロト7のCSVデータを読み込む
df_loto7 = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv")

# A数字とB数字のテーブルを表示
generate_AB_numbers_loto7(df_loto7)

# **予測セクション**
st.header("② セレクト予想")

# 軸数字（最大3個）と削除数字（最大20個）を選択
axis_numbers = st.multiselect("軸数字を選んでください (最大3個まで)", options=range(1, 38), max_selections=3)
remove_numbers = st.multiselect("削除数字を選んでください (最大20個まで)", options=range(1, 38), max_selections=20)

# ボタンを押して予想を生成
if st.button("予想を生成"):
    if axis_numbers or remove_numbers:  # 軸数字か削除数字が選択されていれば予想生成
        select_predictions = generate_select_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(select_predictions)
    else:
        # どちらも選択されていない場合、完全にランダムな予想を生成
        random_predictions = generate_select_prediction(
            axis_numbers, remove_numbers,
            pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv"),
            prediction_count=20  # 20パターンを生成
        )
        display_predictions(random_predictions)
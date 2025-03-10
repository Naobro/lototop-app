import pandas as pd
import random
import streamlit as st
from loto6_predictions import generate_loto6_prediction  # 予測アルゴリズムのインポート

# **ページのタイトル**
st.title("ロト6 AI予想サイト")

# **① 最新の当選番号**を表示
st.header("①最新の当選番号")

# **最新の当選番号テーブルを生成**
def generate_loto6_table(latest_csv, prizes_csv, carryover_csv):
    try:
        # 最新の抽選結果を読み込む
        df_latest = pd.read_csv(latest_csv)
        latest_result = df_latest.iloc[0]  # 最新の結果を取得

        # キャリーオーバーを読み込む
        df_carryover = pd.read_csv(carryover_csv)
        carryover_result = df_carryover.iloc[0]  # 最新のキャリーオーバーを取得

        # 当選口数と金額を読み込む
        df_prizes = pd.read_csv(prizes_csv)
        prizes_result = df_prizes.iloc[0]  # 最新の結果を取得

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
table = generate_loto6_table(
    "/Users/naokinishiyama/loto-prediction-app/data/loto6_latest.csv",
    "/Users/naokinishiyama/loto-prediction-app/data/loto6_prizes.csv",
    "/Users/naokinishiyama/loto-prediction-app/data/loto6_carryover.csv"
)
st.markdown(table, unsafe_allow_html=True)

# **② 直近24回の当選番号**を表示
st.header("② 直近24回の当選番号")

def generate_recent_loto6_table(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.fillna("未定義")
        df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
        df = df.dropna(subset=["日付"])
        df_recent = df.tail(24).sort_values(by="日付", ascending=False)

        table_html = "<table border='1' style='width: 100%; border-collapse: collapse; text-align: right;'>"
        table_html += "<thead><tr><th>抽選日</th><th>第1数字</th><th>第2数字</th><th>第3数字</th><th>第4数字</th><th>第5数字</th><th>第6数字</th></tr></thead><tbody>"

        for _, row in df_recent.iterrows():
            table_html += f"<tr><td>{row['日付'].strftime('%Y-%m-%d')}</td><td>{row['第1数字']}</td><td>{row['第2数字']}</td><td>{row['第3数字']}</td><td>{row['第4数字']}</td><td>{row['第5数字']}</td><td>{row['第6数字']}</td></tr>"

        table_html += "</tbody></table>"

        st.markdown(table_html, unsafe_allow_html=True)
    except Exception as e:
        st.write(f"エラーが発生しました: {e}")
        st.write(f"エラー詳細: {e.__class__}")

recent_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv"
generate_recent_loto6_table(recent_csv_path)

# **③ ランキング**を表示
st.header("③ 直近24回　出現回数　ランキング")
def generate_ranking_table(csv_path):
    df = pd.read_csv(csv_path)
    numbers = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].values.flatten()

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

ranking_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv"
generate_ranking_table(ranking_csv_path)

# **④ 分析**セクション
st.header("④ 分析セクション")

# パターン分析の表示
def analyze_number_patterns(csv_path):
    df = pd.read_csv(csv_path)

    # パターンを取得 (1-9は1、10-19は10...に分類)
    patterns = df[['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']].apply(
        lambda x: '-'.join([str((int(num) - 1) // 10 * 10 + 1) if 1 <= int(num) <= 9 else str((int(num) // 10) * 10) for num in sorted(x)]), axis=1)

    # パターンごとの出現回数をカウント
    pattern_counts = patterns.value_counts().reset_index()
    pattern_counts.columns = ['パターン', '出現回数']

    st.write("出現したパターンとその回数:1→1〜9,10→10〜19,20→20〜29,30→30〜39,40→40〜43,")
    st.write(pattern_counts)

# CSVファイルのパスを指定して関数を呼び出し
analyze_number_patterns("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv")

# **⑤ 各位の出現回数TOP5**
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

    # 各位のTOP5を表示 (インデックスを1位、2位に変更)
    top5_df = pd.DataFrame({
        '1の位': top5_1.head(5).index.tolist(),
        '10の位': top5_10.head(5).index.tolist(),
        '20の位': top5_20.head(5).index.tolist(),
        '30の位': top5_30.head(5).index.tolist()
    })

    # 出現回数が同じ場合は、全て表示されるように変更
    st.write(top5_df)

# **⑥ 各数字の出現回数TOP3**
def get_top3_numbers_by_position(df):
    results = {
        '順位': ['1位', '2位', '3位'],
        '第1数字': [],
        '第2数字': [],
        '第3数字': [],
        '第4数字': [],
        '第5数字': [],
        '第6数字': []
    }

    # 各位（第1数字から第6数字まで）のループ
    for i in range(1, 7):
        col_name = f'第{i}数字'
        
        # 出現回数をカウント
        number_counts = pd.Series(df[col_name]).value_counts()

        # 出現回数が2回以上の数字のみを抽出
        number_counts = number_counts[number_counts > 1]

        # 出現回数でソート
        sorted_counts = number_counts.sort_values(ascending=False)

        # 順位ごとの表示
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

        # 最後の順位も追加
        if same_rank_numbers:
            results[f'第{i}数字'].append(f"{', '.join(map(str, same_rank_numbers))} ({prev_count}回)")

        # 空のセルは空欄にする
        while len(results[f'第{i}数字']) < 3:
            results[f'第{i}数字'].append("")

    # 結果をデータフレームに変換
    top3_df = pd.DataFrame(results)

    # インデックス（左側の列）を削除
    top3_df.index = [''] * len(top3_df)
    
    # テーブルを表示
    st.header("第1数字〜第6数字　各数字の出現回数TOP3")
    st.table(top3_df)

# データの読み込み
df = pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv")

# 出現回数TOP5を表示
get_top5_numbers(df)

# 出現回数TOP3を表示
get_top3_numbers_by_position(df)
import pandas as pd
import streamlit as st

# CSVファイルを読み込む
df = pd.read_csv("/Users/naokinishiyama/loto-prediction-app/data/loto6_50.csv")

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

# **⑩ 予測結果**
st.header("⑤ 予想セクション")
st.write("予想アルゴリズム　A数字、B数字を中心にAI予想:")

# **⑤ 予想数の選択**
prediction_count = st.selectbox("予想数", [10, 30, 100, 300], index=0)

# 予測アルゴリズムを呼び出す
predictions = generate_loto6_prediction(df, prediction_count)

# 予測結果を表示
prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"])

# テーブルとして表示
st.table(prediction_df)

import pandas as pd
import streamlit as st
from miniloto_predictions import generate_miniloto_prediction  # 予測アルゴリズムのインポート

# **ページのタイトル**
st.title("ミニロト AI予想サイト")

# CSVファイルのパス
csv_path = "/Users/naokinishiyama/loto-prediction-app/data/miniloto_50.csv"
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
    "/Users/naokinishiyama/loto-prediction-app/data/miniloto_latest.csv",
    "/Users/naokinishiyama/loto-prediction-app/data/miniloto_prizes.csv"
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
recent_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/miniloto_50.csv"
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
ranking_csv_path = "/Users/naokinishiyama/loto-prediction-app/data/miniloto_50.csv"
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
analyze_number_patterns("/Users/naokinishiyama/loto-prediction-app/data/miniloto_50.csv")

# **⑤ 予測結果**
st.header("⑤ 予想セクション")
st.write("予想アルゴリズム")

# **⑤ 予想数の選択**
prediction_count = st.selectbox("予想数", [10, 30, 100, 300], index=0)

# 予測アルゴリズムを呼び出す
predictions = generate_miniloto_prediction(df, prediction_count)

# 予測結果を表示
prediction_df = pd.DataFrame(predictions, columns=["第1数字", "第2数字", "第3数字", "第4数字", "第5数字"])

# テーブルとして表示
st.table(prediction_df)
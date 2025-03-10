import ssl
import pandas as pd
import random
import streamlit as st
from loto7_predictions import generate_loto7_prediction  # ロト7の予測アルゴリズムをインポート

# SSL証明書の検証を無効にする
ssl._create_default_https_context = ssl._create_unverified_context

# CSVファイルを読み込む
df = pd.read_csv("https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_50.csv")

# **ページのタイトル**
st.title("ロト7 AI予想サイト")

# **予測結果の表示（例: 10件の予測を生成）**
predictions = generate_loto7_prediction(df, 10)  # dfを引数として渡す

# 予測結果の表示
for i, prediction in enumerate(predictions, 1):
    st.write(f"予測{i}: {prediction}")

# **① 最新の当選番号**を表示
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
table = generate_loto7_table(
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_latest.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_prizes.csv",
    "https://raw.githubusercontent.com/Naobro/lototop-app/main/data/loto7_carryover.csv"
)
st.markdown(table, unsafe_allow_html=True)

# **② 直近24回の当選番号**を表示
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

recent_csv_path = "https://raw.githubusercontent.com/Naobro/lot

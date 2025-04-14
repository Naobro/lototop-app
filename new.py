import streamlit as st
import pandas as pd

# タイトル
st.title('宝くじ当選番号スクレイピングページ')

# 手動で当選番号を入力するためのテキストエリア
st.header('当選番号の入力（手動で貼り付けてください）')
input_text = st.text_area(
    "当選番号データを貼り付けてください",
    """
    第1981回　ロト6 当選番号　2025年3月13日 抽選
    ロト６
    当選番号    05    10    15    17    29    41
    ボーナス
    数字    30

    等　級    口　数    賞 金 金 額    ロト６の当選条件
    1等    該当なし    該当なし    本数字6個と全て一致
    2等    9口    6,953,100円    本数字5個とボーナス数字と一致
    3等    171口    395,200円    本数字5個と一致
    4等    10,254口    6,900円    本数字4個と一致
    5等    160,545口    1,000円    本数字3個と一致
    キャリーオーバー    208,586,608円    次回持ち越し分

    第６１７回　ロト7 当選番号速報　2025年3月14日 抽選
    ロト7本数字
    02    06    10    12    25    28    35
    ボーナス数字
    27    31

    等　級    口　数    金　　額    ロト7当選条件
    1等    1口    1,200,000,000円    本数字7個と全て一致
    2等    15口    4,639,700円    本数字6個とＢ数字2個のうち1個と一致
    3等    186口    431,000円    本数字6個と一致
    4等    7,781口    6,200円    本数字5個と一致
    5等    121,794口    1,300円    本数字4個と一致
    6等    194,794口    1,000円    本数字3個と一致とＢ数字2個、または1個一致
    キャリーオーバー    298,721,810円    次回持ち越し分

    第1325回　ミニロト 当選番号速報　抽選日 2025年3月11日
    ミニロト
    当選数字    10    15    22    23    25
    ボーナス
    数字    13

    等　級    口　数    賞 金 金 額    ミニロトの当選条件
    1等    13口    12,476,500円    本数字5個と全て一致
    2等    64口    182,000円    本数字4個とボーナス数字と一致
    3等    1,494口    13,500円    本数字4個と一致
    4等    46,286口    1,100円    本数字3個と一致
    """
)

# 入力されたテキストを処理してデータを抽出する
def process_input_text(input_text):
    # 正規表現を使って必要なデータを抽出（ロト6、ロト7、ミニロト）
    import re

    # ロト6データ抽出
    lotto6_regex = re.compile(r'第(\d+)回\s+ロト6\s+当選番号\s+(.+?)\s+ボーナス\s+数字\s+(\d+)\s+等　級\s+口　数\s+賞 金 金 額\s+ロト６の当選条件\s+(\d+)等\s+(\d+)口\s+([\d,]+)円')
    lotto6_match = lotto6_regex.search(input_text)
    if lotto6_match:
        lotto6_data = {
            "回号": lotto6_match.group(1),
            "当選番号": lotto6_match.group(2),
            "ボーナス数字": lotto6_match.group(3),
            "2等口数": lotto6_match.group(4),
            "2等賞金額": lotto6_match.group(5),
            "キャリーオーバー": lotto6_match.group(6)
        }
    else:
        lotto6_data = {}

    # ロト7データ抽出
    lotto7_regex = re.compile(r'第(\d+)回\s+ロト7\s+当選番号速報\s+(.+?)\s+ボーナス数字\s+(.+?)\s+等　級\s+口　数\s+金\s+額\s+ロト7当選条件\s+(\d+)等\s+(\d+)口\s+([\d,]+)円')
    lotto7_match = lotto7_regex.search(input_text)
    if lotto7_match:
        lotto7_data = {
            "回号": lotto7_match.group(1),
            "当選番号": lotto7_match.group(2),
            "ボーナス数字": lotto7_match.group(3),
            "2等口数": lotto7_match.group(4),
            "2等賞金額": lotto7_match.group(5),
            "キャリーオーバー": lotto7_match.group(6)
        }
    else:
        lotto7_data = {}

    # ミニロトデータ抽出
    minilotto_regex = re.compile(r'第(\d+)回\s+ミニロト\s+当選番号速報\s+抽選日\s+(.+?)\s+当選数字\s+(.+?)\s+ボーナス\s+数字\s+(\d+)\s+等　級\s+口　数\s+賞 金 金 額\s+ミニロトの当選条件\s+(\d+)等\s+(\d+)口\s+([\d,]+)円')
    minilotto_match = minilotto_regex.search(input_text)
    if minilotto_match:
        minilotto_data = {
            "回号": minilotto_match.group(1),
            "抽選日": minilotto_match.group(2),
            "当選番号": minilotto_match.group(3),
            "ボーナス数字": minilotto_match.group(4),
            "1等口数": minilotto_match.group(5),
            "1等賞金額": minilotto_match.group(6)
        }
    else:
        minilotto_data = {}

    return {
        "ロト6": lotto6_data,
        "ロト7": lotto7_data,
        "ミニロト": minilotto_data
    }

# 入力されたテキストを処理
lottery_data = process_input_text(input_text)

# 表示するデータ
st.subheader("ロト6")
st.write(lottery_data.get("ロト6", {}))

st.subheader("ロト7")
st.write(lottery_data.get("ロト7", {}))

st.subheader("ミニロト")
st.write(lottery_data.get("ミニロト", {}))

# CSVとして出力
if st.button('CSVとして出力'):
    df_lotto6 = pd.DataFrame([lottery_data.get("ロト6", {})])
    df_lotto7 = pd.DataFrame([lottery_data.get("ロト7", {})])
    df_minilotto = pd.DataFrame([lottery_data.get("ミニロト", {})])

    # CSVダウンロード
    st.download_button("ロト6 CSV", df_lotto6.to_csv(index=False), "lotto6.csv", "text/csv")
    st.download_button("ロト7 CSV", df_lotto7.to_csv(index=False), "lotto7.csv", "text/csv")
    st.download_button("ミニロト CSV", df_minilotto.to_csv(index=False), "minilotto.csv", "text/csv")
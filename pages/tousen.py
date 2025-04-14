import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

st.set_page_config(page_title="みずほ銀行 抽選結果CSV化 + GitHub自動更新", layout="wide")
st.title("みずほ銀行の抽選結果をコピペしてCSVに変換・GitHub保存")

# 選択時に入力欄をリセットする
if "last_selection" not in st.session_state:
    st.session_state.last_selection = ""
if "text_input" not in st.session_state:
    st.session_state.text_input = ""

lottery_type = st.selectbox("宝くじの種類を選んでください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])
if lottery_type != st.session_state.last_selection:
    st.session_state.text_input = ""
    st.session_state.last_selection = lottery_type

text_input = st.text_area("みずほ銀行の抽選結果をそのままコピペしてください", value=st.session_state.text_input, height=300)
st.session_state.text_input = text_input

# 日付をYYYY-MM-DD形式に変換する関数
def convert_date(date_str):
    for fmt in ("%Y年%m月%d日", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return date_str

# パース関数（安全性強化）
def safe_search(pattern, text, group=1):
    match = re.search(pattern, text)
    return match.group(group) if match else ""

def parse_lottery_text(text, kind):
    text = text.replace("\u3000", " ").replace("抽選日", "").replace("(", "").replace(")", "")
    lines = text.splitlines()
    result = {}

    if kind in ["ロト6", "ロト7", "ミニロト"]:
        result['回号'] = safe_search(r'第(\d+)回', text)
        raw_date = safe_search(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}/\d{1,2}/\d{1,2})', text)
        result['抽せん日'] = convert_date(raw_date)

        numbers = re.findall(r'\d{1,2}', text)
        if kind == "ロト6":
            result['本数字'] = ' '.join(numbers[:6])
            result['ボーナス数字'] = numbers[6] if len(numbers) > 6 else ""
            return pd.DataFrame([result])

        elif kind == "ロト7":
            result['本数字'] = ' '.join(numbers[:7])
            result['ボーナス数字'] = ' '.join(numbers[7:9]) if len(numbers) > 8 else ""
            return pd.DataFrame([result])

        elif kind == "ミニロト":
            result['本数字'] = ' '.join(numbers[:5])
            result['ボーナス数字'] = numbers[5] if len(numbers) > 5 else ""
            return pd.DataFrame([result])

    elif kind in ["ナンバーズ3", "ナンバーズ4"]:
        result['回号'] = safe_search(r'第(\d+)回', text)
        raw_date = safe_search(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}/\d{1,2}/\d{1,2})', text)
        result['抽せん日'] = convert_date(raw_date)
        number_match = re.search(r'(?:抽せん数字|当せん番号)[\s\n]*([0-9]{3,4})', text)
        result['当選番号'] = number_match.group(1) if number_match else ""
        return pd.DataFrame([result])

    return pd.DataFrame()

# 保存関数（上書きではなく追加）
def save_to_csv(df, kind):
    file_map = {
        "ロト6": "data/loto6_50.csv",
        "ロト7": "data/loto7_50.csv",
        "ミニロト": "data/miniloto_50.csv",
        "ナンバーズ3": "data/numbers3_24.csv",
        "ナンバーズ4": "data/numbers4_24.csv",
    }
    file = file_map[kind]

    # 数字を列に展開
    if kind in ["ロト6", "ロト7", "ミニロト"]:
        nums = df["本数字"].iloc[0].split(" ")
        for i, num in enumerate(nums):
            df[f"第{i+1}数字"] = int(num)
        df["ボーナス数字"] = df["ボーナス数字"].astype(str)

    elif kind in ["ナンバーズ3", "ナンバーズ4"]:
        digits = list(df["当選番号"].iloc[0])
        for i, d in enumerate(digits):
            df[f"第{i+1}数字"] = int(d)

    df["日付"] = df.get("抽せん日", df.get("抽選日", ""))
    df = df.drop(columns=[c for c in ["本数字", "当選番号", "抽せん日", "抽選日"] if c in df.columns])

    # 既存CSVに追記
    if os.path.exists(file):
        old = pd.read_csv(file)
        new = pd.concat([df, old]).drop_duplicates(subset=["回号"]).head(200)
    else:
        new = df

    new.to_csv(file, index=False)

# 実行ボタン
if st.button("解析して保存"):
    if text_input:
        try:
            df_parsed = parse_lottery_text(text_input, lottery_type)
            save_to_csv(df_parsed, lottery_type)
            st.success("✅ データを解析して保存しました")
            st.dataframe(df_parsed)
        except Exception as e:
            st.error(f"⚠️ エラーが発生しました: {e}")
    else:
        st.warning("テキストを入力してください。")

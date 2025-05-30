import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv
import subprocess

# GitHubトークン読み込み
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# プロジェクトルートからのdata保存用絶対パス
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="抽選結果CSV化＋GitHub保存", layout="wide")
st.title("抽選結果をコピペしてCSVに保存・GitHubへ反映")

if "text_input" not in st.session_state:
    st.session_state.text_input = ""

lottery_type = st.selectbox("宝くじの種類を選んでください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])
text_input = st.text_area("みずほ銀行の抽選結果をコピペしてください", value=st.session_state.text_input, height=300)
st.session_state.text_input = text_input

def convert_date(text):
    match = re.search(r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日?', text)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return ""

def extract_round(text):
    match = re.search(r'第\s*(\d+)\s*回', text)
    return int(match.group(1)) if match else None

def extract_numbers_from_loto(text, count):
    main_match = re.search(r'本数字[\s\n]*([0-9\s]+)', text)
    bonus_match = re.search(r'ボーナス数字[\s\n]*(\d+(?:\s+\d+)*)', text)
    if main_match:
        main_numbers = re.findall(r'\d{1,2}', main_match.group(1))
        bonus_numbers = re.findall(r'\d{1,2}', bonus_match.group(1)) if bonus_match else []
        if len(main_numbers) >= count:
            return main_numbers[:count], bonus_numbers
    return [], []

def extract_numbers_n(text, count):
    match = re.search(r'(?:抽せん数字|当せん番号)[\s\n]*([0-9]{%d})' % count, text)
    return list(match.group(1)) if match else []

def extract_prizes(text):
    prizes = {}
    for line in text.splitlines():
        if re.search(r'(1等|2等|3等|4等|5等|6等)', line):
            parts = re.findall(r'\d[\d,]*', line)
            if "該当なし" in line or len(parts) < 2:
                prizes[re.search(r'(1等|2等|3等|4等|5等|6等)', line).group(1)] = ["0", "該当なし"]
            else:
                prizes[re.search(r'(1等|2等|3等|4等|5等|6等)', line).group(1)] = [parts[0].replace(",", ""), parts[1].replace(",", "")]
    return prizes

def extract_carryover(text):
    match = re.search(r'キャリーオーバー[\s\n]*([0-9,]+)円', text)
    return match.group(1).replace(",", "") if match else "0"

def save_all_csvs(lottery_type, numbers, bonus, date, round_number, prizes, carryover):
    base_name = lottery_type.lower().replace("ー", "")
    digits = len(numbers)

    row = {f"第{i+1}数字": int(numbers[i]) for i in range(digits)}
    row["ボーナス数字"] = ' '.join(bonus)
    row["日付"] = date
    row["回号"] = round_number
    df_row = pd.DataFrame([row])

    # ファイルパスをすべて絶対パスで定義
    file_50 = os.path.join(DATA_DIR, f"{base_name}_50.csv")
    file_latest = os.path.join(DATA_DIR, f"{base_name}_latest.csv")
    file_prizes = os.path.join(DATA_DIR, f"{base_name}_prizes.csv")
    file_carry = os.path.join(DATA_DIR, f"{base_name}_carryover.csv")

    # 保存：_50.csv（追記）
    if os.path.exists(file_50):
        df_old = pd.read_csv(file_50)
        if round_number in df_old["回号"].astype(str).values:
            st.warning(f"⚠️ 第{round_number}回のデータはすでに存在します。")
            return []
        df_all = pd.concat([df_old, df_row], ignore_index=True)
    else:
        df_all = df_row
    df_all.to_csv(file_50, index=False)

    # 保存：_latest.csv（上書き）
    df_row.to_csv(file_latest, index=False)

    # 保存：_prizes.csv（上書き）
    prize_row = {"回号": round_number}
    for grade, val in prizes.items():
        prize_row[f"{grade}_口数"] = val[0]
        prize_row[f"{grade}_当せん金額"] = val[1]
    pd.DataFrame([prize_row]).to_csv(file_prizes, index=False)

    # 保存：_carryover.csv（上書き）
    pd.DataFrame([{"回号": round_number, "キャリーオーバー": carryover}]).to_csv(file_carry, index=False)

    st.success(f"✅ {lottery_type} 第{round_number}回（{date}）をすべてのCSVに保存しました")
    st.dataframe(df_row)
    return [file_50, file_latest, file_prizes, file_carry]

def push_to_github(file_paths):
    try:
        for file_path in file_paths:
            subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", "Update lottery CSV files"], check=True)
        subprocess.run(["git", "push", f"https://{GITHUB_TOKEN}@github.com/Naobro/lototop-app.git"], check=True)
        st.success("✅ GitHubにpushしました")
    except Exception as e:
        st.error(f"GitHub pushに失敗: {e}")

# 実行ボタン
if st.button("解析して保存＋GitHub反映"):
    if text_input.strip():
        date = convert_date(text_input)
        round_number = extract_round(text_input)
        numbers, bonus = [], []
        prizes = extract_prizes(text_input)
        carry = extract_carryover(text_input)

        if lottery_type in ["ロト6", "ロト7", "ミニロト"]:
            digits = {"ロト6": 6, "ロト7": 7, "ミニロト": 5}[lottery_type]
            numbers, bonus = extract_numbers_from_loto(text_input, digits)
        elif lottery_type in ["ナンバーズ3", "ナンバーズ4"]:
            digits = {"ナンバーズ3": 3, "ナンバーズ4": 4}[lottery_type]
            numbers = extract_numbers_n(text_input, digits)
            bonus = []
            prizes = {}
            carry = "0"

        if date and round_number and len(numbers) == digits:
            files = save_all_csvs(lottery_type, numbers, bonus, date, round_number, prizes, carry)
            if files:
                push_to_github(files)
        else:
            st.error("❌ 日付、回号、または数字が正しく抽出できませんでした。")
    else:
        st.warning("テキストを入力してください。")
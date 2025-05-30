
import os
import re
import pandas as pd
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import subprocess

# ==================== 初期設定 ====================
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="宝くじCSV化＋GitHub保存", layout="wide")
st.title("抽選結果をコピペしてCSVに保存・GitHubへ反映")

lottery_type = st.selectbox("宝くじの種類を選んでください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])
text_input = st.text_area("みずほ銀行の抽選結果をコピペしてください", height=300)

def extract_round(text):
    match = re.search(r'第\s*(\d+)', text)
    return int(match.group(1)) if match else None

def extract_date(text):
    match = re.search(r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})', text)
    if match:
        y, m, d = map(int, match.groups())
        return f"{y:04d}-{m:02d}-{d:02d}"
    return ""

def extract_numbers(text, count):
    return re.findall(r'\b(\d{1,2})\b', text)[:count]

def extract_bonus(text):
    return re.findall(r'\(\s*(\d{1,2})\s*\)', text)

def extract_prize(grade):
    match = re.search(fr"{grade}[\s\S]*?(\d+)口[\s\S]*?(\d[\d,]*)円", text_input)
    return match.groups() if match else ("0", "0")

def extract_carry(text):
    match = re.search(r'キャリーオーバー\s*([\d,]+)円', text)
    return match.group(1).replace(",", "") if match else "0"

def save_record(file_path, record):
    df = pd.DataFrame([record])
    ordered_cols = [col for col in record.keys()]
    df = df[ordered_cols]
    if os.path.exists(file_path):
        old = pd.read_csv(file_path)
        if str(record["回号"]) in old["回号"].astype(str).values:
            st.warning("⚠️ 同じ回号のデータが存在します")
            return False
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(file_path, index=False)
    return True

def push_to_github():
    try:
        repo_path = os.path.join(ROOT_DIR, "..")
        subprocess.run(["git", "-C", repo_path, "add", "data/*.csv"], check=True)
        diff_result = subprocess.run(["git", "-C", repo_path, "diff", "--cached", "--quiet"])
        if diff_result.returncode == 0:
            st.info("🟡 変更内容がないためGitHubへのPushはスキップされました")
            return
        subprocess.run(["git", "-C", repo_path, "commit", "-m", "update lottery data"], check=True)
        push_url = f"https://{GITHUB_TOKEN}@github.com/Naobro/lototop-app.git"
        subprocess.run(["git", "-C", repo_path, "push", push_url], check=True)
        st.success("✅ GitHubへのPushが完了しました！")
        st.markdown("[🌐 GitHubで確認する](https://github.com/Naobro/lototop-app/tree/main/data)", unsafe_allow_html=True)
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Gitコマンド失敗: {e}")
    except Exception as e:
        st.error(f"❌ GitHub push失敗: {e}")

if st.button("CSV保存＋GitHub反映"):
    if not text_input:
        st.warning("⚠️ 抽選結果を貼り付けてください")
    elif lottery_type == "ロト6":
        round_num = extract_round(text_input)
        date = extract_date(text_input)
        numbers = extract_numbers(text_input, 6)
        bonus = extract_bonus(text_input)
        record = {
            "回号": round_num,
            "抽せん日": date,
            "第1数字": numbers[0],
            "第2数字": numbers[1],
            "第3数字": numbers[2],
            "第4数字": numbers[3],
            "第5数字": numbers[4],
            "第6数字": numbers[5],
            "ボーナス数字": bonus[0] if bonus else "0",
            "1等口数": extract_prize("1等")[0],
            "2等口数": extract_prize("2等")[0],
            "3等口数": extract_prize("3等")[0],
            "1等賞金": extract_prize("1等")[1],
            "2等賞金": extract_prize("2等")[1],
            "3等賞金": extract_prize("3等")[1],
            "キャリーオーバー": extract_carry(text_input)
        }
        file_path = os.path.join(DATA_DIR, "loto6.csv")
        if save_record(file_path, record):
            push_to_github()

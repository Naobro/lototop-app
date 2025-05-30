import os
import re
import pandas as pd
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

def extract_prize_info(text, grade):
    match = re.search(fr"{grade}[\s\S]*?(\d+)口[\s\S]*?(\d[\d,]*)円", text)
    return match.groups() if match else ("0", "0")

def extract_carry(text):
    match = re.search(r'キャリーオーバー\s*([\d,]+)円', text)
    return match.group(1).replace(",", "") if match else "0"

def save_record(file_path, record, columns):
    df = pd.DataFrame([record])
    df = df.reindex(columns=columns)
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
        subprocess.run(["git", "-C", repo_path, "commit", "--allow-empty", "-m", "update lottery data"], check=True)
        subprocess.run(["git", "-C", repo_path, "push", f"https://{GITHUB_TOKEN}@github.com/Naobro/lototop-app.git"], check=True)
        st.success("✅ GitHubにPush完了（差分なしでもコミット！）")
    except Exception as e:
        st.error(f"GitHub push失敗: {e}")

# ==================== 実行処理 ====================
if st.button("CSV保存＋GitHub反映"):
    if not text_input:
        st.warning("⚠️ 抽選結果を貼り付けてください")
    else:
        round_no = extract_round(text_input)
        date = extract_date(text_input)
        file_path = ""
        columns = []
        record = {}

        if lottery_type == "ロト6":
            nums = extract_numbers(text_input, 6)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(6)},
                "ボーナス数字": bonus[0] if bonus else "0",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等", "5等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等", "5等"]},
                "キャリーオーバー": extract_carry(text_input)
            }
            file_path = os.path.join(DATA_DIR, "loto6_50.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字",
                       "ボーナス数字", "1等口数", "2等口数", "3等口数", "4等口数", "5等口数",
                       "1等賞金", "2等賞金", "3等賞金", "4等賞金", "5等賞金", "キャリーオーバー"]

        elif lottery_type == "ロト7":
            nums = extract_numbers(text_input, 7)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(7)},
                "BONUS数字1": bonus[0] if len(bonus) > 0 else "0",
                "BONUS数字2": bonus[1] if len(bonus) > 1 else "0",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等", "5等", "6等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等", "5等", "6等"]},
                "キャリーオーバー": extract_carry(text_input)
            }
            file_path = os.path.join(DATA_DIR, "loto7_50.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字", "第7数字",
                       "BONUS数字1", "BONUS数字2", "1等口数", "2等口数", "3等口数", "4等口数", "5等口数", "6等口数",
                       "1等賞金", "2等賞金", "3等賞金", "4等賞金", "5等賞金", "6等賞金", "キャリーオーバー"]

        elif lottery_type == "ミニロト":
            nums = extract_numbers(text_input, 5)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(5)},
                "ボーナス数字": bonus[0] if bonus else "0",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等"]}
            }
            file_path = os.path.join(DATA_DIR, "miniloto_50.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "ボーナス数字",
                       "1等口数", "2等口数", "3等口数", "4等口数",
                       "1等賞金", "2等賞金", "3等賞金", "4等賞金"]

        elif lottery_type == "ナンバーズ3":
            nums = extract_numbers(text_input, 3)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(3)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セットストレート", "セットボックス", "ミニ"]},
                **{f"{g}当選金額": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セットストレート", "セットボックス", "ミニ"]}
            }
            file_path = os.path.join(DATA_DIR, "numbers3_24.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字",
                       "ストレート口数", "ボックス口数", "セットストレート口数", "セットボックス口数", "ミニ口数",
                       "ストレート当選金額", "ボックス当選金額", "セットストレート当選金額", "セットボックス当選金額", "ミニ当選金額"]

        elif lottery_type == "ナンバーズ4":
            nums = extract_numbers(text_input, 4)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(4)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セットストレート", "セットボックス"]},
                **{f"{g}当選金額": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セットストレート", "セットボックス"]}
            }
            file_path = os.path.join(DATA_DIR, "numbers4_24.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字",
                       "ストレート口数", "ボックス口数", "セットストレート口数", "セットボックス口数",
                       "ストレート当選金額", "ボックス当選金額", "セットストレート当選金額", "セットボックス当選金額"]

        if file_path and save_record(file_path, record, columns):
            st.success(f"✅ {lottery_type} 第{round_no}回 保存完了")
            push_to_github()
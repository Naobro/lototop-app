import os
print(os.getcwd())  # カレントディレクトリを確認
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

# ==================== 抽出関数 ====================
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
    if re.search(fr"{grade}[\s\S]*?該当なし", text):
        return ("0", "0")
    match = re.search(fr'{grade}[\s\S]*?(\d[\d,]*)口[\s\S]*?(\d[\d,]*)円', text)
    if match:
        return (match.group(1).replace(",", ""), match.group(2).replace(",", ""))
    return ("0", "0")

def extract_carry(text):
    match = re.search(r'キャリーオーバー\s*([\d,]+)円', text)
    return match.group(1).replace(",", "") if match else "0"

def clean_record_values(record):
    return {k: ("0" if str(v).strip() in ["", "該当なし"] else str(v)) for k, v in record.items()}

# ==================== CSV保存関数 ====================
def save_record(file_path, record):
    df = pd.DataFrame([record])

    if "ボーナス数字" in df.columns:
        ordered_cols = [
            "回号", "抽せん日",
            "第1数字", "第2数字", "第3数字", "第4数字", "第5数字",
            "第6数字" if "第6数字" in df.columns else None,
            "ボーナス数字",
            "1等口数", "2等口数", "3等口数", "4等口数", "5等口数",
            "1等賞金", "2等賞金", "3等賞金", "4等賞金", "5等賞金",
            "キャリーオーバー" if "キャリーオーバー" in df.columns else None
        ]
    elif "BONUS数字1" in df.columns:
        ordered_cols = [
            "回号", "抽せん日",
            "第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字", "第7数字",
            "BONUS数字1", "BONUS数字2",
            "1等口数", "2等口数", "3等口数", "4等口数", "5等口数", "6等口数",
            "1等賞金", "2等賞金", "3等賞金", "4等賞金", "5等賞金", "6等賞金",
            "キャリーオーバー"
        ]
    else:
        ordered_cols = ["回号", "抽せん日"] + [col for col in df.columns if col not in ["回号", "抽せん日"]]

    ordered_cols = [col for col in ordered_cols if col in df.columns]
    df = df[ordered_cols]

    if os.path.exists(file_path):
        old = pd.read_csv(file_path)
        if str(record["回号"]) in old["回号"].astype(str).values:
            st.warning("⚠️ 同じ回号のデータが存在します")
            return False
        df = pd.concat([old, df], ignore_index=True)

    df.to_csv(file_path, index=False)
    return True

# ==================== GitHub自動Push ====================
def push_to_github():
    try:
        repo_path = os.path.join(ROOT_DIR, "..")
        subprocess.run(["git", "-C", repo_path, "add", "data/*.csv"], check=True)
        result = subprocess.run(["git", "-C", repo_path, "diff", "--cached", "--quiet"])
        if result.returncode == 0:
            st.info("🟡 変更内容がないためGitHubへのPushはスキップされました")
            return
        subprocess.run(["git", "-C", repo_path, "commit", "-m", "update lottery data"], check=True)
        subprocess.run([
            "git", "-C", repo_path, "push",
            f"https://{GITHUB_TOKEN}@github.com/Naobro/lototop-app.git"
        ], check=True)
        st.success("✅ GitHubにPush完了しました")
        st.markdown("[🌐 GitHubで確認する](https://github.com/Naobro/lototop-app/tree/main/data)", unsafe_allow_html=True)
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Gitコマンド失敗: {e}")
    except Exception as e:
        st.error(f"❌ GitHub push失敗: {e}")

# ==================== 実行処理 ====================
if st.button("CSV保存＋GitHub反映"):
    if not text_input:
        st.warning("⚠️ 抽選結果を貼り付けてください")
    else:
        round_no = extract_round(text_input)
        date = extract_date(text_input)

        if lottery_type == "ロト6":
            nums = extract_numbers(text_input, 6)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no,
                "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(6)},
                "ボーナス数字": bonus[0] if bonus else "",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等", "5等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等", "5等"]},
                "キャリーオーバー": extract_carry(text_input)
            }
            record = clean_record_values(record)
            file_path = os.path.join(DATA_DIR, "loto6_50.csv")

        elif lottery_type == "ロト7":
            nums = extract_numbers(text_input, 7)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no,
                "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(7)},
                "BONUS数字1": bonus[0] if len(bonus) > 0 else "",
                "BONUS数字2": bonus[1] if len(bonus) > 1 else "",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等", "5等", "6等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等", "5等", "6等"]},
                "キャリーオーバー": extract_carry(text_input)
            }
            record = clean_record_values(record)
            file_path = os.path.join(DATA_DIR, "loto7_50.csv")

        elif lottery_type == "ミニロト":
            nums = extract_numbers(text_input, 5)
            bonus = extract_bonus(text_input)
            record = {
                "回号": round_no,
                "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(5)},
                "ボーナス数字": bonus[0] if bonus else "",
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["1等", "2等", "3等", "4等"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["1等", "2等", "3等", "4等"]}
            }
            record = clean_record_values(record)
            file_path = os.path.join(DATA_DIR, "miniloto_50.csv")

        elif lottery_type == "ナンバーズ3":
            nums = extract_numbers(text_input, 3)
            record = {
                "回号": round_no,
                "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(3)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セット・ストレート", "セット・ボックス", "ミニ"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セット・ストレート", "セット・ボックス", "ミニ"]}
            }
            record = clean_record_values(record)
            file_path = os.path.join(DATA_DIR, "numbers3_24.csv")

        elif lottery_type == "ナンバーズ4":
            nums = extract_numbers(text_input, 4)
            record = {
                "回号": round_no,
                "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(4)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セット・ストレート", "セット・ボックス"]},
                **{f"{g}賞金": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セット・ストレート", "セット・ボックス"]}
            }
            record = clean_record_values(record)
            file_path = os.path.join(DATA_DIR, "numbers4_24.csv")

        else:
            st.error("❌ 未対応の宝くじ種別です")
            file_path = ""

        if file_path and save_record(file_path, record):
            st.success(f"✅ {lottery_type} 第{round_no}回 保存完了")
            push_to_github()

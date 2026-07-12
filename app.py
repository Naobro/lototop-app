import os
import re
import pandas as pd
import streamlit as st
import subprocess  # ← dotenv の import は削除OK
# Cloud環境用：Streamlit Secrets から読み込む
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

# ==================== 初期設定 ====================
# --- 認証 ---
PASSWORD = "nao2480"  # ← あなたが自由に決めてOK

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("🔒 パスワードを入力してください", type="password")
    if pwd == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
st.set_page_config(page_title="宝くじCSV化＋GitHub保存", layout="wide")
st.title("抽選結果をコピペしてCSVに保存・GitHubへ反映")

lottery_type = st.selectbox("宝くじの種類を選んでください", ["ロト6", "ロト7", "ミニロト", "ナンバーズ3", "ナンバーズ4"])
text_input = st.text_area("みずほ銀行の抽選結果をコピペしてください", height=300)
# 初期化（ボタン未選択時のNameError対策）
file_path = ""
record = {}
columns = []

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
    # ✅ 等級名の統一（ナンバーズのカッコ表記に対応）
    grade_map = {
        "セットストレート": "セット（ストレート）",
        "セットボックス": "セット（ボックス）"
    }
    actual_grade = grade_map.get(grade, grade)

    # ✅ 該当なしパターンを事前チェック（例：1等 該当なし）
    pattern_none = fr"{actual_grade}[^\n\d]*該当なし"
    if re.search(pattern_none, text):
        return "0", "0"

    # ✅ カンマ対応＋柔軟な空白対応で抽出（口数／賞金）
    pattern = fr"{actual_grade}[^\d\n]*([\d,]+)口[^\d\n]*([\d,]+)円"
    match = re.search(pattern, text)

    # ✅ ミニロト用の特例処理（ズレ対策）
    if actual_grade == "ミニ" and (not match or match.group(1) == "0"):
        match = re.search(r"ミニ[ \t]*([\d,]+)口[ \t\n]*([\d,]+)円", text)

    # ✅ 通常パターンでマッチした場合
    if match:
        count, prize = match.groups()
        return count.replace(",", ""), prize.replace(",", "")

    # ✅ 最終手段：マッチしなければ「0口／0円」として返す
    return "0", "0"
def extract_carry(text):
    match = re.search(r'キャリーオーバー\s*([\d,]+)円', text)
    return match.group(1).replace(",", "") if match else "0"
def extract_numbers3(text):
    match = re.search(r'抽せん数字[：:\s]*([0-9]{3})', text)
    return list(match.group(1)) if match else ["0", "0", "0"]

def extract_numbers4(text):
    match = re.search(r'抽せん数字[：:\s]*([0-9]{4})', text)
    return list(match.group(1)) if match else ["0", "0", "0", "0"]

def save_record(file_path, record, columns):
    df = pd.DataFrame([record])
    df = df.reindex(columns=columns)
    if os.path.exists(file_path):
        old = pd.read_csv(file_path)
        old.columns = [col.replace("(", "（").replace(")", "）") for col in old.columns]
        if str(record["回号"]) in old["回号"].astype(str).values:
            st.warning("⚠️ 同じ回号のデータが存在します")
            return False
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(file_path, index=False)
    return True
def append_to_numbers_only_csv(full_file, round_no, numbers):
    """n3.csv / n4.csv に回号＋当選数字を追記（重複チェックあり）"""
    try:
        full_path = os.path.join(DATA_DIR, full_file)
        new_row = [round_no] + numbers
        df_new = pd.DataFrame([new_row])
        if os.path.exists(full_path):
            df_full = pd.read_csv(full_path, header=None)
            if str(round_no) in df_full.iloc[:, 0].astype(str).values:
                return  # 同じ回号はスキップ
            df_full = pd.concat([df_full, df_new], ignore_index=True)
        else:
            df_full = df_new
        df_full.to_csv(full_path, index=False, header=False)
    except Exception as e:
        st.error(f"{full_file}への追記に失敗しました: {e}")

def push_to_github():
    try:
        repo_path = os.path.join(ROOT_DIR, "..")

        # Gitユーザー設定（Cloud対応）
        subprocess.run(["git", "config", "--global", "user.email", "naobro@example.com"])
        subprocess.run(["git", "config", "--global", "user.name", "Naobro"])

        # ✅ GitHubトークンを使ったリモートURLを再設定
        subprocess.run([
            "git", "-C", repo_path, "remote", "set-url", "origin",
            f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/Naobro/lototop-app.git"
        ])

        # add, commit, push 実行
        subprocess.run(["git", "-C", repo_path, "add", "-A"], capture_output=True, text=True)
        result_commit = subprocess.run(
            ["git", "-C", repo_path, "commit", "--allow-empty", "-m", "強制コミット: CSV反映"],
            capture_output=True, text=True)

        if result_commit.returncode != 0 and "nothing to commit" not in result_commit.stderr:
            st.error(f"❌ git commit 失敗:\n{result_commit.stderr}")
            return

        result_push = subprocess.run(
            ["git", "-C", repo_path, "push", "origin", "main", "--force"],
            capture_output=True, text=True)

        if result_push.returncode != 0:
            st.error(f"❌ git push 失敗:\n{result_push.stderr}")
            return

        st.success("✅ GitHubに強制Push完了（認証成功）")

    except Exception as e:
        st.error(f"💥 想定外のエラー:\n{str(e)}")
# ==================== 実行処理 ====================
if st.button("CSV保存＋GitHub反映"):
    if not text_input:
        st.warning("⚠️ 抽選結果を貼り付けてください")
    else:
        # ✅ テキストの事前整形（空白統一、改行調整）
        text_input = re.sub(r'\s+', ' ', text_input)  # 複数空白→1つの空白へ
        text_input = text_input.replace('\n', ' ')    # 改行も空白化

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
                       "1���賞金", "2等賞金", "3等賞金", "4等賞金", "5等賞金", "キャリーオーバー"]

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
            nums = extract_numbers3(text_input)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(3)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セット（ストレート）", "セット（ボックス）", "ミニ"]},
                **{f"{g}当選金額": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セット（ストレート）", "セット（ボックス）", "ミニ"]}
            }
            file_path = os.path.join(DATA_DIR, "numbers3_24.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字",
                       "ストレート口数", "ボックス口数", "セット（ストレート）口数", "セット（ボックス）口数", "ミニ口数",
                       "ストレート当選金額", "ボックス当選金額", "セット（ストレート）当選金額", "セット（ボックス）当選金額", "ミニ当選金額"]

        elif lottery_type == "ナンバーズ4":
            nums = extract_numbers4(text_input)
            record = {
                "回号": round_no, "抽せん日": date,
                **{f"第{i+1}数字": nums[i] for i in range(4)},
                **{f"{g}口数": extract_prize_info(text_input, g)[0] for g in ["ストレート", "ボックス", "セット（ストレート）", "セット（ボックス）"]},
                **{f"{g}当選金額": extract_prize_info(text_input, g)[1] for g in ["ストレート", "ボックス", "セット（ストレート）", "セット（ボックス）"]}
            }
            file_path = os.path.join(DATA_DIR, "numbers4_24.csv")
            columns = ["回号", "抽せん日", "第1数字", "第2数字", "第3数字", "第4数字",
                       "ストレート口数", "ボックス口数", "セット（ストレート）口数", "セット（ボックス）口数",
                       "ストレート当選金額", "ボックス当選金額", "セット（ストレート）当選金額", "セット（ボックス）当選金額"]

if file_path and record and columns:
    if save_record(file_path, record, columns):
        st.success(f"✅ {lottery_type} 第{round_no}回 保存完了")

        if lottery_type == "ナンバーズ3":
            append_to_numbers_only_csv("n3.csv", record["回号"], [record["第1数字"], record["第2数字"], record["第3数字"]])
        if lottery_type == "ナンバーズ4":
            append_to_numbers_only_csv("n4.csv", record["回号"], [record["第1数字"], record["第2数字"], record["第3数字"], record["第4数字"]])

        push_to_github()

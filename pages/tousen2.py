import pandas as pd
import os
import subprocess

# === 設定 ===
REPO_DIR = "/Users/naokinishiyama/lototop-app"
GIT_USER = "Naobro"
GIT_EMAIL = "your-email@example.com"

lottery_type = "miniloto"  # "loto6", "loto7", "miniloto", "numbers3"
new_data = {
    "日付": "2024/05/20",
    "数字": [4, 7, 14, 21, 27],
    "ボーナス": [9]  # Bonus不要なら [] か None にする
}

# === ファイルと列構成マップ ===
config_map = {
    "loto6": {
        "path": "data/loto6_50.csv",
        "date_col": "日付",
        "kai_col": "回号",
        "digit_cols": ["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"],
        "bonus_cols": ["ボーナス数字"]
    },
    "loto7": {
        "path": "data/loto7_50.csv",
        "date_col": "日付",
        "kai_col": "回号",
        "digit_cols": ["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字", "第7数字"],
        "bonus_cols": ["BONUS数字1", "BONUS数字2"]
    },
    "miniloto": {
        "path": "data/miniloto_50.csv",
        "date_col": "日付",
        "kai_col": "回号",
        "digit_cols": ["第1数字", "第2数字", "第3数字", "第4数字", "第5数字"],
        "bonus_cols": ["ボーナス数字"]
    },
    "numbers3": {
        "path": "data/numbers3_24.csv",
        "date_col": "抽せん日",
        "kai_col": "回号",
        "digit_cols": ["第1数字", "第2数字", "第3数字"],
        "bonus_cols": []
    }
}

# === 構成取得
cfg = config_map[lottery_type]
csv_path = os.path.join(REPO_DIR, cfg["path"])

# === CSV読み込み
df = pd.read_csv(csv_path, encoding="utf-8-sig")
df.columns = [c.strip().replace('\ufeff', '') for c in df.columns]

# === 重複チェック
if new_data["日付"] in df[cfg["date_col"]].astype(str).values:
    print(f"{lottery_type}: すでに {new_data['日付']} のデータがあります")
    exit()

# === 次の回号
next_kai = int(df[cfg["kai_col"]].iloc[-1]) + 1

# === 追加行作成
row = {cfg["kai_col"]: next_kai, cfg["date_col"]: new_data["日付"]}
for i, col in enumerate(cfg["digit_cols"]):
    row[col] = new_data["数字"][i] if i < len(new_data["数字"]) else ""
for i, col in enumerate(cfg["bonus_cols"]):
    if new_data["ボーナス"]:
        row[col] = new_data["ボーナス"][i] if i < len(new_data["ボーナス"]) else ""
    else:
        row[col] = ""

# === DataFrame追加 & 保存
df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"{lottery_type}: {new_data['日付']} のデータをCSVに追加しました")

# === GitHub 反映
os.chdir(REPO_DIR)
subprocess.run(["git", "config", "user.name", GIT_USER])
subprocess.run(["git", "config", "user.email", GIT_EMAIL])
subprocess.run(["git", "add", cfg["path"]])
subprocess.run(["git", "commit", "-m", f"{lottery_type.upper()} {new_data['日付']} データ追加"])
subprocess.run(["git", "push"])
print(f"{lottery_type}: GitHubにプッシュ完了")
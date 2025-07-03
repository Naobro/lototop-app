import pandas as pd

# ヘッダーなしでCSVを読み込む（1行に3数字が入っている想定）
df = pd.read_csv("data/n3.csv", header=None)

# カラム名を設定
df.columns = ["第1数字", "第2数字", "第3数字"]

# 保存（上書き）
df.to_csv("data/n3.csv", index=False)

print("✅ 正常に3列構成に修正しました：data/n3.csv")

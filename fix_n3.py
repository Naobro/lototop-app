import pandas as pd

# 元のCSVを読み込み（例: 回号,当選数字）
df = pd.read_csv("data/n3.csv")

# "当選数字" 列を分割
df[['第1数字', '第2数字', '第3数字']] = df['当選数字'].str.split(',', expand=True).astype(int)

# 不要な列を削除（"当選数字"）
df = df.drop(columns=["当選数字"])

# 必要なら並び順を変更
df = df[['回号', '第1数字', '第2数字', '第3数字']]

# 上書き保存
df.to_csv("data/n3.csv", index=False)

print("✔️ 整形完了しました")
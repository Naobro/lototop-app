import pandas as pd

# 元のCSVを読み込み
df = pd.read_csv("data/n3.csv", header=None, names=["当選数字"])

# カンマで分割し、3列に展開
df[['第1数字', '第2数字', '第3数字']] = df['当選数字'].str.split(',', expand=True).astype(int)

# 不要な元列を削除
df.drop(columns=['当選数字'], inplace=True)

# 整形したデータを上書き保存
df.to_csv("data/n3.csv", index=False)

print("✅ 整形完了: data/n3.csv を更新しました")
